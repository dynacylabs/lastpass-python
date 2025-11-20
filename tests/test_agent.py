"""Tests for agent key caching system."""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
import socket
from pathlib import Path

from lastpass.agent import Agent
from lastpass.config import Config


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "lpass"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def agent(temp_config_dir):
    """Create agent with temporary config."""
    config = Config()
    config.config_dir = temp_config_dir
    config.config_file = temp_config_dir / "config.json"
    # Ensure config file exists
    config.config_file.touch()
    return Agent(config)


@pytest.mark.unit
class TestAgentInit:
    """Tests for Agent initialization."""
    
    def test_agent_init_default_config(self):
        """Test agent initialization with default config."""
        agent = Agent()
        assert agent.config is not None
        assert agent._socket_path is not None
    
    def test_agent_init_custom_config(self, temp_config_dir):
        """Test agent initialization with custom config."""
        config = Config()
        config.config_dir = temp_config_dir
        agent = Agent(config)
        assert agent.config == config
        assert agent._socket_path == temp_config_dir / "agent.sock"


@pytest.mark.unit
class TestAgentTimeout:
    """Tests for agent timeout configuration."""
    
    def test_get_timeout_default(self, agent):
        """Test default timeout."""
        with patch.dict(os.environ, {}, clear=True):
            timeout = agent._get_timeout()
            assert timeout == 3600
    
    def test_get_timeout_custom(self, agent):
        """Test custom timeout from environment."""
        with patch.dict(os.environ, {'LPASS_AGENT_TIMEOUT': '7200'}):
            timeout = agent._get_timeout()
            assert timeout == 7200
    
    def test_get_timeout_invalid(self, agent):
        """Test invalid timeout falls back to default."""
        with patch.dict(os.environ, {'LPASS_AGENT_TIMEOUT': 'invalid'}):
            timeout = agent._get_timeout()
            assert timeout == 3600


@pytest.mark.unit
class TestAgentDisabled:
    """Tests for agent disabled state."""
    
    def test_is_disabled_false(self, agent):
        """Test agent not disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert agent._is_disabled() is False
    
    def test_is_disabled_true(self, agent):
        """Test agent disabled via environment."""
        with patch.dict(os.environ, {'LPASS_AGENT_DISABLE': '1'}):
            assert agent._is_disabled() is True
    
    def test_is_disabled_other_value(self, agent):
        """Test agent not disabled with other values."""
        with patch.dict(os.environ, {'LPASS_AGENT_DISABLE': '0'}):
            assert agent._is_disabled() is False


@pytest.mark.unit
class TestAgentRunning:
    """Tests for checking if agent is running."""
    
    def test_is_running_no_socket(self, agent):
        """Test agent not running when socket doesn't exist."""
        assert agent.is_running() is False
    
    def test_is_running_socket_exists_but_not_listening(self, agent):
        """Test agent not running when socket exists but not listening."""
        # Create socket file but don't listen
        agent._socket_path.touch()
        assert agent.is_running() is False
    
    @patch('socket.socket')
    def test_is_running_connection_refused(self, mock_socket_cls, agent):
        """Test agent not running when connection refused."""
        agent._socket_path.touch()
        mock_sock = Mock()
        mock_sock.connect.side_effect = ConnectionRefusedError()
        mock_socket_cls.return_value = mock_sock
        assert agent.is_running() is False
    
    @patch('socket.socket')
    def test_is_running_success(self, mock_socket_cls, agent):
        """Test agent running when connection succeeds."""
        agent._socket_path.touch()
        mock_sock = Mock()
        mock_socket_cls.return_value = mock_sock
        assert agent.is_running() is True
        mock_sock.connect.assert_called_once()
        mock_sock.close.assert_called_once()


@pytest.mark.unit
class TestPlaintextKey:
    """Tests for plaintext key storage."""
    
    def test_has_plaintext_key_false(self, agent):
        """Test has_plaintext_key when not present."""
        assert agent._has_plaintext_key() is False
    
    def test_has_plaintext_key_true(self, agent):
        """Test has_plaintext_key when present."""
        agent.config.set('plaintext_key', 'abcd1234')
        assert agent._has_plaintext_key() is True
    
    def test_load_plaintext_key_valid(self, agent):
        """Test loading valid plaintext key."""
        key_bytes = b'0' * 32
        agent.config.set('plaintext_key', key_bytes.hex())
        loaded = agent._load_plaintext_key()
        assert loaded == key_bytes
    
    def test_load_plaintext_key_invalid_hex(self, agent):
        """Test loading invalid hex returns None."""
        agent.config.set('plaintext_key', 'not-hex')
        loaded = agent._load_plaintext_key()
        assert loaded is None
    
    def test_load_plaintext_key_not_present(self, agent):
        """Test loading when key not present."""
        loaded = agent._load_plaintext_key()
        assert loaded is None


