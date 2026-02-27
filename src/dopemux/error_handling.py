#!/usr/bin/env python3
"""
Global Error Handling Framework for Dopemux Services

Provides consistent error handling, retry policies, and circuit breaker patterns
across all 30+ services. Designed for ADHD-friendly operation with gentle degradation.

Features:
- Standardized error classification and handling
- Configurable retry policies with exponential backoff
- Circuit breaker implementation
- ADHD-optimized error messages
- ConPort integration for error tracking
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Standardized error classification for consistent handling."""
    NETWORK = "network"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DATA_VALIDATION = "data_validation"
    BUSINESS_LOGIC = "business_logic"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """Error severity levels for appropriate handling."""
    LOW = "low"          # Log and continue
    MEDIUM = "medium"    # Retry and alert
    HIGH = "high"        # Circuit breaker activation
    CRITICAL = "critical"  # Immediate intervention required

@dataclass
class DopemuxError(Exception):
    """Standardized error representation with ADHD-friendly messaging."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    service_name: Optional[str] = None
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = 0
    adhd_friendly_message: Optional[str] = None

    def __post_init__(self):
        """Generate ADHD-friendly error message if not provided."""
        if not self.adhd_friendly_message:
            self.adhd_friendly_message = self._generate_adhd_message()

    def _generate_adhd_message(self) -> str:
        """Generate gentle, actionable error messages for ADHD users."""
        base_messages = {
            ErrorType.NETWORK: "Network connection issue - might be temporary",
            ErrorType.TIMEOUT: "Service is taking longer than expected",
            ErrorType.AUTHENTICATION: "Authentication needs refreshing",
            ErrorType.RATE_LIMIT: "Service is busy - taking a short break",
            ErrorType.SERVICE_UNAVAILABLE: "Service is temporarily unavailable",
            ErrorType.DATA_VALIDATION: "Input needs a small adjustment",
            ErrorType.BUSINESS_LOGIC: "Business rule check failed",
            ErrorType.RESOURCE_EXHAUSTED: "Service resources are temporarily full",
            ErrorType.CONFIGURATION: "Configuration needs attention",
            ErrorType.UNKNOWN: "Unexpected situation encountered"
        }

        base = base_messages.get(self.error_type, "An issue occurred")

        # Add context-aware suggestions
        if self.severity == ErrorSeverity.CRITICAL:
            return f"{base}. This needs immediate attention - consider taking a focused break first."
        elif self.severity == ErrorSeverity.HIGH:
            return f"{base}. This is important - good time for methodical troubleshooting."
        elif self.severity == ErrorSeverity.MEDIUM:
            return f"{base}. Handle when you have mental bandwidth available."
        else:
            return f"{base}. No immediate action needed."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "adhd_friendly_message": self.adhd_friendly_message,
            "details": self.details,
            "service_name": self.service_name,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count
        }

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    success_threshold: int = 3  # Successes needed to close circuit
    timeout: float = 30.0  # Request timeout
    name: str = "default"

@dataclass
class CircuitBreakerStats:
    """Circuit breaker performance statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    state_changes: List[Dict[str, Any]] = field(default_factory=list)

