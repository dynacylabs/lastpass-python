"""
Feature flag support for server-side configuration
"""

from typing import Optional
from .config import Config
from .cipher import encrypt_aes256_cbc_base64, decrypt_aes256_cbc_base64


class FeatureFlag:
    """Server-side feature flag management"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.url_encryption_enabled = False
        self.url_logging_enabled = False
    
    def load_from_xml_attrs(self, attrs: dict) -> None:
        """
        Load feature flags from XML attributes
        
        Args:
            attrs: Dictionary of XML attributes from server response
        """
        if 'url_encryption' in attrs:
            self.url_encryption_enabled = attrs['url_encryption'] == '1'
        
        if 'url_logging' in attrs:
            self.url_logging_enabled = attrs['url_logging'] == '1'
    
    def save(self, key: bytes) -> None:
        """
        Save feature flags to encrypted config
        
        Args:
            key: Encryption key
        """
        url_enc = '1' if self.url_encryption_enabled else '0'
        url_log = '1' if self.url_logging_enabled else '0'
        
        encrypted_enc = encrypt_aes256_cbc_base64(url_enc, key)
        encrypted_log = encrypt_aes256_cbc_base64(url_log, key)
        
        self.config.set('session_ff_url_encryption', encrypted_enc)
        self.config.set('session_ff_url_logging', encrypted_log)
    
    def load(self, key: bytes) -> None:
        """
        Load feature flags from encrypted config
        
        Args:
            key: Decryption key
        """
        try:
            encrypted_enc = self.config.get('session_ff_url_encryption')
            if encrypted_enc:
                decrypted = decrypt_aes256_cbc_base64(encrypted_enc, key)
                self.url_encryption_enabled = decrypted == '1'
        except Exception:
            pass
        
        try:
            encrypted_log = self.config.get('session_ff_url_logging')
            if encrypted_log:
                decrypted = decrypt_aes256_cbc_base64(encrypted_log, key)
                self.url_logging_enabled = decrypted == '1'
        except Exception:
            pass
    
    def cleanup(self) -> None:
        """Remove feature flags from config"""
        self.config.delete('session_ff_url_encryption')
        self.config.delete('session_ff_url_logging')
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'url_encryption_enabled': self.url_encryption_enabled,
            'url_logging_enabled': self.url_logging_enabled
        }
