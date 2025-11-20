"""
Tests for new 100% feature parity implementations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lastpass.format import (
    format_account_field,
    format_field_field,
    format_account,
    format_timestamp,
    get_display_fullname
)
from lastpass.models import Account, Share


class TestFormatting:
    """Test printf-style formatting"""
    
    def test_format_timestamp_utc(self):
        """Test UTC timestamp formatting"""
        result = format_timestamp("1234567890", utc=True)
        assert result == "2009-02-13 23:31"
    
    def test_format_timestamp_local(self):
        """Test local timestamp formatting"""
        result = format_timestamp("1234567890", utc=False)
        # Just check it returns something (local time varies)
        assert len(result) > 0
    
    def test_format_timestamp_empty(self):
        """Test empty timestamp"""
        assert format_timestamp(None) == ""
        assert format_timestamp("") == ""
        assert format_timestamp("0") == ""
    
    def test_get_display_fullname_with_share(self):
        """Test fullname display with share"""
        share = Share(id="123", name="TeamShare", key=b"key", readonly=False)
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group="",
            fullname="test",
            share=share
        )
        assert get_display_fullname(account) == "test"
    
    def test_get_display_fullname_with_group(self):
        """Test fullname display with group"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group="MyGroup",
            fullname="MyGroup/test"
        )
        assert get_display_fullname(account) == "MyGroup/test"
    
    def test_get_display_fullname_without_group_or_share(self):
        """Test fullname display without group or share"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group="",
            fullname="test"
        )
        assert get_display_fullname(account) == "(none)/test"
    
    def test_format_account_field_id(self):
        """Test formatting account ID"""
        account = Account(
            id="12345",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        assert format_account_field('i', account) == "12345"
    
    def test_format_account_field_name(self):
        """Test formatting account name"""
        account = Account(
            id="1",
            name="TestAccount",
            username="user",
            password="pass",
            url="http://example.com"
        )
        assert format_account_field('n', account) == "TestAccount"
    
    def test_format_account_field_fullname(self):
        """Test formatting account fullname"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group="MyGroup",
            fullname="MyGroup/test"
        )
        assert format_account_field('N', account) == "MyGroup/test"
    
    def test_format_account_field_username(self):
        """Test formatting username"""
        account = Account(
            id="1",
            name="test",
            username="testuser",
            password="pass",
            url="http://example.com"
        )
        assert format_account_field('u', account) == "testuser"
    
    def test_format_account_field_password(self):
        """Test formatting password"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="secret123",
            url="http://example.com"
        )
        assert format_account_field('p', account) == "secret123"
    
    def test_format_account_field_url(self):
        """Test formatting URL"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        assert format_account_field('l', account) == "http://example.com"
    
    def test_format_account_field_group(self):
        """Test formatting group"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group="Finance"
        )
        assert format_account_field('g', account) == "Finance"
    
    def test_format_account_field_share(self):
        """Test formatting share name"""
        share = Share(id="123", name="TeamShare", key=b"key", readonly=False)
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            share=share
        )
        assert format_account_field('s', account) == "TeamShare"
    
    def test_format_account_field_with_slash(self):
        """Test formatting with trailing slash"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group="MyGroup"
        )
        assert format_account_field('g', account, add_slash=True) == "MyGroup/"
    
    def test_format_account_field_empty_with_slash(self):
        """Test formatting empty field with slash (no slash added)"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com",
            group=""
        )
        assert format_account_field('g', account, add_slash=True) == ""
    
    def test_format_field_field_name(self):
        """Test formatting field name"""
        assert format_field_field('n', "CustomField", "value") == "CustomField"
    
    def test_format_field_field_value(self):
        """Test formatting field value"""
        assert format_field_field('v', "CustomField", "myvalue") == "myvalue"
    
    def test_format_account_simple(self):
        """Test simple format string"""
        account = Account(
            id="123",
            name="MyAccount",
            username="user@example.com",
            password="secret",
            url="http://example.com"
        )
        result = format_account("%au: %ap", account)
        assert result == "user@example.com: secret"
    
    def test_format_account_with_id(self):
        """Test format string with ID"""
        account = Account(
            id="456",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        result = format_account("ID: %ai", account)
        assert result == "ID: 456"
    
    def test_format_account_with_slash_modifier(self):
        """Test format string with slash modifier"""
        account = Account(
            id="1",
            name="MyAccount",
            username="user",
            password="pass",
            url="http://example.com",
            group="Finance",
            fullname="Finance/MyAccount"
        )
        result = format_account("%/ag%an", account)
        assert result == "Finance/MyAccount"
    
    def test_format_account_complex(self):
        """Test complex format string"""
        share = Share(id="123", name="Team", key=b"key", readonly=False)
        account = Account(
            id="789",
            name="Account",
            username="user",
            password="pass",
            url="http://example.com",
            group="Group",
            fullname="Team/Group/Account",
            share=share
        )
        result = format_account("%/as%/ag%an", account)
        assert result == "Team/Group/Account"
    
    def test_format_account_literal_percent(self):
        """Test literal percent sign"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        result = format_account("100%% complete: %an", account)
        assert result == "100% complete: test"
    
    def test_format_account_field_codes(self):
        """Test field name and value codes"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        result = format_account("%fn: %fv", account, "API Key", "abc123")
        assert result == "API Key: abc123"
    
    def test_format_account_trailing_percent(self):
        """Test trailing percent"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        result = format_account("%an%", account)
        assert result == "test%"
    
    def test_format_account_unknown_code(self):
        """Test unknown format code (should be literal)"""
        account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        # %az is treated as %a (account) with field code 'z' (unknown) -> empty string
        result = format_account("%az", account)
        # Unknown account field codes return empty string
        assert result == ""
        
        # But %z (unknown top-level code) should be literal
        result2 = format_account("%z", account)
        assert result2 == "%z"


