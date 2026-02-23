import pytest
from dopemux.error_handling import RetryPolicy, DopemuxError, ErrorType, ErrorSeverity

def test_retry_policy_get_delay_no_jitter():
    """Test exponential backoff without jitter."""
    policy = RetryPolicy(
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=10.0,
        jitter=False
    )

    # Attempt 0: 1.0 * (2.0 ** 0) = 1.0
    assert policy.get_delay(0) == 1.0

    # Attempt 1: 1.0 * (2.0 ** 1) = 2.0
    assert policy.get_delay(1) == 2.0

    # Attempt 2: 1.0 * (2.0 ** 2) = 4.0
    assert policy.get_delay(2) == 4.0

    # Attempt 3: 1.0 * (2.0 ** 3) = 8.0
    assert policy.get_delay(3) == 8.0

def test_retry_policy_get_delay_max_cap():
    """Test that delay is capped at max_delay."""
    policy = RetryPolicy(
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=10.0,
        jitter=False
    )

    # Attempt 4: 1.0 * (2.0 ** 4) = 16.0 -> capped at 10.0
    assert policy.get_delay(4) == 10.0

    # Attempt 10: Much larger than max_delay -> capped at 10.0
    assert policy.get_delay(10) == 10.0

def test_retry_policy_get_delay_with_jitter():
    """Test that jitter stays within expected range (±25%)."""
    initial_delay = 2.0
    backoff_factor = 2.0
    max_delay = 100.0
    policy = RetryPolicy(
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
        max_delay=max_delay,
        jitter=True
    )

    for attempt in range(5):
        base_delay = initial_delay * (backoff_factor ** attempt)
        base_delay = min(base_delay, max_delay)

        # Run multiple times to increase confidence in jitter range
        for _ in range(100):
            delay = policy.get_delay(attempt)
            # Jitter is ±25%, so 0.75 * base to 1.25 * base
            assert base_delay * 0.75 <= delay <= base_delay * 1.25

def test_retry_policy_get_delay_different_factors():
    """Test with different initial delay and backoff factor."""
    policy = RetryPolicy(
        initial_delay=0.5,
        backoff_factor=3.0,
        max_delay=20.0,
        jitter=False
    )

    # Attempt 0: 0.5 * (3.0 ** 0) = 0.5
    assert policy.get_delay(0) == 0.5

    # Attempt 1: 0.5 * (3.0 ** 1) = 1.5
    assert policy.get_delay(1) == 1.5

    # Attempt 2: 0.5 * (3.0 ** 2) = 4.5
    assert policy.get_delay(2) == 4.5

    # Attempt 3: 0.5 * (3.0 ** 3) = 13.5
    assert policy.get_delay(3) == 13.5

    # Attempt 4: 0.5 * (3.0 ** 4) = 40.5 -> capped at 20.0
    assert policy.get_delay(4) == 20.0

def test_retry_policy_get_delay_edge_cases():
    """Test edge cases for get_delay."""
    # Zero initial delay
    policy = RetryPolicy(initial_delay=0.0, jitter=False)
    assert policy.get_delay(0) == 0.0
    assert policy.get_delay(5) == 0.0

    # Negative attempt (should technically work with the formula but might be unexpected)
    # 1.0 * (2.0 ** -1) = 0.5
    policy = RetryPolicy(initial_delay=1.0, backoff_factor=2.0, jitter=False)
    assert policy.get_delay(-1) == 0.5

def test_retry_policy_should_retry():
    """Improve overall coverage by testing should_retry as well."""
    policy = RetryPolicy(max_attempts=3)

    # Basic success
    assert policy.should_retry(0, Exception("Generic error")) is True
    assert policy.should_retry(1, Exception("Generic error")) is True
    assert policy.should_retry(2, Exception("Generic error")) is True

    # Exhausted attempts
    assert policy.should_retry(3, Exception("Generic error")) is False

    # Don't retry auth errors
    auth_error = DopemuxError(
        error_type=ErrorType.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Auth failed"
    )
    assert policy.should_retry(0, auth_error) is False

    # Don't retry critical errors
    critical_error = DopemuxError(
        error_type=ErrorType.NETWORK,
        severity=ErrorSeverity.CRITICAL,
        message="Critical failure"
    )
    assert policy.should_retry(0, critical_error) is False
