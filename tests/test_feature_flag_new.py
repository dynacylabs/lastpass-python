"""Tests for feature flag module."""
import pytest
from unittest.mock import Mock, patch

from lastpass.feature_flag import FeatureFlag
from lastpass.config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config."""
    config_dir = tmp_path / "lpass"
    config_dir.mkdir()
    config = Config()
    config.config_dir = config_dir
    config.config_file = config_dir / "config.json"
    # Ensure config file exists
    config.config_file.touch()
    return config


@pytest.fixture
def feature_flag(temp_config):
    """Create FeatureFlag with temporary config."""
    return FeatureFlag(temp_config)


@pytest.mark.unit
class TestFeatureFlagInit:
    """Tests for FeatureFlag initialization."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        ff = FeatureFlag()
        assert ff.config is not None
        assert ff.url_encryption_enabled is False
        assert ff.url_logging_enabled is False
    
    def test_init_custom_config(self, temp_config):
        """Test initialization with custom config."""
        ff = FeatureFlag(temp_config)
        assert ff.config == temp_config
        assert ff.url_encryption_enabled is False
        assert ff.url_logging_enabled is False


@pytest.mark.unit
class TestLoadFromXmlAttrs:
    """Tests for load_from_xml_attrs method."""
    
    def test_load_url_encryption_enabled(self, feature_flag):
        """Test loading URL encryption flag enabled."""
        attrs = {'url_encryption': '1'}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_encryption_enabled is True
    
    def test_load_url_encryption_disabled(self, feature_flag):
        """Test loading URL encryption flag disabled."""
        attrs = {'url_encryption': '0'}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_encryption_enabled is False
    
    def test_load_url_logging_enabled(self, feature_flag):
        """Test loading URL logging flag enabled."""
        attrs = {'url_logging': '1'}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_logging_enabled is True
    
    def test_load_url_logging_disabled(self, feature_flag):
        """Test loading URL logging flag disabled."""
        attrs = {'url_logging': '0'}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_logging_enabled is False
    
    def test_load_both_flags(self, feature_flag):
        """Test loading both flags."""
        attrs = {'url_encryption': '1', 'url_logging': '0'}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_encryption_enabled is True
        assert feature_flag.url_logging_enabled is False
    
    def test_load_missing_flags(self, feature_flag):
        """Test loading with missing flags keeps defaults."""
        attrs = {}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_encryption_enabled is False
        assert feature_flag.url_logging_enabled is False
    
    def test_load_partial_flags(self, feature_flag):
        """Test loading with only some flags."""
        attrs = {'url_encryption': '1'}
        feature_flag.load_from_xml_attrs(attrs)
        assert feature_flag.url_encryption_enabled is True
        assert feature_flag.url_logging_enabled is False


@pytest.mark.unit
class TestSave:
    """Tests for save method."""
    
    @patch('lastpass.feature_flag.encrypt_aes256_cbc_base64')
    def test_save_both_disabled(self, mock_encrypt, feature_flag):
        """Test saving when both flags are disabled."""
        key = b'0' * 32
        mock_encrypt.side_effect = lambda data, k: f'enc_{data}'
        
        feature_flag.url_encryption_enabled = False
        feature_flag.url_logging_enabled = False
        feature_flag.save(key)
        
        assert feature_flag.config.get('session_ff_url_encryption') == 'enc_0'
        assert feature_flag.config.get('session_ff_url_logging') == 'enc_0'
    
    @patch('lastpass.feature_flag.encrypt_aes256_cbc_base64')
    def test_save_both_enabled(self, mock_encrypt, feature_flag):
        """Test saving when both flags are enabled."""
        key = b'0' * 32
        mock_encrypt.side_effect = lambda data, k: f'enc_{data}'
        
        feature_flag.url_encryption_enabled = True
        feature_flag.url_logging_enabled = True
        feature_flag.save(key)
        
        assert feature_flag.config.get('session_ff_url_encryption') == 'enc_1'
        assert feature_flag.config.get('session_ff_url_logging') == 'enc_1'
    
    @patch('lastpass.feature_flag.encrypt_aes256_cbc_base64')
    def test_save_mixed_flags(self, mock_encrypt, feature_flag):
        """Test saving with mixed flag values."""
        key = b'0' * 32
        mock_encrypt.side_effect = lambda data, k: f'enc_{data}'
        
        feature_flag.url_encryption_enabled = True
        feature_flag.url_logging_enabled = False
        feature_flag.save(key)
        
        assert feature_flag.config.get('session_ff_url_encryption') == 'enc_1'
        assert feature_flag.config.get('session_ff_url_logging') == 'enc_0'


