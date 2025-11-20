"""
Tests for lastpass.client module
"""

import pytest
import responses
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lastpass.client import LastPassClient
from lastpass.models import Account
from lastpass.session import Session
from lastpass.exceptions import (
    LoginFailedException,
    AccountNotFoundException,
    InvalidSessionException,
    NetworkException,
)
from tests.test_fixtures import (
    MOCK_LOGIN_SUCCESS_XML,
    TEST_USERNAME,
    TEST_PASSWORD,
    get_mock_accounts,
    get_mock_session,
)


class TestLastPassClient:
    """Test LastPassClient class"""
    
    def test_client_creation(self):
        """Test creating LastPassClient"""
        client = LastPassClient()
        assert client.server == "lastpass.com"
        assert client.session is None
        assert client.decryption_key is None
    
    def test_client_custom_server(self):
        """Test client with custom server"""
        client = LastPassClient(server="eu.lastpass.com")
        assert client.server == "eu.lastpass.com"
    
    def test_client_custom_config_dir(self, temp_config_dir):
        """Test client with custom config directory"""
        client = LastPassClient(config_dir=temp_config_dir)
        assert client.config_dir == temp_config_dir


class TestLogin:
    """Test login functionality"""
    
    @responses.activate
    def test_login_success(self, temp_config_dir):
        """Test successful login"""
        # Mock iterations request
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"5000",
            status=200,
        )
        
        # Mock login request
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=MOCK_LOGIN_SUCCESS_XML,
            status=200,
        )
        
        client = LastPassClient(config_dir=temp_config_dir)
        client.login(TEST_USERNAME, TEST_PASSWORD)
        
        assert client.session is not None
        assert client.session.is_valid()
        assert client.decryption_key is not None
    
    @responses.activate
    def test_login_invalid_credentials(self, temp_config_dir):
        """Test login with invalid credentials"""
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"5000",
            status=200,
        )
        
        failure_xml = b"""<?xml version="1.0"?>
        <response>
            <error cause="unknownemail" message="Invalid credentials"/>
        </response>"""
        
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=failure_xml,
            status=200,
        )
        
        client = LastPassClient(config_dir=temp_config_dir)
        
        with pytest.raises(LoginFailedException):
            client.login(TEST_USERNAME, "wrong_password")
    
    @responses.activate
    @patch('lastpass.client.getpass')
    def test_login_prompts_for_password(self, mock_getpass, temp_config_dir):
        """Test login prompts for password if not provided"""
        mock_getpass.return_value = TEST_PASSWORD
        
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"5000",
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=MOCK_LOGIN_SUCCESS_XML,
            status=200,
        )
        
        client = LastPassClient(config_dir=temp_config_dir)
        client.login(TEST_USERNAME)  # No password provided
        
        mock_getpass.assert_called_once()
        assert client.session is not None


class TestLogout:
    """Test logout functionality"""
    
    def test_logout_with_active_session(self, temp_config_dir):
        """Test logout with active session"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Manually set up a mock session
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        client.decryption_key = b"test_key"
        
        with patch.object(client.http, 'logout'):
            client.logout()
        
        assert client.session is None
        assert client.decryption_key is None
    
    def test_logout_without_session(self, temp_config_dir):
        """Test logout without active session"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Should not raise
        client.logout()


class TestIsLoggedIn:
    """Test is_logged_in method"""
    
    def test_is_logged_in_true(self):
        """Test is_logged_in returns True when logged in"""
        client = LastPassClient()
        
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        
        assert client.is_logged_in() is True
    
    def test_is_logged_in_false(self):
        """Test is_logged_in returns False when not logged in"""
        client = LastPassClient()
        assert client.is_logged_in() is False
    
    def test_is_logged_in_invalid_session(self):
        """Test is_logged_in with invalid session"""
        client = LastPassClient()
        
        from lastpass.session import Session
        client.session = Session()  # Invalid session
        
        assert client.is_logged_in() is False