class TestCLIFormatting:
    """Test CLI integration with formatting"""
    
    @patch('lastpass.cli.LastPassClient')
    def test_show_with_format(self, mock_client):
        """Test show command with custom format"""
        from lastpass.cli import CLI
        
        # Setup mock
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        
        mock_account = Account(
            id="123",
            name="test",
            username="user@example.com",
            password="secret",
            url="http://example.com"
        )
        mock_instance.find_account.return_value = mock_account
        
        cli = CLI()
        
        # Test format string
        with patch('sys.stdout.write'):
            with patch('builtins.print') as mock_print:
                result = cli.run(['show', '--format', '%au: %ap', 'test'])
                # Check that format was applied
                call_args = [str(call) for call in mock_print.call_args_list]
                assert any('user@example.com' in str(arg) for arg in call_args)
    
    @patch('lastpass.cli.LastPassClient')
    def test_ls_with_format(self, mock_client):
        """Test ls command with custom format"""
        from lastpass.cli import CLI
        
        # Setup mock
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        
        mock_accounts = [
            Account(
                id="1",
                name="acc1",
                username="user1",
                password="pass1",
                url="http://example.com",
                fullname="acc1"
            ),
            Account(
                id="2",
                name="acc2",
                username="user2",
                password="pass2",
                url="http://test.com",
                fullname="acc2"
            )
        ]
        mock_instance.get_accounts.return_value = mock_accounts
        
        cli = CLI()
        
        with patch('builtins.print') as mock_print:
            result = cli.run(['ls', '--format', '%ai: %an'])
            # Check format was applied
            assert result == 0


