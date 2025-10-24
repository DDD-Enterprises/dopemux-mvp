#!/usr/bin/env python3
"""
ConPort-KG JWT Utilities
Phase 1 Week 1 Day 1

JWT token generation and validation using RS256 (asymmetric signing).
Supports access tokens (15min) and refresh tokens (30 days).
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt


class JWTManager:
    """
    JWT token creation and validation using RS256 asymmetric signing.

    Features:
    - Automatic RSA key generation if keys don't exist
    - Separate access (15min) and refresh (30 day) tokens
    - Token type validation (access vs refresh)
    - Signature verification
    - Expiry validation

    Security:
    - RS256 (RSA + SHA256) for signature verification
    - Private key kept secure, public key can be shared
    - Token type field prevents token substitution attacks
    """

    # Configuration
    ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 30

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
    ):
        """
        Initialize JWT manager with RSA keys.

        If key files don't exist, automatically generates RSA key pair.

        Args:
            private_key_path: Path to PEM-encoded private key
            public_key_path: Path to PEM-encoded public key
        """
        # Use environment variables or defaults
        self.private_key_path = private_key_path or os.getenv(
            "JWT_PRIVATE_KEY_PATH",
            str(Path(__file__).parent / "keys" / "jwt_private.pem"),
        )
        self.public_key_path = public_key_path or os.getenv(
            "JWT_PUBLIC_KEY_PATH",
            str(Path(__file__).parent / "keys" / "jwt_public.pem"),
        )

        # Ensure keys directory exists
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)

        # Generate keys if they don't exist
        if not os.path.exists(self.private_key_path) or not os.path.exists(
            self.public_key_path
        ):
            self._generate_rsa_keys()

        # Load keys
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()

    def _generate_rsa_keys(self) -> None:
        """
        Generate RSA-2048 key pair and save to PEM files.

        Uses:
        - 2048-bit key size (industry standard, NIST approved)
        - Public exponent 65537 (standard)
        - PKCS8 format for private key
        - SubjectPublicKeyInfo format for public key
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        # Serialize private key to PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),  # No passphrase (stored securely)
        )

        # Extract public key
        public_key = private_key.public_key()

        # Serialize public key to PEM
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Write keys to files
        with open(self.private_key_path, "wb") as f:
            f.write(private_pem)

        with open(self.public_key_path, "wb") as f:
            f.write(public_pem)

        # Set secure permissions (owner read/write only for private key)
        os.chmod(self.private_key_path, 0o600)
        os.chmod(self.public_key_path, 0o644)

    def _load_private_key(self) -> rsa.RSAPrivateKey:
        """Load private key from PEM file"""
        with open(self.private_key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

    def _load_public_key(self) -> rsa.RSAPublicKey:
        """Load public key from PEM file"""
        with open(self.public_key_path, "rb") as f:
            return serialization.load_pem_public_key(f.read(), backend=default_backend())

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create short-lived access token (15 minutes).

        Access tokens are used for API authentication and expire quickly
        for security. Users must refresh using refresh token.

        Args:
            data: Payload data (typically: sub, email, username)

        Returns:
            JWT token string (RS256 signed)

        Example:
            token = jwt_manager.create_access_token({
                "sub": "123",
                "email": "user@example.com",
                "username": "john"
            })
        """
        to_encode = data.copy()

        # Add standard claims
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update(
            {
                "exp": expire,  # Expiration time
                "iat": now,  # Issued at
                "type": "access",  # Token type (prevent substitution)
            }
        )

        # Sign with private key
        encoded_jwt = jwt.encode(
            to_encode, self.private_key, algorithm=self.ALGORITHM
        )

        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create long-lived refresh token (30 days).

        Refresh tokens are used to obtain new access tokens without
        re-entering credentials. Stored in database for revocation.

        Args:
            data: Payload data (typically: sub only)

        Returns:
            JWT token string (RS256 signed)

        Example:
            token = jwt_manager.create_refresh_token({"sub": "123"})
        """
        to_encode = data.copy()

        # Add standard claims
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update(
            {
                "exp": expire,  # Expiration time
                "iat": now,  # Issued at
                "type": "refresh",  # Token type
            }
        )

        # Sign with private key
        encoded_jwt = jwt.encode(
            to_encode, self.private_key, algorithm=self.ALGORITHM
        )

        return encoded_jwt

    def validate_token(
        self, token: str, expected_type: str = "access"
    ) -> Dict[str, Any]:
        """
        Validate JWT token and return decoded payload.

        Validates:
        - Signature (RS256 verification using public key)
        - Expiration (rejects expired tokens)
        - Token type (access vs refresh)

        Args:
            token: JWT token string
            expected_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid, expired, or wrong type

        Example:
            payload = jwt_manager.validate_token(token, "access")
            user_id = payload["sub"]
        """
        try:
            # Decode and verify signature with public key
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.ALGORITHM],
                options={"verify_signature": True, "verify_exp": True},
            )

            # Verify token type
            token_type = payload.get("type")
            if token_type != expected_type:
                raise JWTError(
                    f"Invalid token type: expected {expected_type}, got {token_type}"
                )

            return payload

        except JWTError as e:
            # Re-raise with clear error message
            raise JWTError(f"Token validation failed: {str(e)}")

    def decode_token_unsafe(self, token: str) -> Dict[str, Any]:
        """
        Decode token WITHOUT validation (for inspection only).

        WARNING: Do not use for authentication! This does not verify
        the signature or expiration. Only use for debugging or logging.

        Args:
            token: JWT token string

        Returns:
            Decoded payload (unverified)
        """
        return jwt.decode(
            token,
            self.public_key,
            algorithms=[self.ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )

    def get_token_expiry(self, token: str) -> datetime:
        """
        Get token expiration time without full validation.

        Args:
            token: JWT token string

        Returns:
            Expiration datetime (UTC)
        """
        payload = self.decode_token_unsafe(token)
        exp_timestamp = payload.get("exp")

        if not exp_timestamp:
            raise ValueError("Token has no expiration claim")

        return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without full validation.

        Args:
            token: JWT token string

        Returns:
            True if expired, False otherwise
        """
        try:
            expiry = self.get_token_expiry(token)
            return datetime.now(timezone.utc) >= expiry
        except (JWTError, ValueError):
            return True  # Assume expired if can't parse

    def get_token_subject(self, token: str) -> Optional[str]:
        """
        Extract subject (user_id) from token without validation.

        Useful for logging or debugging, but DO NOT use for authorization.

        Args:
            token: JWT token string

        Returns:
            Subject claim value (typically user ID)
        """
        try:
            payload = self.decode_token_unsafe(token)
            return payload.get("sub")
        except JWTError:
            return None

    def revoke_token(self, token: str) -> str:
        """
        Generate hash for token revocation.

        Store this hash in database refresh_tokens table with revoked=True.
        Token validation should check blacklist before accepting.

        Args:
            token: JWT token string to revoke

        Returns:
            SHA256 hash of token (for database storage)
        """
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()


# Convenience functions for FastAPI dependencies

def get_jwt_manager() -> JWTManager:
    """
    FastAPI dependency for JWT manager.

    Usage:
        @app.get("/protected")
        def protected_route(jwt: JWTManager = Depends(get_jwt_manager)):
            # Use jwt.validate_token(...)
    """
    return JWTManager()