@pytest.mark.unit
class TestVerifyKey:
    """Tests for key verification."""
    
    def test_verify_key_no_verify_string(self, agent):
        """Test verification fails when no verify string."""
        key = b'0' * 32
        assert agent._verify_key(key) is False
    
    @patch('lastpass.agent.decrypt_aes256_cbc_base64')
    def test_verify_key_success(self, mock_decrypt, agent):
        """Test successful key verification."""
        key = b'0' * 32
        agent.config.set('verify', 'encrypted_data')
        mock_decrypt.return_value = Agent.VERIFICATION_STRING
        assert agent._verify_key(key) is True
    
    @patch('lastpass.agent.decrypt_aes256_cbc_base64')
    def test_verify_key_wrong_key(self, mock_decrypt, agent):
        """Test verification fails with wrong key."""
        key = b'0' * 32
        agent.config.set('verify', 'encrypted_data')
        mock_decrypt.return_value = "wrong string"
        assert agent._verify_key(key) is False
    
    @patch('lastpass.agent.decrypt_aes256_cbc_base64')
    def test_verify_key_decrypt_error(self, mock_decrypt, agent):
        """Test verification fails when decryption error."""
        key = b'0' * 32
        agent.config.set('verify', 'encrypted_data')
        mock_decrypt.side_effect = Exception("Decrypt failed")
        assert agent._verify_key(key) is False


@pytest.mark.unit
class TestAskAgent:
    """Tests for asking running agent for key."""
    
    def test_ask_agent_not_running(self, agent):
        """Test asking agent when not running."""
        result = agent._ask_agent()
        assert result is None
    
    @patch('socket.socket')
    def test_ask_agent_success(self, mock_socket_cls, agent):
        """Test successfully getting key from agent."""
        agent._socket_path.touch()
        mock_sock = Mock()
        test_key = b'1' * 32
        mock_sock.recv.return_value = test_key
        mock_socket_cls.return_value = mock_sock
        
        result = agent._ask_agent()
        assert result == test_key
        mock_sock.sendall.assert_called_once()
        # close() called twice: once in is_running(), once in _ask_agent()
        assert mock_sock.close.call_count == 2
    
    @patch('socket.socket')
    def test_ask_agent_short_response(self, mock_socket_cls, agent):
        """Test agent returns None for short response."""
        agent._socket_path.touch()
        mock_sock = Mock()
        mock_sock.recv.return_value = b'short'
        mock_socket_cls.return_value = mock_sock
        
        result = agent._ask_agent()
        assert result is None
    
    @patch('socket.socket')
    def test_ask_agent_connection_error(self, mock_socket_cls, agent):
        """Test agent returns None on connection error."""
        agent._socket_path.touch()
        mock_sock = Mock()
        # Connection error in is_running() - should catch and return False
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection failed")
        mock_socket_cls.return_value = mock_sock
        
        result = agent._ask_agent()
        assert result is None


@pytest.mark.unit
class TestGetDecryptionKey:
    """Tests for getting decryption key."""
    
    @patch.object(Agent, '_has_plaintext_key')
    @patch.object(Agent, '_load_plaintext_key')
    @patch.object(Agent, '_verify_key')
    def test_get_decryption_key_from_plaintext(self, mock_verify, mock_load, mock_has, agent):
        """Test getting key from plaintext storage."""
        test_key = b'0' * 32
        mock_has.return_value = True
        mock_load.return_value = test_key
        mock_verify.return_value = True
        
        result = agent.get_decryption_key()
        assert result == test_key
    
    @patch.object(Agent, '_has_plaintext_key')
    @patch.object(Agent, '_load_plaintext_key')
    @patch.object(Agent, '_verify_key')
    @patch.object(Agent, '_ask_agent')
    def test_get_decryption_key_from_agent(self, mock_ask, mock_verify, mock_load, mock_has, agent):
        """Test getting key from running agent."""
        test_key = b'1' * 32
        mock_has.return_value = False
        mock_ask.return_value = test_key
        mock_verify.return_value = True
        
        result = agent.get_decryption_key()
        assert result == test_key
    
    @patch.object(Agent, '_has_plaintext_key')
    @patch.object(Agent, '_load_plaintext_key')
    @patch.object(Agent, '_verify_key')
    def test_get_decryption_key_invalid_plaintext(self, mock_verify, mock_load, mock_has, agent):
        """Test plaintext key removed when invalid."""
        test_key = b'0' * 32
        mock_has.return_value = True
        mock_load.return_value = test_key
        mock_verify.return_value = False
        
        with patch.object(agent.config, 'delete') as mock_delete:
            result = agent.get_decryption_key()
            assert result is None
            mock_delete.assert_called_once_with('plaintext_key')


