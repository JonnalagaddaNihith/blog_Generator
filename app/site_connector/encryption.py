"""Encryption utilities for storing sensitive WordPress credentials."""

import os
from cryptography.fernet import Fernet


# Generate a default key if none is provided (not recommended for production)
# This should be overridden by ENCRYPTION_KEY in environment
DEFAULT_ENCRYPTION_KEY = Fernet.generate_key()


def get_encryption_key() -> bytes:
    """Get or generate encryption key for Fernet."""
    try:
        from app.config import settings
        key = getattr(settings, 'encryption_key', None)
        if key:
            return key.encode() if isinstance(key, str) else key
    except Exception:
        pass
    
    # Generate a key if not configured (not recommended for production)
    return DEFAULT_ENCRYPTION_KEY


_fernet = None


def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    global _fernet
    if _fernet is None:
        key = get_encryption_key()
        _fernet = Fernet(key)
    return _fernet


def encrypt(data: str) -> str:
    """Encrypt a string using Fernet symmetric encryption.
    
    Args:
        data: The string to encrypt
        
    Returns:
        Encrypted string as base64-encoded bytes converted to string
    """
    if not data:
        return ""
    fernet = get_fernet()
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt(encrypted_data: str) -> str:
    """Decrypt a string that was encrypted using Fernet.
    
    Args:
        encrypted_data: The encrypted string to decrypt
        
    Returns:
        Decrypted string
        
    Raises:
        ValueError: If decryption fails
    """
    if not encrypted_data:
        return ""
    fernet = get_fernet()
    try:
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {e}")
