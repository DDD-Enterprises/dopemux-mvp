"""
Failure Handler - Circuit breaker pattern and graceful degradation

This module implements circuit breaker patterns, failure analysis, and graceful
degradation strategies for the Claude Brain service.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing recovery


class FailureType(Enum):
    """Types of failures."""
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    success_threshold: int = 3  # Successes needed to close circuit
    monitoring_window: int = 300  # Seconds to track failures


@dataclass
class FailureRecord:
    """Record of a failure event."""
    timestamp: datetime
    failure_type: FailureType
    service: str
    error_message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation."""
    service_name: str
    config: CircuitBreakerConfig
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_count: int = 0
    failure_records: List[FailureRecord] = field(default_factory=list)

    def can_proceed(self) -> bool:
        """Check if requests can proceed."""
        now = datetime.now()

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.last_failure_time and
                (now - self.last_failure_time).total_seconds() >= self.config.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker for {self.service_name} entering HALF_OPEN state")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self, failure_type: FailureType, error_message: str, context: Dict[str, Any] = None) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        # Record the failure
        failure_record = FailureRecord(
            timestamp=self.last_failure_time,
            failure_type=failure_type,
            service=self.service_name,
            error_message=error_message,
            context=context or {}
        )
        self.failure_records.append(failure_record)

        # Keep only recent records
        cutoff_time = datetime.now() - timedelta(seconds=self.config.monitoring_window)
        self.failure_records = [r for r in self.failure_records if r.timestamp > cutoff_time]

        # Check if circuit should open
        if (self.state == CircuitState.CLOSED and
            self.failure_count >= self.config.failure_threshold):
            self._open_circuit()

        logger.warning(f"Failure recorded for {self.service_name}: {failure_type.value} - {error_message}")

    def _open_circuit(self) -> None:
        """Open the circuit breaker."""
        self.state = CircuitState.OPEN
        logger.error(f"Circuit breaker for {self.service_name} OPENED after {self.failure_count} failures")

    def _close_circuit(self) -> None:
        """Close the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker for {self.service_name} CLOSED - service recovered")

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "service": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recent_failures": len(self.failure_records)
        }


class FailureHandler:
    """
    Comprehensive failure handling and circuit breaker management.

    Implements graceful degradation, failure analysis, and recovery strategies.
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.failure_patterns: Dict[str, List[FailureRecord]] = {}
        self.recovery_strategies: Dict[str, List[str]] = {}

        # Default circuit breaker config
        self.default_config = CircuitBreakerConfig()

        # Initialize common service circuit breakers
        self._initialize_circuit_breakers()

    def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for common services."""
        services = {
            "openrouter": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30),
            "anthropic": CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60),
            "openai": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=45),
            "groq": CircuitBreakerConfig(failure_threshold=2, recovery_timeout=15),
            "adhd_engine": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30),
            "conport": CircuitBreakerConfig(failure_threshold=2, recovery_timeout=20),
            "serena": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=25)
        }

        for service_name, config in services.items():
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)

    def can_proceed(self, service_name: str) -> bool:
        """Check if operations can proceed for a service."""
        if service_name not in self.circuit_breakers:
            # Create circuit breaker on demand
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, self.default_config)

        return self.circuit_breakers[service_name].can_proceed()

    def record_result(self, service_name: str, success: bool, error_details: Dict[str, Any] = None) -> None:
        """Record the result of an operation."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, self.default_config)

        circuit_breaker = self.circuit_breakers[service_name]

        if success:
            circuit_breaker.record_success()
        else:
            # Classify the failure
            failure_type = self._classify_failure(error_details or {})
            error_message = error_details.get('error_message', 'Unknown error') if error_details else 'Unknown error'

            circuit_breaker.record_failure(failure_type, error_message, error_details)

            # Record in failure patterns for analysis
            self._record_failure_pattern(service_name, circuit_breaker.failure_records[-1])

    def _classify_failure(self, error_details: Dict[str, Any]) -> FailureType:
        """Classify the type of failure."""
        error_message = error_details.get('error_message', '').lower()

        if 'rate limit' in error_message or 'quota' in error_message:
            return FailureType.RATE_LIMIT
        elif 'timeout' in error_message or 'timed out' in error_message:
            return FailureType.TIMEOUT
        elif 'network' in error_message or 'connection' in error_message:
            return FailureType.NETWORK
        elif 'auth' in error_message or 'unauthorized' in error_message:
            return FailureType.AUTHENTICATION
        elif 'api' in error_message and 'error' in error_message:
            return FailureType.API_ERROR
        else:
            return FailureType.UNKNOWN

    def _record_failure_pattern(self, service_name: str, failure: FailureRecord) -> None:
        """Record failure patterns for analysis."""
        if service_name not in self.failure_patterns:
            self.failure_patterns[service_name] = []

        self.failure_patterns[service_name].append(failure)

        # Keep only recent failures (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.failure_patterns[service_name] = [
            f for f in self.failure_patterns[service_name]
            if f.timestamp > cutoff_time
        ]

    def get_fallback_service(self, primary_service: str) -> Optional[str]:
        """Get a fallback service when primary is failing."""
        fallbacks = {
            "anthropic": "openrouter",
            "openrouter": "groq",
            "openai": "groq",
            "groq": "openrouter"
        }

        fallback = fallbacks.get(primary_service)
        if fallback and self.can_proceed(fallback):
            return fallback

        return None

    def analyze_failure_patterns(self, service_name: str) -> Dict[str, Any]:
        """Analyze failure patterns for a service."""
        if service_name not in self.failure_patterns:
            return {"analysis": "No failure data available"}

        failures = self.failure_patterns[service_name]
        if not failures:
            return {"analysis": "No recent failures"}

        # Analyze failure types
        failure_types = {}
        for failure in failures:
            failure_type = failure.failure_type.value
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1

        # Find most common failure type
        most_common = max(failure_types.items(), key=lambda x: x[1]) if failure_types else ("none", 0)

        # Analyze timing patterns
        timestamps = [f.timestamp for f in failures]
        if len(timestamps) > 1:
            intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = 0

        analysis = {
            "total_failures": len(failures),
            "most_common_failure_type": most_common[0],
            "failure_type_distribution": failure_types,
            "average_interval_seconds": avg_interval,
            "time_range": {
                "oldest": min(timestamps).isoformat(),
                "newest": max(timestamps).isoformat()
            }
        }

        # Generate recommendations
        recommendations = []
        if most_common[0] == "rate_limit":
            recommendations.append("Implement exponential backoff for rate limits")
        elif most_common[0] == "timeout":
            recommendations.append("Increase timeout values or implement retry logic")
        elif most_common[0] == "api_error":
            recommendations.append("Check API compatibility and update client libraries")
        elif most_common[0] == "network":
            recommendations.append("Implement connection pooling and retry mechanisms")

        if avg_interval < 60:  # Frequent failures
            recommendations.append("Circuit breaker may be too sensitive - consider increasing thresholds")

        analysis["recommendations"] = recommendations
        return analysis

    def get_recovery_strategy(self, service_name: str) -> List[str]:
        """Get recovery strategy for a failing service."""
        if service_name not in self.recovery_strategies:
            # Generate default strategy
            self.recovery_strategies[service_name] = self._generate_recovery_strategy(service_name)

        return self.recovery_strategies[service_name]

    def _generate_recovery_strategy(self, service_name: str) -> List[str]:
        """Generate a recovery strategy for a service."""
        strategy = []

        # Check circuit breaker status
        if service_name in self.circuit_breakers:
            cb = self.circuit_breakers[service_name]
            if cb.state == CircuitState.OPEN:
                strategy.append("Circuit breaker is OPEN - wait for recovery timeout")
                strategy.append(f"Recovery timeout: {cb.config.recovery_timeout} seconds")
            elif cb.state == CircuitState.HALF_OPEN:
                strategy.append("Circuit breaker is HALF_OPEN - testing recovery")

        # Service-specific strategies
        if "api" in service_name:
            strategy.extend([
                "Check API key validity and permissions",
                "Verify rate limits and quotas",
                "Test with minimal request payload",
                "Check service status page for outages"
            ])
        elif "engine" in service_name:
            strategy.extend([
                "Check service health endpoint",
                "Verify database connectivity",
                "Check memory and CPU usage",
                "Review recent error logs"
            ])
        elif "brain" in service_name:
            strategy.extend([
                "Verify model availability",
                "Check token limits and costs",
                "Test with simpler prompts",
                "Validate provider credentials"
            ])

        # General strategies
        strategy.extend([
            "Implement exponential backoff retry",
            "Add request timeouts",
            "Enable detailed error logging",
            "Consider fallback services"
        ])

        return strategy

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive failure handler status."""
        circuit_status = {}
        for name, cb in self.circuit_breakers.items():
            circuit_status[name] = cb.get_status()

        return {
            "circuit_breakers": circuit_status,
            "services_with_failures": list(self.failure_patterns.keys()),
            "total_failure_records": sum(len(records) for records in self.failure_patterns.values()),
            "recovery_strategies_available": len(self.recovery_strategies)
        }

    async def graceful_shutdown(self) -> None:
        """Perform graceful shutdown of failure handling."""
        logger.info("Failure handler shutting down gracefully")

        # Log final status
        status = self.get_status()
        logger.info(f"Final status: {status}")

        # Clear resources
        self.failure_patterns.clear()
        self.recovery_strategies.clear()
