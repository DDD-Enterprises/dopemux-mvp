import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from dopemux.error_handling import (
    DopemuxError,
    ErrorType,
    ErrorSeverity,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    RetryPolicy,
    GlobalErrorHandler,
    get_global_error_handler
)

# --- DopemuxError Tests ---

def test_dopemux_error_initialization():
    error = DopemuxError(
        error_type=ErrorType.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        message="Connection failed"
    )
    assert error.error_type == ErrorType.NETWORK
    assert error.severity == ErrorSeverity.MEDIUM
    assert error.message == "Connection failed"
    assert error.adhd_friendly_message is not None
    assert "Network connection issue" in error.adhd_friendly_message

def test_dopemux_error_adhd_message_generation():
    # Test critical severity
    error = DopemuxError(
        error_type=ErrorType.SERVICE_UNAVAILABLE,
        severity=ErrorSeverity.CRITICAL,
        message="Service down"
    )
    assert "immediate attention" in error.adhd_friendly_message

    # Test low severity
    error = DopemuxError(
        error_type=ErrorType.UNKNOWN,
        severity=ErrorSeverity.LOW,
        message="Whoops"
    )
    assert "No immediate action needed" in error.adhd_friendly_message

def test_dopemux_error_to_dict():
    timestamp = datetime.now(timezone.utc)
    error = DopemuxError(
        error_type=ErrorType.TIMEOUT,
        severity=ErrorSeverity.HIGH,
        message="Timed out",
        timestamp=timestamp,
        retry_count=2
    )
    data = error.to_dict()
    assert data["error_type"] == "timeout"
    assert data["severity"] == "high"
    assert data["message"] == "Timed out"
    assert data["retry_count"] == 2
    assert data["timestamp"] == timestamp.isoformat()

# --- RetryPolicy Tests ---

def test_retry_policy_should_retry():
    policy = RetryPolicy(max_attempts=3)

    # Should retry on normal error
    error = ValueError("Something wrong")
    assert policy.should_retry(1, error) is True

    # Should not retry if max attempts reached
    assert policy.should_retry(3, error) is False

    # Should not retry Auth errors
    auth_error = DopemuxError(
        error_type=ErrorType.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Auth failed"
    )
    assert policy.should_retry(1, auth_error) is False

    # Should not retry Critical errors
    critical_error = DopemuxError(
        error_type=ErrorType.NETWORK,
        severity=ErrorSeverity.CRITICAL,
        message="Critical failure"
    )
    assert policy.should_retry(1, critical_error) is False

def test_retry_policy_delay_calculation():
    policy = RetryPolicy(
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=10.0,
        jitter=False
    )

    assert policy.get_delay(0) == 1.0
    assert policy.get_delay(1) == 2.0
    assert policy.get_delay(2) == 4.0
    assert policy.get_delay(3) == 8.0
    assert policy.get_delay(4) == 10.0  # Capped at max_delay

@patch('random.uniform')
def test_retry_policy_jitter(mock_random):
    mock_random.return_value = 1.1  # 10% jitter
    policy = RetryPolicy(initial_delay=1.0, jitter=True)

    delay = policy.get_delay(0)
    assert delay == 1.1

# --- CircuitBreaker Tests ---

@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    config = CircuitBreakerConfig(failure_threshold=2)
    breaker = CircuitBreaker(config)

    mock_func = AsyncMock(return_value="success")

    result = await breaker.call(mock_func)
    assert result == "success"
    assert breaker.state == CircuitBreakerState.CLOSED
    assert breaker.stats.successful_requests == 1
    assert breaker.stats.failed_requests == 0

@pytest.mark.asyncio
async def test_circuit_breaker_open_state():
    config = CircuitBreakerConfig(failure_threshold=2)
    breaker = CircuitBreaker(config)

    mock_func = AsyncMock(side_effect=ValueError("fail"))

    # First failure
    with pytest.raises(ValueError):
        await breaker.call(mock_func)
    assert breaker.state == CircuitBreakerState.CLOSED

    # Second failure - should open circuit
    with pytest.raises(ValueError):
        await breaker.call(mock_func)
    assert breaker.state == CircuitBreakerState.OPEN

    # Subsequent calls should fail fast with DopemuxError
    with pytest.raises(DopemuxError) as excinfo:
        await breaker.call(mock_func)

    assert excinfo.value.error_type == ErrorType.SERVICE_UNAVAILABLE
    assert "is OPEN" in excinfo.value.message