@pytest.mark.unit
class TestLoad:
    """Tests for load method."""
    
    @patch('lastpass.feature_flag.decrypt_aes256_cbc_base64')
    def test_load_both_enabled(self, mock_decrypt, feature_flag):
        """Test loading when both flags are enabled."""
        key = b'0' * 32
        feature_flag.config.set('session_ff_url_encryption', 'encrypted_1')
        feature_flag.config.set('session_ff_url_logging', 'encrypted_1')
        mock_decrypt.side_effect = lambda data, k: '1'
        
        feature_flag.load(key)
        
        assert feature_flag.url_encryption_enabled is True
        assert feature_flag.url_logging_enabled is True
    
    @patch('lastpass.feature_flag.decrypt_aes256_cbc_base64')
    def test_load_both_disabled(self, mock_decrypt, feature_flag):
        """Test loading when both flags are disabled."""
        key = b'0' * 32
        feature_flag.config.set('session_ff_url_encryption', 'encrypted_0')
        feature_flag.config.set('session_ff_url_logging', 'encrypted_0')
        mock_decrypt.side_effect = lambda data, k: '0'
        
        feature_flag.load(key)
        
        assert feature_flag.url_encryption_enabled is False
        assert feature_flag.url_logging_enabled is False
    
    @patch('lastpass.feature_flag.decrypt_aes256_cbc_base64')
    def test_load_mixed_flags(self, mock_decrypt, feature_flag):
        """Test loading with mixed flag values."""
        key = b'0' * 32
        feature_flag.config.set('session_ff_url_encryption', 'encrypted_1')
        feature_flag.config.set('session_ff_url_logging', 'encrypted_0')
        
        def decrypt_side_effect(data, k):
            return '1' if data == 'encrypted_1' else '0'
        mock_decrypt.side_effect = decrypt_side_effect
        
        feature_flag.load(key)
        
        assert feature_flag.url_encryption_enabled is True
        assert feature_flag.url_logging_enabled is False
    
    def test_load_missing_config(self, feature_flag):
        """Test loading when config values don't exist."""
        key = b'0' * 32
        
        feature_flag.load(key)
        
        # Should keep default values
        assert feature_flag.url_encryption_enabled is False
        assert feature_flag.url_logging_enabled is False
    
    @patch('lastpass.feature_flag.decrypt_aes256_cbc_base64')
    def test_load_decrypt_error(self, mock_decrypt, feature_flag):
        """Test loading handles decryption errors."""
        key = b'0' * 32
        feature_flag.config.set('session_ff_url_encryption', 'bad_data')
        feature_flag.config.set('session_ff_url_logging', 'bad_data')
        mock_decrypt.side_effect = Exception("Decrypt failed")
        
        # Should not raise exception
        feature_flag.load(key)
        
        # Should keep default values
        assert feature_flag.url_encryption_enabled is False
        assert feature_flag.url_logging_enabled is False


@pytest.mark.unit
class TestCleanup:
    """Tests for cleanup method."""
    
    def test_cleanup_removes_config(self, feature_flag):
        """Test cleanup removes config values."""
        feature_flag.config.set('session_ff_url_encryption', 'data1')
        feature_flag.config.set('session_ff_url_logging', 'data2')
        
        feature_flag.cleanup()
        
        assert feature_flag.config.get('session_ff_url_encryption') is None
        assert feature_flag.config.get('session_ff_url_logging') is None
    
    def test_cleanup_when_empty(self, feature_flag):
        """Test cleanup when config already empty."""
        # Should not raise exception
        feature_flag.cleanup()
        
        assert feature_flag.config.get('session_ff_url_encryption') is None
        assert feature_flag.config.get('session_ff_url_logging') is None


@pytest.mark.unit
class TestToDict:
    """Tests for to_dict method."""
    
    def test_to_dict_both_disabled(self, feature_flag):
        """Test to_dict when both flags disabled."""
        feature_flag.url_encryption_enabled = False
        feature_flag.url_logging_enabled = False
        
        result = feature_flag.to_dict()
        
        assert result == {
            'url_encryption_enabled': False,
            'url_logging_enabled': False
        }
    
    def test_to_dict_both_enabled(self, feature_flag):
        """Test to_dict when both flags enabled."""
        feature_flag.url_encryption_enabled = True
        feature_flag.url_logging_enabled = True
        
        result = feature_flag.to_dict()
        
        assert result == {
            'url_encryption_enabled': True,
            'url_logging_enabled': True
        }
    
    def test_to_dict_mixed(self, feature_flag):
        """Test to_dict with mixed values."""
        feature_flag.url_encryption_enabled = True
        feature_flag.url_logging_enabled = False
        
        result = feature_flag.to_dict()
        
        assert result == {
            'url_encryption_enabled': True,
            'url_logging_enabled': False
        }


@pytest.mark.unit
class TestFeatureFlagIntegration:
    """Integration tests for feature flag lifecycle."""
    
    @patch('lastpass.feature_flag.encrypt_aes256_cbc_base64')
    @patch('lastpass.feature_flag.decrypt_aes256_cbc_base64')
    def test_save_and_load_roundtrip(self, mock_decrypt, mock_encrypt, feature_flag):
        """Test saving and loading flags."""
        key = b'0' * 32
        
        # Setup encryption/decryption mocks
        encrypted_values = {}
        def encrypt_side_effect(data, k):
            encrypted = f'encrypted_{data}'
            encrypted_values[encrypted] = data
            return encrypted
        
        def decrypt_side_effect(data, k):
            return encrypted_values.get(data, '0')
        
        mock_encrypt.side_effect = encrypt_side_effect
        mock_decrypt.side_effect = decrypt_side_effect
        
        # Set initial values
        feature_flag.url_encryption_enabled = True
        feature_flag.url_logging_enabled = False
        
        # Save
        feature_flag.save(key)
        
        # Create new instance and load
        new_ff = FeatureFlag(feature_flag.config)
        new_ff.load(key)
        
        # Should have same values
        assert new_ff.url_encryption_enabled is True
        assert new_ff.url_logging_enabled is False
