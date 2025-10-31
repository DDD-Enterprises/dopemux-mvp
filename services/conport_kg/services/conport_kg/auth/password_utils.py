#!/usr/bin/env python3
"""
ConPort-KG Password Utilities
Part of Phase 1 Security Hardening

Secure password hashing and verification using bcrypt.
"""

import bcrypt
import secrets
import string
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, field_validator

class PasswordValidationError(Exception):
    """Raised when password validation fails"""
    pass

class PasswordManager:
    """Password hashing and verification utilities"""

    # Password requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        # Convert to bytes if needed
        if isinstance(password, str):
            password = password.encode('utf-8')

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds for good security/performance balance
        hashed = bcrypt.hashpw(password, salt)

        # Return as string for storage
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed_password: Stored hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Convert to bytes
            if isinstance(password, str):
                password = password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')

            # Verify password
            return bcrypt.checkpw(password, hashed_password)

        except Exception as e:
            print(f"❌ Password verification error: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Validate password strength requirements.

        Args:
            password: Password to validate

        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        errors = []

        # Length check
        if len(password) < PasswordManager.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordManager.MIN_LENGTH} characters long")

        if len(password) > PasswordManager.MAX_LENGTH:
            errors.append(f"Password must be at most {PasswordManager.MAX_LENGTH} characters long")

        # Character requirements
        if PasswordManager.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if PasswordManager.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if PasswordManager.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        if PasswordManager.REQUIRE_SPECIAL and not any(c in PasswordManager.SPECIAL_CHARS for c in password):
            errors.append(f"Password must contain at least one special character: {PasswordManager.SPECIAL_CHARS}")

        if errors:
            raise PasswordValidationError("; ".join(errors))

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Desired password length (minimum 12)

        Returns:
            Secure random password string
        """
        if length < 12:
            length = 12

        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = PasswordManager.SPECIAL_CHARS

        # Ensure at least one of each type
        password_chars = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]

        # Fill remaining length
        all_chars = lowercase + uppercase + digits + special
        password_chars.extend(secrets.choice(all_chars) for _ in range(length - 4))

        # Shuffle for randomness
        secrets.SystemRandom().shuffle(password_chars)

        return ''.join(password_chars)

    @staticmethod
    def get_password_requirements() -> Dict[str, Any]:
        """
        Get password requirements for API responses.

        Returns:
            Dictionary with password requirements
        """
        return {
            "min_length": PasswordManager.MIN_LENGTH,
            "max_length": PasswordManager.MAX_LENGTH,
            "require_uppercase": PasswordManager.REQUIRE_UPPERCASE,
            "require_lowercase": PasswordManager.REQUIRE_LOWERCASE,
            "require_digits": PasswordManager.REQUIRE_DIGITS,
            "require_special": PasswordManager.REQUIRE_SPECIAL,
            "special_chars": PasswordManager.SPECIAL_CHARS,
            "examples": [
                "MySecurePass123!",
                "DevEnvironment2024$",
                "ConPortUser@567"
            ]
        }

class PasswordResetManager:
    """Password reset token management"""

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a secure password reset token.

        Returns:
            URL-safe reset token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_reset_token(token: str) -> str:
        """
        Hash a reset token for storage.

        Args:
            token: Plain reset token

        Returns:
            Hashed token for database storage
        """
        if isinstance(token, str):
            token = token.encode('utf-8')

        # Use bcrypt for reset tokens too
        salt = bcrypt.gensalt(rounds=10)  # Fewer rounds for tokens
        hashed = bcrypt.hashpw(token, salt)

        return hashed.decode('utf-8')

    @staticmethod
    def verify_reset_token(token: str, hashed_token: str) -> bool:
        """
        Verify a reset token against its hash.

        Args:
            token: Plain reset token
            hashed_token: Stored hashed token

        Returns:
            True if token matches, False otherwise
        """
        try:
            if isinstance(token, str):
                token = token.encode('utf-8')
            if isinstance(hashed_token, str):
                hashed_token = hashed_token.encode('utf-8')

            return bcrypt.checkpw(token, hashed_token)

        except Exception as e:
            print(f"❌ Reset token verification error: {e}")
            return False

# Pydantic models for API validation
class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        PasswordManager.validate_password_strength(v)
        return v

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        PasswordManager.validate_password_strength(v)
        return v

# Export key classes and functions
__all__ = [
    "PasswordManager",
    "PasswordResetManager",
    "PasswordValidationError",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm"
]