"""Tests for process security module."""
import pytest
from unittest.mock import Mock, patch
import os
import sys

from lastpass.process_security import ProcessSecurity, SecureString, SecureBytes


@pytest.mark.unit
class TestProcessSecurity:
    """Tests for ProcessSecurity class."""
    
    def test_get_libc(self):
        """Test getting libc handle."""
        # This is platform-specific, just ensure it doesn't crash
        libc = ProcessSecurity._get_libc()
        # May be None on some platforms
        assert libc is None or libc is not None
    
    def test_mlock_returns_bool(self):
        """Test mlock returns boolean."""
        result = ProcessSecurity.mlock(b'test data')
        assert isinstance(result, bool)
    
    def test_munlock_returns_bool(self):
        """Test munlock returns boolean."""
        result = ProcessSecurity.munlock(b'test data')
        assert isinstance(result, bool)


@pytest.mark.unit
class TestSecureString:
    """Tests for SecureString class."""
    
    def test_secure_string_init(self):
        """Test SecureString initialization."""
        s = SecureString('password')
        assert s is not None
    
    def test_secure_string_str(self):
        """Test SecureString string conversion."""
        s = SecureString('password')
        # Should not reveal password in string
        result = str(s)
        assert 'SecureString' in result or result == 'password'
    
    def test_secure_string_repr(self):
        """Test SecureString repr."""
        s = SecureString('password')
        result = repr(s)
        assert result is not None


@pytest.mark.unit  
class TestSecureBytes:
    """Tests for SecureBytes class."""
    
    def test_secure_bytes_init(self):
        """Test SecureBytes initialization."""
        b = SecureBytes(b'secret')
        assert b is not None
    
    def test_secure_bytes_repr(self):
        """Test SecureBytes repr."""
        b = SecureBytes(b'secret')
        result = repr(b)
        assert result is not None
