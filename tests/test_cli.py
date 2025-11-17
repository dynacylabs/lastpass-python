"""
Tests for CLI module
"""

import pytest
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from lastpass.cli import CLI, main
from lastpass.models import Account, Field
from lastpass.exceptions import LastPassException, AccountNotFoundException


@pytest.fixture
def cli():
    """Create CLI instance"""
    return CLI()


@pytest.fixture
def mock_client(cli):
    """Mock the client"""
    cli.client = Mock()
    return cli.client


@pytest.fixture
def sample_account():
    """Create sample account"""
    account = Account(
        id='123',
        name='Test Account',
        username='testuser',
        password='testpass',
        url='https://example.com',
        notes='Test notes',
        group='TestGroup',
        fullname='TestGroup/Test Account'
    )
    account.fields = [
        Field(name='field1', value='value1', type='text', checked=False),
        Field(name='field2', value='value2', type='text', checked=False)
    ]
    return account


class TestCLIInit:
    """Test CLI initialization"""
    
    def test_cli_init(self):
        """Test CLI creates client"""
        cli = CLI()
        assert cli.client is not None
        from lastpass.client import LastPassClient
        assert isinstance(cli.client, LastPassClient)


class TestCLIRun:
    """Test CLI run method"""
    
    def test_run_no_args_shows_help(self, cli):
        """Test running with no args shows help"""
        with patch('sys.argv', ['lpass']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli.run([])
                assert result == 1
                # Help should be printed
    
    def test_run_with_help_flag(self, cli):
        """Test running with --help flag"""
        with pytest.raises(SystemExit) as exc_info:
            cli.run(['--help'])
        assert exc_info.value.code == 0
    
    def test_run_with_version_flag(self, cli):
        """Test running with --version flag"""
        with pytest.raises(SystemExit) as exc_info:
            cli.run(['--version'])
        assert exc_info.value.code == 0
    
    def test_run_catches_lastpass_exception(self, cli, mock_client):
        """Test run catches LastPassException"""
        mock_client.is_logged_in.side_effect = LastPassException("Test error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['status'])
            assert result == 1
            assert "Error: Test error" in mock_stderr.getvalue()
    
    def test_run_catches_keyboard_interrupt(self, cli, mock_client):
        """Test run catches KeyboardInterrupt"""
        mock_client.is_logged_in.side_effect = KeyboardInterrupt()
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['status'])
            assert result == 130
            assert "Aborted" in mock_stderr.getvalue()
    
    def test_run_catches_unexpected_exception(self, cli, mock_client):
        """Test run catches unexpected exceptions"""
        mock_client.is_logged_in.side_effect = RuntimeError("Unexpected")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['status'])
            assert result == 1
            assert "Unexpected error: Unexpected" in mock_stderr.getvalue()


class TestCLILogin:
    """Test login command"""
    
    def test_login_success(self, cli, mock_client):
        """Test successful login"""
        mock_client.login.return_value = None
        
        with patch('getpass.getpass', return_value='password123'):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = cli.run(['login', 'user@example.com'])
                assert result == 0
                mock_client.login.assert_called_once_with(
                    'user@example.com',
                    'password123',
                    trust=False,
                    otp=None,
                    force=False
                )
                assert "Success: Logged in as user@example.com" in mock_stdout.getvalue()
    
    def test_login_with_trust(self, cli, mock_client):
        """Test login with trust flag"""
        mock_client.login.return_value = None
        
        with patch('getpass.getpass', return_value='password123'):
            with patch('sys.stdout', new_callable=StringIO):
                result = cli.run(['login', 'user@example.com', '--trust'])
                assert result == 0
                mock_client.login.assert_called_once_with(
                    'user@example.com',
                    'password123',
                    trust=True,
                    otp=None,
                    force=False
                )
    
    def test_login_with_otp(self, cli, mock_client):
        """Test login with OTP"""
        mock_client.login.return_value = None
        
        with patch('getpass.getpass', return_value='password123'):
            with patch('sys.stdout', new_callable=StringIO):
                result = cli.run(['login', 'user@example.com', '--otp', '123456'])
                assert result == 0
                mock_client.login.assert_called_once_with(
                    'user@example.com',
                    'password123',
                    trust=False,
                    otp='123456',
                    force=False
                )
    
    def test_login_with_force(self, cli, mock_client):
        """Test login with force flag"""
        mock_client.login.return_value = None
        
        with patch('getpass.getpass', return_value='password123'):
            with patch('sys.stdout', new_callable=StringIO):
                result = cli.run(['login', 'user@example.com', '--force'])
                assert result == 0
                mock_client.login.assert_called_once_with(
                    'user@example.com',
                    'password123',
                    trust=False,
                    otp=None,
                    force=True
                )
    
    def test_login_failure(self, cli, mock_client):
        """Test login failure"""
        mock_client.login.side_effect = Exception("Invalid credentials")
        
        with patch('getpass.getpass', return_value='wrongpass'):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                result = cli.run(['login', 'user@example.com'])
                assert result == 1
                assert "Login failed: Invalid credentials" in mock_stderr.getvalue()


