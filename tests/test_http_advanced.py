"""
Tests for advanced HTTP client features (attachments, logging, share limits, batch operations)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lastpass.http import HTTPClient
from lastpass.session import Session
from lastpass.exceptions import NetworkException


@pytest.fixture
def mock_session():
    """Create a mock session"""
    session = Mock(spec=Session)
    session.id = "test_session_id"
    session.token = "test_token"
    return session


@pytest.fixture
def http_client():
    """Create HTTP client"""
    return HTTPClient()


class TestUploadAttachment:
    """Test attachment upload functionality"""
    
    def test_upload_attachment_success(self, http_client, mock_session):
        """Test successful attachment upload"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.upload_attachment(
                mock_session, 
                "account123", 
                "test.pdf", 
                b"PDF content here",
                None
            )
            
            mock_post.assert_called_once()
            args = mock_post.call_args
            assert args[0][0] == "show_website.php"  # endpoint
            # session is passed as keyword arg
            assert args.kwargs['session'] == mock_session
            
            params = args[0][1]  # data is 2nd positional arg
            assert params["cmd"] == "upload"
            assert params["aid"] == "account123"
            assert "mimetype" in params
    
    def test_upload_attachment_with_share(self, http_client, mock_session):
        """Test attachment upload to shared account"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.upload_attachment(
                mock_session, 
                "account456", 
                "doc.txt", 
                b"text content",
                "share789"
            )
            
            mock_post.assert_called_once()
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["sharedfolderid"] == "share789"
    
    def test_upload_attachment_network_error(self, http_client, mock_session):
        """Test attachment upload network failure"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            with pytest.raises(NetworkException, match="Failed to upload attachment"):
                http_client.upload_attachment(
                    mock_session, 
                    "account123", 
                    "test.pdf", 
                    b"content",
                    None
                )


class TestLogAccess:
    """Test access logging functionality"""
    
    def test_log_access_success(self, http_client, mock_session):
        """Test successful access logging"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.log_access(
                mock_session, 
                "account123", 
                "https://example.com",
                None
            )
            
            mock_post.assert_called_once()
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "loglogin"
            assert params["aid"] == "account123"
            assert params["url"] == "https://example.com"
    
    def test_log_access_with_share(self, http_client, mock_session):
        """Test logging access to shared account"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.log_access(
                mock_session, 
                "account456", 
                "https://test.com",
                "share789"
            )
            
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["sharedfolderid"] == "share789"
    
    def test_log_access_network_error_silenced(self, http_client, mock_session):
        """Test that log_access doesn't raise on network errors (fire-and-forget)"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            # Should not raise exception
            http_client.log_access(
                mock_session, 
                "account123", 
                "https://example.com",
                None
            )


class TestGetShareLimits:
    """Test get share limits functionality"""
    
    def test_get_share_limits_whitelist(self, http_client, mock_session):
        """Test getting whitelist configuration"""
        xml_response = """<?xml version="1.0"?>
<ok>
    <whitelist>
        <aid>account123</aid>
        <aid>account456</aid>
    </whitelist>
</ok>"""
        
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (xml_response.encode(), 200)
            
            result = http_client.get_share_limits(
                mock_session,
                "share789",
                "user123"
            )
            
            assert result["whitelist"] is True
            assert "account123" in result["account_ids"]
            assert "account456" in result["account_ids"]
    
    def test_get_share_limits_blacklist(self, http_client, mock_session):
        """Test getting blacklist configuration"""
        xml_response = """<?xml version="1.0"?>
<ok>
    <blacklist>
        <aid>account999</aid>
    </blacklist>
</ok>"""
        
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (xml_response.encode(), 200)
            
            result = http_client.get_share_limits(
                mock_session,
                "share789",
                "user123"
            )
            
            assert result["whitelist"] is False
            assert "account999" in result["account_ids"]
    
    def test_get_share_limits_no_restrictions(self, http_client, mock_session):
        """Test when there are no restrictions"""
        xml_response = """<?xml version="1.0"?><ok></ok>"""
        
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (xml_response.encode(), 200)
            
            result = http_client.get_share_limits(
                mock_session,
                "share789",
                "user123"
            )
            
            # Default to whitelist with empty list (no restrictions)
            assert result["whitelist"] is True
            assert result["account_ids"] == []
    
    def test_get_share_limits_network_error(self, http_client, mock_session):
        """Test network error when getting limits"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            with pytest.raises(NetworkException, match="Failed to get share limits"):
                http_client.get_share_limits(
                    mock_session,
                    "share789",
                    "user123"
                )


