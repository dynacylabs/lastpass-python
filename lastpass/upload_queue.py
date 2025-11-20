"""
Upload queue for reliable background synchronization
"""

import os
import time
import json
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .config import Config
from .cipher import encrypt_aes256_cbc_base64, decrypt_aes256_cbc_base64


class UploadQueue:
    """Background queue for reliable server updates"""
    
    MAX_RETRIES = 5
    FAIL_MAX_AGE_DAYS = 14
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._queue_dir = self._get_queue_dir()
        self._lock_dir = self._queue_dir / "locks"
        self._fail_dir = self._queue_dir / "failed"
    
    def _get_queue_dir(self) -> Path:
        """Get queue directory path"""
        return self.config.config_dir / "upload-queue"
    
    def _ensure_dirs(self) -> None:
        """Ensure queue directories exist"""
        self._queue_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._lock_dir.mkdir(exist_ok=True, mode=0o700)
        self._fail_dir.mkdir(exist_ok=True, mode=0o700)
    
    def enqueue(self, endpoint: str, params: Dict[str, Any], key: bytes) -> None:
        """
        Add operation to upload queue
        
        Args:
            endpoint: API endpoint path
            params: Request parameters
            key: Encryption key for queue entry
        """
        self._ensure_dirs()
        
        # Create queue entry
        entry = {
            'endpoint': endpoint,
            'params': params,
            'timestamp': time.time()
        }
        
        # Serialize and encrypt
        entry_json = json.dumps(entry)
        encrypted = encrypt_aes256_cbc_base64(entry_json, key)
        
        # Find unique filename
        serial = 0
        while serial < 10000:
            timestamp = int(time.time())
            filename = f"{timestamp}{serial:04d}"
            filepath = self._queue_dir / filename
            
            if not filepath.exists():
                break
            serial += 1
        
        if serial >= 10000:
            raise RuntimeError("No available upload queue slots")
        
        # Write encrypted entry
        with open(filepath, 'w') as f:
            f.write(encrypted)
        
        os.chmod(filepath, 0o600)
    
    def _get_next_entry(self, key: bytes) -> Optional[tuple]:
        """
        Get next queue entry to process
        
        Args:
            key: Decryption key
        
        Returns:
            Tuple of (filename, entry_dict, lock_file) or None
        """
        self._ensure_dirs()
        
        # Get all queue files
        queue_files = sorted([f for f in self._queue_dir.iterdir() 
                            if f.is_file() and not f.name.startswith('.')])
        
        for filepath in queue_files:
            # Try to acquire lock
            lock_file = self._lock_dir / filepath.name
            try:
                # Create lock file atomically
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
            except FileExistsError:
                # Already locked
                continue
            
            # Read and decrypt entry
            try:
                with open(filepath, 'r') as f:
                    encrypted = f.read()
                
                decrypted = decrypt_aes256_cbc_base64(encrypted, key)
                entry = json.loads(decrypted)
                
                return (filepath.name, entry, lock_file)
            except Exception:
                # Failed to decrypt/parse, skip
                lock_file.unlink(missing_ok=True)
                continue
        
        return None
    
    def _drop_entry(self, filename: str) -> None:
        """
        Remove entry from queue
        
        Args:
            filename: Queue entry filename
        """
        filepath = self._queue_dir / filename
        lock_file = self._lock_dir / filename
        
        filepath.unlink(missing_ok=True)
        lock_file.unlink(missing_ok=True)
    
    def _mark_failed(self, filename: str) -> None:
        """
        Mark entry as failed
        
        Args:
            filename: Queue entry filename
        """
        filepath = self._queue_dir / filename
        fail_file = self._fail_dir / filename
        lock_file = self._lock_dir / filename
        
        try:
            if filepath.exists():
                filepath.rename(fail_file)
        except Exception:
            pass
        
        lock_file.unlink(missing_ok=True)
    
    def _cleanup_failures(self) -> None:
        """Remove old failed entries"""
        self._ensure_dirs()
        
        cutoff = datetime.now() - timedelta(days=self.FAIL_MAX_AGE_DAYS)
        
        for fail_file in self._fail_dir.iterdir():
            if fail_file.is_file():
                try:
                    mtime = datetime.fromtimestamp(fail_file.stat().st_mtime)
                    if mtime < cutoff:
                        fail_file.unlink()
                except Exception:
                    pass
    
    def upload_all(self, session, key: bytes) -> None:
        """
        Process all queued uploads
        
        Args:
            session: Active LastPass session
            key: Decryption key
        """
        from .http import HttpClient
        
        self._cleanup_failures()
        
        http = HttpClient()
        
        while True:
            entry_info = self._get_next_entry(key)
            if not entry_info:
                break
            
            filename, entry, lock_file = entry_info
            endpoint = entry['endpoint']
            params = entry['params']
            
            # Try upload with exponential backoff
            success = False
            for attempt in range(self.MAX_RETRIES):
                try:
                    if attempt > 0:
                        # Exponential backoff: 1, 2, 4, 8, 16 seconds
                        backoff = 2 ** (attempt - 1)
                        time.sleep(backoff)
                    
                    # Make request
                    response = http.post(
                        f"https://{session.server}/{endpoint}",
                        params,
                        session=session
                    )
                    
                    # Check if successful
                    if response.status_code == 200:
                        success = True
                        break
                    elif response.status_code >= 500:
                        # Server error, retry
                        continue
                    else:
                        # Client error, don't retry
                        break
                except Exception:
                    # Network error, retry
                    continue
            
            # Handle result
            if success:
                self._drop_entry(filename)
            else:
                self._mark_failed(filename)
            
            # Release lock
            lock_file.unlink(missing_ok=True)
    
    def is_running(self) -> bool:
        """Check if queue processor is running"""
        pid_file = self._queue_dir / "processor.pid"
        
        if not pid_file.exists():
            return False
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # Process doesn't exist
            pid_file.unlink(missing_ok=True)
            return False
    
    def ensure_running(self, session, key: bytes) -> None:
        """
        Ensure queue processor is running
        
        Args:
            session: Active LastPass session
            key: Decryption key
        """
        if self.is_running():
            return
        
        # Start background processor
        pid = os.fork()
        if pid == 0:
            # Child process
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
                
                # Write PID file
                pid_file = self._queue_dir / "processor.pid"
                with open(pid_file, 'w') as f:
                    f.write(str(os.getpid()))
                
                # Set up signal handlers
                def cleanup_handler(signum, frame):
                    pid_file.unlink(missing_ok=True)
                    os._exit(0)
                
                signal.signal(signal.SIGHUP, cleanup_handler)
                signal.signal(signal.SIGINT, cleanup_handler)
                signal.signal(signal.SIGQUIT, cleanup_handler)
                signal.signal(signal.SIGTERM, cleanup_handler)
                signal.signal(signal.SIGALRM, cleanup_handler)
                
                # Process queue
                self.upload_all(session, key)
                
                # Cleanup
                pid_file.unlink(missing_ok=True)
            except Exception:
                pass
            
            os._exit(0)
    
    def kill(self) -> None:
        """Kill running queue processor"""
        pid_file = self._queue_dir / "processor.pid"
        
        if not pid_file.exists():
            return
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
            
            pid_file.unlink(missing_ok=True)
        except (OSError, ValueError):
            pass
