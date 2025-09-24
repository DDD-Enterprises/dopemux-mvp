"""
Security utilities for Dopemux.

Provides secure token management and authentication helpers.
"""

import hashlib
import secrets


class SecureTokenManager:
    """Manages secure tokens for API authentication."""

    def __init__(self):
        self._tokens = {}

    def generate_token(self, identifier: str) -> str:
        """Generate a secure token for an identifier."""
        token = secrets.token_urlsafe(32)
        self._tokens[identifier] = token
        return token

    def validate_token(self, identifier: str, token: str) -> bool:
        """Validate a token for an identifier."""
        stored_token = self._tokens.get(identifier)
        return stored_token == token

    def hash_token(self, token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def remove_token(self, identifier: str) -> bool:
        """Remove a token for an identifier."""
        if identifier in self._tokens:
            del self._tokens[identifier]
            return True
        return False
