
import pytest
import hashlib
from src.utils.security import SecureTokenManager

class TestSecureTokenManager:

    def test_generate_token_returns_string(self):
        manager = SecureTokenManager()
        token = manager.generate_token("user1")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_tokens_are_stored_securely(self):
        manager = SecureTokenManager()
        identifier = "user1"
        token = manager.generate_token(identifier)

        # Verify stored value is not the plain token
        stored_value = manager._tokens[identifier]
        assert stored_value != token

        # Verify stored value has the correct format (salt$hash)
        assert "$" in stored_value
        parts = stored_value.split("$")
        assert len(parts) == 2

    def test_validate_token_success(self):
        manager = SecureTokenManager()
        identifier = "user1"
        token = manager.generate_token(identifier)

        assert manager.validate_token(identifier, token) is True

    def test_validate_token_failure(self):
        manager = SecureTokenManager()
        identifier = "user1"
        token = manager.generate_token(identifier)

        assert manager.validate_token(identifier, "wrong_token") is False

    def test_validate_token_unknown_identifier(self):
        manager = SecureTokenManager()
        assert manager.validate_token("unknown_user", "some_token") is False

    def test_hash_token_is_salted(self):
        manager = SecureTokenManager()
        token = "test_token"

        hash1 = manager.hash_token(token)
        hash2 = manager.hash_token(token)

        assert hash1 != hash2

    def test_verify_token(self):
        manager = SecureTokenManager()
        token = "test_token"

        # Manually hash
        hashed = manager.hash_token(token)

        # Verify correct token matches
        assert manager.verify_token(token, hashed) is True

        # Verify incorrect token fails
        assert manager.verify_token("wrong_token", hashed) is False

    def test_remove_token(self):
        manager = SecureTokenManager()
        identifier = "user1"
        manager.generate_token(identifier)

        assert identifier in manager._tokens
        assert manager.remove_token(identifier) is True
        assert identifier not in manager._tokens
        assert manager.remove_token(identifier) is False