class TestCLILogout:
    """Test logout command"""
    
    def test_logout_success(self, cli, mock_client):
        """Test successful logout"""
        mock_client.logout.return_value = None
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['logout'])
            assert result == 0
            mock_client.logout.assert_called_once_with(force=False)
            assert "Logged out successfully" in mock_stdout.getvalue()
    
    def test_logout_with_force(self, cli, mock_client):
        """Test logout with force flag"""
        mock_client.logout.return_value = None
        
        with patch('sys.stdout', new_callable=StringIO):
            result = cli.run(['logout', '--force'])
            assert result == 0
            mock_client.logout.assert_called_once_with(force=True)
    
    def test_logout_failure(self, cli, mock_client):
        """Test logout failure"""
        mock_client.logout.side_effect = Exception("Logout error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['logout'])
            assert result == 1
            assert "Logout failed: Logout error" in mock_stderr.getvalue()


class TestCLIStatus:
    """Test status command"""
    
    def test_status_logged_in(self, cli, mock_client):
        """Test status when logged in"""
        mock_client.is_logged_in.return_value = True
        mock_client.session = Mock(uid='user@example.com')
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['status'])
            assert result == 0
            assert "Logged in as user@example.com" in mock_stdout.getvalue()
    
    def test_status_not_logged_in(self, cli, mock_client):
        """Test status when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['status'])
            assert result == 1
            assert "Not logged in" in mock_stdout.getvalue()
    
    def test_status_quiet_logged_in(self, cli, mock_client):
        """Test status --quiet when logged in"""
        mock_client.is_logged_in.return_value = True
        mock_client.session = Mock(uid='user@example.com')
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['status', '--quiet'])
            assert result == 0
            assert mock_stdout.getvalue() == ""
    
    def test_status_quiet_not_logged_in(self, cli, mock_client):
        """Test status --quiet when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['status', '--quiet'])
            assert result == 1
            assert mock_stdout.getvalue() == ""


