#!/usr/bin/env python3
"""
ConPort-KG Password Utilities Tests
TDD implementation of password security features.
"""

import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.unit

class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password_creates_valid_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        from conport_kg.auth.password_utils import PasswordManager

        password = "testpassword123"
        hashed = PasswordManager.hash_password(password)

        # Should return a string
        assert isinstance(hashed, str)
        assert len(hashed) > 0

        # Should start with bcrypt identifier ($2b$ or $2a$)
        assert hashed.startswith("$2")

    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password multiple times produces different hashes (due to salt)."""
        from conport_kg.auth.password_utils import PasswordManager

        password = "testpassword123"
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)

        # Hashes should be different due to unique salts
        assert hash1 != hash2

        # But both should verify correctly
        assert PasswordManager.verify_password(password, hash1)
        assert PasswordManager.verify_password(password, hash2)

    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        from conport_kg.auth.password_utils import PasswordManager

        password = "correctpassword123"
        hashed = PasswordManager.hash_password(password)

        assert PasswordManager.verify_password(password, hashed)

    def test_verify_password_wrong_password(self):
        """Test that verify_password returns False for incorrect password."""
        from conport_kg.auth.password_utils import PasswordManager

        correct_password = "correctpassword123"
        wrong_password = "wrongpassword123"
        hashed = PasswordManager.hash_password(correct_password)

        assert not PasswordManager.verify_password(wrong_password, hashed)

    def test_verify_password_invalid_hash(self):
        """Test that verify_password handles invalid hash gracefully."""
        from conport_kg.auth.password_utils import PasswordManager

        password = "testpassword123"
        invalid_hash = "not-a-valid-hash"

        # Should return False, not raise exception
        assert not PasswordManager.verify_password(password, invalid_hash)

class TestPasswordValidation:
    """Test password strength validation."""

    def test_validate_password_strength_valid_password(self):
        """Test that valid passwords pass validation."""
        from conport_kg.auth.password_utils import PasswordManager

        # Test various valid passwords
        valid_passwords = [
            "MySecurePass123!",
            "Complex@Password#456",
            "StrongPwd789$%^"
        ]

        for password in valid_passwords:
            # Should not raise exception
            PasswordManager.validate_password_strength(password)

    def test_validate_password_strength_too_short(self):
        """Test that passwords shorter than minimum length are rejected."""
        from conport_kg.auth.password_utils import PasswordManager, PasswordValidationError

        short_password = "Short1!"

        with pytest.raises(PasswordValidationError) as exc_info:
            PasswordManager.validate_password_strength(short_password)

        assert "must be at least" in str(exc_info.value)

    def test_validate_password_strength_missing_uppercase(self):
        """Test that passwords without uppercase letters are rejected."""
        from conport_kg.auth.password_utils import PasswordManager, PasswordValidationError

        no_upper_password = "nouppercasepassword123!"

        with pytest.raises(PasswordValidationError) as exc_info:
            PasswordManager.validate_password_strength(no_upper_password)

        assert "uppercase letter" in str(exc_info.value)

    def test_validate_password_strength_missing_lowercase(self):
        """Test that passwords without lowercase letters are rejected."""
        from conport_kg.auth.password_utils import PasswordManager, PasswordValidationError

        no_lower_password = "NOLOWERCASEPASSWORD123!"

        with pytest.raises(PasswordValidationError) as exc_info:
            PasswordManager.validate_password_strength(no_lower_password)

        assert "lowercase letter" in str(exc_info.value)

    def test_validate_password_strength_missing_digits(self):
        """Test that passwords without digits are rejected."""
        from conport_kg.auth.password_utils import PasswordManager, PasswordValidationError

        no_digit_password = "NoDigitsPassword!"

        with pytest.raises(PasswordValidationError) as exc_info:
            PasswordManager.validate_password_strength(no_digit_password)

        assert "digit" in str(exc_info.value)

    def test_validate_password_strength_missing_special_chars(self):
        """Test that passwords without special characters are rejected."""
        from conport_kg.auth.password_utils import PasswordManager, PasswordValidationError

        no_special_password = "NoSpecialCharacters123"

        with pytest.raises(PasswordValidationError) as exc_info:
            PasswordManager.validate_password_strength(no_special_password)

        assert "special character" in str(exc_info.value)

    def test_validate_password_strength_too_long(self):
        """Test that passwords longer than maximum length are rejected."""
        from conport_kg.auth.password_utils import PasswordManager, PasswordValidationError

        # Create password longer than max length
        long_password = "A" * (PasswordManager.MAX_LENGTH + 1) + "1!"

        with pytest.raises(PasswordValidationError) as exc_info:
            PasswordManager.validate_password_strength(long_password)

        assert "must be at most" in str(exc_info.value)

class TestPasswordRequirements:
    """Test password requirements configuration."""

    def test_get_password_requirements(self):
        """Test that password requirements are correctly returned."""
        from conport_kg.auth.password_utils import PasswordManager

        requirements = PasswordManager.get_password_requirements()

        required_keys = [
            "min_length", "max_length", "require_uppercase", "require_lowercase",
            "require_digits", "require_special", "special_chars", "examples"
        ]

        for key in required_keys:
            assert key in requirements

        # Check specific values
        assert requirements["min_length"] == PasswordManager.MIN_LENGTH
        assert requirements["max_length"] == PasswordManager.MAX_LENGTH
        assert requirements["require_uppercase"] is True
        assert isinstance(requirements["examples"], list)
        assert len(requirements["examples"]) > 0

class TestPasswordResetManager:
    """Test password reset token management."""

    def test_generate_reset_token(self):
        """Test that reset tokens are generated securely."""
        from conport_kg.auth.password_utils import PasswordResetManager

        token1 = PasswordResetManager.generate_reset_token()
        token2 = PasswordResetManager.generate_reset_token()

        # Tokens should be strings
        assert isinstance(token1, str)
        assert isinstance(token2, str)

        # Tokens should be different
        assert token1 != token2

        # Tokens should be URL-safe (no special chars that need encoding)
        import string
        allowed_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in allowed_chars for c in token1)
        assert all(c in allowed_chars for c in token2)

    def test_hash_reset_token(self):
        """Test that reset tokens can be hashed."""
        from conport_kg.auth.password_utils import PasswordResetManager

        token = "test-reset-token-123"
        hashed = PasswordResetManager.hash_reset_token(token)

        # Should return a string
        assert isinstance(hashed, str)
        assert hashed != token  # Should be hashed, not plain

    def test_verify_reset_token_correct(self):
        """Test that correct reset tokens verify successfully."""
        from conport_kg.auth.password_utils import PasswordResetManager

        token = "correct-reset-token"
        hashed = PasswordResetManager.hash_reset_token(token)

        assert PasswordResetManager.verify_reset_token(token, hashed)

    def test_verify_reset_token_wrong_token(self):
        """Test that wrong reset tokens fail verification."""
        from conport_kg.auth.password_utils import PasswordResetManager

        correct_token = "correct-token"
        wrong_token = "wrong-token"
        hashed = PasswordResetManager.hash_reset_token(correct_token)

        assert not PasswordResetManager.verify_reset_token(wrong_token, hashed)

    def test_verify_reset_token_invalid_hash(self):
        """Test that invalid hashes are handled gracefully."""
        from conport_kg.auth.password_utils import PasswordResetManager

        token = "test-token"
        invalid_hash = "not-a-valid-hash"

        # Should return False, not raise exception
        assert not PasswordResetManager.verify_reset_token(token, invalid_hash)

class TestPydanticModels:
    """Test Pydantic models for API validation."""

    def test_password_change_request_validation(self):
        """Test PasswordChangeRequest validation."""
        from conport_kg.auth.password_utils import PasswordChangeRequest, PasswordValidationError

        # Valid request
        valid_request = PasswordChangeRequest(
            current_password="OldPass123!",
            new_password="NewPass456!"
        )
        assert valid_request.current_password == "OldPass123!"
        assert valid_request.new_password == "NewPass456!"

        # Invalid new password
        with pytest.raises(ValueError):  # Pydantic validation error
            PasswordChangeRequest(
                current_password="OldPass123!",
                new_password="weak"  # Too short, missing requirements
            )

    def test_password_reset_request_validation(self):
        """Test PasswordResetRequest validation."""
        from conport_kg.auth.password_utils import PasswordResetRequest

        # Valid request
        valid_request = PasswordResetRequest(email="user@example.com")
        assert valid_request.email == "user@example.com"

    def test_password_reset_confirm_validation(self):
        """Test PasswordResetConfirm validation."""
        from conport_kg.auth.password_utils import PasswordResetConfirm, PasswordValidationError

        # Valid request
        valid_request = PasswordResetConfirm(
            token="valid-reset-token-123",
            new_password="NewSecurePass789!"
        )
        assert valid_request.token == "valid-reset-token-123"
        assert valid_request.new_password == "NewSecurePass789!"

        # Invalid new password
        with pytest.raises(ValueError):  # Pydantic validation error
            PasswordResetConfirm(
                token="valid-token",
                new_password="weak"
            )