class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail fast
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_state_change = datetime.now(timezone.utc)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        self.stats.total_requests += 1

        # Check if circuit should allow request
        if not self._should_allow_request():
            raise DopemuxError(
                error_type=ErrorType.SERVICE_UNAVAILABLE,
                severity=ErrorSeverity.HIGH,
                message=f"Circuit breaker {self.config.name} is OPEN",
                service_name=self.config.name,
                details={"circuit_breaker_state": self.state.value}
            )

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )

            # Success - update stats
            self._record_success()
            return result

        except Exception as e:
            # Failure - update stats and potentially open circuit
            self._record_failure(e)
            raise

            logger.error(f"Error: {e}")
    def _should_allow_request(self) -> bool:
        """Determine if request should be allowed based on circuit state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if enough time has passed to try recovery
            if self.stats.last_failure_time:
                time_since_failure = (datetime.now(timezone.utc) - self.stats.last_failure_time).total_seconds()
                if time_since_failure >= self.config.recovery_timeout:
                    self._transition_to(CircuitBreakerState.HALF_OPEN)
                    return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited requests for testing
            return self.stats.consecutive_successes < self.config.success_threshold

        return False

    def _record_success(self):
        """Record successful request."""
        self.stats.successful_requests += 1
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes += 1

        # Check if we should close circuit
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self._transition_to(CircuitBreakerState.CLOSED)

    def _record_failure(self, error: Exception):
        """Record failed request."""
        self.stats.failed_requests += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = datetime.now(timezone.utc)

        # Check if we should open circuit
        if self.state == CircuitBreakerState.CLOSED:
            if self.stats.consecutive_failures >= self.config.failure_threshold:
                self._transition_to(CircuitBreakerState.OPEN)
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state sends us back to open
            self._transition_to(CircuitBreakerState.OPEN)

    def _transition_to(self, new_state: CircuitBreakerState):
        """Transition to new circuit breaker state."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.now(timezone.utc)

        # Log state change
        state_change = {
            "timestamp": self.last_state_change.isoformat(),
            "from_state": old_state.value,
            "to_state": new_state.value,
            "reason": f"Consecutive failures: {self.stats.consecutive_failures}" if new_state == CircuitBreakerState.OPEN else "Recovery test" if new_state == CircuitBreakerState.HALF_OPEN else f"Consecutive successes: {self.stats.consecutive_successes}"
        }
        self.stats.state_changes.append(state_change)

        logger.info(f"Circuit breaker {self.config.name}: {old_state.value} → {new_state.value}")

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        success_rate = (self.stats.successful_requests / max(1, self.stats.total_requests)) * 100

        return {
            "name": self.config.name,
            "state": self.state.value,
            "success_rate": round(success_rate, 1),
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "consecutive_failures": self.stats.consecutive_failures,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "recent_state_changes": self.stats.state_changes[-5:]  # Last 5 changes
        }