class TestCLIShow:
    """Test show command"""
    
    def test_show_account_default(self, cli, mock_client, sample_account):
        """Test show account with default format"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account'])
            assert result == 0
            output = mock_stdout.getvalue()
            assert "Name: Test Account" in output
            assert "Username: testuser" in output
            assert "Password: testpass" in output
            assert "URL: https://example.com" in output
            assert "Notes: Test notes" in output
    
    def test_show_account_password(self, cli, mock_client, sample_account):
        """Test show account password only"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account', '--password'])
            assert result == 0
            assert mock_stdout.getvalue().strip() == "testpass"
    
    def test_show_account_username(self, cli, mock_client, sample_account):
        """Test show account username only"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account', '--username'])
            assert result == 0
            assert mock_stdout.getvalue().strip() == "testuser"
    
    def test_show_account_url(self, cli, mock_client, sample_account):
        """Test show account URL only"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account', '--url'])
            assert result == 0
            assert mock_stdout.getvalue().strip() == "https://example.com"
    
    def test_show_account_notes(self, cli, mock_client, sample_account):
        """Test show account notes only"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account', '--notes'])
            assert result == 0
            assert mock_stdout.getvalue().strip() == "Test notes"
    
    def test_show_account_field(self, cli, mock_client, sample_account):
        """Test show account specific field"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account', '--field', 'field1'])
            assert result == 0
            assert mock_stdout.getvalue().strip() == "value1"
    
    def test_show_account_field_not_found(self, cli, mock_client, sample_account):
        """Test show account with nonexistent field"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['show', 'Test Account', '--field', 'nonexistent'])
            assert result == 1
            assert "Field not found: nonexistent" in mock_stderr.getvalue()
    
    def test_show_account_json(self, cli, mock_client, sample_account):
        """Test show account as JSON"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['show', 'Test Account', '--json'])
            assert result == 0
            output = json.loads(mock_stdout.getvalue())
            assert output['name'] == 'Test Account'
            assert output['username'] == 'testuser'
    
    def test_show_account_clip(self, cli, mock_client, sample_account):
        """Test show account with clipboard"""
        mock_client.find_account.return_value = sample_account
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch.object(cli, '_copy_to_clipboard') as mock_clip:
                result = cli.run(['show', 'Test Account', '--password', '--clip'])
                assert result == 0
                mock_clip.assert_called_once_with('testpass')
                assert "Copied to clipboard" in mock_stdout.getvalue()
    
    def test_show_account_not_found(self, cli, mock_client):
        """Test show account not found"""
        mock_client.find_account.return_value = None
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['show', 'Nonexistent'])
            assert result == 1
            assert "Account not found: Nonexistent" in mock_stderr.getvalue()
    
    def test_show_account_exception(self, cli, mock_client):
        """Test show account raises exception"""
        mock_client.find_account.side_effect = AccountNotFoundException("Not found")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['show', 'Test'])
            assert result == 1
            assert "Error: Not found" in mock_stderr.getvalue()


class TestCLIList:
    """Test ls command"""
    
    def test_ls_all_accounts(self, cli, mock_client, sample_account):
        """Test list all accounts"""
        accounts = [sample_account]
        mock_client.get_accounts.return_value = accounts
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['ls'])
            assert result == 0
            output = mock_stdout.getvalue()
            # The ls command prints fullname
            assert 'TestGroup/Test Account' in output
    
    def test_ls_with_group_filter(self, cli, mock_client, sample_account):
        """Test list accounts with group filter"""
        account1 = Account(id='1', name='Account1', group='Group1', username='', password='', url='', fullname='Group1/Account1')
        account2 = Account(id='2', name='Account2', group='Group2', username='', password='', url='', fullname='Group2/Account2')
        mock_client.get_accounts.return_value = [account1, account2]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['ls', 'Group1'])
            assert result == 0
            output = mock_stdout.getvalue()
            # Check that only Group1 account is shown
            assert 'Group1/Account1' in output
            assert 'Group2/Account2' not in output
    
    def test_ls_long_format(self, cli, mock_client, sample_account):
        """Test list accounts in long format"""
        mock_client.get_accounts.return_value = [sample_account]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['ls', '--long'])
            assert result == 0
            output = mock_stdout.getvalue()
            assert "123" in output
            assert "testuser" in output
    
    def test_ls_json_format(self, cli, mock_client, sample_account):
        """Test list accounts as JSON"""
        mock_client.get_accounts.return_value = [sample_account]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['ls', '--json'])
            assert result == 0
            output = json.loads(mock_stdout.getvalue())
            assert len(output) == 1
            assert output[0]['name'] == 'Test Account'
    
    def test_ls_failure(self, cli, mock_client):
        """Test list accounts failure"""
        mock_client.get_accounts.side_effect = Exception("List error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['ls'])
            assert result == 1
            assert "Error: List error" in mock_stderr.getvalue()


class TestCLIGenerate:
    """Test generate command"""
    
    def test_generate_default(self, cli, mock_client):
        """Test generate password with defaults"""
        mock_client.generate_password.return_value = "generatedpass123"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['generate'])
            assert result == 0
            mock_client.generate_password.assert_called_once_with(
                length=16,
                symbols=True
            )
            assert "generatedpass123" in mock_stdout.getvalue()
    
    def test_generate_custom_length(self, cli, mock_client):
        """Test generate password with custom length"""
        mock_client.generate_password.return_value = "pass24"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['generate', '24'])
            assert result == 0
            mock_client.generate_password.assert_called_once_with(
                length=24,
                symbols=True
            )
    
    def test_generate_no_symbols(self, cli, mock_client):
        """Test generate password without symbols"""
        mock_client.generate_password.return_value = "alphanumeric"
        
        with patch('sys.stdout', new_callable=StringIO):
            result = cli.run(['generate', '--no-symbols'])
            assert result == 0
            mock_client.generate_password.assert_called_once_with(
                length=16,
                symbols=False
            )
    
    def test_generate_with_clip(self, cli, mock_client):
        """Test generate password to clipboard"""
        mock_client.generate_password.return_value = "clippass"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch.object(cli, '_copy_to_clipboard') as mock_clip:
                result = cli.run(['generate', '--clip'])
                assert result == 0
                mock_clip.assert_called_once_with('clippass')
                assert "Password copied to clipboard" in mock_stdout.getvalue()


