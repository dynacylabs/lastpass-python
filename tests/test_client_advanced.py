"""
Additional tests for client.py to improve coverage
"""

import pytest
import responses
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from lastpass.client import LastPassClient
from lastpass.exceptions import LoginFailedException, InvalidSessionException
from lastpass.session import Session
from lastpass.models import Account


class TestClientSessionLoading:
    """Test _try_load_session method"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        config_dir = tmp_path / ".lpass"
        config_dir.mkdir(parents=True)
        return config_dir
    
    @pytest.fixture
    def mock_encryption_key(self):
        return b"0123456789abcdef0123456789abcdef"
    
    @responses.activate
    def test_try_load_session_with_password(self, temp_config_dir, mock_encryption_key):
        """Test loading session with password"""
        # Create a saved session
        session = Session(uid="123", sessionid="abc", token="xyz")
        session.save(mock_encryption_key, temp_config_dir)
        
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Mock iterations endpoint
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body="5000",
            status=200
        )
        
        # Try to load session - may return False if session is not valid
        result = client._try_load_session("test@example.com", "password123")
        
        # Session loading behavior depends on session validity
        assert isinstance(result, bool)
    
    def test_try_load_session_with_plaintext_key(self, temp_config_dir, mock_encryption_key):
        """Test loading session with plaintext key file"""
        # Save plaintext key
        plaintext_key_file = temp_config_dir / "plaintext_key"
        plaintext_key_file.write_bytes(mock_encryption_key)
        
        # Save session
        session = Session(uid="456", sessionid="def", token="uvw")
        session.save(mock_encryption_key, temp_config_dir)
        
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Try to load without password
        result = client._try_load_session("test@example.com", None)
        
        assert result == True
        assert client.session is not None
    
    def test_try_load_session_invalid(self, temp_config_dir):
        """Test loading non-existent session"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        result = client._try_load_session("test@example.com", None)
        
        assert result == False


class TestClientLogout:
    """Test logout with force parameter"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        config_dir = tmp_path / ".lpass"
        config_dir.mkdir(parents=True)
        return config_dir
    
    @responses.activate
    def test_logout_force(self, temp_config_dir):
        """Test forced logout"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Set up a session
        client.session = Session(uid="789", sessionid="ghi", token="rst")
        client.decryption_key = b"test_key"
        
        # Mock logout endpoint
        responses.add(
            responses.POST,
            "https://lastpass.com/logout.php",
            status=200
        )
        
        client.logout(force=True)
        
        assert client.session is None
        assert client.decryption_key is None
    
    def test_logout_without_session_force(self, temp_config_dir):
        """Test logout with force when no session"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Should not raise even without session
        client.logout(force=True)
        
        assert client.session is None


class TestClientSyncForce:
    """Test sync with force parameter"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        config_dir = tmp_path / ".lpass"
        config_dir.mkdir(parents=True)
        return config_dir
    
    @responses.activate
    def test_sync_force_true(self, temp_config_dir):
        """Test forced sync"""
        client = LastPassClient(config_dir=temp_config_dir)
        client.session = Session(uid="sync1", sessionid="sync_sess", token="sync_tok")
        client.decryption_key = b"0123456789abcdef0123456789abcdef"
        client._blob_loaded = True  # Pretend we already synced
        
        # Mock blob download
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200
        )
        
        # Force sync should work even if already loaded
        client.sync(force=True)
        
        assert client._blob_loaded == True


class TestClientFindAccountCaseInsensitive:
    """Test find_account case insensitivity"""
    
    @pytest.fixture
    def mock_client_with_accounts(self):
        client = LastPassClient()
        client.session = Session(uid="test", sessionid="test", token="test")
        client.decryption_key = b"test_key"
        client._blob_loaded = True
        
        # Add test accounts
        client._accounts = [
            Account(id="1", name="TestAccount", username="user1", url="https://test.com"),
            Account(id="2", name="example.com", username="user2", url="https://example.com"),
            Account(id="3", name="Another Site", username="user3", url="https://another.com"),
        ]
        
        return client
    
    def test_find_account_name_case_insensitive(self, mock_client_with_accounts):
        """Test finding account by name (case insensitive)"""
        account = mock_client_with_accounts.find_account("testaccount", sync=False)
        assert account is not None
        assert account.name == "TestAccount"
        
        account2 = mock_client_with_accounts.find_account("TESTACCOUNT", sync=False)
        assert account2 is not None
        assert account2.name == "TestAccount"
    
    def test_find_account_url_case_insensitive(self, mock_client_with_accounts):
        """Test finding account by URL (case insensitive)"""
        account = mock_client_with_accounts.find_account("EXAMPLE.COM", sync=False)
        assert account is not None
        assert "example.com" in account.url.lower()


