import unittest
import asyncio
from dopemux.error_handling import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    DopemuxError,
    ErrorType,
    ErrorSeverity
)

class TestCircuitBreaker(unittest.IsolatedAsyncioTestCase):
    async def test_circuit_breaker_open_raises_error(self):
        # Arrange
        config = CircuitBreakerConfig(name="test_service")
        breaker = CircuitBreaker(config)
        # Manually set state to OPEN
        breaker.state = CircuitBreakerState.OPEN

        async def dummy_func():
            return "success"

        # Act & Assert
        try:
            await breaker.call(dummy_func)
            self.fail("DopemuxError not raised")
        except DopemuxError as error:
            self.assertEqual(error.error_type, ErrorType.SERVICE_UNAVAILABLE)
            self.assertEqual(error.severity, ErrorSeverity.HIGH)
            self.assertIn("is OPEN", error.message)
            self.assertEqual(error.service_name, "test_service")
            self.assertEqual(error.details["circuit_breaker_state"], "open")