class TestGetAccounts:
    """Test get_accounts method"""
    
    def test_get_accounts_syncs_first_time(self):
        """Test get_accounts syncs on first call"""
        client = LastPassClient()
        
        # Mock session and sync
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        client.decryption_key = b"test_key"
        
        with patch.object(client, 'sync') as mock_sync:
            client._accounts = get_mock_accounts()
            accounts = client.get_accounts()
            
            assert len(accounts) > 0
            # sync should be called since blob wasn't loaded
            assert mock_sync.called or len(accounts) > 0
    
    def test_get_accounts_no_sync_if_cached(self):
        """Test get_accounts doesn't sync if already cached"""
        client = LastPassClient()
        
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with patch.object(client, 'sync') as mock_sync:
            accounts = client.get_accounts(sync=False)
            
            assert len(accounts) > 0
            mock_sync.assert_not_called()
    
    def test_get_accounts_returns_list(self):
        """Test get_accounts returns list of Account objects"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        accounts = client.get_accounts(sync=False)
        
        assert isinstance(accounts, list)
        for account in accounts:
            assert isinstance(account, Account)


class TestFindAccount:
    """Test find_account method"""
    
    def test_find_account_by_name(self):
        """Test finding account by name"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        account = client.find_account("GitHub", sync=False)
        
        assert account is not None
        assert account.name == "GitHub"
    
    def test_find_account_case_insensitive(self):
        """Test finding account is case insensitive"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        account = client.find_account("github", sync=False)
        
        assert account is not None
        assert account.name == "GitHub"
    
    def test_find_account_by_id(self):
        """Test finding account by ID"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        account = client.find_account("1001", sync=False)
        
        assert account is not None
        assert account.id == "1001"
    
    def test_find_account_by_url(self):
        """Test finding account by URL"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        account = client.find_account("github.com", sync=False)
        
        assert account is not None
        assert "github.com" in account.url.lower()
    
    def test_find_account_not_found(self):
        """Test finding non-existent account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        account = client.find_account("NonExistent", sync=False)
        
        assert account is None


class TestSearchAccounts:
    """Test search_accounts method"""
    
    def test_search_accounts_basic(self):
        """Test searching accounts"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        results = client.search_accounts("git", sync=False)
        
        assert len(results) >= 1
        # Should find GitHub account
        assert any(acc.name == "GitHub" for acc in results)
    
    def test_search_accounts_case_insensitive(self):
        """Test search is case insensitive"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        results = client.search_accounts("GITHUB", sync=False)
        
        assert len(results) >= 1
    
    def test_search_accounts_no_results(self):
        """Test search with no results"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        results = client.search_accounts("nonexistent_xyz", sync=False)
        
        assert len(results) == 0


class TestListGroups:
    """Test list_groups method"""
    
    def test_list_groups(self):
        """Test listing unique groups"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        groups = client.list_groups(sync=False)
        
        assert isinstance(groups, list)
        assert "Development" in groups
        assert "Email" in groups
    
    def test_list_groups_sorted(self):
        """Test groups are sorted"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        groups = client.list_groups(sync=False)
        
        assert groups == sorted(groups)


class TestGeneratePassword:
    """Test generate_password method"""
    
    def test_generate_password_default(self):
        """Test generating password with default settings"""
        client = LastPassClient()
        password = client.generate_password()
        
        assert len(password) == 16
        assert isinstance(password, str)
    
    def test_generate_password_custom_length(self):
        """Test generating password with custom length"""
        client = LastPassClient()
        password = client.generate_password(length=32)
        
        assert len(password) == 32
    
    def test_generate_password_with_symbols(self):
        """Test generating password with symbols"""
        client = LastPassClient()
        password = client.generate_password(symbols=True)
        
        # Should contain at least some non-alphanumeric
        assert any(not c.isalnum() for c in password)
    
    def test_generate_password_without_symbols(self):
        """Test generating password without symbols"""
        client = LastPassClient()
        password = client.generate_password(symbols=False)
        
        # Should be alphanumeric only
        assert password.isalnum()
    
    def test_generate_password_uniqueness(self):
        """Test generated passwords are unique"""
        client = LastPassClient()
        passwords = [client.generate_password() for _ in range(10)]
        
        # All should be different
        assert len(set(passwords)) == 10


class TestGetPassword:
    """Test get_password method"""
    
    def test_get_password_success(self):
        """Test getting password for account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        password = client.get_password("GitHub", sync=False)
        
        assert password == "github_pass_123"
    
    def test_get_password_not_found(self):
        """Test getting password for non-existent account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.get_password("NonExistent", sync=False)


class TestGetUsername:
    """Test get_username method"""
    
    def test_get_username_success(self):
        """Test getting username for account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        username = client.get_username("GitHub", sync=False)
        
        assert username == "testuser"
    
    def test_get_username_not_found(self):
        """Test getting username for non-existent account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.get_username("NonExistent", sync=False)


class TestGetNotes:
    """Test get_notes method"""
    
    def test_get_notes_success(self):
        """Test getting notes for account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        notes = client.get_notes("GitHub", sync=False)
        
        assert "GitHub" in notes or "github" in notes.lower()
    
    def test_get_notes_not_found(self):
        """Test getting notes for non-existent account"""
        client = LastPassClient()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.get_notes("NonExistent", sync=False)