@pytest.mark.unit
class TestSaveKey:
    """Tests for saving key to agent."""
    
    @patch('lastpass.cipher.encrypt_aes256_cbc_base64')
    @patch.object(Agent, '_is_disabled')
    @patch.object(Agent, '_has_plaintext_key')
    @patch.object(Agent, 'start')
    def test_save_starts_agent(self, mock_start, mock_has_plaintext, mock_disabled, mock_encrypt, agent):
        """Test save starts agent when not disabled."""
        key = b'0' * 32
        mock_disabled.return_value = False
        mock_has_plaintext.return_value = False
        mock_encrypt.return_value = 'encrypted_verify'
        
        agent.save('user@example.com', 100100, key)
        
        assert agent.config.get('username') == 'user@example.com'
        assert agent.config.get('iterations') == 100100
        assert agent.config.get('verify') == 'encrypted_verify'
        mock_start.assert_called_once_with(key)
    
    @patch('lastpass.cipher.encrypt_aes256_cbc_base64')
    @patch.object(Agent, '_is_disabled')
    @patch.object(Agent, 'start')
    def test_save_disabled_no_start(self, mock_start, mock_disabled, mock_encrypt, agent):
        """Test save doesn't start agent when disabled."""
        key = b'0' * 32
        mock_disabled.return_value = True
        mock_encrypt.return_value = 'encrypted_verify'
        
        agent.save('user@example.com', 100100, key)
        
        mock_start.assert_not_called()


@pytest.mark.unit
class TestKillAgent:
    """Tests for killing running agent."""
    
    def test_kill_agent_not_running(self, agent):
        """Test killing agent when not running."""
        # Should not raise exception
        agent.kill()
    
    @patch('socket.socket')
    @patch('time.sleep')
    def test_kill_agent_running(self, mock_sleep, mock_socket_cls, agent):
        """Test killing running agent."""
        agent._socket_path.touch()
        mock_sock = Mock()
        mock_socket_cls.return_value = mock_sock
        
        agent.kill()
        
        # connect() called twice: once in is_running(), once in kill()
        assert mock_sock.connect.call_count == 2
        # close() called twice: once in is_running(), once in kill()
        assert mock_sock.close.call_count == 2


@pytest.mark.unit
class TestLoadKey:
    """Tests for loading key by password."""
    
    @patch('getpass.getpass')
    @patch('lastpass.agent.kdf_decryption_key')
    @patch.object(Agent, '_verify_key')
    def test_load_key_success(self, mock_verify, mock_kdf, mock_getpass, agent):
        """Test successfully loading key."""
        agent.config.set('username', 'user@example.com')
        agent.config.set('iterations', 100100)
        mock_getpass.return_value = 'password123'
        test_key = b'0' * 32
        mock_kdf.return_value = test_key
        mock_verify.return_value = True
        
        result = agent.load_key()
        assert result == test_key
        mock_kdf.assert_called_once_with('user@example.com', 'password123', 100100)
    
    def test_load_key_no_username(self, agent):
        """Test loading key fails without username."""
        agent.config.set('iterations', 100100)
        result = agent.load_key()
        assert result is None
    
    def test_load_key_no_iterations(self, agent):
        """Test loading key fails without iterations."""
        agent.config.set('username', 'user@example.com')
        result = agent.load_key()
        assert result is None
    
    @patch('getpass.getpass')
    def test_load_key_no_password(self, mock_getpass, agent):
        """Test loading key fails with empty password."""
        agent.config.set('username', 'user@example.com')
        agent.config.set('iterations', 100100)
        mock_getpass.return_value = ''
        result = agent.load_key()
        assert result is None
    
    @patch('getpass.getpass')
    @patch('lastpass.agent.kdf_decryption_key')
    @patch.object(Agent, '_verify_key')
    def test_load_key_wrong_password(self, mock_verify, mock_kdf, mock_getpass, agent):
        """Test loading key fails with wrong password."""
        agent.config.set('username', 'user@example.com')
        agent.config.set('iterations', 100100)
        mock_getpass.return_value = 'wrongpass'
        test_key = b'0' * 32
        mock_kdf.return_value = test_key
        mock_verify.return_value = False
        
        result = agent.load_key()
        assert result is None