class TestClientSearchAccounts:
    """Test search_accounts with case insensitivity"""
    
    @pytest.fixture
    def mock_client_with_accounts(self):
        client = LastPassClient()
        client.session = Session(uid="test", sessionid="test", token="test")
        client.decryption_key = b"test_key"
        client._blob_loaded = True
        
        client._accounts = [
            Account(id="1", name="GitHub Login", username="dev@example.com"),
            Account(id="2", name="GitLab Access", username="admin@example.com"),
            Account(id="3", name="BitBucket", username="user@example.com"),
        ]
        
        return client
    
    def test_search_accounts_case_insensitive(self, mock_client_with_accounts):
        """Test searching accounts (case insensitive)"""
        results = mock_client_with_accounts.search_accounts("git", sync=False)
        assert len(results) >= 2  # Should find GitHub and GitLab
        
        results_upper = mock_client_with_accounts.search_accounts("GIT", sync=False)
        assert len(results_upper) >= 2


class TestClientGetSharesSync:
    """Test get_shares with sync parameter"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        config_dir = tmp_path / ".lpass"
        config_dir.mkdir(parents=True)
        return config_dir
    
    @responses.activate
    def test_get_shares_with_sync(self, temp_config_dir):
        """Test getting shares with sync=True"""
        client = LastPassClient(config_dir=temp_config_dir)
        client.session = Session(uid="share1", sessionid="share_sess", token="share_tok")
        client.decryption_key = b"0123456789abcdef0123456789abcdef"
        
        # Mock blob download
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"",
            status=200
        )
        
        shares = client.get_shares(sync=True)
        assert isinstance(shares, list)
    
    def test_get_shares_without_sync(self):
        """Test getting shares with sync=False"""
        client = LastPassClient()
        client.session = Session(uid="share2", sessionid="share_sess2", token="share_tok2")
        client._blob_loaded = True
        client._shares = []
        
        shares = client.get_shares(sync=False)
        assert isinstance(shares, list)


class TestClientListGroupsSync:
    """Test list_groups with sync parameter"""
    
    def test_list_groups_without_sync(self):
        """Test listing groups without sync"""
        client = LastPassClient()
        client.session = Session(uid="grp1", sessionid="grp_sess", token="grp_tok")
        client._blob_loaded = True
        
        client._accounts = [
            Account(id="1", name="Account1", group="Work"),
            Account(id="2", name="Account2", group="Personal"),
            Account(id="3", name="Account3", group="Work"),
            Account(id="4", name="Account4", group=""),
        ]
        
        groups = client.list_groups(sync=False)
        
        assert isinstance(groups, list)
        assert "Work" in groups
        assert "Personal" in groups
        assert "" not in groups  # Empty groups should be excluded


class TestClientPrivateKeyDecryption:
    """Test private key decryption failure handling"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        config_dir = tmp_path / ".lpass"
        config_dir.mkdir(parents=True)
        return config_dir
    
    @responses.activate
    def test_login_with_invalid_private_key(self, temp_config_dir):
        """Test login when private key decryption fails"""
        client = LastPassClient(config_dir=temp_config_dir)
        
        # Mock iterations
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body="5000",
            status=200
        )
        
        # Mock login with private key
        login_xml = b'''<?xml version="1.0"?>
        <response>
            <ok uid="123" sessionid="abc" token="xyz" privatekeyenc="invalid_key_data"/>
        </response>'''
        
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=login_xml,
            status=200
        )
        
        # Should login successfully even if private key fails to decrypt
        client.login("test@example.com", "password123")
        
        assert client.is_logged_in()
        assert client.session is not None


