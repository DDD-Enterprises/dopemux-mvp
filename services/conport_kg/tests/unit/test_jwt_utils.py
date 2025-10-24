#!/usr/bin/env python3
"""
ConPort-KG JWT Utilities Tests
Phase 1 Week 1 Day 1

Comprehensive testing of JWT token generation and validation.
"""

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jose import JWTError

# Ensure auth package is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.jwt_utils import JWTManager


@pytest.fixture
def jwt_manager(tmp_path):
    """JWT manager with temporary keys for testing"""
    key_dir = tmp_path / "keys"
    key_dir.mkdir()

    return JWTManager(
        private_key_path=str(key_dir / "test_private.pem"),
        public_key_path=str(key_dir / "test_public.pem"),
    )


@pytest.fixture
def sample_payload():
    """Sample JWT payload for testing"""
    return {"sub": "123", "email": "test@example.com", "username": "testuser"}


class TestJWTKeyGeneration:
    """Test RSA key pair generation"""

    def test_keys_auto_generated_if_missing(self, tmp_path):
        """Test that JWT manager auto-generates keys if they don't exist"""
        key_dir = tmp_path / "keys"
        key_dir.mkdir()

        private_path = key_dir / "private.pem"
        public_path = key_dir / "public.pem"

        # Keys don't exist yet
        assert not private_path.exists()
        assert not public_path.exists()

        # Initialize manager (should generate keys)
        manager = JWTManager(
            private_key_path=str(private_path), public_key_path=str(public_path)
        )

        # Keys now exist
        assert private_path.exists()
        assert public_path.exists()

    def test_private_key_has_secure_permissions(self, tmp_path):
        """Test that private key has restrictive permissions (0600)"""
        key_dir = tmp_path / "keys"
        key_dir.mkdir()

        private_path = key_dir / "private.pem"

        manager = JWTManager(
            private_key_path=str(private_path), public_key_path=str(key_dir / "public.pem")
        )

        # Check file permissions (owner read/write only)
        stat_info = os.stat(private_path)
        permissions = stat_info.st_mode & 0o777

        assert permissions == 0o600, f"Expected 0o600, got {oct(permissions)}"

    def test_public_key_has_readable_permissions(self, tmp_path):
        """Test that public key is readable (0644)"""
        key_dir = tmp_path / "keys"
        key_dir.mkdir()

        public_path = key_dir / "public.pem"

        manager = JWTManager(
            private_key_path=str(key_dir / "private.pem"), public_key_path=str(public_path)
        )

        stat_info = os.stat(public_path)
        permissions = stat_info.st_mode & 0o777

        assert permissions == 0o644, f"Expected 0o644, got {oct(permissions)}"


class TestJWTTokenCreation:
    """Test JWT token creation functionality"""

    def test_create_access_token_with_valid_payload(self, jwt_manager, sample_payload):
        """Test creating access token with valid user payload"""
        token = jwt_manager.create_access_token(sample_payload)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_create_access_token_includes_required_claims(
        self, jwt_manager, sample_payload
    ):
        """Test that access tokens include required JWT claims"""
        token = jwt_manager.create_access_token(sample_payload)
        decoded = jwt_manager.validate_token(token, "access")

        # Standard JWT claims
        assert "exp" in decoded, "Missing expiration claim"
        assert "iat" in decoded, "Missing issued-at claim"
        assert "type" in decoded, "Missing type claim"

        # Custom claims
        assert decoded["sub"] == sample_payload["sub"]
        assert decoded["email"] == sample_payload["email"]
        assert decoded["type"] == "access"

    def test_create_refresh_token_with_valid_payload(self, jwt_manager):
        """Test creating refresh token with valid user payload"""
        payload = {"sub": "123"}
        token = jwt_manager.create_refresh_token(payload)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_has_longer_expiration(self, jwt_manager, sample_payload):
        """Test that refresh tokens have longer expiration than access tokens"""
        access_token = jwt_manager.create_access_token(sample_payload)
        refresh_token = jwt_manager.create_refresh_token({"sub": sample_payload["sub"]})

        access_decoded = jwt_manager.validate_token(access_token, "access")
        refresh_decoded = jwt_manager.validate_token(refresh_token, "refresh")

        access_exp = datetime.fromtimestamp(access_decoded["exp"], tz=timezone.utc)
        refresh_exp = datetime.fromtimestamp(refresh_decoded["exp"], tz=timezone.utc)

        # Refresh should expire much later than access
        assert refresh_exp > access_exp
        diff = (refresh_exp - access_exp).total_seconds()
        assert diff > 86400  # At least 1 day difference

    def test_access_token_expires_in_15_minutes(self, jwt_manager, sample_payload):
        """Test that access tokens expire in 15 minutes"""
        token = jwt_manager.create_access_token(sample_payload)
        decoded = jwt_manager.validate_token(token, "access")

        iat = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

        diff_minutes = (exp - iat).total_seconds() / 60

        assert 14.9 <= diff_minutes <= 15.1, f"Expected ~15 minutes, got {diff_minutes}"