class TestCLISync:
    """Test sync command"""
    
    def test_sync_success(self, cli, mock_client):
        """Test successful sync"""
        mock_client.sync.return_value = None
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['sync'])
            assert result == 0
            mock_client.sync.assert_called_once_with(force=True)
            assert "Vault synced successfully" in mock_stdout.getvalue()
    
    def test_sync_failure(self, cli, mock_client):
        """Test sync failure"""
        mock_client.sync.side_effect = Exception("Sync error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['sync'])
            assert result == 1
            assert "Sync failed: Sync error" in mock_stderr.getvalue()


class TestCLIHelpers:
    """Test CLI helper methods"""
    
    def test_format_account(self, cli, sample_account):
        """Test format account for display"""
        output = cli._format_account(sample_account)
        assert "Name: Test Account" in output
        assert "Username: testuser" in output
        assert "Password: testpass" in output
        assert "Notes: Test notes" in output
        assert "field1: value1" in output
    
    def test_format_account_no_notes(self, cli):
        """Test format account without notes"""
        account = Account(
            id='1', name='Test', username='user', password='pass',
            url='http://test.com', notes='', group=''
        )
        output = cli._format_account(account)
        assert "Name: Test" in output
        assert "Notes:" not in output
    
    def test_format_account_no_fields(self, cli):
        """Test format account without fields"""
        account = Account(
            id='1', name='Test', username='user', password='pass',
            url='http://test.com', notes='', group=''
        )
        account.fields = []
        output = cli._format_account(account)
        assert "Name: Test" in output
        assert "Fields:" not in output
    
    def test_copy_to_clipboard_pyperclip(self, cli):
        """Test copy to clipboard with pyperclip"""
        mock_pyperclip = MagicMock()
        with patch.dict('sys.modules', {'pyperclip': mock_pyperclip}):
            cli._copy_to_clipboard("test text")
            mock_pyperclip.copy.assert_called_once_with("test text")
    
    def test_copy_to_clipboard_macos(self, cli):
        """Test copy to clipboard on macOS"""
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError()
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('platform.system', return_value='Darwin'):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock()
                    cli._copy_to_clipboard("test text")
                    mock_run.assert_called_once()
                    assert mock_run.call_args[0][0] == ['pbcopy']
    
    def test_copy_to_clipboard_linux_xclip(self, cli):
        """Test copy to clipboard on Linux with xclip"""
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError()
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('platform.system', return_value='Linux'):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock()
                    cli._copy_to_clipboard("test text")
                    mock_run.assert_called_once()
                    assert 'xclip' in mock_run.call_args[0][0]
    
    def test_copy_to_clipboard_linux_xsel(self, cli):
        """Test copy to clipboard on Linux with xsel fallback"""
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError()
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('platform.system', return_value='Linux'):
                with patch('subprocess.run') as mock_run:
                    # First call (xclip) fails, second call (xsel) succeeds
                    mock_run.side_effect = [
                        FileNotFoundError(),
                        Mock()
                    ]
                    cli._copy_to_clipboard("test text")
                    assert mock_run.call_count == 2
                    assert 'xsel' in mock_run.call_args[0][0]
    
    def test_copy_to_clipboard_unsupported_platform(self, cli):
        """Test copy to clipboard on unsupported platform"""
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError()
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('platform.system', return_value='Windows'):
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    cli._copy_to_clipboard("test text")
                    assert "Clipboard not supported" in mock_stderr.getvalue()
    
    def test_copy_to_clipboard_command_not_found(self, cli):
        """Test copy to clipboard when commands not available"""
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError()
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('platform.system', return_value='Linux'):
                with patch('subprocess.run', side_effect=FileNotFoundError):
                    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                        cli._copy_to_clipboard("test text")
                        assert "Could not copy to clipboard" in mock_stderr.getvalue()
    
    def test_copy_to_clipboard_subprocess_error(self, cli):
        """Test copy to clipboard with subprocess error"""
        import subprocess
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'pyperclip':
                raise ImportError()
            return real_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('platform.system', return_value='Darwin'):
                with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'pbcopy')):
                    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                        cli._copy_to_clipboard("test text")
                        assert "Could not copy to clipboard" in mock_stderr.getvalue()


