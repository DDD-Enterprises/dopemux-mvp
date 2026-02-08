import pytest


def test_password_reset_confirm_validation():
    """PasswordResetConfirm rejects weak passwords and accepts strong ones."""
    from conport_kg.auth.password_utils import PasswordResetConfirm, PasswordValidationError

    valid_request = PasswordResetConfirm(
        token="valid-reset-token-123",
        new_password="NewSecurePass789!",
    )
    assert valid_request.token == "valid-reset-token-123"
    assert valid_request.new_password == "NewSecurePass789!"

    with pytest.raises(PasswordValidationError):
        PasswordResetConfirm(
            token="valid-token",
            new_password="weak",
        )