@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    config = CircuitBreakerConfig(
        failure_threshold=1,
        recovery_timeout=0.1,  # Short timeout for testing
        success_threshold=2
    )
    breaker = CircuitBreaker(config)

    # Force open state
    breaker._transition_to(CircuitBreakerState.OPEN)
    breaker.stats.last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=1)

    mock_func = AsyncMock(return_value="success")

    # First success - should transition to HALF_OPEN
    await breaker.call(mock_func)
    assert breaker.state == CircuitBreakerState.HALF_OPEN
    assert breaker.stats.consecutive_successes == 1

    # Second success - should transition to CLOSED
    await breaker.call(mock_func)
    assert breaker.state == CircuitBreakerState.CLOSED
    assert breaker.stats.consecutive_successes == 2

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    config = CircuitBreakerConfig(recovery_timeout=0, success_threshold=2)
    breaker = CircuitBreaker(config)

    # Set to HALF_OPEN
    breaker.state = CircuitBreakerState.HALF_OPEN

    mock_func = AsyncMock(side_effect=ValueError("fail"))

    with pytest.raises(ValueError):
        await breaker.call(mock_func)

    assert breaker.state == CircuitBreakerState.OPEN

# --- GlobalErrorHandler Tests ---

@pytest.mark.asyncio
async def test_global_error_handler_decorator_success():
    handler = GlobalErrorHandler("test_service")

    @handler.with_error_handling("test_op")
    async def success_func():
        return "ok"

    result = await success_func()
    assert result == "ok"

@pytest.mark.asyncio
async def test_global_error_handler_retry_logic():
    handler = GlobalErrorHandler("test_service")
    policy = RetryPolicy(max_attempts=2, initial_delay=0.01, jitter=False)
    handler.register_retry_policy("fast_retry", policy)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), "success"])

    @handler.with_error_handling("test_op", retry_policy="fast_retry")
    async def retrying_func():
        return await mock_func()

    result = await retrying_func()
    assert result == "success"
    assert mock_func.call_count == 2

@pytest.mark.asyncio
async def test_global_error_handler_exhausted_retries():
    handler = GlobalErrorHandler("test_service")
    policy = RetryPolicy(max_attempts=2, initial_delay=0.01, jitter=False)
    handler.register_retry_policy("fast_retry", policy)

    @handler.with_error_handling("test_op", retry_policy="fast_retry")
    async def failing_func():
        raise ValueError("persistent failure")

    with pytest.raises(DopemuxError) as excinfo:
        await failing_func()

    assert excinfo.value.error_type == ErrorType.UNKNOWN
    assert "Operation failed after 2 attempts" in excinfo.value.message

@pytest.mark.asyncio
async def test_global_error_handler_circuit_breaker_integration():
    handler = GlobalErrorHandler("test_service")
    config = CircuitBreakerConfig(failure_threshold=1, name="cb_test")
    handler.register_circuit_breaker("cb_test", config)

    @handler.with_error_handling("test_op", circuit_breaker="cb_test")
    async def failing_func():
        raise ValueError("fail")

    # Trigger open circuit
    with pytest.raises(ValueError):
        await failing_func()

    # Next call should be blocked by circuit breaker
    with pytest.raises(DopemuxError) as excinfo:
        await failing_func()

    assert excinfo.value.error_type == ErrorType.SERVICE_UNAVAILABLE
    assert "is OPEN" in excinfo.value.message

def test_error_classification():
    handler = GlobalErrorHandler("test_service")

    # Network error
    err = handler._classify_error(ConnectionError("Connection refused"), "op")
    assert err.error_type == ErrorType.NETWORK

    # Timeout error
    err = handler._classify_error(TimeoutError("Request timeout"), "op")
    assert err.error_type == ErrorType.TIMEOUT

    # Auth error
    err = handler._classify_error(Exception("401 Unauthorized"), "op")
    assert err.error_type == ErrorType.AUTHENTICATION