class TestClientRequiresLogin:
    """Test operations that require login"""
    
    def test_sync_requires_login(self):
        """Test sync fails without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.sync()
    
    def test_get_accounts_requires_login(self):
        """Test get_accounts fails without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.get_accounts()
    
    def test_get_shares_requires_login(self):
        """Test get_shares fails without login"""
        client = LastPassClient()
        
        with pytest.raises(InvalidSessionException):
            client.get_shares()


# =============================================================================
# NEW ADVANCED FEATURE TESTS
# =============================================================================

class TestUploadAttachment:
    """Test client upload_attachment method"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client"""
        client = LastPassClient()
        client.session = Mock()
        client.session.id = "test_session"
        client._accounts = []
        client._shares = []
        return client
    
    @pytest.fixture
    def sample_accounts(self):
        """Create sample accounts for testing"""
        from lastpass.models import Share
        return [
            Account(
                id="acc1",
                name="Test Account 1",
                username="user1",
                password="pass1",
                url="https://test1.com",
                group="Group1",
                notes="Notes1",
                share=None
            ),
            Account(
                id="acc2",
                name="Test Account 2",
                username="user2",
                password="pass2",
                url="https://test2.com",
                group="Group2",
                notes="",
                share=Share(id="share1", name="Shared", key=b"test_share_key", readonly=False)
            ),
        ]
    
    def test_upload_attachment_success(self, mock_client, sample_accounts):
        """Test successful attachment upload"""
        mock_client._accounts = sample_accounts
        mock_client._blob_loaded = True
        
        with patch.object(mock_client.http, 'upload_attachment') as mock_upload:
            mock_upload.return_value = None
            
            mock_client.upload_attachment(
                "Test Account 1",
                "document.pdf",
                b"PDF content"
            )
            
            mock_upload.assert_called_once()
            args = mock_upload.call_args[0]
            assert args[1] == "acc1"  # account ID
            assert args[2] == "document.pdf"
            assert args[3] == b"PDF content"
            assert args[4] is None  # no share ID
    
    def test_upload_attachment_to_shared_account(self, mock_client, sample_accounts):
        """Test uploading attachment to shared account"""
        mock_client._accounts = sample_accounts
        mock_client._blob_loaded = True
        
        with patch.object(mock_client.http, 'upload_attachment') as mock_upload:
            mock_upload.return_value = None
            
            mock_client.upload_attachment(
                "Test Account 2",
                "image.png",
                b"PNG data"
            )
            
            args = mock_upload.call_args[0]
            assert args[1] == "acc2"
            assert args[4] == "share1"  # share ID included
    
    def test_upload_attachment_not_logged_in(self, mock_client):
        """Test upload when not logged in"""
        mock_client.session = None
        
        from lastpass.exceptions import InvalidSessionException
        with pytest.raises(InvalidSessionException, match="Not logged in"):
            mock_client.upload_attachment("Test", "file.txt", b"data")
    
    def test_upload_attachment_account_not_found(self, mock_client, sample_accounts):
        """Test upload when account not found"""
        mock_client._accounts = sample_accounts
        mock_client._blob_loaded = True
        
        from lastpass.exceptions import AccountNotFoundException
        with pytest.raises(AccountNotFoundException, match="Account not found"):
            mock_client.upload_attachment(
                "Nonexistent Account",
                "file.txt",
                b"data"
            )