class TestSetShareLimits:
    """Test set share limits functionality"""
    
    def test_set_share_limits_whitelist(self, http_client, mock_session):
        """Test setting whitelist"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.set_share_limits(
                mock_session,
                "share789",
                "user123",
                True,  # whitelist
                ["account1", "account2"]
            )
            
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "setshareacctswhitelist"
            assert params["shareid"] == "share789"
            assert params["uid"] == "user123"
            assert "hidebydefault='1'" in params["white"]
            assert "account1" in params["white"]
    
    def test_set_share_limits_blacklist(self, http_client, mock_session):
        """Test setting blacklist"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.set_share_limits(
                mock_session,
                "share789",
                "user123",
                False,  # blacklist
                ["account3"]
            )
            
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "setshareacctsblacklist"
            assert "hidebydefault='0'" in params["black"]
    
    def test_set_share_limits_empty_list(self, http_client, mock_session):
        """Test setting limits with empty list (no restrictions)"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            http_client.set_share_limits(
                mock_session,
                "share789",
                "user123",
                True,
                []
            )
            
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "setshareacctswhitelist"
            # Should just have hidebydefault, no account IDs
            assert "<aid>" not in params["white"]
    
    def test_set_share_limits_network_error(self, http_client, mock_session):
        """Test network error when setting limits"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            with pytest.raises(NetworkException, match="Failed to set share limits"):
                http_client.set_share_limits(
                    mock_session,
                    "share789",
                    "user123",
                    True,
                    ["account1"]
                )


class TestBatchUploadAccounts:
    """Test batch account upload functionality"""
    
    def test_batch_upload_success(self, http_client, mock_session):
        """Test successful batch upload"""
        accounts = [
            {
                "name": "Account 1",
                "username": "user1",
                "password": "pass1",
                "url": "https://site1.com",
                "notes": "Notes 1",
                "group": "Group1"
            },
            {
                "name": "Account 2",
                "username": "user2",
                "password": "pass2"
            }
        ]
        
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            result = http_client.batch_upload_accounts(mock_session, accounts)
            
            mock_post.assert_called_once()
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "uploadaccounts"
            assert "accounts" in params
            # Should be XML formatted
            assert "<account>" in params["accounts"]
    
    def test_batch_upload_empty_list(self, http_client, mock_session):
        """Test batch upload with empty list"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"", 200)
            
            result = http_client.batch_upload_accounts(mock_session, [])
            
            # Should still work, just upload empty set
            assert result == {}
    
    def test_batch_upload_network_error(self, http_client, mock_session):
        """Test network error during batch upload"""
        accounts = [{"name": "Test", "username": "test"}]
        
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            with pytest.raises(NetworkException, match="Failed to batch upload accounts"):
                http_client.batch_upload_accounts(mock_session, accounts)


class TestPasswordChange:
    """Test password change functionality"""
    
    def test_change_password_start_success(self, http_client, mock_session):
        """Test starting password change"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"<ok></ok>", 200)
            
            result = http_client.change_password_start(
                mock_session,
                "user@example.com",
                "abc123hash"
            )
            
            assert result["status"] == "started"
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "getacctschangepw"
            assert params["username"] == "user@example.com"
            assert params["hash"] == "abc123hash"
    
    def test_change_password_start_network_error(self, http_client, mock_session):
        """Test password change start network error"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            with pytest.raises(NetworkException, match="Failed to start password change"):
                http_client.change_password_start(
                    mock_session,
                    "user@example.com",
                    "abc123hash"
                )
    
    def test_change_password_complete_success(self, http_client, mock_session):
        """Test completing password change"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"pwchangeok", 200)
            
            http_client.change_password_complete(
                mock_session,
                "user@example.com",
                "encrypted_username",
                "old_hash",
                "new_hash",
                100000,
                "reencrypt_data",
                "token123"
            )
            
            params = mock_post.call_args[0][1]  # data dict is 2nd positional arg
            assert params["cmd"] == "updatepassword"
            assert params["email"] == "user@example.com"
            assert params["token"] == "token123"
            assert params["newpasswordhash"] == "new_hash"
    
    def test_change_password_complete_network_error(self, http_client, mock_session):
        """Test password change complete network error"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"error", 500)
            
            with pytest.raises(NetworkException, match="Failed to complete password change"):
                http_client.change_password_complete(
                    mock_session,
                    "user@example.com",
                    "encrypted_username",
                    "old_hash",
                    "new_hash",
                    100000,
                    "reencrypt_data",
                    "token123"
                )
    
    def test_change_password_complete_invalid_response(self, http_client, mock_session):
        """Test password change complete with invalid response"""
        with patch.object(http_client, 'post') as mock_post:
            mock_post.return_value = (b"some response without pwchangeok", 200)
            
            with pytest.raises(NetworkException, match="Password change failed"):
                http_client.change_password_complete(
                    mock_session,
                    "user@example.com",
                    "encrypted_username",
                    "old_hash",
                    "new_hash",
                    100000,
                    "reencrypt_data",
                    "token123"
                )
