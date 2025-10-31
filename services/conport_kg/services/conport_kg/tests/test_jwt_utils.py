#!/usr/bin/env python3
"""
ConPort-KG JWT Utilities Tests
TDD implementation of JWT token management.
"""

import pytest
import time
from datetime import datetime, timedelta

pytestmark = pytest.mark.unit

class TestJWTTokenCreation:
    """Test JWT token creation functionality."""

    def test_create_access_token_with_valid_payload(self):
        """Test creating access token with valid user payload."""
        from conport_kg.auth.jwt_utils import create_access_token

        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

        token = create_access_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Token should have 3 parts separated by dots
        parts = token.split('.')
        assert len(parts) == 3

    def test_create_access_token_includes_required_claims(self):
        """Test that access tokens include required JWT claims."""
        from conport_kg.auth.jwt_utils import validate_token

        user_data = {
            "id": 123,
            "email": "user@example.com",
            "username": "testuser"
        }

        token = create_access_token(user_data)
        payload = validate_token(token)

        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "user@example.com"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_with_valid_payload(self):
        """Test creating refresh token with valid user payload."""
        from conport_kg.auth.jwt_utils import create_refresh_token

        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

        token = create_refresh_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Token should have 3 parts separated by dots
        parts = token.split('.')
        assert len(parts) == 3

    def test_refresh_token_has_longer_expiration(self):
        """Test that refresh tokens have longer expiration than access tokens."""
        from conport_kg.auth.jwt_utils import create_access_token, create_refresh_token, get_token_expiration

        user_data = {"id": 1, "email": "test@example.com", "username": "testuser"}

        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        access_exp = get_token_expiration(access_token)
        refresh_exp = get_token_expiration(refresh_token)

        assert access_exp is not None
        assert refresh_exp is not None
        assert refresh_exp > access_exp

        # Refresh token should be valid for ~30 days
        time_diff = refresh_exp - datetime.utcnow()
        assert time_diff.days >= 25  # Allow some margin

class TestJWTTokenValidation:
    """Test JWT token validation functionality."""

    def test_validate_token_valid_access_token(self):
        """Test validating a valid access token."""
        from conport_kg.auth.jwt_utils import create_access_token, validate_token

        user_data = {
            "id": 456,
            "email": "valid@example.com",
            "username": "validuser"
        }

        token = create_access_token(user_data)
        payload = validate_token(token)

        assert payload is not None
        assert payload["sub"] == "456"
        assert payload["email"] == "valid@example.com"
        assert payload["username"] == "validuser"
        assert payload["type"] == "access"

    def test_validate_token_valid_refresh_token(self):
        """Test validating a valid refresh token."""
        from conport_kg.auth.jwt_utils import create_refresh_token, validate_token

        user_data = {
            "id": 789,
            "email": "refresh@example.com",
            "username": "refreshuser"
        }

        token = create_refresh_token(user_data)
        payload = validate_token(token)

        assert payload is not None
        assert payload["sub"] == "789"
        assert payload["email"] == "refresh@example.com"
        assert payload["username"] == "refreshuser"
        assert payload["type"] == "refresh"

    def test_validate_token_expired_token(self):
        """Test that expired tokens are rejected."""
        from conport_kg.auth.jwt_utils import create_access_token, validate_token

        user_data = {"id": 1, "email": "test@example.com", "username": "testuser"}

        # Create token that expires in 1 second
        token = create_access_token(user_data, expires_delta=timedelta(seconds=1))

        # Wait for expiration
        time.sleep(1.1)

        # Should return None for expired token
        payload = validate_token(token)
        assert payload is None

    def test_validate_token_invalid_token(self):
        """Test that invalid tokens are rejected."""
        from conport_kg.auth.jwt_utils import validate_token

        invalid_tokens = [
            "not-a-jwt-token",
            "header.payload",  # Missing signature
            "header.payload.signature.extra",  # Too many parts
            "",  # Empty
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature"  # Invalid payload
        ]

        for invalid_token in invalid_tokens:
            payload = validate_token(invalid_token)
            assert payload is None, f"Token '{invalid_token}' should be invalid"

    def test_validate_token_wrong_algorithm(self):
        """Test that tokens with wrong algorithm are rejected."""
        import jwt

        # Create token with HS256 but our system expects RS256
        payload = {
            "sub": "123",
            "email": "test@example.com",
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }

        # Use HS256 algorithm (not RS256)
        wrong_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        from conport_kg.auth.jwt_utils import validate_token
        payload = validate_token(wrong_token)
        assert payload is None