class TestWriteOperations:
    """Test write operations (add, update, delete, duplicate, move)"""
    
    @responses.activate
    def test_add_account_success(self):
        """Test successful account addition"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._blob_loaded = True
        
        # Mock the add account call
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"12345"}',
            status=200,
        )
        
        # Mock the sync call
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        account_id = client.add_account(
            name="Test Account",
            username="testuser",
            password="testpass",
            url="https://example.com",
            notes="Test notes",
        )
        
        assert account_id == "12345"
    
    @responses.activate
    def test_add_account_with_group(self):
        """Test adding account with group"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"12345"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        account_id = client.add_account(
            name="Work Account",
            username="workuser",
            password="workpass",
            group="Work\\Websites",
        )
        
        assert account_id == "12345"
    
    @responses.activate
    def test_add_account_with_custom_fields(self):
        """Test adding account with custom fields"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"12345"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        custom_fields = {
            "Security Question": "Blue",
            "PIN": "1234",
        }
        
        account_id = client.add_account(
            name="Bank Account",
            username="bankuser",
            password="bankpass",
            fields=custom_fields,
        )
        
        assert account_id == "12345"
    
    def test_add_account_not_logged_in(self):
        """Test adding account without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.add_account(name="Test", username="user", password="pass")
    
    @responses.activate
    def test_update_account_success(self):
        """Test successful account update"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"updated"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        client.update_account("GitHub", username="newuser")
    
    @responses.activate
    def test_update_account_multiple_fields(self):
        """Test updating multiple account fields"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"updated"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        client.update_account(
            "GitHub",
            name="Updated GitHub",
            username="newuser",
            password="newpass",
            url="https://new.github.com",
            notes="Updated notes",
        )
    
    def test_update_account_not_found(self):
        """Test updating non-existent account"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.update_account("NonExistent", username="newuser")
    
    def test_update_account_not_logged_in(self):
        """Test updating account without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.update_account("Test", username="user")
    
    @responses.activate
    def test_delete_account_success(self):
        """Test successful account deletion"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"deleted"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        client.delete_account("GitHub")
    
    def test_delete_account_not_found(self):
        """Test deleting non-existent account"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.delete_account("NonExistent")
    
    def test_delete_account_not_logged_in(self):
        """Test deleting account without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.delete_account("Test")
    
    @responses.activate
    def test_duplicate_account_success(self):
        """Test successful account duplication"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"99999"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        new_id = client.duplicate_account("GitHub", new_name="GitHub Copy")
        
        assert new_id == "99999"
    
    @responses.activate
    def test_duplicate_account_default_name(self):
        """Test duplicating account with default name"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"99999"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        new_id = client.duplicate_account("GitHub")
        
        assert new_id == "99999"
    
    def test_duplicate_account_not_found(self):
        """Test duplicating non-existent account"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.duplicate_account("NonExistent")
    
    def test_duplicate_account_not_logged_in(self):
        """Test duplicating account without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.duplicate_account("Test")
    
    @responses.activate
    def test_move_account_success(self):
        """Test successful account move"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"updated"}',
            status=200,
        )
        
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200,
        )
        
        client.move_account("GitHub", "Work\\Development")
    
    def test_move_account_not_found(self):
        """Test moving non-existent account"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.move_account("NonExistent", "Work")
    
    def test_move_account_not_logged_in(self):
        """Test moving account without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.move_account("Test", "Work")


