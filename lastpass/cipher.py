"""
Cryptographic operations for LastPass
"""

import base64
import hashlib
import struct
from typing import Optional, Tuple
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from .exceptions import DecryptionException


def aes_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES-256-CBC
    Format: '!' + base64(iv) + '|' + base64(ciphertext)
    or just ciphertext for ECB mode
    """
    if not ciphertext:
        return b''
    
    # Check if it's in the '!base64|base64' format
    if ciphertext.startswith(b'!'):
        try:
            # Split into IV and ciphertext
            parts = ciphertext[1:].split(b'|', 1)
            if len(parts) != 2:
                raise DecryptionException("Invalid encrypted data format")
            
            iv = base64.b64decode(parts[0])
            data = base64.b64decode(parts[1])
            
            # Decrypt with CBC mode
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = cipher.decrypt(data)
            
            # Remove PKCS7 padding
            try:
                plaintext = unpad(plaintext, AES.block_size)
            except ValueError:
                # If unpadding fails, return as-is
                pass
            
            return plaintext
        except Exception as e:
            raise DecryptionException(f"AES decryption failed: {e}")
    else:
        # Legacy ECB mode
        try:
            cipher = AES.new(key, AES.MODE_ECB)
            plaintext = cipher.decrypt(ciphertext)
            
            # Remove PKCS7 padding
            try:
                plaintext = unpad(plaintext, AES.block_size)
            except ValueError:
                pass
            
            return plaintext
        except Exception as e:
            raise DecryptionException(f"AES decryption failed: {e}")


def aes_decrypt_base64(ciphertext: str, key: bytes) -> str:
    """Decrypt base64-encoded AES ciphertext"""
    if not ciphertext:
        return ""
    
    try:
        ciphertext_bytes = base64.b64decode(ciphertext)
        plaintext = aes_decrypt(ciphertext_bytes, key)
        return plaintext.decode('utf-8', errors='replace')
    except Exception as e:
        raise DecryptionException(f"Base64 AES decryption failed: {e}")


def aes_encrypt(plaintext: str, key: bytes) -> bytes:
    """
    Encrypt data using AES-256-CBC
    Returns: b'!' + base64(iv) + b'|' + base64(ciphertext)
    """
    if not plaintext:
        return b''
    
    try:
        # Generate random IV
        iv = get_random_bytes(AES.block_size)
        
        # Encrypt with CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # Handle both string and bytes input
        if isinstance(plaintext, bytes):
            plaintext_bytes = plaintext
        else:
            plaintext_bytes = plaintext.encode('utf-8')
        padded = pad(plaintext_bytes, AES.block_size)
        ciphertext = cipher.encrypt(padded)
        
        # Format: '!' + base64(iv) + '|' + base64(ciphertext)
        result = b'!' + base64.b64encode(iv) + b'|' + base64.b64encode(ciphertext)
        return result
    except Exception as e:
        raise DecryptionException(f"AES encryption failed: {e}")


def encrypt_and_base64(plaintext: str, key: bytes) -> str:
    """Encrypt and return base64-encoded result"""
    encrypted = aes_encrypt(plaintext, key)
    return base64.b64encode(encrypted).decode('ascii')


def rsa_decrypt(ciphertext: bytes, private_key_pem: str) -> str:
    """Decrypt data using RSA private key"""
    try:
        key = RSA.import_key(private_key_pem)
        cipher = PKCS1_OAEP.new(key)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise DecryptionException(f"RSA decryption failed: {e}")


def rsa_encrypt(plaintext: str, public_key_pem: str) -> bytes:
    """Encrypt data using RSA public key"""
    try:
        key = RSA.import_key(public_key_pem)
        cipher = PKCS1_OAEP.new(key)
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext = cipher.encrypt(plaintext_bytes)
        return ciphertext
    except Exception as e:
        raise DecryptionException(f"RSA encryption failed: {e}")


def decrypt_private_key(key_hex: str, decryption_key: bytes) -> str:
    """Decrypt the RSA private key using the decryption key"""
    try:
        encrypted_key = bytes.fromhex(key_hex)
        decrypted = aes_decrypt(encrypted_key, decryption_key)
        return decrypted.decode('utf-8')
    except Exception as e:
        raise DecryptionException(f"Private key decryption failed: {e}")


def sha256_hex(data: bytes) -> str:
    """SHA256 hash as hex string"""
    return hashlib.sha256(data).hexdigest()


def sha256_base64(data: bytes) -> str:
    """SHA256 hash as base64 string"""
    hash_bytes = hashlib.sha256(data).digest()
    return base64.b64encode(hash_bytes).decode('ascii')


def hex_to_bytes(hex_string: str) -> bytes:
    """Convert hex string to bytes"""
    try:
        return bytes.fromhex(hex_string)
    except ValueError as e:
        raise DecryptionException(f"Invalid hex string: {e}")


# Aliases for compatibility with new modules
decrypt_aes256_cbc_base64 = aes_decrypt_base64
encrypt_aes256_cbc_base64 = encrypt_and_base64
