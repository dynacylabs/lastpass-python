"""Tests for process_security module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import ctypes

from lastpass.process_security import ProcessSecurity, SecureString, SecureBytes


@pytest.mark.unit
class TestProcessSecurityGetLibc:
    """Tests for ProcessSecurity._get_libc()."""
    
    def test_get_libc_cached(self):
        """Test libc handle is cached."""
        ProcessSecurity._libc = None
        
        with patch('ctypes.util.find_library', return_value='/lib/libc.so'):
            with patch('ctypes.CDLL') as mock_cdll:
                mock_lib = Mock()
                mock_cdll.return_value = mock_lib
                
                libc1 = ProcessSecurity._get_libc()
                libc2 = ProcessSecurity._get_libc()
                
                assert libc1 is libc2
                assert mock_cdll.call_count == 1
    
    def test_get_libc_not_found(self):
        """Test when libc not found."""
        ProcessSecurity._libc = None
        
        with patch('ctypes.util.find_library', return_value=None):
            libc = ProcessSecurity._get_libc()
            assert libc is None
    
    def test_get_libc_load_error(self):
        """Test when libc load fails."""
        ProcessSecurity._libc = None
        
        with patch('ctypes.util.find_library', return_value='/lib/libc.so'):
            with patch('ctypes.CDLL', side_effect=Exception("Load failed")):
                libc = ProcessSecurity._get_libc()
                assert libc is None


@pytest.mark.unit
class TestMlock:
    """Tests for ProcessSecurity.mlock()."""
    
    def test_mlock_returns_false(self):
        """Test mlock currently returns False."""
        data = b'sensitive data'
        result = ProcessSecurity.mlock(data)
        # Current implementation returns False
        assert result is False
    
    def test_mlock_accepts_bytes(self):
        """Test mlock accepts bytes data."""
        data = b'test data'
        # Should not raise exception
        ProcessSecurity.mlock(data)


@pytest.mark.unit
class TestMunlock:
    """Tests for ProcessSecurity.munlock()."""
    
    def test_munlock_returns_true(self):
        """Test munlock returns True."""
        data = b'sensitive data'
        result = ProcessSecurity.munlock(data)
        assert result is True
    
    def test_munlock_accepts_bytes(self):
        """Test munlock accepts bytes data."""
        data = b'test data'
        # Should not raise exception
        ProcessSecurity.munlock(data)


@pytest.mark.unit
class TestDisablePtrace:
    """Tests for ProcessSecurity.disable_ptrace()."""
    
    @patch('sys.platform', 'darwin')
    def test_disable_ptrace_not_linux(self):
        """Test disable_ptrace returns False on non-Linux."""
        result = ProcessSecurity.disable_ptrace()
        assert result is False
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_disable_ptrace_no_libc(self, mock_get_libc):
        """Test disable_ptrace when libc not available."""
        mock_get_libc.return_value = None
        result = ProcessSecurity.disable_ptrace()
        assert result is False
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_disable_ptrace_success(self, mock_get_libc):
        """Test successful disable_ptrace."""
        mock_libc = Mock()
        mock_libc.prctl.return_value = 0
        mock_get_libc.return_value = mock_libc
        
        result = ProcessSecurity.disable_ptrace()
        
        assert result is True
        # Should have called prctl with PR_SET_DUMPABLE
        mock_libc.prctl.assert_called()
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_disable_ptrace_prctl_fails(self, mock_get_libc):
        """Test disable_ptrace when prctl fails."""
        mock_libc = Mock()
        mock_libc.prctl.return_value = -1
        mock_get_libc.return_value = mock_libc
        
        result = ProcessSecurity.disable_ptrace()
        
        assert result is False
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_disable_ptrace_exception(self, mock_get_libc):
        """Test disable_ptrace handles exceptions."""
        mock_libc = Mock()
        mock_libc.prctl.side_effect = Exception("prctl failed")
        mock_get_libc.return_value = mock_libc
        
        result = ProcessSecurity.disable_ptrace()
        
        assert result is False


@pytest.mark.unit
class TestSetProcessName:
    """Tests for ProcessSecurity.set_process_name()."""
    
    @patch('sys.platform', 'darwin')
    def test_set_process_name_not_linux(self):
        """Test set_process_name returns False on non-Linux."""
        result = ProcessSecurity.set_process_name('test')
        assert result is False
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_set_process_name_no_libc(self, mock_get_libc):
        """Test set_process_name when libc not available."""
        mock_get_libc.return_value = None
        result = ProcessSecurity.set_process_name('test')
        assert result is False
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_set_process_name_success(self, mock_get_libc):
        """Test successful set_process_name."""
        mock_libc = Mock()
        mock_libc.prctl.return_value = 0
        mock_get_libc.return_value = mock_libc
        
        result = ProcessSecurity.set_process_name('myprocess')
        
        assert result is True
        mock_libc.prctl.assert_called_once()
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_set_process_name_truncates(self, mock_get_libc):
        """Test set_process_name truncates long names."""
        mock_libc = Mock()
        mock_libc.prctl.return_value = 0
        mock_get_libc.return_value = mock_libc
        
        long_name = 'a' * 100
        result = ProcessSecurity.set_process_name(long_name)
        
        assert result is True
        # Check that name was truncated to 15 chars
        call_args = mock_libc.prctl.call_args[0]
        assert len(call_args[1]) <= 15
    
    @patch('sys.platform', 'linux')
    @patch.object(ProcessSecurity, '_get_libc')
    def test_set_process_name_exception(self, mock_get_libc):
        """Test set_process_name handles exceptions."""
        mock_libc = Mock()
        mock_libc.prctl.side_effect = Exception("prctl failed")
        mock_get_libc.return_value = mock_libc
        
        result = ProcessSecurity.set_process_name('test')
        
        assert result is False


@pytest.mark.unit
class TestSecureClear:
    """Tests for ProcessSecurity.secure_clear()."""
    
    def test_secure_clear_zeros_data(self):
        """Test secure_clear zeros all bytes."""
        data = bytearray(b'sensitive data')
        ProcessSecurity.secure_clear(data)
        
        # All bytes should be zero
        assert all(b == 0 for b in data)
    
    def test_secure_clear_empty(self):
        """Test secure_clear with empty data."""
        data = bytearray()
        # Should not raise exception
        ProcessSecurity.secure_clear(data)
    
    def test_secure_clear_modifies_in_place(self):
        """Test secure_clear modifies data in place."""
        data = bytearray(b'test')
        original_id = id(data)
        ProcessSecurity.secure_clear(data)
        
        # Should be same object
        assert id(data) == original_id
        assert data == bytearray(b'\x00\x00\x00\x00')


@pytest.mark.unit
class TestIsSameExecutable:
    """Tests for ProcessSecurity.is_same_executable()."""
    
    @patch('os.readlink')
    def test_is_same_executable_true(self, mock_readlink):
        """Test is_same_executable when same."""
        mock_readlink.return_value = '/usr/bin/python3'
        
        result = ProcessSecurity.is_same_executable(12345)
        
        assert result is True
        assert mock_readlink.call_count == 2
    
    @patch('os.readlink')
    def test_is_same_executable_false(self, mock_readlink):
        """Test is_same_executable when different."""
        mock_readlink.side_effect = ['/usr/bin/python3', '/usr/bin/bash']
        
        result = ProcessSecurity.is_same_executable(12345)
        
        assert result is False
    
    @patch('os.readlink')
    def test_is_same_executable_error(self, mock_readlink):
        """Test is_same_executable handles errors."""
        mock_readlink.side_effect = OSError("No such process")
        
        result = ProcessSecurity.is_same_executable(12345)
        
        assert result is False


@pytest.mark.unit
class TestSecureString:
    """Tests for SecureString class."""
    
    def test_secure_string_init(self):
        """Test SecureString initialization."""
        s = SecureString("password")
        assert str(s) == "password"
    
    def test_secure_string_empty(self):
        """Test SecureString with empty string."""
        s = SecureString()
        assert str(s) == ""
    
    def test_secure_string_get(self):
        """Test SecureString.get() method."""
        s = SecureString("test")
        assert s.get() == "test"
    
    def test_secure_string_repr(self):
        """Test SecureString repr."""
        s = SecureString("password")
        repr_str = repr(s)
        assert "SecureString" in repr_str
        assert "8 bytes" in repr_str
        # Password should not be in repr
        assert "password" not in repr_str
    
    def test_secure_string_clear(self):
        """Test SecureString.clear() method."""
        s = SecureString("password")
        s.clear()
        # After clear, data should be zeros
        assert all(b == 0 for b in s._data)
    
    @patch.object(ProcessSecurity, 'mlock')
    @patch.object(ProcessSecurity, 'munlock')
    def test_secure_string_mlock_called(self, mock_munlock, mock_mlock):
        """Test SecureString calls mlock."""
        s = SecureString("test")
        mock_mlock.assert_called_once()
    
    @patch.object(ProcessSecurity, 'secure_clear')
    @patch.object(ProcessSecurity, 'munlock')
    def test_secure_string_del_clears(self, mock_munlock, mock_clear):
        """Test SecureString clears on deletion."""
        s = SecureString("password")
        s.__del__()
        mock_clear.assert_called_once()
        mock_munlock.assert_called_once()


@pytest.mark.unit
class TestSecureBytes:
    """Tests for SecureBytes class."""
    
    def test_secure_bytes_init(self):
        """Test SecureBytes initialization."""
        b = SecureBytes(b"data")
        assert bytes(b) == b"data"
    
    def test_secure_bytes_empty(self):
        """Test SecureBytes with empty bytes."""
        b = SecureBytes()
        assert bytes(b) == b""
    
    def test_secure_bytes_get(self):
        """Test SecureBytes.get() method."""
        b = SecureBytes(b"test")
        assert b.get() == b"test"
    
    def test_secure_bytes_repr(self):
        """Test SecureBytes repr."""
        b = SecureBytes(b"secret")
        repr_str = repr(b)
        assert "SecureBytes" in repr_str
        assert "6 bytes" in repr_str
        # Data should not be in repr
        assert "secret" not in repr_str
    
    def test_secure_bytes_clear(self):
        """Test SecureBytes.clear() method."""
        b = SecureBytes(b"secret")
        b.clear()
        # After clear, data should be zeros
        assert all(byte == 0 for byte in b._data)
    
    @patch.object(ProcessSecurity, 'mlock')
    @patch.object(ProcessSecurity, 'munlock')
    def test_secure_bytes_mlock_called(self, mock_munlock, mock_mlock):
        """Test SecureBytes calls mlock."""
        b = SecureBytes(b"data")
        mock_mlock.assert_called_once()
    
    @patch.object(ProcessSecurity, 'secure_clear')
    @patch.object(ProcessSecurity, 'munlock')
    def test_secure_bytes_del_clears(self, mock_munlock, mock_clear):
        """Test SecureBytes clears on deletion."""
        b = SecureBytes(b"secret")
        b.__del__()
        mock_clear.assert_called_once()
        mock_munlock.assert_called_once()


@pytest.mark.unit
class TestSecureStringIntegration:
    """Integration tests for SecureString."""
    
    def test_secure_string_lifecycle(self):
        """Test SecureString full lifecycle."""
        s = SecureString("password123")
        
        # Can get value
        assert s.get() == "password123"
        assert str(s) == "password123"
        
        # Can clear
        s.clear()
        # Data is zeroed (but get() will return empty string from zeros)
        
        # String representation doesn't leak data
        assert "password" not in repr(s)


@pytest.mark.unit
class TestSecureBytesIntegration:
    """Integration tests for SecureBytes."""
    
    def test_secure_bytes_lifecycle(self):
        """Test SecureBytes full lifecycle."""
        b = SecureBytes(b"secret_key_123")
        
        # Can get value
        assert b.get() == b"secret_key_123"
        assert bytes(b) == b"secret_key_123"
        
        # Can clear
        b.clear()
        # Data is zeroed
        
        # Bytes representation doesn't leak data
        assert b"secret" not in repr(b).encode()