class TestCLIWriteCommands:
    """Test CLI write commands (add, edit, rm, duplicate, mv)"""
    
    def test_add_command_basic(self, cli, mock_client):
        """Test add command with basic arguments"""
        mock_client.is_logged_in.return_value = True
        mock_client.add_account.return_value = "12345"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('getpass.getpass', return_value='testpass'):
                result = cli.run([
                    'add',
                    'Test Account',
                    '--username', 'testuser',
                    '--url', 'https://example.com',
                ])
                
                assert result == 0
                mock_client.add_account.assert_called_once()
                assert "Added account: Test Account" in mock_stdout.getvalue()
    
    def test_add_command_with_generate(self, cli, mock_client):
        """Test add command with password generation"""
        mock_client.is_logged_in.return_value = True
        mock_client.add_account.return_value = "12345"
        mock_client.generate_password.return_value = "GeneratedPass123!"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run([
                'add',
                'Test Account',
                '--username', 'testuser',
                '--generate', '16',
            ])
            
            assert result == 0
            mock_client.generate_password.assert_called_once_with(length=16)
            mock_client.add_account.assert_called_once()
            # Check that a password was generated (not empty)
            call_args = mock_client.add_account.call_args
            assert call_args[1]['password'] == 'GeneratedPass123!'
    
    def test_add_command_with_group(self, cli, mock_client):
        """Test add command with group"""
        mock_client.is_logged_in.return_value = True
        mock_client.add_account.return_value = "12345"
        
        with patch('getpass.getpass', return_value='testpass'):
            result = cli.run([
                'add',
                'Work Account',
                '--username', 'workuser',
                '--group', 'Work\\Websites',
            ])
            
            assert result == 0
            call_args = mock_client.add_account.call_args
            assert call_args[1]['group'] == 'Work\\Websites'
    
    def test_add_command_with_notes(self, cli, mock_client):
        """Test add command with notes"""
        mock_client.is_logged_in.return_value = True
        mock_client.add_account.return_value = "12345"
        
        with patch('getpass.getpass', return_value='testpass'):
            result = cli.run([
                'add',
                'Test Account',
                '--username', 'testuser',
                '--notes', 'Important notes here',
            ])
            
            assert result == 0
            call_args = mock_client.add_account.call_args
            assert call_args[1]['notes'] == 'Important notes here'
    
    def test_add_command_not_logged_in(self, cli, mock_client):
        """Test add command when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['add', 'Test Account', '--username', 'user'])
            
            assert result == 1
            assert "not logged in" in mock_stderr.getvalue()
            mock_client.add_account.assert_not_called()
    
    def test_edit_command_basic(self, cli, mock_client):
        """Test edit command with basic arguments"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run([
                'edit',
                'GitHub',
                '--username', 'newuser',
            ])
            
            assert result == 0
            mock_client.update_account.assert_called_once()
            call_args = mock_client.update_account.call_args
            assert call_args[0][0] == 'GitHub'
            assert call_args[1]['username'] == 'newuser'
    
    def test_edit_command_multiple_fields(self, cli, mock_client):
        """Test edit command updating multiple fields"""
        mock_client.is_logged_in.return_value = True
        
        result = cli.run([
            'edit',
            'GitHub',
            '--name', 'GitHub Updated',
            '--username', 'newuser',
            '--password', 'newpass',
            '--url', 'https://new.github.com',
            '--notes', 'Updated notes',
        ])
        
        assert result == 0
        call_args = mock_client.update_account.call_args
        assert call_args[1]['name'] == 'GitHub Updated'
        assert call_args[1]['username'] == 'newuser'
        assert call_args[1]['password'] == 'newpass'
        assert call_args[1]['url'] == 'https://new.github.com'
        assert call_args[1]['notes'] == 'Updated notes'
    
    def test_edit_command_with_group(self, cli, mock_client):
        """Test edit command with group change"""
        mock_client.is_logged_in.return_value = True
        
        result = cli.run([
            'edit',
            'GitHub',
            '--group', 'Work',
        ])
        
        assert result == 0
        call_args = mock_client.update_account.call_args
        assert call_args[1]['group'] == 'Work'
    
    def test_edit_command_not_found(self, cli, mock_client):
        """Test edit command for non-existent account"""
        mock_client.is_logged_in.return_value = True
        mock_client.update_account.side_effect = AccountNotFoundException("Not found")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['edit', 'NonExistent', '--username', 'newuser'])
            
            assert result == 1
            assert "Not found" in mock_stderr.getvalue()
    
    def test_edit_command_not_logged_in(self, cli, mock_client):
        """Test edit command when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['edit', 'GitHub', '--username', 'newuser'])
            
            assert result == 1
            assert "not logged in" in mock_stderr.getvalue()
            mock_client.update_account.assert_not_called()
    
    def test_rm_command_with_confirmation(self, cli, mock_client):
        """Test rm command with user confirmation"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('builtins.input', return_value='y'):
                result = cli.run(['rm', 'GitHub'])
                
                assert result == 0
                mock_client.delete_account.assert_called_once_with('GitHub')
                assert "Deleted account: GitHub" in mock_stdout.getvalue()
    
    def test_rm_command_cancel_confirmation(self, cli, mock_client):
        """Test rm command cancelled by user"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('builtins.input', return_value='n'):
                result = cli.run(['rm', 'GitHub'])
                
                assert result == 0
                mock_client.delete_account.assert_not_called()
                assert "Cancelled" in mock_stdout.getvalue()
    
    def test_rm_command_with_force(self, cli, mock_client):
        """Test rm command with --force flag"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['rm', 'GitHub', '--force'])
            
            assert result == 0
            mock_client.delete_account.assert_called_once_with('GitHub')
            assert "Deleted account: GitHub" in mock_stdout.getvalue()
    
    def test_rm_command_not_found(self, cli, mock_client):
        """Test rm command for non-existent account"""
        mock_client.is_logged_in.return_value = True
        mock_client.delete_account.side_effect = AccountNotFoundException("Not found")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with patch('builtins.input', return_value='y'):
                result = cli.run(['rm', 'NonExistent'])
                
                assert result == 1
                assert "Not found" in mock_stderr.getvalue()
    
    def test_rm_command_not_logged_in(self, cli, mock_client):
        """Test rm command when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['rm', 'GitHub', '--force'])
            
            assert result == 1
            assert "not logged in" in mock_stderr.getvalue()
            mock_client.delete_account.assert_not_called()
    
    def test_duplicate_command_basic(self, cli, mock_client):
        """Test duplicate command with basic arguments"""
        mock_client.is_logged_in.return_value = True
        mock_client.duplicate_account.return_value = "99999"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['duplicate', 'GitHub'])
            
            assert result == 0
            mock_client.duplicate_account.assert_called_once()
            call_args = mock_client.duplicate_account.call_args
            assert call_args[0][0] == 'GitHub'
            assert "Duplicated account" in mock_stdout.getvalue()
    
    def test_duplicate_command_with_name(self, cli, mock_client):
        """Test duplicate command with custom name"""
        mock_client.is_logged_in.return_value = True
        mock_client.duplicate_account.return_value = "99999"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['duplicate', 'GitHub', '--name', 'GitHub Copy'])
            
            assert result == 0
            call_args = mock_client.duplicate_account.call_args
            assert call_args[0][0] == 'GitHub'
            # Second positional arg is new_name
            assert call_args[0][1] == 'GitHub Copy'
    
    def test_duplicate_command_not_found(self, cli, mock_client):
        """Test duplicate command for non-existent account"""
        mock_client.is_logged_in.return_value = True
        mock_client.duplicate_account.side_effect = AccountNotFoundException("Not found")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['duplicate', 'NonExistent'])
            
            assert result == 1
            assert "Not found" in mock_stderr.getvalue()
    
    def test_duplicate_command_not_logged_in(self, cli, mock_client):
        """Test duplicate command when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['duplicate', 'GitHub'])
            
            assert result == 1
            assert "not logged in" in mock_stderr.getvalue()
            mock_client.duplicate_account.assert_not_called()
    
    def test_mv_command_basic(self, cli, mock_client):
        """Test mv command with basic arguments"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['mv', 'GitHub', 'Work\\Development'])
            
            assert result == 0
            mock_client.move_account.assert_called_once()
            call_args = mock_client.move_account.call_args
            assert call_args[0][0] == 'GitHub'
            assert call_args[0][1] == 'Work\\Development'
            assert "Moved account 'GitHub'" in mock_stdout.getvalue()
    
    def test_mv_command_to_root(self, cli, mock_client):
        """Test mv command moving to root folder"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['mv', 'GitHub', ''])
            
            assert result == 0
            call_args = mock_client.move_account.call_args
            assert call_args[0][1] == ''
    
    def test_mv_command_not_found(self, cli, mock_client):
        """Test mv command for non-existent account"""
        mock_client.is_logged_in.return_value = True
        mock_client.move_account.side_effect = AccountNotFoundException("Not found")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['mv', 'NonExistent', 'Work'])
            
            assert result == 1
            assert "Not found" in mock_stderr.getvalue()
    
    def test_mv_command_not_logged_in(self, cli, mock_client):
        """Test mv command when not logged in"""
        mock_client.is_logged_in.return_value = False
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['mv', 'GitHub', 'Work'])
            
            assert result == 1
            assert "not logged in" in mock_stderr.getvalue()
            mock_client.move_account.assert_not_called()