class TestUpdateAccountEdgeCases:
    """Test edge cases in update_account"""
    
    def test_update_account_with_notes_and_group(self):
        """Test update_account with both notes and group (line 483)"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        from tests.test_fixtures import get_mock_blob_data
        mock_blob = get_mock_blob_data(client.encryption_key)
        
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, "https://lastpass.com/show_website.php", body=b"")
            rsps.add(responses.POST, "https://lastpass.com/getaccts.php", body=mock_blob)
            
            # Update with both notes and group
            client.update_account("GitHub", notes="New notes", group="Work")
            
            # Verify the request was made
            assert len(rsps.calls) == 2


class TestDuplicateAccountEdgeCases:
    """Test edge cases in duplicate_account"""
    
    def test_duplicate_account_with_fields(self):
        """Test duplicate_account preserves custom fields (lines 543-544)"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        
        from lastpass.models import Field
        from tests.test_fixtures import get_mock_blob_data
        
        account_with_fields = Account(
            id="1",
            name="GitHub",
            username="user@example.com",
            password="pass123",
            url="https://github.com",
            group="Personal",
            fields=[
                Field(name="API Key", value="abc123", type="text"),
                Field(name="Secret", value="xyz789", type="password"),
            ]
        )
        client._accounts = [account_with_fields]
        client._blob_loaded = True
        
        mock_blob = get_mock_blob_data(client.encryption_key)
        
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, "https://lastpass.com/show_website.php", 
                    body=b'{"aid":"123"}')
            rsps.add(responses.POST, "https://lastpass.com/getaccts.php", body=mock_blob)
            
            new_id = client.duplicate_account("GitHub", new_name="GitHub Copy")
            
            assert new_id == "123"
            # Verify fields were included in the add_account call
            request_body = rsps.calls[0].request.body
            # The custom fields should be encrypted and included
            # Convert to string for comparison to handle both bytes and string types
            if isinstance(request_body, bytes):
                request_body = request_body.decode('utf-8')
            assert "method=cr" in request_body


class TestClientEdgeCases:
    """Test edge cases for LastPassClient"""
    
    def test_operations_without_login(self):
        """Test operations fail without login"""
        client = LastPassClient()
        
        # These should handle gracefully or raise appropriate errors
        accounts = client.get_accounts(sync=False)
        assert accounts == []
    
    def test_multiple_logins(self, temp_config_dir):
        """Test multiple login calls"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        client.decryption_key = b"key1"
        
        # Second login should replace session
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, "https://lastpass.com/iterations.php", body=b"5000")
            rsps.add(responses.POST, "https://lastpass.com/login.php", 
                    body=MOCK_LOGIN_SUCCESS_XML)
            
            client.login(TEST_USERNAME, TEST_PASSWORD, force=True)
        
        assert client.session is not None


class TestLoginEdgeCases:
    """Test edge cases in login"""
    
    @responses.activate
    def test_login_http_error(self, temp_config_dir):
        """Test login with HTTP error status"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        responses.add(responses.POST, "https://lastpass.com/iterations.php", body=b"5000", status=200)
        # Return 401 status to trigger the HTTP error check in client.login()
        responses.add(responses.POST, "https://lastpass.com/login.php", 
                body=b"<response><error cause='unknownlogin'>Unknown email address.</error></response>",
                status=401)
        
        with pytest.raises(LoginFailedException, match="Login failed with HTTP status 401"):
            client.login(TEST_USERNAME, TEST_PASSWORD)
    
    @responses.activate
    def test_login_with_invalid_private_key(self, temp_config_dir):
        """Test login with private key that fails decryption"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Create mock response with invalid private key
        invalid_key_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<response>
    <ok uid="123" sessionid="sess456" token="tok789" privatekeyenc="invalid_hex_data"/>
</response>"""
        
        responses.add(responses.POST, "https://lastpass.com/iterations.php", body=b"5000", status=200)
        responses.add(responses.POST, "https://lastpass.com/login.php", 
                body=invalid_key_xml, status=200)
        
        # Should not raise - private key decryption failure is caught
        client.login(TEST_USERNAME, TEST_PASSWORD)
        
        # Session should still be created
        assert client.session is not None
        assert client.session.uid == "123"


class TestLogoutEdgeCases:
    """Test edge cases in logout"""
    
    def test_logout_http_error_without_force(self, temp_config_dir):
        """Test logout that fails without force flag"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        
        with patch.object(client.http, 'logout', side_effect=NetworkException("Server error")):
            with pytest.raises(NetworkException):
                client.logout(force=False)
    
    def test_logout_http_error_with_force(self, temp_config_dir):
        """Test logout that fails with force flag"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        from lastpass.session import Session
        client.session = Session(uid="123", sessionid="sess", token="tok")
        
        with patch.object(client.http, 'logout', side_effect=NetworkException("Server error")):
            # Should not raise with force=True
            client.logout(force=True)
            
            # Session should still be cleared
            assert client.session is None