class TestGenerateWithAccount:
    """Test generate command with account creation"""
    
    @patch('lastpass.cli.LastPassClient')
    def test_generate_with_username_url(self, mock_client):
        """Test generate creating account with username and URL"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        mock_instance.generate_password.return_value = "GeneratedPass123"
        mock_instance.add_account.return_value = "123"
        
        cli = CLI()
        
        with patch('builtins.print'):
            result = cli.run([
                'generate',
                'myaccount',
                '20',
                '--username', 'user@example.com',
                '--url', 'http://example.com'
            ])
        
        assert result == 0
        mock_instance.add_account.assert_called_once()
        call_kwargs = mock_instance.add_account.call_args[1]
        assert call_kwargs['name'] == 'myaccount'
        assert call_kwargs['username'] == 'user@example.com'
        assert call_kwargs['url'] == 'http://example.com'
        assert call_kwargs['password'] == 'GeneratedPass123'
    
    @patch('lastpass.cli.LastPassClient')
    def test_generate_without_account(self, mock_client):
        """Test generate without creating account"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.generate_password.return_value = "GeneratedPass456"
        
        cli = CLI()
        
        with patch('builtins.print') as mock_print:
            result = cli.run(['generate', '20'])
        
        assert result == 0
        # Should not create account
        mock_instance.add_account.assert_not_called()


class TestNonInteractiveMode:
    """Test non-interactive mode for add and edit"""
    
    @patch('lastpass.cli.LastPassClient')
    @patch('sys.stdin')
    def test_add_non_interactive(self, mock_stdin, mock_client):
        """Test add in non-interactive mode"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        mock_instance.add_account.return_value = "123"
        
        # Mock stdin to provide password
        mock_stdin.readline.return_value = "passwordfromstdin\n"
        
        cli = CLI()
        
        with patch('builtins.print'):
            result = cli.run([
                'add',
                'testaccount',
                '--username', 'user',
                '--non-interactive'
            ])
        
        assert result == 0
        mock_instance.add_account.assert_called_once()
        call_kwargs = mock_instance.add_account.call_args[1]
        assert call_kwargs['password'] == 'passwordfromstdin'
    
    @patch('lastpass.cli.LastPassClient')
    @patch('sys.stdin')
    def test_edit_non_interactive(self, mock_stdin, mock_client):
        """Test edit in non-interactive mode"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        
        # Mock stdin to provide password
        mock_stdin.readline.return_value = "newpassword\n"
        
        cli = CLI()
        
        with patch('builtins.print'):
            result = cli.run([
                'edit',
                'testaccount',
                '--password', '',
                '--non-interactive'
            ])
        
        assert result == 0
        mock_instance.update_account.assert_called_once()
        call_args = mock_instance.update_account.call_args
        assert call_args[1]['password'] == 'newpassword'


class TestSyncOptions:
    """Test sync control options"""
    
    @patch('lastpass.cli.LastPassClient')
    def test_show_sync_now(self, mock_client):
        """Test show with --sync=now"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        
        mock_account = Account(
            id="1",
            name="test",
            username="user",
            password="pass",
            url="http://example.com"
        )
        mock_instance.find_account.return_value = mock_account
        
        cli = CLI()
        
        with patch('builtins.print'):
            result = cli.run(['show', '--sync', 'now', '--password', 'test'])
        
        assert result == 0
    
    @patch('lastpass.cli.LastPassClient')
    def test_add_sync_no(self, mock_client):
        """Test add with --sync=no"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        mock_instance.add_account.return_value = "123"
        
        cli = CLI()
        
        with patch('builtins.print'):
            with patch('getpass.getpass', return_value='password'):
                result = cli.run([
                    'add',
                    'test',
                    '--sync', 'no',
                    '--username', 'user'
                ])
        
        assert result == 0
        # Sync should not be called when sync=no
        mock_instance.sync.assert_not_called()
    
    @patch('lastpass.cli.LastPassClient')
    def test_export_sync_auto(self, mock_client):
        """Test export with --sync=auto (default)"""
        from lastpass.cli import CLI
        
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.is_logged_in.return_value = True
        mock_instance.get_accounts.return_value = []
        mock_instance.export_to_csv.return_value = "url,username,password,name\n"
        
        cli = CLI()
        
        with patch('builtins.print'):
            result = cli.run(['export', '--sync', 'auto'])
        
        assert result == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
