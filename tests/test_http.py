"""
Tests for lastpass.http module
"""

import pytest
import responses
from requests.exceptions import RequestException
from unittest.mock import patch
from lastpass.http import HTTPClient
from lastpass.session import Session
from lastpass.exceptions import NetworkException
from tests.test_fixtures import MOCK_LOGIN_SUCCESS_XML, get_mock_session


class TestHTTPClient:
    """Test HTTPClient class"""
    
    def test_http_client_creation(self):
        """Test creating HTTPClient"""
        client = HTTPClient()
        assert client.server == "lastpass.com"
        assert "lastpass.com" in client.base_url
    
    def test_http_client_custom_server(self):
        """Test HTTPClient with custom server"""
        client = HTTPClient(server="eu.lastpass.com")
        assert client.server == "eu.lastpass.com"
        assert "eu.lastpass.com" in client.base_url
    
    @responses.activate
    def test_post_request(self):
        """Test basic POST request"""
        responses.add(
            responses.POST,
            "https://lastpass.com/test.php",
            body=b"response",
            status=200,
        )
        
        client = HTTPClient()
        content, status = client.post("test.php", {"data": "test"})
        
        assert status == 200
        assert content == b"response"
    
    @responses.activate
    def test_post_with_session(self):
        """Test POST with session credentials"""
        responses.add(
            responses.POST,
            "https://lastpass.com/test.php",
            body=b"authenticated",
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        content, status = client.post("test.php", {}, session=session)
        
        assert status == 200
        # Verify session credentials were added to request
        assert len(responses.calls) == 1
        assert "token=tok" in responses.calls[0].request.body
        assert "sessionid=sess" in responses.calls[0].request.body
    
    def test_post_network_error(self):
        """Test POST with network error"""
        client = HTTPClient(server="nonexistent.invalid")
        
        with pytest.raises(NetworkException) as exc_info:
            client.post("test.php", {})
        
        assert "HTTP request failed" in str(exc_info.value)


class TestGetIterations:
    """Test get_iterations method"""
    
    @responses.activate
    def test_get_iterations_success(self):
        """Test getting iteration count"""
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"5000",
            status=200,
        )
        
        client = HTTPClient()
        iterations = client.get_iterations("user@example.com")
        
        assert iterations == 5000
    
    @responses.activate
    def test_get_iterations_high_value(self):
        """Test getting high iteration count"""
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"100000",
            status=200,
        )
        
        client = HTTPClient()
        iterations = client.get_iterations("user@example.com")
        
        assert iterations == 100000
    
    @responses.activate
    def test_get_iterations_invalid_response(self):
        """Test getting iterations with invalid response"""
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"not a number",
            status=200,
        )
        
        client = HTTPClient()
        
        with pytest.raises(NetworkException) as exc_info:
            client.get_iterations("user@example.com")
        
        assert "Invalid iterations response" in str(exc_info.value)
    
    @responses.activate
    def test_get_iterations_too_low(self):
        """Test iteration count that's too low"""
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"1",
            status=200,
        )
        
        client = HTTPClient()
        
        with pytest.raises(NetworkException) as exc_info:
            client.get_iterations("user@example.com")
        
        assert "Invalid iteration count" in str(exc_info.value)
    
    @responses.activate
    def test_get_iterations_http_error(self):
        """Test getting iterations with HTTP error"""
        responses.add(
            responses.POST,
            "https://lastpass.com/iterations.php",
            body=b"error",
            status=500,
        )
        
        client = HTTPClient()
        
        with pytest.raises(NetworkException) as exc_info:
            client.get_iterations("user@example.com")
        
        assert "Failed to get iterations" in str(exc_info.value)