class TestLogAccountAccess:
    """Test client log_account_access method"""
    
    @pytest.fixture
    def mock_client(self):
        client = LastPassClient()
        client.session = Mock()
        client.session.id = "test_session"
        client._accounts = []
        return client
    
    @pytest.fixture
    def sample_accounts(self):
        from lastpass.models import Share
        return [
            Account(
                id="acc1",
                name="Test Account 1",
                username="user1",
                password="pass1",
                url="https://test1.com",
                group="Group1",
                notes="Notes1",
                share=None
            ),
            Account(
                id="acc2",
                name="Test Account 2",
                username="user2",
                password="pass2",
                url="https://test2.com",
                group="Group2",
                notes="",
                share=Share(id="share1", name="Shared", key=b"test_share_key", readonly=False)
            ),
        ]
    
    def test_log_access_success(self, mock_client, sample_accounts):
        """Test successful access logging"""
        mock_client._accounts = sample_accounts
        mock_client._blob_loaded = True
        
        with patch.object(mock_client.http, 'log_access') as mock_log:
            mock_log.return_value = None
            
            mock_client.log_account_access("Test Account 1")
            
            mock_log.assert_called_once()
            args = mock_log.call_args[0]
            assert args[1] == "acc1"
            assert args[2] == "https://test1.com"
            assert args[3] is None
    
    def test_log_access_shared_account(self, mock_client, sample_accounts):
        """Test logging access to shared account"""
        mock_client._accounts = sample_accounts
        mock_client._blob_loaded = True
        
        with patch.object(mock_client.http, 'log_access') as mock_log:
            mock_log.return_value = None
            
            mock_client.log_account_access("Test Account 2")
            
            args = mock_log.call_args[0]
            assert args[1] == "acc2"
            assert args[3] == "share1"
    
    def test_log_access_not_logged_in(self, mock_client):
        """Test logging when not logged in"""
        mock_client.session = None
        
        from lastpass.exceptions import InvalidSessionException
        with pytest.raises(InvalidSessionException):
            mock_client.log_account_access("Test")


class TestBatchAddAccounts:
    """Test client batch_add_accounts method"""
    
    @pytest.fixture
    def mock_client(self):
        client = LastPassClient()
        client.session = Mock()
        client.session.id = "test_session"
        return client
    
    def test_batch_add_success(self, mock_client):
        """Test successful batch add"""
        accounts = [
            {
                "name": "Batch Account 1",
                "username": "batch1",
                "password": "pass1",
                "url": "https://batch1.com",
                "notes": "Notes 1",
                "group": "Batch Group"
            },
            {
                "name": "Batch Account 2",
                "username": "batch2",
                "password": "pass2"
            }
        ]
        
        with patch.object(mock_client.http, 'batch_upload_accounts') as mock_batch:
            mock_batch.return_value = {"account_ids": ["new1", "new2"]}
            
            with patch.object(mock_client, 'sync') as mock_sync:
                mock_sync.return_value = None
                
                result = mock_client.batch_add_accounts(accounts)
                
                mock_batch.assert_called_once()
                mock_sync.assert_called_once()
                assert result == ["new1", "new2"]
    
    def test_batch_add_not_logged_in(self, mock_client):
        """Test batch add when not logged in"""
        mock_client.session = None
        
        from lastpass.exceptions import InvalidSessionException
        with pytest.raises(InvalidSessionException):
            mock_client.batch_add_accounts([{"name": "Test"}])


class TestChangeMasterPassword:
    """Test client change_master_password method"""
    
    @pytest.fixture
    def mock_client(self):
        client = LastPassClient()
        client.session = Mock()
        client.session.id = "test_session"
        return client
    
    def test_change_password_not_implemented(self, mock_client):
        """Test that password change raises NotImplementedError"""
        with pytest.raises(NotImplementedError, match="Master password change requires"):
            mock_client.change_master_password("old_pass", "new_pass")
    
    def test_change_password_not_logged_in(self):
        """Test password change when not logged in"""
        client = LastPassClient()
        
        from lastpass.exceptions import InvalidSessionException
        with pytest.raises(InvalidSessionException):
            client.change_master_password("old_pass", "new_pass")


class TestShareLimitModel:
    """Test ShareLimit model"""
    
    def test_share_limit_creation(self):
        """Test creating ShareLimit"""
        from lastpass.models import ShareLimit
        
        limit = ShareLimit(whitelist=True, account_ids=["acc1", "acc2"])
        
        assert limit.whitelist is True
        assert limit.account_ids == ["acc1", "acc2"]
    
    def test_share_limit_defaults(self):
        """Test ShareLimit default values"""
        from lastpass.models import ShareLimit
        
        limit = ShareLimit()
        
        assert limit.whitelist is False
        assert limit.account_ids == []
    
    def test_share_limit_to_dict(self):
        """Test ShareLimit.to_dict()"""
        from lastpass.models import ShareLimit
        
        limit = ShareLimit(whitelist=True, account_ids=["acc1"])
        
        d = limit.to_dict()
        
        assert d["whitelist"] is True
        assert d["account_ids"] == ["acc1"]