class TestJWTTokenValidation:
    """Test JWT token validation functionality"""

    def test_validate_token_valid_access_token(self, jwt_manager, sample_payload):
        """Test validating a valid access token"""
        token = jwt_manager.create_access_token(sample_payload)
        decoded = jwt_manager.validate_token(token, "access")

        assert decoded["sub"] == sample_payload["sub"]
        assert decoded["email"] == sample_payload["email"]
        assert decoded["username"] == sample_payload["username"]

    def test_validate_token_valid_refresh_token(self, jwt_manager):
        """Test validating a valid refresh token"""
        payload = {"sub": "456"}
        token = jwt_manager.create_refresh_token(payload)
        decoded = jwt_manager.validate_token(token, "refresh")

        assert decoded["sub"] == "456"
        assert decoded["type"] == "refresh"

    def test_validate_token_expired_token(self, jwt_manager):
        """Test that expired tokens are rejected"""
        # Create token with past expiration
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            "sub": "123",
            "exp": past_time,
            "iat": past_time - timedelta(minutes=15),
            "type": "access",
        }

        # Manually create expired token (bypass create_access_token)
        from jose import jwt as jose_jwt

        expired_token = jose_jwt.encode(
            payload, jwt_manager.private_key, algorithm=jwt_manager.ALGORITHM
        )

        # Validation should fail
        with pytest.raises(JWTError, match="expired"):
            jwt_manager.validate_token(expired_token, "access")

    def test_validate_token_invalid_token(self, jwt_manager):
        """Test that invalid tokens are rejected"""
        invalid_token = "not.a.valid.jwt.token"

        with pytest.raises(JWTError):
            jwt_manager.validate_token(invalid_token, "access")

    def test_validate_token_wrong_type(self, jwt_manager, sample_payload):
        """Test that token type mismatch is rejected"""
        # Create access token
        access_token = jwt_manager.create_access_token(sample_payload)

        # Try to validate as refresh token
        with pytest.raises(JWTError, match="Invalid token type"):
            jwt_manager.validate_token(access_token, "refresh")

    def test_validate_token_wrong_signature(self, jwt_manager, tmp_path, sample_payload):
        """Test that tokens signed with different key are rejected"""
        # Create second JWT manager with different keys
        key_dir = tmp_path / "other_keys"
        key_dir.mkdir()

        other_manager = JWTManager(
            private_key_path=str(key_dir / "other_private.pem"),
            public_key_path=str(key_dir / "other_public.pem"),
        )

        # Create token with other manager
        token = other_manager.create_access_token(sample_payload)

        # Try to validate with original manager (different public key)
        with pytest.raises(JWTError):
            jwt_manager.validate_token(token, "access")


class TestJWTTokenUtilities:
    """Test utility methods"""

    def test_decode_token_unsafe(self, jwt_manager, sample_payload):
        """Test decoding token without validation"""
        token = jwt_manager.create_access_token(sample_payload)
        decoded = jwt_manager.decode_token_unsafe(token)

        # Should decode without error (no validation)
        assert decoded["sub"] == sample_payload["sub"]
        assert decoded["email"] == sample_payload["email"]

    def test_decode_unsafe_works_on_expired_token(self, jwt_manager):
        """Test that unsafe decode works even on expired tokens"""
        # Create expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            "sub": "123",
            "exp": past_time,
            "type": "access",
        }

        from jose import jwt as jose_jwt

        expired_token = jose_jwt.encode(
            payload, jwt_manager.private_key, algorithm=jwt_manager.ALGORITHM
        )

        # Unsafe decode should work
        decoded = jwt_manager.decode_token_unsafe(expired_token)
        assert decoded["sub"] == "123"

    def test_get_token_expiry(self, jwt_manager, sample_payload):
        """Test extracting token expiry time"""
        token = jwt_manager.create_access_token(sample_payload)
        expiry = jwt_manager.get_token_expiry(token)

        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)

    def test_is_token_expired_false_for_valid_token(self, jwt_manager, sample_payload):
        """Test that valid tokens are not marked as expired"""
        token = jwt_manager.create_access_token(sample_payload)
        assert jwt_manager.is_token_expired(token) is False

    def test_is_token_expired_true_for_expired_token(self, jwt_manager):
        """Test that expired tokens are correctly identified"""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "123", "exp": past_time, "type": "access"}

        from jose import jwt as jose_jwt

        expired_token = jose_jwt.encode(
            payload, jwt_manager.private_key, algorithm=jwt_manager.ALGORITHM
        )

        assert jwt_manager.is_token_expired(expired_token) is True

    def test_get_token_subject(self, jwt_manager, sample_payload):
        """Test extracting subject from token"""
        token = jwt_manager.create_access_token(sample_payload)
        subject = jwt_manager.get_token_subject(token)

        assert subject == sample_payload["sub"]

    def test_revoke_token_generates_hash(self, jwt_manager, sample_payload):
        """Test that revoke_token generates consistent hash"""
        token = jwt_manager.create_access_token(sample_payload)

        hash1 = jwt_manager.revoke_token(token)
        hash2 = jwt_manager.revoke_token(token)

        # Same token should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex = 64 characters