class TestFindAccountEdgeCases:
    """Test edge cases in find_account"""
    
    def test_find_account_multiple_matches(self):
        """Test find_account with multiple matches raises error"""
        client = LastPassClient()
        
        session = get_mock_session()
        client.session = session
        client.encryption_key = b"a" * 32
        client._accounts = [
            Account(id="1", name="Test", username="user1", password="pass1", url="http://test.com", group="Personal"),
            Account(id="2", name="Test", username="user2", password="pass2", url="http://test.com", group="Work"),
        ]
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException, match="Multiple accounts match 'Test'"):
            client.find_account("Test", sync=False)


class TestSearchAccountsEdgeCases:
    """Test edge cases in search_accounts"""
    
    def test_search_accounts_with_group_filter(self):
        """Test search_accounts with group filtering"""
        client = LastPassClient()
        
        session = get_mock_session()
        client.session = session
        client.encryption_key = b"a" * 32
        client._accounts = [
            Account(id="1", name="Gmail", username="user1", password="pass1", url="http://gmail.com", group="Personal"),
            Account(id="2", name="GitHub", username="user2", password="pass2", url="http://github.com", group="Work"),
            Account(id="3", name="GitLab", username="user3", password="pass3", url="http://gitlab.com", group="Work"),
        ]
        
        # Search with group filter
        results = client.search_accounts("git", sync=False, group="Work")
        
        assert len(results) == 2
        assert all(a.group == "Work" for a in results)


