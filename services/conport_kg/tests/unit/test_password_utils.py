#!/usr/bin/env python3
"""
ConPort-KG Password Utilities Tests
Phase 1 Week 1 Day 1

Comprehensive testing of password hashing, validation, and breach detection.
"""

from pathlib import Path

import pytest

# Ensure auth package is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.password_utils import PasswordManager, PasswordValidationError


@pytest.fixture
def password_manager():
    """Password manager for testing"""
    return PasswordManager()


class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password_creates_valid_hash(self, password_manager):
        """Test that password hashing produces valid Argon2id hash"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50
        assert "$" in hashed  # Argon2 format uses $ separators

    def test_hash_password_different_salts(self, password_manager):
        """Test that same password produces different hashes (random salt)"""
        password = "SecurePassword123!@#"

        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)

        # Different hashes due to random salt
        assert hash1 != hash2

    def test_verify_password_correct_password(self, password_manager):
        """Test that correct password verifies successfully"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password(password, hashed) is True

    def test_verify_password_wrong_password(self, password_manager):
        """Test that wrong password is rejected"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password("WrongPassword", hashed) is False
        assert password_manager.verify_password("securepassword123!@#", hashed) is False

    def test_verify_password_empty_password(self, password_manager):
        """Test that empty password is rejected"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self, password_manager):
        """Test that invalid hash format returns False"""
        password = "SecurePassword123!@#"
        invalid_hash = "not-a-valid-hash"

        assert password_manager.verify_password(password, invalid_hash) is False


class TestPasswordValidation:
    """Test password strength validation"""

    def test_validate_password_too_short(self, password_manager):
        """Test that short passwords are rejected"""
        with pytest.raises(PasswordValidationError, match="at least 12 characters"):
            password_manager.validate_password_strength("Short1!")

    def test_validate_password_no_uppercase(self, password_manager):
        """Test that passwords without uppercase are rejected"""
        with pytest.raises(PasswordValidationError, match="uppercase"):
            password_manager.validate_password_strength("longpassword123!")

    def test_validate_password_no_lowercase(self, password_manager):
        """Test that passwords without lowercase are rejected"""
        with pytest.raises(PasswordValidationError, match="lowercase"):
            password_manager.validate_password_strength("LONGPASSWORD123!")

    def test_validate_password_no_digit(self, password_manager):
        """Test that passwords without digits are rejected"""
        with pytest.raises(PasswordValidationError, match="digit"):
            password_manager.validate_password_strength("LongPasswordOnly!")

    def test_validate_password_no_special_char(self, password_manager):
        """Test that passwords without special characters are rejected"""
        with pytest.raises(PasswordValidationError, match="special character"):
            password_manager.validate_password_strength("LongPassword123")

    def test_validate_password_common_pattern_password(self, password_manager):
        """Test that passwords starting with 'password' are rejected"""
        with pytest.raises(PasswordValidationError, match="common pattern"):
            password_manager.validate_password_strength("Password123!@#")

    def test_validate_password_common_pattern_admin(self, password_manager):
        """Test that passwords starting with 'admin' are rejected"""
        with pytest.raises(PasswordValidationError, match="common pattern"):
            password_manager.validate_password_strength("Admin123!@#Pass")

    def test_validate_password_sequential_numbers(self, password_manager):
        """Test that passwords with sequential numbers are rejected"""
        with pytest.raises(PasswordValidationError, match="common pattern"):
            password_manager.validate_password_strength("SecurePass12345!")

    def test_validate_password_keyboard_pattern(self, password_manager):
        """Test that keyboard patterns are rejected"""
        with pytest.raises(PasswordValidationError, match="common pattern"):
            password_manager.validate_password_strength("Qwerty123!@#Pass")

    def test_validate_password_valid_strong_password(self, password_manager):
        """Test that strong valid password passes validation"""
        # Should not raise exception
        password_manager.validate_password_strength("MyStr0ng!Pass#2025")
        password_manager.validate_password_strength("Tr0ub4dor&3Extended")
        password_manager.validate_password_strength("C0rrect#Horse$Battery")


class TestPasswordBreachDetection:
    """Test HaveIBeenPwned breach detection"""

    @pytest.mark.asyncio
    async def test_check_password_breach_known_breached(self, password_manager):
        """Test that known breached password is detected"""
        # "password" is known to be in HIBP database
        is_breached = await password_manager.check_password_breach("password")

        # Should be breached (common password)
        assert is_breached is True

    @pytest.mark.asyncio
    async def test_check_password_breach_unique_password(self, password_manager):
        """Test that unique password is not flagged"""
        # Very unlikely to be breached (random string)
        unique = "MyVeryUn1que!Pass#XyZ2025$Random"
        is_breached = await password_manager.check_password_breach(unique)

        # Should not be breached
        assert is_breached is False

    @pytest.mark.asyncio
    async def test_check_password_breach_handles_api_failure(
        self, password_manager, monkeypatch
    ):
        """Test that API failures don't block user (graceful degradation)"""

        # Mock HTTPX AsyncClient context manager
        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, *args, **kwargs):
                raise Exception("Network error")

        import httpx

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockAsyncClient())

        # Should return False (allow user, don't block on API failure)
        is_breached = await password_manager.check_password_breach("SomePassword123!")
        assert is_breached is False


class TestPasswordResetTokens:
    """Test password reset token generation"""

    def test_generate_reset_token_creates_token(self, password_manager):
        """Test that reset token is generated"""
        token = password_manager.generate_password_reset_token(user_id=123)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) == 64  # 32 bytes * 2 (hex encoding)

    def test_generate_reset_token_unique(self, password_manager):
        """Test that each reset token is unique"""
        token1 = password_manager.generate_password_reset_token(user_id=123)
        token2 = password_manager.generate_password_reset_token(user_id=123)

        # Different tokens even for same user
        assert token1 != token2

    def test_hash_reset_token_consistent(self, password_manager):
        """Test that hashing reset token is deterministic"""
        token = "test_token_12345"

        hash1 = password_manager.hash_reset_token(token)
        hash2 = password_manager.hash_reset_token(token)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex = 64 chars

    def test_hash_reset_token_different_for_different_tokens(self, password_manager):
        """Test that different tokens produce different hashes"""
        hash1 = password_manager.hash_reset_token("token1")
        hash2 = password_manager.hash_reset_token("token2")

        assert hash1 != hash2


class TestPasswordRehashing:
    """Test password rehashing detection"""

    def test_check_needs_rehash_false_for_current_params(self, password_manager):
        """Test that hashes with current parameters don't need rehash"""
        password = "SecurePassword123!@#"
        hashed = password_manager.hash_password(password)

        assert password_manager.check_needs_rehash(hashed) is False

    def test_check_needs_rehash_true_for_invalid_hash(self, password_manager):
        """Test that invalid hashes are flagged for rehash"""
        invalid_hash = "not-a-valid-argon2-hash"

        assert password_manager.check_needs_rehash(invalid_hash) is True
