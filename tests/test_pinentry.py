"""Tests for pinentry module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import subprocess

from lastpass.pinentry import Pinentry, AskpassPrompt, prompt_password


@pytest.mark.unit
class TestPinentryIsAvailable:
    """Tests for Pinentry.is_available()."""
    
    @patch.dict(os.environ, {'LPASS_DISABLE_PINENTRY': '1'})
    def test_disabled_by_env(self):
        """Test pinentry disabled by environment variable."""
        assert Pinentry.is_available() is False
    
    @patch.dict(os.environ, {}, clear=True)
    @patch.object(Pinentry, '_get_pinentry_path')
    def test_available_when_found(self, mock_get_path):
        """Test available when pinentry found."""
        mock_get_path.return_value = '/usr/bin/pinentry'
        assert Pinentry.is_available() is True
    
    @patch.dict(os.environ, {}, clear=True)
    @patch.object(Pinentry, '_get_pinentry_path')
    def test_not_available_when_not_found(self, mock_get_path):
        """Test not available when pinentry not found."""
        mock_get_path.return_value = None
        assert Pinentry.is_available() is False


@pytest.mark.unit
class TestGetPinentryPath:
    """Tests for Pinentry._get_pinentry_path()."""
    
    @patch.dict(os.environ, {'LPASS_PINENTRY': '/custom/pinentry'})
    @patch('shutil.which')
    def test_custom_path_from_env(self, mock_which):
        """Test custom pinentry path from environment."""
        mock_which.return_value = '/custom/pinentry'
        path = Pinentry._get_pinentry_path()
        assert path == '/custom/pinentry'
        mock_which.assert_called_with('/custom/pinentry')
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('shutil.which')
    def test_finds_pinentry_variant(self, mock_which):
        """Test finds pinentry variant."""
        def which_side_effect(cmd):
            if cmd == 'pinentry-qt':
                return '/usr/bin/pinentry-qt'
            return None
        
        mock_which.side_effect = which_side_effect
        path = Pinentry._get_pinentry_path()
        assert path == '/usr/bin/pinentry-qt'
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('shutil.which')
    def test_tries_multiple_variants(self, mock_which):
        """Test tries multiple pinentry variants."""
        mock_which.return_value = None
        path = Pinentry._get_pinentry_path()
        assert path is None
        # Should have tried multiple variants
        assert mock_which.call_count > 1
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('shutil.which')
    def test_returns_first_found(self, mock_which):
        """Test returns first found variant."""
        def which_side_effect(cmd):
            if cmd == 'pinentry':
                return '/usr/bin/pinentry'
            return '/usr/bin/' + cmd
        
        mock_which.side_effect = which_side_effect
        path = Pinentry._get_pinentry_path()
        assert path == '/usr/bin/pinentry'


@pytest.mark.unit
class TestPinentryEscape:
    """Tests for Pinentry._escape()."""
    
    def test_escape_percent(self):
        """Test escaping percent sign."""
        result = Pinentry._escape('100%')
        assert result == '100%25'
    
    def test_escape_newline(self):
        """Test escaping newline."""
        result = Pinentry._escape('line1\nline2')
        assert result == 'line1%0Aline2'
    
    def test_escape_carriage_return(self):
        """Test escaping carriage return."""
        result = Pinentry._escape('text\rmore')
        assert result == 'text%0Dmore'
    
    def test_escape_multiple_special_chars(self):
        """Test escaping multiple special characters."""
        result = Pinentry._escape('100%\n\r')
        assert result == '100%25%0A%0D'
    
    def test_escape_normal_text(self):
        """Test normal text unchanged."""
        result = Pinentry._escape('normal text 123')
        assert result == 'normal text 123'


@pytest.mark.unit
class TestPinentryUnescape:
    """Tests for Pinentry._unescape()."""
    
    def test_unescape_percent(self):
        """Test unescaping percent sign."""
        result = Pinentry._unescape('100%25')
        assert result == '100%'
    
    def test_unescape_newline(self):
        """Test unescaping newline."""
        result = Pinentry._unescape('line1%0Aline2')
        assert result == 'line1\nline2'
    
    def test_unescape_carriage_return(self):
        """Test unescaping carriage return."""
        result = Pinentry._unescape('text%0Dmore')
        assert result == 'text\rmore'
    
    def test_unescape_invalid_escape(self):
        """Test invalid escape sequence."""
        result = Pinentry._unescape('%ZZ')
        # Should keep as-is or handle gracefully
        assert '%ZZ' in result or result == '%ZZ'
    
    def test_unescape_normal_text(self):
        """Test normal text unchanged."""
        result = Pinentry._unescape('normal text 123')
        assert result == 'normal text 123'


@pytest.mark.unit
class TestPinentryPromptPassword:
    """Tests for Pinentry.prompt_password()."""
    
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, '_terminal_prompt')
    def test_fallback_when_not_available(self, mock_terminal, mock_available):
        """Test falls back to terminal when not available."""
        mock_available.return_value = False
        mock_terminal.return_value = 'password'
        
        result = Pinentry.prompt_password('Password:')
        
        assert result == 'password'
        mock_terminal.assert_called_once()
    
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, '_get_pinentry_path')
    @patch('subprocess.Popen')
    def test_success(self, mock_popen, mock_path, mock_available):
        """Test successful password prompt."""
        mock_available.return_value = True
        mock_path.return_value = '/usr/bin/pinentry'
        
        mock_proc = Mock()
        mock_proc.communicate.return_value = ('D password123\nOK\n', '')
        mock_popen.return_value = mock_proc
        
        result = Pinentry.prompt_password('Password:')
        
        assert result == 'password123'
    
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, '_get_pinentry_path')
    @patch('subprocess.Popen')
    def test_cancelled(self, mock_popen, mock_path, mock_available):
        """Test cancelled password prompt."""
        mock_available.return_value = True
        mock_path.return_value = '/usr/bin/pinentry'
        
        mock_proc = Mock()
        mock_proc.communicate.return_value = ('ERR 83886179 canceled\n', '')
        mock_popen.return_value = mock_proc
        
        result = Pinentry.prompt_password('Password:')
        
        assert result is None
    
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, '_get_pinentry_path')
    @patch('subprocess.Popen')
    @patch.object(Pinentry, '_terminal_prompt')
    def test_fallback_on_error(self, mock_terminal, mock_popen, mock_path, mock_available):
        """Test fallback to terminal on error."""
        mock_available.return_value = True
        mock_path.return_value = '/usr/bin/pinentry'
        mock_popen.side_effect = Exception("Process failed")
        mock_terminal.return_value = 'password'
        
        result = Pinentry.prompt_password('Password:')
        
        assert result == 'password'
        mock_terminal.assert_called_once()
    
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, '_get_pinentry_path')
    @patch('subprocess.Popen')
    @patch.dict(os.environ, {'TERM': 'xterm', 'DISPLAY': ':0'})
    def test_sets_options(self, mock_popen, mock_path, mock_available):
        """Test sets terminal and display options."""
        mock_available.return_value = True
        mock_path.return_value = '/usr/bin/pinentry'
        
        mock_proc = Mock()
        mock_proc.communicate.return_value = ('D pass\nOK\n', '')
        mock_popen.return_value = mock_proc
        
        Pinentry.prompt_password('Password:', description='Enter password')
        
        # Check that communicate was called with commands
        call_args = mock_proc.communicate.call_args
        input_text = call_args[1]['input']
        assert 'OPTION ttytype=xterm' in input_text
        assert 'OPTION display=:0' in input_text
        assert 'SETPROMPT' in input_text
        assert 'SETDESC' in input_text


@pytest.mark.unit
class TestTerminalPrompt:
    """Tests for Pinentry._terminal_prompt()."""
    
    @patch('getpass.getpass')
    def test_terminal_prompt_success(self, mock_getpass):
        """Test successful terminal prompt."""
        mock_getpass.return_value = 'password'
        result = Pinentry._terminal_prompt('Password:')
        assert result == 'password'
    
    @patch('getpass.getpass')
    @patch('sys.stderr.write')
    def test_terminal_prompt_with_error(self, mock_stderr, mock_getpass):
        """Test terminal prompt with error message."""
        mock_getpass.return_value = 'password'
        result = Pinentry._terminal_prompt('Password:', error='Wrong password')
        assert result == 'password'
        # Should have printed error
        mock_stderr.assert_called()
    
    @patch('getpass.getpass')
    @patch('builtins.print')
    def test_terminal_prompt_with_description(self, mock_print, mock_getpass):
        """Test terminal prompt with description."""
        mock_getpass.return_value = 'password'
        result = Pinentry._terminal_prompt('Password:', description='Enter your password')
        assert result == 'password'
        mock_print.assert_called_with('Enter your password')
    
    @patch('getpass.getpass')
    def test_terminal_prompt_keyboard_interrupt(self, mock_getpass):
        """Test terminal prompt cancelled with KeyboardInterrupt."""
        mock_getpass.side_effect = KeyboardInterrupt()
        result = Pinentry._terminal_prompt('Password:')
        assert result is None
    
    @patch('getpass.getpass')
    def test_terminal_prompt_eof(self, mock_getpass):
        """Test terminal prompt cancelled with EOF."""
        mock_getpass.side_effect = EOFError()
        result = Pinentry._terminal_prompt('Password:')
        assert result is None


@pytest.mark.unit
class TestAskpassPrompt:
    """Tests for AskpassPrompt class."""
    
    @patch.dict(os.environ, {'LPASS_ASKPASS': '/usr/bin/ssh-askpass'})
    @patch('shutil.which')
    def test_is_available_true(self, mock_which):
        """Test askpass available when configured."""
        mock_which.return_value = '/usr/bin/ssh-askpass'
        assert AskpassPrompt.is_available() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_available_false_not_configured(self):
        """Test askpass not available when not configured."""
        assert AskpassPrompt.is_available() is False
    
    @patch.dict(os.environ, {'LPASS_ASKPASS': '/nonexistent'})
    @patch('shutil.which')
    def test_is_available_false_not_found(self, mock_which):
        """Test askpass not available when not found."""
        mock_which.return_value = None
        assert AskpassPrompt.is_available() is False
    
    @patch.dict(os.environ, {'LPASS_ASKPASS': '/usr/bin/ssh-askpass'})
    @patch('subprocess.run')
    def test_prompt_password_success(self, mock_run):
        """Test successful askpass prompt."""
        mock_run.return_value = Mock(returncode=0, stdout='password\n')
        result = AskpassPrompt.prompt_password('Enter password')
        assert result == 'password'
    
    @patch.dict(os.environ, {'LPASS_ASKPASS': '/usr/bin/ssh-askpass'})
    @patch('subprocess.run')
    def test_prompt_password_cancelled(self, mock_run):
        """Test cancelled askpass prompt."""
        mock_run.return_value = Mock(returncode=1, stdout='')
        result = AskpassPrompt.prompt_password('Enter password')
        assert result is None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_prompt_password_not_configured(self):
        """Test askpass prompt when not configured."""
        result = AskpassPrompt.prompt_password('Enter password')
        assert result is None
    
    @patch.dict(os.environ, {'LPASS_ASKPASS': '/usr/bin/ssh-askpass'})
    @patch('subprocess.run')
    def test_prompt_password_error(self, mock_run):
        """Test askpass prompt handles errors."""
        mock_run.side_effect = Exception("Command failed")
        result = AskpassPrompt.prompt_password('Enter password')
        assert result is None


@pytest.mark.unit
class TestPromptPassword:
    """Tests for prompt_password function."""
    
    @patch.object(AskpassPrompt, 'is_available')
    @patch.object(AskpassPrompt, 'prompt_password')
    def test_uses_askpass_first(self, mock_askpass, mock_available):
        """Test uses askpass first when available."""
        mock_available.return_value = True
        mock_askpass.return_value = 'password'
        
        result = prompt_password('Password', description='Enter password')
        
        assert result == 'password'
        mock_askpass.assert_called_once()
    
    @patch.object(AskpassPrompt, 'is_available')
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, 'prompt_password')
    def test_uses_pinentry_fallback(self, mock_pinentry, mock_pin_avail, mock_ask_avail):
        """Test uses pinentry when askpass fails."""
        mock_ask_avail.return_value = False
        mock_pin_avail.return_value = True
        mock_pinentry.return_value = 'password'
        
        result = prompt_password('Password', description='Enter password')
        
        assert result == 'password'
        mock_pinentry.assert_called_once()
    
    @patch.object(AskpassPrompt, 'is_available')
    @patch.object(Pinentry, 'is_available')
    @patch.object(Pinentry, '_terminal_prompt')
    def test_uses_terminal_fallback(self, mock_terminal, mock_pin_avail, mock_ask_avail):
        """Test uses terminal when other methods unavailable."""
        mock_ask_avail.return_value = False
        mock_pin_avail.return_value = False
        mock_terminal.return_value = 'password'
        
        result = prompt_password('Password', description='Enter password')
        
        assert result == 'password'
        mock_terminal.assert_called_once()