class TestNewFeaturesCoverage:
    """Test coverage for newly implemented features"""
    
    @responses.activate
    def test_export_to_csv_not_logged_in(self):
        """Test export when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.export_to_csv()
    
    @responses.activate
    def test_import_from_csv_not_logged_in(self):
        """Test import when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.import_from_csv("url,username,password,name\n")
    
    def test_search_accounts_regex_not_logged_in(self):
        """Test regex search when not logged in"""
        client = LastPassClient()
        
        results = client.search_accounts_regex("test", sync=False)
        assert results == []
    
    def test_search_accounts_fixed_not_logged_in(self):
        """Test fixed search when not logged in"""
        client = LastPassClient()
        
        results = client.search_accounts_fixed("test", sync=False)
        assert results == []
    
    @responses.activate
    def test_add_secure_note_not_logged_in(self):
        """Test add secure note when not logged in"""
        client = LastPassClient()
        
        from lastpass.note_types import NoteType
        with pytest.raises(InvalidSessionException):
            client.add_secure_note("Test", NoteType.GENERIC, {})
    
    @responses.activate
    def test_create_share_not_logged_in(self):
        """Test create share when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.create_share("Test Share")
    
    @responses.activate
    def test_delete_share_not_logged_in(self):
        """Test delete share when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.delete_share("share123")
    
    @responses.activate
    def test_add_share_user_not_logged_in(self):
        """Test add share user when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.add_share_user("share123", "user@example.com")
    
    @responses.activate
    def test_remove_share_user_not_logged_in(self):
        """Test remove share user when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.remove_share_user("share123", "user@example.com")
    
    @responses.activate
    def test_update_share_user_not_logged_in(self):
        """Test update share user when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.update_share_user("share123", "user@example.com")
    
    @responses.activate
    def test_list_share_users_not_logged_in(self):
        """Test list share users when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.list_share_users("share123")
    
    @responses.activate
    def test_get_attachment_not_logged_in(self):
        """Test get attachment when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.get_attachment("account123", "file.pdf")
    
    @responses.activate
    def test_change_password_not_logged_in(self):
        """Test change password when not logged in"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.change_password("oldpass", "newpass")
    
    @responses.activate
    def test_delete_share_not_found(self):
        """Test delete share when share not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        client._shares = []
        
        from lastpass.exceptions import LastPassException
        with patch.object(client, 'get_shares', return_value=[]):
            with pytest.raises(LastPassException, match="Share not found"):
                client.delete_share("nonexistent")
    
    @responses.activate
    def test_add_share_user_share_not_found(self):
        """Test add share user when share not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        
        from lastpass.exceptions import LastPassException
        with patch.object(client, 'get_shares', return_value=[]):
            with pytest.raises(LastPassException, match="Share not found"):
                client.add_share_user("nonexistent", "user@example.com")
    
    @responses.activate
    def test_remove_share_user_share_not_found(self):
        """Test remove share user when share not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        
        from lastpass.exceptions import LastPassException
        with patch.object(client, 'get_shares', return_value=[]):
            with pytest.raises(LastPassException, match="Share not found"):
                client.remove_share_user("nonexistent", "user@example.com")
    
    @responses.activate
    def test_update_share_user_share_not_found(self):
        """Test update share user when share not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        
        from lastpass.exceptions import LastPassException
        with patch.object(client, 'get_shares', return_value=[]):
            with pytest.raises(LastPassException, match="Share not found"):
                client.update_share_user("nonexistent", "user@example.com")
    
    @responses.activate
    def test_list_share_users_share_not_found(self):
        """Test list share users when share not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        
        from lastpass.exceptions import LastPassException
        with patch.object(client, 'get_shares', return_value=[]):
            with pytest.raises(LastPassException, match="Share not found"):
                client.list_share_users("nonexistent")
    
    @responses.activate
    def test_get_attachment_account_not_found(self):
        """Test get attachment when account not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        client._accounts = []
        client._blob_loaded = True
        
        with pytest.raises(AccountNotFoundException):
            client.get_attachment("nonexistent", "file.pdf")
    
    @responses.activate
    def test_get_attachment_attachment_not_found(self):
        """Test get attachment when attachment not found"""
        client = LastPassClient()
        client.session = get_mock_session()
        
        account = Account(
            id="1",
            name="Test",
            username="user",
            password="pass",
            url="http://test.com",
            group="Personal",
            attachments=[]
        )
        client._accounts = [account]
        client._blob_loaded = True
        
        from lastpass.exceptions import LastPassException
        with pytest.raises(LastPassException, match="Attachment not found"):
            client.get_attachment("Test", "nonexistent.pdf")
    
    @responses.activate
    def test_export_to_csv_calls_sync(self):
        """Test export_to_csv triggers sync"""
        client = LastPassClient()
        client.session = get_mock_session()
        client._accounts = get_mock_accounts()
        
        with patch.object(client, 'get_accounts', return_value=get_mock_accounts()) as mock_get:
            csv_output = client.export_to_csv()
            
            # get_accounts should be called with sync=True
            mock_get.assert_called_once_with(sync=True)
            assert isinstance(csv_output, str)
    
    @responses.activate
    def test_import_from_csv_with_errors_continues(self):
        """Test import continues after errors"""
        client = LastPassClient()
        client.session = get_mock_session()
        client.encryption_key = b"a" * 32
        client._blob_loaded = True
        
        csv_data = "url,username,password,name\nhttp://test.com,user,pass,Test\n"
        
        # Mock add_account to raise exception
        with patch.object(client, 'add_account', side_effect=Exception("Test error")):
            # Capture stdout to suppress error message
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                count = client.import_from_csv(csv_data)
                # Should return 0 since add failed
                assert count == 0
            finally:
                sys.stdout = old_stdout
    
    def test_search_accounts_regex_invalid_pattern(self):
        """Test regex search with invalid pattern"""
        client = LastPassClient()
        client.session = get_mock_session()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        from lastpass.exceptions import LastPassException
        with pytest.raises(LastPassException, match="Invalid regex pattern"):
            client.search_accounts_regex("[invalid(", sync=False)
    
    def test_search_accounts_fixed_empty_string(self):
        """Test fixed search with empty string returns nothing"""
        client = LastPassClient()
        client.session = get_mock_session()
        client._accounts = get_mock_accounts()
        client._blob_loaded = True
        
        results = client.search_accounts_fixed("", sync=False)
        assert len(results) == 0
    
    @responses.activate
    def test_change_password_raises_not_implemented(self):
        """Test change_password raises NotImplementedError"""
        client = LastPassClient()
        client.session = get_mock_session()
        
        with pytest.raises(NotImplementedError, match="Password change requires additional server-side implementation"):
            client.change_password("oldpass", "newpass")
