#!/usr/bin/env python3
"""
ConPort-KG JWT Utilities
Part of Phase 1 Security Hardening

JWT token generation, validation, and management using RS256.
"""

import os
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# JWT Configuration
JWT_ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30 days

# Key file paths
KEYS_DIR = os.path.join(os.path.dirname(__file__), "keys")
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "jwt_private.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "jwt_public.pem")

def load_or_generate_keys() -> Tuple[str, str]:
    """
    Load RSA keys from files or generate new ones if they don't exist.

    Returns:
        Tuple of (private_key_pem, public_key_pem)
    """
    try:
        # Try to load existing keys
        with open(PRIVATE_KEY_PATH, "rb") as f:
            private_key_pem = f.read().decode()

        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key_pem = f.read().decode()

        print("✅ Loaded existing JWT keys")
        return private_key_pem, public_key_pem

    except FileNotFoundError:
        # Generate new keys
        print("🔑 Generating new JWT RSA keys...")

        # Ensure keys directory exists
        os.makedirs(KEYS_DIR, exist_ok=True)

        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Serialize private key
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        # Serialize public key
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Save keys to files
        with open(PRIVATE_KEY_PATH, "w") as f:
            f.write(private_key_pem)

        with open(PUBLIC_KEY_PATH, "w") as f:
            f.write(public_key_pem)

        print("✅ Generated and saved new JWT keys")
        return private_key_pem, public_key_pem

# Load keys on module import
PRIVATE_KEY_PEM, PUBLIC_KEY_PEM = load_or_generate_keys()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time

    Returns:
        JWT access token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY_PEM, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Token payload data

    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY_PEM, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, PUBLIC_KEY_PEM, algorithms=[JWT_ALGORITHM])

        # Check token type
        if payload.get("type") not in ["access", "refresh"]:
            return None

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None

        return payload

    except jwt.ExpiredSignatureError:
        print("⚠️ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"⚠️ Invalid token: {e}")
        return None
    except Exception as e:
        print(f"❌ Token verification error: {e}")
        return None

# Alias for backward compatibility
validate_token = verify_token

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification (for debugging).

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid format, None otherwise
    """
    try:
        # Decode without verification (dangerous, only for debugging)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        print(f"❌ Token decode error: {e}")
        return None

def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get token expiration time.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime if valid, None otherwise
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.utcfromtimestamp(payload["exp"])
    return None

def is_token_expired(token: str) -> bool:
    """
    Check if token is expired.

    Args:
        token: JWT token string

    Returns:
        True if expired, False otherwise
    """
    exp_time = get_token_expiration(token)
    if exp_time:
        return datetime.utcnow() > exp_time
    return True

class JWTManager:
    """JWT token management utility class"""

    @staticmethod
    def create_token_pair(user_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Create both access and refresh tokens for a user.

        Args:
            user_data: User information for token payload

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create payload with user info
        payload = {
            "sub": str(user_data["id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "type": "user"
        }

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return access_token, refresh_token

    @staticmethod
    def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an access token.

        Args:
            token: JWT access token

        Returns:
            User data if valid, None otherwise
        """
        payload = verify_token(token)
        if payload and payload.get("type") == "access":
            return {
                "user_id": int(payload["sub"]),
                "email": payload["email"],
                "username": payload["username"]
            }
        return None

    @staticmethod
    def validate_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a refresh token.

        Args:
            token: JWT refresh token

        Returns:
            User data if valid, None otherwise
        """
        payload = verify_token(token)
        if payload and payload.get("type") == "refresh":
            return {
                "user_id": int(payload["sub"]),
                "email": payload["email"],
                "username": payload["username"]
            }
        return None

    @staticmethod
    def get_token_info(token: str) -> Dict[str, Any]:
        """
        Get comprehensive token information.

        Args:
            token: JWT token string

        Returns:
            Dictionary with token information
        """
        payload = decode_token(token)
        if not payload:
            return {"valid": False}

        return {
            "valid": True,
            "type": payload.get("type"),
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "issued_at": datetime.utcfromtimestamp(payload.get("iat", 0)) if payload.get("iat") else None,
            "expires_at": datetime.utcfromtimestamp(payload.get("exp", 0)) if payload.get("exp") else None,
            "expired": is_token_expired(token)
        }

# Export key functions
__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "validate_token",
    "decode_token",
    "get_token_expiration",
    "is_token_expired",
    "JWTManager",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS"
]