class TestLogin:
    """Test login method"""
    
    @responses.activate
    def test_login_success(self):
        """Test successful login"""
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=MOCK_LOGIN_SUCCESS_XML,
            status=200,
        )
        
        client = HTTPClient()
        content, status = client.login(
            username="user@example.com",
            login_key="abcd1234",
            iterations=5000,
        )
        
        assert status == 200
        assert b"<ok" in content
    
    @responses.activate
    def test_login_with_otp(self):
        """Test login with OTP"""
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=MOCK_LOGIN_SUCCESS_XML,
            status=200,
        )
        
        client = HTTPClient()
        content, status = client.login(
            username="user@example.com",
            login_key="abcd1234",
            iterations=5000,
            otp="123456",
        )
        
        assert status == 200
        # Verify OTP was included in request
        assert len(responses.calls) == 1
        assert "otp=123456" in responses.calls[0].request.body
    
    @responses.activate
    def test_login_with_trust(self):
        """Test login with trust device"""
        responses.add(
            responses.POST,
            "https://lastpass.com/login.php",
            body=MOCK_LOGIN_SUCCESS_XML,
            status=200,
        )
        
        client = HTTPClient()
        content, status = client.login(
            username="user@example.com",
            login_key="abcd1234",
            iterations=5000,
            trust=True,
        )
        
        assert status == 200
        # Verify trust flag was included
        assert "trust=1" in responses.calls[0].request.body


