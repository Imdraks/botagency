"""
Two-Factor Authentication (2FA) implementation using TOTP.
"""

import pyotp
import qrcode
import io
import base64
from typing import Optional, Tuple
from datetime import datetime


class TwoFactorAuth:
    """Two-Factor Authentication manager."""
    
    ISSUER_NAME = "Opportunities Radar"
    VALID_WINDOW = 1  # Accept codes 30 seconds before/after
    
    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret key."""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp(secret: str) -> pyotp.TOTP:
        """Get TOTP instance for a secret."""
        return pyotp.TOTP(secret)
    
    @classmethod
    def generate_provisioning_uri(
        cls, 
        secret: str, 
        email: str
    ) -> str:
        """
        Generate the provisioning URI for authenticator apps.
        
        Args:
            secret: The TOTP secret key
            email: User's email address
            
        Returns:
            URI string for QR code
        """
        totp = cls.get_totp(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=cls.ISSUER_NAME
        )
    
    @classmethod
    def generate_qr_code(
        cls, 
        secret: str, 
        email: str
    ) -> str:
        """
        Generate QR code as base64 encoded image.
        
        Args:
            secret: The TOTP secret key
            email: User's email address
            
        Returns:
            Base64 encoded PNG image data
        """
        uri = cls.generate_provisioning_uri(secret, email)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @classmethod
    def verify_code(
        cls, 
        secret: str, 
        code: str
    ) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            secret: The user's TOTP secret
            code: The 6-digit code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        if not secret or not code:
            return False
        
        # Clean the code (remove spaces/dashes)
        code = code.replace(" ", "").replace("-", "")
        
        if len(code) != 6 or not code.isdigit():
            return False
        
        totp = cls.get_totp(secret)
        return totp.verify(code, valid_window=cls.VALID_WINDOW)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """
        Generate backup codes for 2FA recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        import secrets
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            # Format as XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes
    
    @staticmethod
    def verify_backup_code(
        provided_code: str, 
        stored_codes: list[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code and return it if valid (for removal).
        
        Args:
            provided_code: The code provided by user
            stored_codes: List of valid backup codes
            
        Returns:
            Tuple of (is_valid, used_code)
        """
        # Normalize the code
        normalized = provided_code.upper().replace(" ", "")
        
        for stored in stored_codes:
            stored_normalized = stored.replace("-", "")
            provided_normalized = normalized.replace("-", "")
            
            if stored_normalized == provided_normalized:
                return True, stored
        
        return False, None


# Singleton instance
two_factor_auth = TwoFactorAuth()
