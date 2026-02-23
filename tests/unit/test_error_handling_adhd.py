import pytest
from datetime import datetime, timezone
from dopemux.error_handling import (
    DopemuxError,
    ErrorType,
    ErrorSeverity,
    create_dopemux_error
)

def test_adhd_message_generation_all_types():
    """Test that each ErrorType maps to the correct ADHD-friendly base message."""
    test_cases = [
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
    ]

    for error_type, expected_base in test_cases:
        error = DopemuxError(
            error_type=error_type,
            severity=ErrorSeverity.LOW,
            message="Technical error message"
        )
        assert expected_base in error.adhd_friendly_message
        assert error.adhd_friendly_message.endswith("No immediate action needed.")

def test_adhd_message_generation_all_severities():
    """Test that each ErrorSeverity appends the correct actionable suggestion."""
    base_type = ErrorType.NETWORK
    base_msg = "Network connection issue - might be temporary"

    test_cases = [
        (ErrorSeverity.CRITICAL, "This needs immediate attention - consider taking a focused break first."),
        (ErrorSeverity.HIGH, "This is important - good time for methodical troubleshooting."),
        (ErrorSeverity.MEDIUM, "Handle when you have mental bandwidth available."),
        (ErrorSeverity.LOW, "No immediate action needed."),
    ]

    for severity, expected_suffix in test_cases:
        error = DopemuxError(
            error_type=base_type,
            severity=severity,
            message="Technical error message"
        )
        expected_full = f"{base_msg}. {expected_suffix}"
        assert error.adhd_friendly_message == expected_full

def test_adhd_message_automatic_generation():
    """Verify that adhd_friendly_message is generated during __post_init__."""
    error = DopemuxError(
        error_type=ErrorType.TIMEOUT,
        severity=ErrorSeverity.MEDIUM,
        message="Request timed out"
    )
    assert error.adhd_friendly_message is not None
    assert "Service is taking longer than expected" in error.adhd_friendly_message

def test_manual_adhd_message_preservation():
    """Verify that a manually provided ADHD message is not overwritten."""
    custom_msg = "Chill out, it's just a test."
    error = DopemuxError(
        error_type=ErrorType.NETWORK,
        severity=ErrorSeverity.CRITICAL,
        message="Connection failed",
        adhd_friendly_message=custom_msg
    )
    assert error.adhd_friendly_message == custom_msg

def test_create_dopemux_error_convenience():
    """Test the create_dopemux_error convenience function."""
    error = create_dopemux_error(
        error_type=ErrorType.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Invalid token",
        service_name="auth-service",
        operation="login"
    )
    assert isinstance(error, DopemuxError)
    assert error.error_type == ErrorType.AUTHENTICATION
    assert error.severity == ErrorSeverity.HIGH
    assert error.message == "Invalid token"
    assert error.service_name == "auth-service"
    assert error.operation == "login"
    assert "Authentication needs refreshing" in error.adhd_friendly_message

def test_dopemux_error_to_dict():
    """Verify that to_dict correctly serializes the error including ADHD message."""
    timestamp = datetime.now(timezone.utc)
    error = DopemuxError(
        error_type=ErrorType.RATE_LIMIT,
        severity=ErrorSeverity.MEDIUM,
        message="Too many requests",
        details={"limit": 100},
        service_name="api-gateway",
        operation="get_data",
        timestamp=timestamp
    )

    error_dict = error.to_dict()

    assert error_dict["error_type"] == "rate_limit"
    assert error_dict["severity"] == "medium"
    assert error_dict["message"] == "Too many requests"
    assert "Service is busy - taking a short break" in error_dict["adhd_friendly_message"]
    assert error_dict["details"] == {"limit": 100}
    assert error_dict["service_name"] == "api-gateway"
    assert error_dict["operation"] == "get_data"
    assert error_dict["timestamp"] == timestamp.isoformat()
    assert error_dict["retry_count"] == 0

def test_unknown_error_type_fallback():
    """Test fallback when an unknown error type is encountered."""
    # Using a string or different object that might be passed in less strict environments
    # or if the Enum is extended without updating the message map.
    class FakeErrorType:
        value = "something_exotic"

    error = DopemuxError(
        error_type=FakeErrorType, # type: ignore
        severity=ErrorSeverity.LOW,
        message="Unexpected error"
    )

    assert "An issue occurred. No immediate action needed." == error.adhd_friendly_message
