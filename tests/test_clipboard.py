"""
Tests for clipboard functionality
"""

import os
import pytest
from unittest.mock import Mock, patch

from lastpass.clipboard import ClipboardManager


class TestClipboardManager:
    """Test clipboard functionality"""
    
    def test_get_clipboard_timeout_default(self):
        """Test default clipboard timeout"""
        timeout = ClipboardManager.get_clipboard_timeout()
        assert timeout == 45
    
    def test_get_clipboard_timeout_env(self):
        """Test clipboard timeout from environment"""
        with patch.dict(os.environ, {'LPASS_CLIP_CLEAR_TIME': '30'}):
            timeout = ClipboardManager.get_clipboard_timeout()
            assert timeout == 30
    
    def test_get_clipboard_timeout_disabled(self):
        """Test clipboard timeout disabled"""
        with patch.dict(os.environ, {'LPASS_CLIP_CLEAR_TIME': '0'}):
            timeout = ClipboardManager.get_clipboard_timeout()
            assert timeout is None
    
    @patch('subprocess.Popen')
    def test_copy_custom_command(self, mock_popen):
        """Test custom clipboard command"""
        mock_process = Mock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        with patch.dict(os.environ, {'LPASS_CLIPBOARD_COMMAND': 'custom-clipboard'}):
            result = ClipboardManager.copy_to_clipboard("test text")
            assert result is True
    
    @patch('subprocess.Popen')
    def test_copy_xclip(self, mock_popen):
        """Test xclip clipboard"""
        mock_process = Mock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        result = ClipboardManager._try_command(['xclip', '-selection', 'clipboard'], 'test')
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
