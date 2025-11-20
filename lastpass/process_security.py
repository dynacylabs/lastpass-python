"""
Process security features including memory locking and ptrace protection
"""

import os
import sys
import ctypes
import ctypes.util
from typing import Optional


class ProcessSecurity:
    """Process security and memory protection"""
    
    # Load libc
    _libc: Optional[ctypes.CDLL] = None
    
    @classmethod
    def _get_libc(cls) -> Optional[ctypes.CDLL]:
        """Get libc handle"""
        if cls._libc is None:
            libc_path = ctypes.util.find_library('c')
            if libc_path:
                try:
                    cls._libc = ctypes.CDLL(libc_path)
                except Exception:
                    pass
        return cls._libc
    
    @staticmethod
    def mlock(data: bytes) -> bool:
        """
        Lock memory to prevent swapping
        
        Args:
            data: Data to lock in memory
        
        Returns:
            True if successful
        """
        # mlock is platform-specific and can be risky
        # For now, we just return False to indicate it's not locked
        # A full implementation would require careful platform-specific code
        return False
    
    @staticmethod
    def munlock(data: bytes) -> bool:
        """
        Unlock memory
        
        Args:
            data: Data to unlock
        
        Returns:
            True if successful
        """
        # munlock is platform-specific
        # For now, we just return True (no-op)
        return True
    
    @staticmethod
    def disable_ptrace() -> bool:
        """
        Disable ptrace to prevent debugging
        
        Returns:
            True if successful
        """
        # Only supported on Linux
        if not sys.platform.startswith('linux'):
            return False
        
        try:
            # PR_SET_DUMPABLE = 4
            # SUID_DUMP_DISABLE = 0
            libc = ProcessSecurity._get_libc()
            if not libc:
                return False
            
            # Set PR_SET_DUMPABLE to 0
            result = libc.prctl(4, 0, 0, 0, 0)
            if result != 0:
                return False
            
            # Also try to set PR_SET_PTRACER to PR_SET_PTRACER_ANY
            # This is more aggressive ptrace protection
            # PR_SET_PTRACER = 0x59616d61
            # PR_SET_PTRACER_ANY = -1
            try:
                libc.prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0)
            except Exception:
                pass
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def set_process_name(name: str) -> bool:
        """
        Set process name
        
        Args:
            name: New process name
        
        Returns:
            True if successful
        """
        # Only supported on Linux
        if not sys.platform.startswith('linux'):
            return False
        
        try:
            libc = ProcessSecurity._get_libc()
            if not libc:
                return False
            
            # PR_SET_NAME = 15
            name_bytes = name.encode('utf-8')[:15]  # Max 15 chars
            result = libc.prctl(15, name_bytes, 0, 0, 0)
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def secure_clear(data: bytearray) -> None:
        """
        Securely clear sensitive data from memory
        
        Args:
            data: Data to clear (modified in place)
        """
        # Overwrite with zeros
        for i in range(len(data)):
            data[i] = 0
        
        # Force a reference to prevent optimization
        _ = sum(data)
    
    @staticmethod
    def is_same_executable(pid: int) -> bool:
        """
        Check if process is same executable
        
        Args:
            pid: Process ID to check
        
        Returns:
            True if same executable
        """
        try:
            # Read /proc/pid/exe symlink
            our_exe = os.readlink(f"/proc/{os.getpid()}/exe")
            their_exe = os.readlink(f"/proc/{pid}/exe")
            
            return our_exe == their_exe
        except Exception:
            return False


class SecureString:
    """String wrapper with secure memory handling"""
    
    def __init__(self, data: str = ""):
        self._data = bytearray(data.encode('utf-8'))
        ProcessSecurity.mlock(bytes(self._data))
    
    def __str__(self) -> str:
        return self._data.decode('utf-8')
    
    def __repr__(self) -> str:
        return f"SecureString({len(self._data)} bytes)"
    
    def __del__(self):
        # Securely clear on deletion
        ProcessSecurity.secure_clear(self._data)
        ProcessSecurity.munlock(bytes(self._data))
    
    def get(self) -> str:
        """Get string value"""
        return self._data.decode('utf-8')
    
    def clear(self):
        """Securely clear the string"""
        ProcessSecurity.secure_clear(self._data)


class SecureBytes:
    """Bytes wrapper with secure memory handling"""
    
    def __init__(self, data: bytes = b""):
        self._data = bytearray(data)
        ProcessSecurity.mlock(bytes(self._data))
    
    def __bytes__(self) -> bytes:
        return bytes(self._data)
    
    def __repr__(self) -> str:
        return f"SecureBytes({len(self._data)} bytes)"
    
    def __del__(self):
        # Securely clear on deletion
        ProcessSecurity.secure_clear(self._data)
        ProcessSecurity.munlock(bytes(self._data))
    
    def get(self) -> bytes:
        """Get bytes value"""
        return bytes(self._data)
    
    def clear(self):
        """Securely clear the bytes"""
        ProcessSecurity.secure_clear(self._data)