class TestLogout:
    """Test logout method"""
    
    @responses.activate
    def test_logout_success(self):
        """Test successful logout"""
        responses.add(
            responses.POST,
            "https://lastpass.com/logout.php",
            body=b"OK",
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        # Should not raise
        client.logout(session)
    
    @responses.activate
    def test_logout_failure_ignored(self):
        """Test logout failure is ignored"""
        responses.add(
            responses.POST,
            "https://lastpass.com/logout.php",
            body=b"error",
            status=500,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        # Should not raise even on failure
        client.logout(session)


class TestDownloadBlob:
    """Test download_blob method"""
    
    @responses.activate
    def test_download_blob_success(self):
        """Test downloading vault blob"""
        blob_data = b"encrypted_blob_data_here"
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=blob_data,
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        blob = client.download_blob(session)
        assert blob == blob_data
    
    @responses.activate
    def test_download_blob_http_error(self):
        """Test download blob with HTTP error"""
        responses.add(
            responses.POST,
            "https://lastpass.com/getaccts.php",
            body=b"error",
            status=401,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        with pytest.raises(NetworkException) as exc_info:
            client.download_blob(session)
        
        assert "Failed to download blob" in str(exc_info.value)


class TestUploadBlob:
    """Test upload_blob method"""
    
    @responses.activate
    def test_upload_blob_success(self):
        """Test uploading vault blob"""
        responses.add(
            responses.POST,
            "https://lastpass.com/update.php",
            body=b"OK",
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        # Should not raise
        client.upload_blob(session, "encrypted_blob")
    
    @responses.activate
    def test_upload_blob_error(self):
        """Test upload blob with error"""
        responses.add(
            responses.POST,
            "https://lastpass.com/update.php",
            body=b"error",
            status=500,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        with pytest.raises(NetworkException) as exc_info:
            client.upload_blob(session, "encrypted_blob")
        
        assert "Failed to upload blob" in str(exc_info.value)


class TestGetAttachment:
    """Test get_attachment method"""
    
    @responses.activate
    def test_get_attachment_success(self):
        """Test downloading attachment"""
        attachment_data = b"file contents here"
        responses.add(
            responses.POST,
            "https://lastpass.com/getattach.php",
            body=attachment_data,
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        data = client.get_attachment(session, "att_123")
        assert data == attachment_data
    
    @responses.activate
    def test_get_attachment_with_share(self):
        """Test downloading attachment from shared folder"""
        responses.add(
            responses.POST,
            "https://lastpass.com/getattach.php",
            body=b"data",
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        data = client.get_attachment(session, "att_123", share_id="share_001")
        assert data == b"data"
        
        # Verify share_id was included
        assert "shareid=share_001" in responses.calls[0].request.body
    
    @responses.activate
    def test_get_attachment_error(self):
        """Test get attachment with error"""
        responses.add(
            responses.POST,
            "https://lastpass.com/getattach.php",
            body=b"error",
            status=404,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        with pytest.raises(NetworkException) as exc_info:
            client.get_attachment(session, "att_999")
        
        assert "Failed to get attachment" in str(exc_info.value)


class TestDeleteAccount:
    """Test delete_account method"""
    
    @responses.activate
    def test_delete_account_success(self):
        """Test deleting account"""
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b"OK",
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        # Should not raise
        client.delete_account(session, "1001")
    
    @responses.activate
    def test_delete_account_with_share(self):
        """Test deleting account from shared folder"""
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b"OK",
            status=200,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        client.delete_account(session, "1002", share_id="share_001")
        
        # Verify share_id was included
        assert "sharedfolderid=share_001" in responses.calls[0].request.body
    
    @responses.activate
    def test_delete_account_error(self):
        """Test delete account with error"""
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b"error",
            status=500,
        )
        
        client = HTTPClient()
        session = Session(uid="123", sessionid="sess", token="tok")
        
        with pytest.raises(NetworkException) as exc_info:
            client.delete_account(session, "1001")
        
        assert "Failed to delete account" in str(exc_info.value)


class TestAddAccount:
    """Test add_account method"""
    
    @responses.activate
    def test_add_account_success(self):
        """Test successful account addition"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"12345","msg":"accountadded"}',
            status=200,
        )
        
        client = HTTPClient()
        account_data = {
            "name": "Test Account",
            "username": "testuser",
            "password": "testpass",
            "url": "https://example.com",
        }
        
        account_id = client.add_account(session, account_data)
        
        assert account_id == "12345"
        assert len(responses.calls) == 1
        assert responses.calls[0].request.body
        assert "method=cr" in str(responses.calls[0].request.body)
    
    @responses.activate
    def test_add_account_with_group(self):
        """Test adding account with group"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"aid":"12345"}',
            status=200,
        )
        
        client = HTTPClient()
        account_data = {
            "name": "Test Account",
            "username": "testuser",
            "password": "testpass",
            "url": "https://example.com",
            "grouping": "Personal",
        }
        
        account_id = client.add_account(session, account_data)
        
        assert account_id == "12345"
    
    @responses.activate
    def test_add_account_failure(self):
        """Test failed account addition"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b"error",
            status=500,
        )
        
        client = HTTPClient()
        account_data = {"name": "Test Account"}
        
        with pytest.raises(NetworkException) as exc_info:
            client.add_account(session, account_data)
        
        assert "Failed to add account" in str(exc_info.value)
    
    @responses.activate
    def test_add_account_no_aid_in_response(self):
        """Test adding account when response doesn't contain aid"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"accountadded"}',
            status=200,
        )
        
        client = HTTPClient()
        account_data = {"name": "Test Account"}
        
        account_id = client.add_account(session, account_data)
        
        assert account_id == ""


class TestUpdateAccount:
    """Test update_account method"""
    
    @responses.activate
    def test_update_account_success(self):
        """Test successful account update"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"accountupdated"}',
            status=200,
        )
        
        client = HTTPClient()
        account_data = {
            "name": "Updated Account",
            "username": "newuser",
        }
        
        client.update_account(session, "12345", account_data)
        
        assert len(responses.calls) == 1
        assert "method=save" in str(responses.calls[0].request.body)
        assert "aid=12345" in str(responses.calls[0].request.body)
    
    @responses.activate
    def test_update_account_all_fields(self):
        """Test updating all account fields"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b'{"msg":"accountupdated"}',
            status=200,
        )
        
        client = HTTPClient()
        account_data = {
            "name": "Updated Account",
            "username": "newuser",
            "password": "newpass",
            "url": "https://newurl.com",
            "notes": "Updated notes",
            "grouping": "Work",
        }
        
        client.update_account(session, "12345", account_data)
        
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_update_account_failure(self):
        """Test failed account update"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/show_website.php",
            body=b"error",
            status=500,
        )
        
        client = HTTPClient()
        account_data = {"name": "Updated Account"}
        
        with pytest.raises(NetworkException) as exc_info:
            client.update_account(session, "12345", account_data)
        
        assert "Failed to update account" in str(exc_info.value)


class TestHTTPEdgeCases:
    """Test edge cases for HTTP client"""
    
    @responses.activate
    def test_empty_response(self):
        """Test handling empty response"""
        responses.add(
            responses.POST,
            "https://lastpass.com/test.php",
            body=b"",
            status=200,
        )
        
        client = HTTPClient()
        content, status = client.post("test.php", {})
        
        assert content == b""
        assert status == 200
    
    @responses.activate
    def test_large_response(self):
        """Test handling large response"""
        large_data = b"x" * 10000000  # 10MB
        responses.add(
            responses.POST,
            "https://lastpass.com/test.php",
            body=large_data,
            status=200,
        )
        
        client = HTTPClient()
        content, status = client.post("test.php", {})
        
        assert len(content) == 10000000
        assert status == 200


class TestHTTPRetryEdgeCases:
    """Test HTTP retry edge cases"""
    
    @responses.activate
    def test_max_retries_exceeded(self):
        """Test that request exceptions after max retries raise NetworkException"""
        import requests
        
        # Mock connection error that will trigger retries
        client = HTTPClient()
        
        # Patch the session.post to always raise
        with patch.object(client.session, 'post', side_effect=requests.ConnectionError("Connection failed")):
            with pytest.raises(NetworkException, match="HTTP request failed"):
                client.post("test.php", {})
    
    @responses.activate
    def test_rate_limit_in_download_blob(self):
        """Test persistent rate limiting in download_blob"""
        # Setup session
        session = Session(uid="123", sessionid="sess", token="tok")
        
        # All attempts return 429
        for _ in range(4):  # Initial + 3 retries
            responses.add(
                responses.POST,
                "https://lastpass.com/getaccts.php",
                status=429,
            )
        
        client = HTTPClient()
        
        # Should raise with specific rate limit message
        with pytest.raises(NetworkException, match="Rate limited by LastPass"):
            client.download_blob(session)


class TestShareManagementEndpoints:
    """Test share management HTTP endpoints"""
    
    @responses.activate
    def test_create_share(self):
        """Test creating a share"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"id":"share123"}',
            status=200,
        )
        
        client = HTTPClient()
        share_id = client.create_share(
            session=session,
            share_name="Team Share"
        )
        
        assert share_id == "share123"
    
    @responses.activate
    def test_delete_share(self):
        """Test deleting a share"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"result":"success"}',
            status=200,
        )
        
        client = HTTPClient()
        client.delete_share(
            session=session,
            share_id="share123"
        )
        
        # Should not raise
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_get_share_users(self):
        """Test getting share users"""
        session = get_mock_session()
        
        user_data = b'[{"username":"user@example.com","uid":"123"}]'
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=user_data,
            status=200,
        )
        
        client = HTTPClient()
        users = client.get_share_users(
            session=session,
            share_id="share123"
        )
        
        # Returns a list
        assert isinstance(users, list)
    
    @responses.activate
    def test_add_share_user(self):
        """Test adding user to share"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"result":"success"}',
            status=200,
        )
        
        client = HTTPClient()
        client.add_share_user(
            session=session,
            share_id="share123",
            username="newuser@example.com",
            readonly=True,
            admin=False
        )
        
        # Should not raise
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_remove_share_user(self):
        """Test removing user from share"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"result":"success"}',
            status=200,
        )
        
        client = HTTPClient()
        client.remove_share_user(
            session=session,
            share_id="share123",
            username="user@example.com"
        )
        
        # Should not raise
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_update_share_user(self):
        """Test updating share user permissions"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"result":"success"}',
            status=200,
        )
        
        client = HTTPClient()
        client.update_share_user(
            session=session,
            share_id="share123",
            username="user@example.com",
            readonly=False,
            admin=True
        )
        
        # Should not raise
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_create_share_network_error(self):
        """Test create_share with network error"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            status=500,
        )
        
        client = HTTPClient()
        
        with pytest.raises(NetworkException):
            client.create_share(session, "Test Share")
    
    @responses.activate
    def test_get_share_users_network_error(self):
        """Test get_share_users with network error"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            status=500,
        )
        
        client = HTTPClient()
        
        with pytest.raises(NetworkException):
            client.get_share_users(session, "share123")
    
    @responses.activate
    def test_add_share_user_with_all_permissions(self):
        """Test adding share user with all permission options"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"result":"success"}',
            status=200,
        )
        
        client = HTTPClient()
        client.add_share_user(
            session=session,
            share_id="share123",
            username="admin@example.com",
            readonly=False,
            admin=True,
            hide_passwords=False
        )
        
        # Should not raise
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_update_share_user_partial_permissions(self):
        """Test updating share user with only some permissions"""
        session = get_mock_session()
        
        responses.add(
            responses.POST,
            "https://lastpass.com/share.php",
            body=b'{"result":"success"}',
            status=200,
        )
        
        client = HTTPClient()
        client.update_share_user(
            session=session,
            share_id="share123",
            username="user@example.com",
            readonly=True
        )
        
        # Should not raise
        assert len(responses.calls) == 1