class TestJWTTokenUtilities:
    """Test JWT token utility functions."""

    def test_get_token_expiration_valid_token(self):
        """Test getting expiration time from valid token."""
        from conport_kg.auth.jwt_utils import create_access_token, get_token_expiration

        user_data = {"id": 1, "email": "test@example.com", "username": "testuser"}
        token = create_access_token(user_data)

        exp_time = get_token_expiration(token)
        assert exp_time is not None
        assert isinstance(exp_time, datetime)

        # Should expire in about 15 minutes
        now = datetime.utcnow()
        time_diff = exp_time - now
        assert time_diff.seconds >= 800  # At least 13 minutes
        assert time_diff.seconds <= 1000  # At most 17 minutes

    def test_get_token_expiration_invalid_token(self):
        """Test getting expiration from invalid token returns None."""
        from conport_kg.auth.jwt_utils import get_token_expiration

        invalid_tokens = [
            "not-a-jwt",
            "",
            "header.payload.signature"
        ]

        for invalid_token in invalid_tokens:
            exp_time = get_token_expiration(invalid_token)
            assert exp_time is None

    def test_is_token_expired_valid_token(self):
        """Test checking if valid token is expired."""
        from conport_kg.auth.jwt_utils import create_access_token, is_token_expired

        user_data = {"id": 1, "email": "test@example.com", "username": "testuser"}
        token = create_access_token(user_data)

        # Should not be expired
        assert not is_token_expired(token)

    def test_is_token_expired_expired_token(self):
        """Test checking if expired token is expired."""
        from conport_kg.auth.jwt_utils import create_access_token, is_token_expired

        user_data = {"id": 1, "email": "test@example.com", "username": "testuser"}

        # Create token that expires in 1 second
        token = create_access_token(user_data, expires_delta=timedelta(seconds=1))

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert is_token_expired(token)

    def test_is_token_expired_invalid_token(self):
        """Test checking if invalid token is expired."""
        from conport_kg.auth.jwt_utils import is_token_expired

        invalid_tokens = [
            "not-a-jwt",
            "",
            "header.payload.signature"
        ]

        for invalid_token in invalid_tokens:
            # Invalid tokens are considered expired
            assert is_token_expired(invalid_token)

class TestJWTManager:
    """Test JWTManager class functionality."""

    def test_create_token_pair_creates_both_tokens(self):
        """Test creating both access and refresh tokens."""
        from conport_kg.auth.jwt_utils import JWTManager

        user_data = {
            "id": 999,
            "email": "manager@example.com",
            "username": "tokenmanager"
        }

        access_token, refresh_token = JWTManager.create_token_pair(user_data)

        assert access_token is not None
        assert refresh_token is not None
        assert access_token != refresh_token

        # Both should be valid JWTs
        assert len(access_token.split('.')) == 3
        assert len(refresh_token.split('.')) == 3

    def test_validate_access_token_valid_token(self):
        """Test validating a valid access token."""
        from conport_kg.auth.jwt_utils import JWTManager

        user_data = {
            "id": 111,
            "email": "access@example.com",
            "username": "accesstester"
        }

        access_token, _ = JWTManager.create_token_pair(user_data)
        validated_data = JWTManager.validate_access_token(access_token)

        assert validated_data is not None
        assert validated_data["user_id"] == 111
        assert validated_data["email"] == "access@example.com"
        assert validated_data["username"] == "accesstester"

    def test_validate_access_token_invalid_token(self):
        """Test validating an invalid access token."""
        from conport_kg.auth.jwt_utils import JWTManager

        invalid_tokens = [
            "invalid-token",
            "",
            "not.a.jwt"
        ]

        for invalid_token in invalid_tokens:
            validated_data = JWTManager.validate_access_token(invalid_token)
            assert validated_data is None

    def test_validate_refresh_token_valid_token(self):
        """Test validating a valid refresh token."""
        from conport_kg.auth.jwt_utils import JWTManager

        user_data = {
            "id": 222,
            "email": "refresh@example.com",
            "username": "refreshtester"
        }

        _, refresh_token = JWTManager.create_token_pair(user_data)
        validated_data = JWTManager.validate_refresh_token(refresh_token)

        assert validated_data is not None
        assert validated_data["user_id"] == 222
        assert validated_data["email"] == "refresh@example.com"
        assert validated_data["username"] == "refreshtester"

    def test_validate_refresh_token_invalid_token(self):
        """Test validating an invalid refresh token."""
        from conport_kg.auth.jwt_utils import JWTManager

        invalid_tokens = [
            "invalid-token",
            "",
            "not.a.jwt"
        ]

        for invalid_token in invalid_tokens:
            validated_data = JWTManager.validate_refresh_token(invalid_token)
            assert validated_data is None

    def test_get_token_info_valid_tokens(self):
        """Test getting comprehensive token information."""
        from conport_kg.auth.jwt_utils import JWTManager

        user_data = {
            "id": 333,
            "email": "info@example.com",
            "username": "infotester"
        }

        access_token, refresh_token = JWTManager.create_token_pair(user_data)

        # Test access token info
        access_info = JWTManager.get_token_info(access_token)
        assert access_info["valid"] is True
        assert access_info["type"] == "access"
        assert access_info["user_id"] == 333
        assert access_info["email"] == "info@example.com"
        assert access_info["username"] == "infotester"
        assert access_info["expired"] is False
        assert "issued_at" in access_info
        assert "expires_at" in access_info

        # Test refresh token info
        refresh_info = JWTManager.get_token_info(refresh_token)
        assert refresh_info["valid"] is True
        assert refresh_info["type"] == "refresh"
        assert refresh_info["expired"] is False

    def test_get_token_info_invalid_token(self):
        """Test getting token info for invalid tokens."""
        from conport_kg.auth.jwt_utils import JWTManager

        invalid_tokens = [
            "invalid-token",
            "",
            "not.a.jwt"
        ]

        for invalid_token in invalid_tokens:
            info = JWTManager.get_token_info(invalid_token)
            assert info["valid"] is False
            assert "type" not in info or info.get("type") is None