class TestCLIEdgeCases:
    """Test CLI edge cases"""
    
    def test_add_command_exception_handling(self, cli, mock_client):
        """Test add command handles exceptions"""
        mock_client.is_logged_in.return_value = True
        mock_client.add_account.side_effect = Exception("Database error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = cli.run(['add', 'test', '--username', 'user', '--password', 'pass'])
            
            assert result == 1
            assert "Failed to add account" in mock_stderr.getvalue()
            assert "Database error" in mock_stderr.getvalue()
    
    def test_edit_command_with_no_changes(self, cli, mock_client):
        """Test edit command with no changes specified"""
        mock_client.is_logged_in.return_value = True
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            # Run edit with no update flags
            result = cli.run(['edit', 'GitHub'])
            
            assert result == 1
            assert "No changes specified" in mock_stderr.getvalue()
            mock_client.update_account.assert_not_called()
    
    def test_edit_command_with_empty_password_prompts(self, cli, mock_client):
        """Test edit command with empty password string prompts for input"""
        mock_client.is_logged_in.return_value = True
        
        with patch('getpass.getpass', return_value='prompted_password'):
            result = cli.run(['edit', 'GitHub', '--password', ''])
            
            assert result == 0
            # Should have called update_account with prompted password
            mock_client.update_account.assert_called_once()
            call_kwargs = mock_client.update_account.call_args[1]
            assert call_kwargs['password'] == 'prompted_password'


class TestMain:
    """Test main entry point"""
    
    def test_main_function(self):
        """Test main function calls CLI.run()"""
        with patch('lastpass.cli.CLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.run.return_value = 0
            mock_cli_class.return_value = mock_cli
            
            with patch('sys.exit') as mock_exit:
                main()
                mock_cli.run.assert_called_once()
                mock_exit.assert_called_once_with(0)
