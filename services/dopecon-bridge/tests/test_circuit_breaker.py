"""
Tests for Circuit Breaker Pattern
Validates state transitions, fallback behavior, and recovery
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock

from circuit_breaker import CircuitBreaker, CircuitBreakerManager, CircuitState


class TestCircuitBreaker:
    """Test suite for CircuitBreaker"""

    @pytest.fixture
    def breaker(self):
        """Create CircuitBreaker with short timeouts for testing"""
        return CircuitBreaker(
            name="test-service",
            failure_threshold=3,
            failure_window=10,
            recovery_timeout=1,  # 1 second for faster testing
            success_threshold=2
        )

    @pytest.mark.asyncio
    async def test_starts_in_closed_state(self, breaker):
        """Test that circuit breaker starts in CLOSED state"""
        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.is_open() is False

    @pytest.mark.asyncio
    async def test_successful_calls_stay_closed(self, breaker):
        """Test that successful operations keep circuit CLOSED"""
        async def successful_operation():
            return "success"

        # Make 10 successful calls
        for _ in range(10):
            result = await breaker.call(successful_operation)
            assert result == "success"

        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.total_successes == 10

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self, breaker):
        """Test that circuit opens after failure threshold exceeded"""
        async def failing_operation():
            raise Exception("Service unavailable")

        # Make failures (threshold is 3)
        for i in range(3):
            try:
                await breaker.call(failing_operation)
            except:
                pass

        # Circuit should now be OPEN
        assert breaker.get_state() == CircuitState.OPEN
        assert breaker.is_open() is True
        assert breaker.total_failures == 3

    @pytest.mark.asyncio
    async def test_uses_fallback_when_open(self, breaker):
        """Test that fallback is called when circuit is OPEN"""
        async def failing_operation():
            raise Exception("Service unavailable")

        async def fallback_operation():
            return "fallback_result"

        # Open the circuit
        for _ in range(3):
            try:
                await breaker.call(failing_operation, fallback=fallback_operation)
            except:
                pass

        assert breaker.get_state() == CircuitState.OPEN

        # Next call should use fallback
        result = await breaker.call(failing_operation, fallback=fallback_operation)

        assert result == "fallback_result"
        assert breaker.fallback_calls >= 1

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self, breaker):
        """Test transition to HALF_OPEN after recovery timeout"""
        async def failing_operation():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(3):
            try:
                await breaker.call(failing_operation)
            except:
                pass

        assert breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout (1 second in test config)
        await asyncio.sleep(1.5)

        # Next call should transition to HALF_OPEN
        try:
            await breaker.call(failing_operation)
        except:
            pass

        # Should have transitioned through HALF_OPEN (then back to OPEN due to failure)
        assert breaker.get_state() == CircuitState.OPEN
        assert breaker.state_transitions >= 2  # CLOSED→OPEN→HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_successful_recovery(self, breaker):
        """Test circuit closes after successful operations in HALF_OPEN"""
        call_count = 0

        async def sometimes_failing_operation():
            nonlocal call_count
            call_count += 1

            if call_count <= 3:
                raise Exception("Service unavailable")

            return "recovered"

        # Open the circuit (3 failures)
        for _ in range(3):
            try:
                await breaker.call(sometimes_failing_operation)
            except:
                pass

        assert breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.5)

        # Make successful calls (threshold is 2)
        result1 = await breaker.call(sometimes_failing_operation)
        result2 = await breaker.call(sometimes_failing_operation)

        assert result1 == "recovered"
        assert result2 == "recovered"

        # Circuit should be CLOSED
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_count_resets_after_window(self, breaker):
        """Test that failure count resets after failure window expires"""
        async def failing_operation():
            raise Exception("Service unavailable")

        # Make 2 failures (below threshold of 3)
        for _ in range(2):
            try:
                await breaker.call(failing_operation)
            except:
                pass

        assert breaker.failure_count == 2
        assert breaker.get_state() == CircuitState.CLOSED

        # Wait for failure window to expire (10 seconds in test, but we can manipulate time)
        breaker.last_failure_time = time.time() - 11  # Simulate 11 seconds ago

        # Next call should reset counter
        try:
            await breaker.call(failing_operation)
        except:
            pass

        # Failure count should be 1 (reset, then this failure)
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, breaker):
        """Test that circuit breaker tracks metrics correctly"""
        # Track successes and failures manually
        successes = 0
        failures = 0

        async def success_operation():
            return "success"

        async def failure_operation():
            raise Exception("Failed")

        # Make 2 successful calls
        for _ in range(2):
            await breaker.call(success_operation)
            successes += 1

        # Make 3 failing calls
        for _ in range(3):
            try:
                await breaker.call(failure_operation)
            except:
                pass
            failures += 1

        metrics = breaker.get_metrics()

        assert metrics["name"] == "test-service"
        assert metrics["total_calls"] == 5
        assert metrics["total_successes"] == 2
        assert metrics["total_failures"] == 3
        assert metrics["state"] in [s.value for s in CircuitState]

    @pytest.mark.asyncio
    async def test_reset_returns_to_closed(self, breaker):
        """Test that reset returns circuit to CLOSED state"""
        async def failing_operation():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(3):
            try:
                await breaker.call(failing_operation)
            except:
                pass

        assert breaker.get_state() == CircuitState.OPEN

        # Reset
        breaker.reset()

        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager"""

    @pytest.fixture
    def manager(self):
        """Create CircuitBreakerManager"""
        return CircuitBreakerManager()

    def test_creates_new_breaker(self, manager):
        """Test creating new circuit breaker"""
        breaker = manager.get_or_create("test-service")

        assert breaker.name == "test-service"
        assert "test-service" in manager.breakers

    def test_returns_existing_breaker(self, manager):
        """Test that get_or_create returns same instance"""
        breaker1 = manager.get_or_create("test-service")
        breaker2 = manager.get_or_create("test-service")

        assert breaker1 is breaker2

    def test_get_all_metrics(self, manager):
        """Test retrieving metrics for all breakers"""
        manager.get_or_create("service-1")
        manager.get_or_create("service-2")

        metrics = manager.get_all_metrics()

        assert len(metrics) == 2
        assert "service-1" in metrics
        assert "service-2" in metrics

    @pytest.mark.asyncio
    async def test_get_open_breakers(self, manager):
        """Test getting list of open circuit breakers"""
        breaker1 = manager.get_or_create("service-1", failure_threshold=1)
        breaker2 = manager.get_or_create("service-2", failure_threshold=1)

        # Open service-1
        try:
            await breaker1.call(lambda: asyncio.ensure_future(self._failing_op()))
        except:
            pass

        open_breakers = manager.get_open_breakers()

        assert "service-1" in open_breakers
        assert "service-2" not in open_breakers

    async def _failing_op(self):
        raise Exception("Fail")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
