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

        # Invalid new password - validator raises PasswordValidationError directly
        with pytest.raises(PasswordValidationError):
            PasswordResetConfirm(
                token="valid-token",
                new_password="weak"
            )