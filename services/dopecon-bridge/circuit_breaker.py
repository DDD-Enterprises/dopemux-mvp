"""
Circuit Breaker Pattern for DopeconBridge

Protects ConPort and agents from cascading failures by:
- Detecting failure patterns
- Automatically opening circuit to prevent overload
- Providing graceful degradation (local fallback)
- Testing for recovery and closing circuit when service healthy

Based on Michael Nygard's Release It! pattern
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Awaitable

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, using fallback
    HALF_OPEN = "half_open" # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for protecting services from cascading failures.

    State Transitions:
    - CLOSED → OPEN: After failure_threshold failures in failure_window
    - OPEN → HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN → CLOSED: After success_threshold successes
    - HALF_OPEN → OPEN: On any failure

    Example:
        breaker = CircuitBreaker(
            name="conport-mcp",
            failure_threshold=5,
            failure_window=60,
            recovery_timeout=30
        )

        result = await breaker.call(
            operation=lambda: conport_client.log_decision(...),
            fallback=lambda: log_to_local_file(...)
        )
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        failure_window: int = 60,
        recovery_timeout: int = 30,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name (for logging)
            failure_threshold: Failures needed to open circuit (default: 5)
            failure_window: Time window for counting failures in seconds (default: 60)
            recovery_timeout: Seconds to wait before testing recovery (default: 30)
            success_threshold: Successes needed in HALF_OPEN to close (default: 2)
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.failure_window = failure_window
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_transitions = 0
        self.fallback_calls = 0

    def _record_success(self):
        """Record successful operation"""
        self.total_calls += 1
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            # Close circuit after enough successes
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()

    def _record_failure(self):
        """Record failed operation"""
        self.total_calls += 1
        self.total_failures += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1

            # Check if we should open circuit
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()

        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN reopens circuit
            self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state"""
        if self.state != CircuitState.OPEN:
            logger.warning(
                f"⚠️  Circuit breaker [{self.name}] OPENING "
                f"({self.failure_count} failures in {self.failure_window}s)"
            )
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            self.failure_count = 0  # Reset for next cycle
            self.success_count = 0
            self.state_transitions += 1

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        if self.state != CircuitState.HALF_OPEN:
            logger.info(f"🔄 Circuit breaker [{self.name}] HALF_OPEN (testing recovery)")
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
            self.state_transitions += 1

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            logger.info(f"✅ Circuit breaker [{self.name}] CLOSED (service recovered)")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.state_transitions += 1

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to test recovery"""
        if self.state == CircuitState.OPEN and self.opened_at:
            elapsed = time.time() - self.opened_at
            return elapsed >= self.recovery_timeout
        return False

    def _should_reset_failure_count(self) -> bool:
        """Check if failure window has expired (reset counter)"""
        if self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            return elapsed >= self.failure_window
        return False

    async def call(
        self,
        operation: Callable[[], Awaitable[T]],
        fallback: Optional[Callable[[], Awaitable[T]]] = None
    ) -> Optional[T]:
        """
        Call operation through circuit breaker.

        Args:
            operation: Async operation to call
            fallback: Optional fallback operation if circuit is OPEN

        Returns:
            Result from operation or fallback, None if no fallback and circuit OPEN

        Raises:
            Exception from operation if circuit is CLOSED or HALF_OPEN
        """
        # Reset failure count if window expired
        if self._should_reset_failure_count():
            self.failure_count = 0

        # Check if should attempt recovery
        if self._should_attempt_recovery():
            self._transition_to_half_open()

        # Handle based on state
        if self.state == CircuitState.OPEN:
            # Circuit is open - use fallback
            logger.debug(f"⚠️  Circuit breaker [{self.name}] OPEN - using fallback")

            if fallback:
                self.fallback_calls += 1
                try:
                    return await fallback()
                except Exception as e:
                    logger.error(f"Fallback also failed for [{self.name}]: {e}")
                    return None

            return None

        # Try the operation (CLOSED or HALF_OPEN)
        try:
            result = await operation()
            self._record_success()
            return result

        except Exception as e:
            self._record_failure()
            logger.error(f"Operation failed for [{self.name}]: {e}")

            # Use fallback if available
            if fallback and self.state == CircuitState.OPEN:
                self.fallback_calls += 1
                try:
                    return await fallback()
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for [{self.name}]: {fallback_error}")

            raise

    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state

    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == CircuitState.OPEN

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with state, counts, failure rate, etc.
        """
        failure_rate = (
            (self.total_failures / self.total_calls * 100)
            if self.total_calls > 0
            else 0.0
        )

        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "failure_rate_percent": round(failure_rate, 2),
            "state_transitions": self.state_transitions,
            "fallback_calls": self.fallback_calls,
            "current_failure_count": self.failure_count,
            "opened_at": (
                datetime.fromtimestamp(self.opened_at).isoformat()
                if self.opened_at
                else None
            )
        }

    def reset(self):
        """Reset circuit breaker to initial state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None
        logger.info(f"🔄 Circuit breaker [{self.name}] reset to CLOSED")


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services.

    Provides centralized circuit breaker creation and monitoring.
    """

    def __init__(self):
        """Initialize circuit breaker manager"""
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        failure_window: int = 60,
        recovery_timeout: int = 30,
        success_threshold: int = 2,
    ) -> CircuitBreaker:
        """
        Get existing circuit breaker or create new one.

        Args:
            name: Circuit breaker name
            failure_threshold: Failures to open circuit
            failure_window: Window for counting failures (seconds)
            recovery_timeout: Wait time before testing recovery (seconds)
            success_threshold: Successes needed to close circuit

        Returns:
            CircuitBreaker instance
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                failure_window=failure_window,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
            )
            logger.info(f"✅ Created circuit breaker: {name}")

        return self.breakers[name]

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all circuit breakers.

        Returns:
            Dictionary mapping breaker names to their metrics
        """
        return {
            name: breaker.get_metrics()
            for name, breaker in self.breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()

    def get_open_breakers(self) -> List[str]:
        """
        Get list of circuit breakers in OPEN state.

        Returns:
            List of breaker names that are currently OPEN
        """
        return [
            name
            for name, breaker in self.breakers.items()
            if breaker.is_open()
        ]
