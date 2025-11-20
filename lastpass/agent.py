"""
Agent system for secure key caching
"""

import os
import socket
import struct
import signal
import time
import getpass
from pathlib import Path
from typing import Optional
import threading

from .config import Config
from .kdf import kdf_decryption_key
from .cipher import decrypt_aes256_cbc_base64


class Agent:
    """Background agent for caching decryption keys"""
    
    VERIFICATION_STRING = "`lpass` was written by LastPass.\n"
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._socket_path = self._get_socket_path()
    
    def _get_socket_path(self) -> Path:
        """Get path to agent socket"""
        config_dir = self.config.config_dir
        return config_dir / "agent.sock"
    
    def _get_timeout(self) -> int:
        """Get agent timeout from environment (seconds)"""
        timeout_str = os.environ.get('LPASS_AGENT_TIMEOUT', '3600')
        try:
            return int(timeout_str)
        except ValueError:
            return 3600  # 1 hour default
    
    def _is_disabled(self) -> bool:
        """Check if agent is disabled"""
        return os.environ.get('LPASS_AGENT_DISABLE') == '1'
    
    def is_running(self) -> bool:
        """Check if agent is running"""
        if not self._socket_path.exists():
            return False
        
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(str(self._socket_path))
            sock.close()
            return True
        except (ConnectionRefusedError, FileNotFoundError):
            return False
    
    def get_decryption_key(self) -> Optional[bytes]:
        """
        Get decryption key from agent or plaintext storage
        
        Returns:
            32-byte decryption key or None if not available
        """
        # Check for plaintext key first
        if self._has_plaintext_key():
            key = self._load_plaintext_key()
            if key and self._verify_key(key):
                return key
            else:
                # Invalid key, remove it
                self.config.delete('plaintext_key')
        
        # Try to get from agent
        key = self._ask_agent()
        if key and self._verify_key(key):
            return key
        
        return None
    
    def _has_plaintext_key(self) -> bool:
        """Check if plaintext key exists"""
        return self.config.get('plaintext_key') is not None
    
    def _load_plaintext_key(self) -> Optional[bytes]:
        """Load key from plaintext storage"""
        key_hex = self.config.get('plaintext_key')
        if not key_hex:
            return None
        
        try:
            return bytes.fromhex(key_hex)
        except ValueError:
            return None
    
    def _verify_key(self, key: bytes) -> bool:
        """Verify key is correct by checking verification string"""
        verify_encrypted = self.config.get('verify')
        if not verify_encrypted:
            return False
        
        try:
            decrypted = decrypt_aes256_cbc_base64(verify_encrypted, key)
            return decrypted == self.VERIFICATION_STRING
        except Exception:
            return False
    
    def _ask_agent(self) -> Optional[bytes]:
        """Ask running agent for key"""
        if not self.is_running():
            return None
        
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(str(self._socket_path))
            
            # Send PID
            pid = os.getpid()
            sock.sendall(struct.pack('i', pid))
            
            # Receive key
            key = sock.recv(32)
            sock.close()
            
            if len(key) == 32:
                return key
        except Exception:
            pass
        
        return None
    
    def save(self, username: str, iterations: int, key: bytes) -> None:
        """
        Save key to agent
        
        Args:
            username: LastPass username
            iterations: KDF iterations
            key: 32-byte decryption key
        """
        # Save metadata
        self.config.set('iterations', iterations)
        self.config.set('username', username)
        
        # Save verification string
        from .cipher import encrypt_aes256_cbc_base64
        verify_encrypted = encrypt_aes256_cbc_base64(self.VERIFICATION_STRING, key)
        self.config.set('verify', verify_encrypted)
        
        # Start agent if not disabled
        if not self._is_disabled() and not self._has_plaintext_key():
            self.start(key)
    
    def start(self, key: bytes) -> None:
        """
        Start agent daemon in background
        
        Args:
            key: 32-byte decryption key to cache
        """
        if self._is_disabled():
            return
        
        if self._has_plaintext_key():
            return
        
        # Kill existing agent
        self.kill()
        
        # Fork daemon process
        pid = os.fork()
        if pid == 0:
            # Child process - become daemon
            try:
                # Detach from parent
                os.setsid()
                os.chdir('/')
                
                # Redirect standard file descriptors
                devnull = os.open(os.devnull, os.O_RDWR)
                os.dup2(devnull, 0)
                os.dup2(devnull, 1)
                os.dup2(devnull, 2)
                os.close(devnull)
                
                # Run agent
                self._run_daemon(key)
            except Exception:
                os._exit(1)
            
            os._exit(0)
    
    def _run_daemon(self, key: bytes) -> None:
        """
        Run agent daemon (called in child process)
        
        Args:
            key: Decryption key to cache
        """
        # Set up signal handlers for cleanup
        def cleanup_handler(signum, frame):
            if self._socket_path.exists():
                self._socket_path.unlink()
            os._exit(0)
        
        signal.signal(signal.SIGHUP, cleanup_handler)
        signal.signal(signal.SIGINT, cleanup_handler)
        signal.signal(signal.SIGQUIT, cleanup_handler)
        signal.signal(signal.SIGTERM, cleanup_handler)
        
        # Set up timeout alarm
        timeout = self._get_timeout()
        if timeout > 0:
            signal.signal(signal.SIGALRM, cleanup_handler)
            signal.alarm(timeout)
        
        # Create socket
        if self._socket_path.exists():
            self._socket_path.unlink()
        
        self._socket_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(str(self._socket_path))
        sock.listen(16)
        
        # Set socket permissions
        os.chmod(self._socket_path, 0o600)
        
        # Accept connections
        while True:
            try:
                client_sock, _ = sock.accept()
                
                # Verify client credentials
                try:
                    # Receive PID from client
                    pid_bytes = client_sock.recv(4)
                    if len(pid_bytes) != 4:
                        client_sock.close()
                        continue
                    
                    # Get client UID/GID using socket credentials
                    creds = client_sock.getsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_PEERCRED,
                        struct.calcsize('3i')
                    )
                    client_pid, client_uid, client_gid = struct.unpack('3i', creds)
                    
                    # Verify same user
                    if client_uid != os.getuid() or client_gid != os.getgid():
                        client_sock.close()
                        continue
                    
                    # Send key
                    client_sock.sendall(key)
                except Exception:
                    pass
                finally:
                    client_sock.close()
            except Exception:
                break
        
        sock.close()
        if self._socket_path.exists():
            self._socket_path.unlink()
    
    def kill(self) -> None:
        """Kill running agent"""
        if not self.is_running():
            return
        
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(str(self._socket_path))
            
            # Send termination signal by closing immediately
            sock.close()
            
            # Try to read PID from socket file if possible
            # and send SIGTERM
            time.sleep(0.1)
            
            # Remove socket file
            if self._socket_path.exists():
                self._socket_path.unlink()
        except Exception:
            pass
    
    def load_key(self) -> Optional[bytes]:
        """
        Load key by prompting for password
        
        Returns:
            32-byte decryption key or None
        """
        username = self.config.get('username')
        iterations = self.config.get('iterations')
        
        if not username or not iterations:
            return None
        
        # Prompt for password
        password = getpass.getpass(f"Master Password for {username}: ")
        if not password:
            return None
        
        # Derive key
        key = kdf_decryption_key(username, password, iterations)
        
        # Verify key
        if not self._verify_key(key):
            return None
        
        return key
