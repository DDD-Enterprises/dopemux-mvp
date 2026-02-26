"""
Security utilities for Dopemux.

Provides secure token management and authentication helpers.
"""

import hashlib
import secrets


class SecureTokenManager:
    """Manages secure tokens for API authentication using salted PBKDF2 hashing."""

    def __init__(self):
        self._tokens = {}

    def generate_token(self, identifier: str) -> str:
        """Generate a secure token for an identifier."""
        token = secrets.token_urlsafe(32)
        # Store the hash of the token, not the plain token
        self._tokens[identifier] = self.hash_token(token)
        return token

    def validate_token(self, identifier: str, token: str) -> bool:
        """Validate a token for an identifier."""
        stored_hash = self._tokens.get(identifier)
        if not stored_hash:
            return False
        return self.verify_token(token, stored_hash)

    def hash_token(self, token: str) -> str:
        """Hash a token securely using PBKDF2 with a random salt."""
        salt = secrets.token_bytes(16)
        key = hashlib.pbkdf2_hmac('sha256', token.encode('utf-8'), salt, 100000)
        # Return format: salt$hash
        return f"{salt.hex()}${key.hex()}"

    def verify_token(self, token: str, stored_hash: str) -> bool:
        """Verify a token against a stored hash."""
        try:
            salt_hex, key_hex = stored_hash.split('$')
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            key = hashlib.pbkdf2_hmac('sha256', token.encode('utf-8'), salt, 100000)
            return secrets.compare_digest(key, expected_key)
        except (ValueError, TypeError):
            return False

    def remove_token(self, identifier: str) -> bool:
        """Remove a token for an identifier."""
        if identifier in self._tokens:
            del self._tokens[identifier]
            return True
        return False
