"""
Encryption utilities for sensitive data (IBAN, etc.)
Uses Fernet symmetric encryption with key derived from SECRET_KEY
"""
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_encryption_key() -> bytes:
    """
    Derive a Fernet-compatible key from SECRET_KEY.
    Fernet requires a 32-byte base64-encoded key.
    """
    # Use SHA256 to derive a 32-byte key from secret_key
    key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
    # Fernet needs base64-encoded key
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_sensitive(value: str) -> str:
    """
    Encrypt a sensitive string value.
    Returns base64-encoded encrypted string.
    """
    if not value:
        return ""
    
    fernet = Fernet(_get_encryption_key())
    encrypted = fernet.encrypt(value.encode())
    return encrypted.decode()


def decrypt_sensitive(encrypted_value: str) -> str:
    """
    Decrypt a sensitive string value.
    Returns original string.
    """
    if not encrypted_value:
        return ""
    
    try:
        fernet = Fernet(_get_encryption_key())
        decrypted = fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except Exception:
        # If decryption fails (corrupted or wrong key), return empty
        return ""


def encrypt_iban(iban: str) -> str:
    """Encrypt IBAN for secure storage."""
    # Normalize IBAN (remove spaces)
    iban_clean = iban.replace(" ", "").upper() if iban else ""
    return encrypt_sensitive(iban_clean)


def decrypt_iban(encrypted_iban: str) -> str:
    """Decrypt IBAN for display."""
    return decrypt_sensitive(encrypted_iban)


def mask_iban(iban: str) -> str:
    """
    Mask IBAN for safe display: FR76 **** **** **** **** ***1 234
    Only shows first 4 and last 4 characters.
    """
    if not iban or len(iban) < 10:
        return iban or ""
    
    clean = iban.replace(" ", "").upper()
    first4 = clean[:4]
    last4 = clean[-4:]
    middle_len = len(clean) - 8
    masked = first4 + " " + "*" * middle_len + " " + last4
    
    # Format with spaces every 4 chars
    formatted = first4 + " " + "****" + " " * ((middle_len // 4) - 1) + " " + last4
    return f"{first4} {'**** ' * ((middle_len // 4))} {last4}".strip()


def format_iban(iban: str) -> str:
    """Format IBAN with spaces every 4 characters."""
    if not iban:
        return ""
    clean = iban.replace(" ", "").upper()
    return " ".join([clean[i:i+4] for i in range(0, len(clean), 4)])