class RetryPolicy:
    """
    Configurable retry policy with exponential backoff and jitter.

    ADHD-optimized: Gentle backoff that doesn't create frustration.
    """

    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 30.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if retry should be attempted."""
        if attempt >= self.max_attempts:
            return False

        # Don't retry certain error types
        if isinstance(error, DopemuxError):
            if error.error_type in [ErrorType.AUTHENTICATION, ErrorType.AUTHORIZATION]:
                return False  # Don't retry auth errors
            if error.severity == ErrorSeverity.CRITICAL:
                return False  # Don't retry critical errors

        return True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter (±25%) to prevent thundering herd
            import random
            jitter_factor = random.uniform(0.75, 1.25)
            delay *= jitter_factor

        return delay

class GlobalErrorHandler:
    """
    Global error handling framework for consistent Dopemux error management.

    Provides decorators and utilities for standardized error handling across services.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}

        # Default configurations
        self.default_retry_policy = RetryPolicy()
        self.default_circuit_config = CircuitBreakerConfig(name=f"{service_name}_default")

    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """Register a named circuit breaker."""
        self.circuit_breakers[name] = CircuitBreaker(config)

    def register_retry_policy(self, name: str, policy: RetryPolicy):
        """Register a named retry policy."""
        self.retry_policies[name] = policy

    def with_error_handling(self,
                           operation_name: str,
                           retry_policy: Optional[str] = None,
                           circuit_breaker: Optional[str] = None):
        """
        Decorator for consistent error handling.

        @error_handler.with_error_handling("api_call", retry_policy="api_retry", circuit_breaker="api_circuit")
        async def call_external_api():
            # Your code here
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                policy = self.retry_policies.get(retry_policy or "default", self.default_retry_policy)
                breaker = self.circuit_breakers.get(circuit_breaker) if circuit_breaker else None

                attempt = 0
                last_error = None

                while attempt <= policy.max_attempts:
                    try:
                        if breaker:
                            return await breaker.call(func, *args, **kwargs)
                        else:
                            return await func(*args, **kwargs)

                    except Exception as e:
                        attempt += 1
                        last_error = e

                        # Convert to DopemuxError if not already
                        if not isinstance(e, DopemuxError):
                            dopemux_error = self._classify_error(e, operation_name)
                        else:
                            dopemux_error = e
                            dopemux_error.retry_count = attempt - 1

                        # Log error (ADHD-friendly)
                        logger.warning(f"{self.service_name}.{operation_name}: {dopemux_error.adhd_friendly_message}")

                        # Check if we should retry
                        if not policy.should_retry(attempt, dopemux_error):
                            break

                        # Wait before retry
                        if attempt < policy.max_attempts:
                            delay = policy.get_delay(attempt - 1)
                            logger.info(f"Retrying {operation_name} in {delay:.1f}s (attempt {attempt}/{policy.max_attempts})")
                            await asyncio.sleep(delay)

                # All retries exhausted
                if isinstance(last_error, DopemuxError):
                    raise last_error
                else:
                    raise DopemuxError(
                        error_type=ErrorType.UNKNOWN,
                        severity=ErrorSeverity.HIGH,
                        message=f"Operation failed after {policy.max_attempts} attempts",
                        service_name=self.service_name,
                        operation=operation_name,
                        details={"last_error": str(last_error)}
                    )

            return wrapper
        return decorator

    def _classify_error(self, error: Exception, operation: str) -> DopemuxError:
        """Classify exception into standardized DopemuxError."""
        error_str = str(error).lower()
        error_type = ErrorType.UNKNOWN
        severity = ErrorSeverity.MEDIUM

        # Network and connectivity errors
        if any(keyword in error_str for keyword in ["connection", "network", "socket", "dns"]):
            error_type = ErrorType.NETWORK
            severity = ErrorSeverity.MEDIUM
        elif any(keyword in error_str for keyword in ["timeout", "deadline"]):
            error_type = ErrorType.TIMEOUT
            severity = ErrorSeverity.MEDIUM
        elif any(keyword in error_str for keyword in ["auth", "unauthorized", "forbidden"]):
            error_type = ErrorType.AUTHENTICATION
            severity = ErrorSeverity.HIGH
        elif any(keyword in error_str for keyword in ["rate limit", "429", "too many requests"]):
            error_type = ErrorType.RATE_LIMIT
            severity = ErrorSeverity.MEDIUM
        elif any(keyword in error_str for keyword in ["service unavailable", "502", "503", "504"]):
            error_type = ErrorType.SERVICE_UNAVAILABLE
            severity = ErrorSeverity.HIGH
        elif any(keyword in error_str for keyword in ["validation", "invalid", "malformed"]):
            error_type = ErrorType.DATA_VALIDATION
            severity = ErrorSeverity.MEDIUM

        return DopemuxError(
            error_type=error_type,
            severity=severity,
            message=str(error),
            service_name=self.service_name,
            operation=operation,
            details={"original_exception": type(error).__name__}
        )

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of error handling system."""
        circuit_status = {}
        for name, breaker in self.circuit_breakers.items():
            circuit_status[name] = breaker.get_stats()

        return {
            "service_name": self.service_name,
            "circuit_breakers": circuit_status,
            "total_circuit_breakers": len(self.circuit_breakers),
            "retry_policies": list(self.retry_policies.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global instance for easy access
_default_error_handler = None

def get_global_error_handler(service_name: str) -> GlobalErrorHandler:
    """Get or create global error handler instance."""
    global _default_error_handler
    if _default_error_handler is None or _default_error_handler.service_name != service_name:
        _default_error_handler = GlobalErrorHandler(service_name)
    return _default_error_handler

# Convenience functions
def with_error_handling(operation_name: str, retry_policy: Optional[str] = None, circuit_breaker: Optional[str] = None):
    """Convenience decorator for error handling."""
    def decorator(func):
        handler = get_global_error_handler("dopemux_service")
        return handler.with_error_handling(operation_name, retry_policy, circuit_breaker)(func)
    return decorator

def create_dopemux_error(error_type: ErrorType,
                        severity: ErrorSeverity,
                        message: str,
                        **kwargs) -> DopemuxError:
    """Convenience function to create DopemuxError instances."""
    return DopemuxError(error_type=error_type, severity=severity, message=message, **kwargs)