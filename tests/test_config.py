"""
Tests for configuration management
"""

import pytest
from pathlib import Path

from lastpass.config import Config


class TestConfig:
    """Test configuration management"""
    
    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create temporary config directory"""
        config_dir = tmp_path / "lpass_test"
        return Config(config_dir)
    
    def test_config_get_default(self, temp_config):
        """Test getting config with default"""
        value = temp_config.get("nonexistent", "default")
        assert value == "default"
    
    def test_config_set_get(self, temp_config):
        """Test setting and getting config"""
        temp_config.set("test_key", "test_value")
        value = temp_config.get("test_key")
        assert value == "test_value"
    
    def test_config_delete(self, temp_config):
        """Test deleting config"""
        temp_config.set("test_key", "test_value")
        temp_config.delete("test_key")
        value = temp_config.get("test_key")
        assert value is None
    
    def test_alias_operations(self, temp_config):
        """Test alias operations"""
        temp_config.set_alias("ll", "ls --long")
        alias = temp_config.get_alias("ll")
        assert alias == "ls --long"
        
        temp_config.delete_alias("ll")
        alias = temp_config.get_alias("ll")
        assert alias is None
    
    def test_expand_alias(self, temp_config):
        """Test alias expansion"""
        temp_config.set_alias("ll", "ls --long")
        
        expanded = temp_config.expand_alias(["ll", "group1"])
        assert expanded == ["ls", "--long", "group1"]
    
    def test_expand_no_alias(self, temp_config):
        """Test expansion with no alias"""
        expanded = temp_config.expand_alias(["ls", "group1"])
        assert expanded == ["ls", "group1"]
    
    def test_plaintext_key_operations(self, temp_config):
        """Test plaintext key storage"""
        key = b"test_key_data_12345678901234567890123456"
        
        assert not temp_config.has_plaintext_key()
        
        temp_config.set_plaintext_key(key)
        assert temp_config.has_plaintext_key()
        
        retrieved = temp_config.get_plaintext_key()
        assert retrieved == key
        
        temp_config.delete_plaintext_key()
        assert not temp_config.has_plaintext_key()
    
    def test_write_read_buffer(self, temp_config):
        """Test binary buffer operations"""
        data = b"binary data test"
        
        temp_config.write_buffer("test_buffer", data)
        retrieved = temp_config.read_buffer("test_buffer")
        assert retrieved == data
        
        temp_config.unlink("test_buffer")
        retrieved = temp_config.read_buffer("test_buffer")
        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
