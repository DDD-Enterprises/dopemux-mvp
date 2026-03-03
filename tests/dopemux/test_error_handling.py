import pytest
from src.dopemux.error_handling import DopemuxError, ErrorType, ErrorSeverity

class TestDopemuxError:

    @pytest.mark.parametrize("error_type, expected_base", [
        (ErrorType.NETWORK, "Network connection issue - might be temporary"),
        (ErrorType.TIMEOUT, "Service is taking longer than expected"),
        (ErrorType.AUTHENTICATION, "Authentication needs refreshing"),
        (ErrorType.RATE_LIMIT, "Service is busy - taking a short break"),
        (ErrorType.SERVICE_UNAVAILABLE, "Service is temporarily unavailable"),
        (ErrorType.DATA_VALIDATION, "Input needs a small adjustment"),
        (ErrorType.BUSINESS_LOGIC, "Business rule check failed"),
        (ErrorType.RESOURCE_EXHAUSTED, "Service resources are temporarily full"),
        (ErrorType.CONFIGURATION, "Configuration needs attention"),
        (ErrorType.UNKNOWN, "Unexpected situation encountered"),
        # AUTHORIZATION is not in the map, so it should use the default
        (ErrorType.AUTHORIZATION, "An issue occurred"),
    ])
    def test_adhd_message_base_content(self, error_type, expected_base):
        """Test that the base message corresponds to the error type."""
        error = DopemuxError(
            error_type=error_type,
            severity=ErrorSeverity.LOW,
            message="Something went wrong"
        )
        assert expected_base in error.adhd_friendly_message

    @pytest.mark.parametrize("severity, expected_suffix", [
        (ErrorSeverity.CRITICAL, "This needs immediate attention - consider taking a focused break first."),
        (ErrorSeverity.HIGH, "This is important - good time for methodical troubleshooting."),
        (ErrorSeverity.MEDIUM, "Handle when you have mental bandwidth available."),
        (ErrorSeverity.LOW, "No immediate action needed."),
    ])
    def test_adhd_message_severity_suffix(self, severity, expected_suffix):
        """Test that the suffix corresponds to the error severity."""
        error = DopemuxError(
            error_type=ErrorType.UNKNOWN,
            severity=severity,
            message="Something went wrong"
        )
        assert expected_suffix in error.adhd_friendly_message

    def test_adhd_message_preserved_if_provided(self):
        """Test that a manually provided ADHD message is not overwritten."""
        custom_msg = "Take a breath, it's just a glitch."
        error = DopemuxError(
            error_type=ErrorType.NETWORK,
            severity=ErrorSeverity.HIGH,
            message="Connection reset",
            adhd_friendly_message=custom_msg
        )
        assert error.adhd_friendly_message == custom_msg

    def test_full_message_composition(self):
        """Test the full composition of base message and severity suffix."""
        error = DopemuxError(
            error_type=ErrorType.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            message="Request timed out"
        )
        expected = "Service is taking longer than expected. Handle when you have mental bandwidth available."
        assert error.adhd_friendly_message == expected
