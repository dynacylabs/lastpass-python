"""Tests for browser module (opening URLs in browser)."""
import pytest
from unittest.mock import patch, Mock
import os
import subprocess

from lastpass.browser import open_url, get_browser_command


@pytest.mark.unit
class TestOpenUrl:
    """Test open_url function."""
    
    @patch.dict(os.environ, {'BROWSER': '/usr/bin/firefox'})
    @patch('subprocess.Popen')
    def test_open_url_with_browser_env_variable(self, mock_popen):
        """Test opening URL with BROWSER environment variable set."""
        result = open_url('https://example.com')
        assert result is True
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert 'https://example.com' in call_args
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('webbrowser.open')
    def test_open_url_with_system_default(self, mock_webbrowser):
        """Test opening URL with system default browser."""
        mock_webbrowser.return_value = True
        result = open_url('https://example.com')
        assert result is True
        mock_webbrowser.assert_called_once_with('https://example.com')
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('webbrowser.open')
    def test_open_url_failure(self, mock_webbrowser):
        """Test open_url when all methods fail."""
        mock_webbrowser.side_effect = Exception("Failed to open")
        result = open_url('https://example.com')
        assert result is False
    
    @patch.dict(os.environ, {'BROWSER': 'firefox %s'})
    @patch('subprocess.Popen')
    def test_open_url_with_browser_cmd_placeholder(self, mock_popen):
        """Test BROWSER with %s placeholder."""
        result = open_url('https://example.com')
        assert result is True
        # Check that %s was replaced with URL
        call_args = mock_popen.call_args[0][0]
        assert 'firefox https://example.com' in call_args
    
    @patch.dict(os.environ, {'BROWSER': 'firefox'})
    @patch('subprocess.Popen')
    def test_open_url_browser_cmd_without_placeholder(self, mock_popen):
        """Test BROWSER without %s placeholder."""
        result = open_url('https://example.com')
        assert result is True
        # URL should be appended
        call_args = mock_popen.call_args[0][0]
        assert 'firefox https://example.com' in call_args
    
    @patch.dict(os.environ, {'BROWSER': '/nonexistent/browser'})
    @patch('subprocess.Popen')
    @patch('webbrowser.open')
    def test_open_url_browser_cmd_failure_fallback(self, mock_webbrowser, mock_popen):
        """Test fallback to webbrowser when BROWSER command fails."""
        mock_popen.side_effect = Exception("Command not found")
        mock_webbrowser.return_value = True
        result = open_url('https://example.com')
        assert result is True
        mock_webbrowser.assert_called_once()
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('webbrowser.open')
    def test_open_url_empty_url(self, mock_webbrowser):
        """Test opening empty URL."""
        mock_webbrowser.return_value = True
        result = open_url('')
        assert result is True
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('webbrowser.open')
    def test_open_url_special_characters(self, mock_webbrowser):
        """Test URL with special characters."""
        mock_webbrowser.return_value = True
        url = 'https://example.com/path?foo=bar&baz=qux#fragment'
        result = open_url(url)
        assert result is True
        mock_webbrowser.assert_called_once_with(url)
    
    @patch.dict(os.environ, {'BROWSER': 'google-chrome --new-tab'})
    @patch('subprocess.Popen')
    def test_open_url_browser_with_args(self, mock_popen):
        """Test BROWSER with additional arguments."""
        result = open_url('https://example.com')
        assert result is True
        call_args = mock_popen.call_args[0][0]
        assert 'google-chrome --new-tab https://example.com' in call_args
    
    @patch.dict(os.environ, {'BROWSER': 'xdg-open'})
    @patch('subprocess.Popen')
    def test_open_url_with_xdg_open(self, mock_popen):
        """Test using xdg-open as browser."""
        result = open_url('https://example.com')
        assert result is True
        mock_popen.assert_called_once()
    
    @patch.dict(os.environ, {'BROWSER': '/usr/bin/chrome'})
    @patch('subprocess.Popen')
    def test_open_url_popen_devnull(self, mock_popen):
        """Test that Popen uses DEVNULL for stdout/stderr."""
        result = open_url('https://example.com')
        assert result is True
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs['stdout'] == subprocess.DEVNULL
        assert call_kwargs['stderr'] == subprocess.DEVNULL
        assert call_kwargs['shell'] is True


@pytest.mark.unit
class TestGetBrowserCommand:
    """Test get_browser_command function."""
    
    @patch.dict(os.environ, {'BROWSER': '/usr/bin/chrome'})
    def test_get_browser_command_with_env(self):
        """Test getting browser from environment."""
        result = get_browser_command()
        assert result == '/usr/bin/chrome'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_browser_command_without_env(self):
        """Test getting browser when env not set."""
        result = get_browser_command()
        assert result is None
    
    @patch.dict(os.environ, {'BROWSER': ''})
    def test_get_browser_command_empty_string(self):
        """Test getting browser when env is empty string."""
        result = get_browser_command()
        assert result == ''
    
    @patch.dict(os.environ, {'BROWSER': 'firefox %s --new-tab'})
    def test_get_browser_command_with_placeholder(self):
        """Test getting browser command with placeholder."""
        result = get_browser_command()
        assert result == 'firefox %s --new-tab'
    
    @patch.dict(os.environ, {'BROWSER': 'google-chrome'})
    def test_get_browser_command_simple(self):
        """Test getting simple browser command."""
        result = get_browser_command()
        assert result == 'google-chrome'
