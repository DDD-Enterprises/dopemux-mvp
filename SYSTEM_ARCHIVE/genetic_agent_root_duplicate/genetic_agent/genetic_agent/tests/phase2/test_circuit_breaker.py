"""Unit tests for the Adaptive Circuit Breaker."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from genetic_agent.reliability.adaptive_circuit_breaker import (
    AdaptiveCircuitBreaker,
    CircuitBreakerState,
    ServiceStats,
    CircuitBreakerOpenException
)


@pytest.fixture
def circuit_breaker():
    """Fixture for adaptive circuit breaker."""
    return AdaptiveCircuitBreaker(
        failure_threshold=0.5,
        recovery_timeout=1.0,  # Short for testing
        success_threshold=2,
        health_check_interval=10.0
    )


class TestAdaptiveCircuitBreaker:
    """Test suite for AdaptiveCircuitBreaker."""

    def test_initialization(self, circuit_breaker):
        """Test circuit breaker initialization."""
        assert len(circuit_breaker.service_stats) == 0
        assert len(circuit_breaker.service_states) == 0
        assert circuit_breaker.failure_threshold == 0.5
        assert circuit_breaker.recovery_timeout == 1.0

    def test_register_service(self, circuit_breaker):
        """Test service registration."""
        circuit_breaker.register_service("test_service")

        assert "test_service" in circuit_breaker.service_stats
        assert "test_service" in circuit_breaker.service_states
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.CLOSED

    def test_register_service_with_custom_policy(self, circuit_breaker):
        """Test service registration with custom policy."""
        custom_policy = {"failure_threshold": 0.3, "recovery_timeout": 30.0}
        circuit_breaker.register_service("custom_service", custom_policy)

        policy = circuit_breaker.get_service_policy("custom_service")
        assert policy["failure_threshold"] == 0.3
        assert policy["recovery_timeout"] == 30.0
        assert policy["success_threshold"] == 3  # Default value

    def test_get_service_policy_defaults(self, circuit_breaker):
        """Test getting default service policy."""
        policy = circuit_breaker.get_service_policy("nonexistent")

        assert policy["failure_threshold"] == 0.5
        assert policy["recovery_timeout"] == 1.0
        assert policy["success_threshold"] == 2

    def test_can_attempt_request_closed_state(self, circuit_breaker):
        """Test request attempts in closed state."""
        circuit_breaker.register_service("test_service")

        # Should allow requests initially
        assert circuit_breaker.can_attempt_request("test_service") is True

        # Record failures to trigger open state
        for _ in range(5):
            circuit_breaker.record_failure("test_service", 1.0)

        # Should now be open and reject requests
        assert circuit_breaker.can_attempt_request("test_service") is False
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_success(self, circuit_breaker):
        """Test successful execution with circuit breaker."""
        circuit_breaker.register_service("test_service")

        async def successful_operation():
            return "success"

        result = await circuit_breaker.execute_with_circuit_breaker(
            "test_service", successful_operation
        )

        assert result == "success"
        stats = circuit_breaker.service_stats["test_service"]
        assert stats.successful_requests == 1
        assert stats.total_requests == 1
        assert stats.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_failure(self, circuit_breaker):
        """Test failed execution with circuit breaker."""
        circuit_breaker.register_service("test_service")

        async def failing_operation():
            raise ValueError("Test failure")

        with pytest.raises(ValueError):
            await circuit_breaker.execute_with_circuit_breaker(
                "test_service", failing_operation
            )

        stats = circuit_breaker.service_stats["test_service"]
        assert stats.failed_requests == 1
        assert stats.consecutive_failures == 1
        assert stats.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_execute_with_fallback(self, circuit_breaker):
        """Test execution with fallback when circuit is open."""
        circuit_breaker.register_service("test_service")

        # Force open state
        for _ in range(5):
            circuit_breaker.record_failure("test_service", 1.0)
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.OPEN

        async def failing_operation():
            raise ValueError("Primary failure")

        async def fallback_operation():
            return "fallback_success"

        result = await circuit_breaker.execute_with_circuit_breaker(
            "test_service", failing_operation, fallback_operation
        )

        assert result == "fallback_success"

    @pytest.mark.asyncio
    async def test_execute_circuit_breaker_open_exception(self, circuit_breaker):
        """Test CircuitBreakerOpenException when circuit is open."""
        circuit_breaker.register_service("test_service")

        # Force open state
        for _ in range(5):
            circuit_breaker.record_failure("test_service", 1.0)

        async def operation():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenException) as exc_info:
            await circuit_breaker.execute_with_circuit_breaker("test_service", operation)

        assert exc_info.value.service_name == "test_service"

    def test_record_success(self, circuit_breaker):
        """Test recording successful requests."""
        circuit_breaker.register_service("test_service")

        circuit_breaker.record_success("test_service", 0.5)

        stats = circuit_breaker.service_stats["test_service"]
        assert stats.successful_requests == 1
        assert stats.total_requests == 1
        assert stats.consecutive_successes == 1
        assert stats.average_response_time == 0.5

    def test_record_failure(self, circuit_breaker):
        """Test recording failed requests."""
        circuit_breaker.register_service("test_service")

        circuit_breaker.record_failure("test_service", 1.0)

        stats = circuit_breaker.service_stats["test_service"]
        assert stats.failed_requests == 1
        assert stats.total_requests == 1
        assert stats.consecutive_failures == 1
        assert stats.success_rate == 0.0

    def test_half_open_recovery(self, circuit_breaker):
        """Test recovery from open to half-open state."""
        circuit_breaker.register_service("test_service")

        # Force open state
        for _ in range(5):
            circuit_breaker.record_failure("test_service", 1.0)
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.OPEN

        # Simulate time passing (recovery timeout)
        import time
        original_time = time.time
        time.time = lambda: original_time() + 2.0  # 2 seconds later

        try:
            # Should now allow recovery attempt
            assert circuit_breaker.can_attempt_request("test_service") is True
            assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.HALF_OPEN
        finally:
            time.time = original_time

    def test_half_open_to_closed(self, circuit_breaker):
        """Test transition from half-open to closed on consecutive successes."""
        circuit_breaker.register_service("test_service")

        # Force half-open state
        circuit_breaker.service_states["test_service"] = CircuitBreakerState.HALF_OPEN

        # Record consecutive successes
        circuit_breaker.record_success("test_service", 0.5)
        circuit_breaker.record_success("test_service", 0.5)

        # Should now be closed
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.CLOSED

    def test_half_open_to_open_on_failure(self, circuit_breaker):
        """Test transition from half-open back to open on failure."""
        circuit_breaker.register_service("test_service")

        # Force half-open state
        circuit_breaker.service_states["test_service"] = CircuitBreakerState.HALF_OPEN

        # Record failure
        circuit_breaker.record_failure("test_service", 1.0)

        # Should be back to open
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.OPEN

    def test_get_service_status(self, circuit_breaker):
        """Test getting service status."""
        circuit_breaker.register_service("test_service")

        # Record some activity
        circuit_breaker.record_success("test_service", 0.5)
        circuit_breaker.record_failure("test_service", 1.0)

        status = circuit_breaker.get_service_status("test_service")

        assert status["service_name"] == "test_service"
        assert status["state"] == "closed"
        assert status["stats"]["total_requests"] == 2
        assert status["stats"]["success_rate"] == 0.5
        assert status["policy"]["failure_threshold"] == 0.5

    def test_get_system_status(self, circuit_breaker):
        """Test getting overall system status."""
        circuit_breaker.register_service("service1")
        circuit_breaker.register_service("service2")

        # Record activity
        circuit_breaker.record_success("service1", 0.5)
        circuit_breaker.record_failure("service2", 1.0)

        status = circuit_breaker.get_system_status()

        assert status["total_services"] == 2
        assert status["total_requests"] == 2
        assert "service_details" in status
        assert len(status["service_details"]) == 2

    def test_reset_service(self, circuit_breaker):
        """Test resetting a service to closed state."""
        circuit_breaker.register_service("test_service")

        # Force open state
        for _ in range(5):
            circuit_breaker.record_failure("test_service", 1.0)
        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.OPEN

        # Reset
        circuit_breaker.reset_service("test_service")

        assert circuit_breaker.service_states["test_service"] == CircuitBreakerState.CLOSED

    def test_response_time_tracking(self, circuit_breaker):
        """Test response time tracking and statistics."""
        circuit_breaker.register_service("test_service")

        # Record multiple response times
        times = [0.1, 0.2, 0.3, 0.1, 0.2]
        for response_time in times:
            circuit_breaker.record_success("test_service", response_time)

        stats = circuit_breaker.service_stats["test_service"]
        avg_time = stats.average_response_time

        # Should be close to the average of recorded times
        expected_avg = sum(times) / len(times)
        assert abs(avg_time - expected_avg) < 0.01

    def test_health_check_integration(self, circuit_breaker):
        """Test health check integration."""
        circuit_breaker.register_service("test_service")

        # Initially healthy
        assert circuit_breaker.service_stats["test_service"].health_status is True

        # Simulate health check
        import asyncio
        asyncio.run(circuit_breaker.perform_health_checks())

        # Should still be healthy (mock health check returns True)
        assert circuit_breaker.service_stats["test_service"].health_status is True
        assert circuit_breaker.service_stats["test_service"].last_health_check is not None

    def test_service_stats_properties(self):
        """Test ServiceStats computed properties."""
        stats = ServiceStats("test_service")

        # Initially perfect success rate
        assert stats.success_rate == 1.0
        assert stats.failure_rate == 0.0

        # Record successes and failures
        stats.record_request(True, 0.5)   # Success
        stats.record_request(False, 1.0)  # Failure
        stats.record_request(True, 0.3)   # Success

        assert stats.total_requests == 3
        assert stats.successful_requests == 2
        assert stats.failed_requests == 1
        assert stats.success_rate == 2/3
        assert stats.failure_rate == 1/3
        assert stats.average_response_time > 0

    def test_adaptive_policies(self, circuit_breaker):
        """Test adaptive policy application."""
        # Register services with different policies
        circuit_breaker.register_service("strict_service",
                                       {"failure_threshold": 0.2, "recovery_timeout": 30.0})
        circuit_breaker.register_service("lenient_service",
                                       {"failure_threshold": 0.8, "recovery_timeout": 5.0})

        strict_policy = circuit_breaker.get_service_policy("strict_service")
        lenient_policy = circuit_breaker.get_service_policy("lenient_service")

        assert strict_policy["failure_threshold"] == 0.2
        assert lenient_policy["failure_threshold"] == 0.8
        assert strict_policy["recovery_timeout"] == 30.0
        assert lenient_policy["recovery_timeout"] == 5.0