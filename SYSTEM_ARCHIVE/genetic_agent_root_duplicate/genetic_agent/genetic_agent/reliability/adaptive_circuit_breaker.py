"""Adaptive Circuit Breaker for MCP service reliability."""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics


class CircuitBreakerState(Enum):
    """States of the circuit breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ServiceStats:
    """Statistics for a specific MCP service."""
    service_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    response_times: List[float] = field(default_factory=list)
    last_health_check: Optional[float] = None
    health_status: bool = True

    @property
    def success_rate(self) -> float:
        """Calculate success rate over recent requests."""
        if self.total_requests == 0:
            return 1.0  # Assume perfect for new services
        return self.successful_requests / self.total_requests

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times[-20:])  # Last 20 requests

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate

    def record_request(self, success: bool, response_time: float):
        """Record the result of a service request."""
        self.total_requests += 1

        if success:
            self.successful_requests += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.last_success_time = time.time()
        else:
            self.failed_requests += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_failure_time = time.time()

        # Keep response time history (last 50 requests)
        self.response_times.append(response_time)
        if len(self.response_times) > 50:
            self.response_times.pop(0)

    def update_health_status(self, healthy: bool):
        """Update the health status of the service."""
        self.health_status = healthy
        self.last_health_check = time.time()

    def should_attempt_recovery(self, open_timeout: float) -> bool:
        """Check if we should attempt to recover from open state."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= open_timeout


class AdaptiveCircuitBreaker:
    """Adaptive circuit breaker that adjusts thresholds based on service performance."""

    def __init__(self,
                 failure_threshold: float = 0.5,  # 50% failure rate
                 recovery_timeout: float = 60.0,   # 60 seconds
                 success_threshold: int = 3,       # 3 consecutive successes
                 health_check_interval: float = 300.0,  # 5 minutes
                 max_open_time: float = 600.0):    # 10 minutes max open

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.health_check_interval = health_check_interval
        self.max_open_time = max_open_time

        # Service-specific state
        self.service_stats: Dict[str, ServiceStats] = {}
        self.service_states: Dict[str, CircuitBreakerState] = {}
        self.service_policies: Dict[str, Dict[str, Any]] = {}

        # Global stats
        self.total_requests = 0
        self.global_failure_rate = 0.0

    def register_service(self, service_name: str, custom_policy: Optional[Dict[str, Any]] = None):
        """Register a service with optional custom policy."""
        if service_name not in self.service_stats:
            self.service_stats[service_name] = ServiceStats(service_name)
            self.service_states[service_name] = CircuitBreakerState.CLOSED

        if custom_policy:
            self.service_policies[service_name] = custom_policy

    def get_service_policy(self, service_name: str) -> Dict[str, Any]:
        """Get the policy for a specific service."""
        base_policy = {
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "success_threshold": self.success_threshold,
            "health_check_interval": self.health_check_interval,
            "max_open_time": self.max_open_time
        }

        # Merge with custom policy
        custom = self.service_policies.get(service_name, {})
        return {**base_policy, **custom}

    def can_attempt_request(self, service_name: str) -> bool:
        """Check if a request can be attempted for the given service."""
        if service_name not in self.service_stats:
            self.register_service(service_name)
            return True

        state = self.service_states[service_name]
        stats = self.service_stats[service_name]
        policy = self.get_service_policy(service_name)

        if state == CircuitBreakerState.CLOSED:
            # Check if we should open the circuit
            if stats.failure_rate >= policy["failure_threshold"]:
                self.service_states[service_name] = CircuitBreakerState.OPEN
                return False
            return True

        elif state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if stats.should_attempt_recovery(policy["recovery_timeout"]):
                self.service_states[service_name] = CircuitBreakerState.HALF_OPEN
                return True
            return False

        elif state == CircuitBreakerState.HALF_OPEN:
            # Allow requests in half-open state for testing
            return True

        return False

    async def execute_with_circuit_breaker(self, service_name: str,
                                         operation: Callable[[], Any],
                                         fallback: Optional[Callable[[], Any]] = None) -> Any:
        """Execute an operation with circuit breaker protection."""
        self.total_requests += 1

        if not self.can_attempt_request(service_name):
            if fallback:
                return await self._execute_operation(fallback, is_fallback=True)
            raise CircuitBreakerOpenException(service_name)

        try:
            start_time = time.time()
            result = await self._execute_operation(operation)
            response_time = time.time() - start_time

            self.record_success(service_name, response_time)
            return result

        except Exception as e:
            response_time = time.time() - time.time()  # Approximate
            self.record_failure(service_name, response_time)

            # Try fallback if available
            if fallback:
                try:
                    return await self._execute_operation(fallback, is_fallback=True)
                except Exception:
                    pass  # Fallback also failed

            raise e

    async def _execute_operation(self, operation: Callable[[], Any], is_fallback: bool = False) -> Any:
        """Execute the operation, handling async/sync differences."""
        if asyncio.iscoroutinefunction(operation):
            return await operation()
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation)

    def record_success(self, service_name: str, response_time: float):
        """Record a successful request."""
        if service_name not in self.service_stats:
            self.register_service(service_name)

        stats = self.service_stats[service_name]
        stats.record_request(True, response_time)

        # Update circuit breaker state
        if self.service_states[service_name] == CircuitBreakerState.HALF_OPEN:
            if stats.consecutive_successes >= self.get_service_policy(service_name)["success_threshold"]:
                self.service_states[service_name] = CircuitBreakerState.CLOSED

    def record_failure(self, service_name: str, response_time: float):
        """Record a failed request."""
        if service_name not in self.service_stats:
            self.register_service(service_name)

        stats = self.service_stats[service_name]
        stats.record_request(False, response_time)

        # Update circuit breaker state
        policy = self.get_service_policy(service_name)

        if self.service_states[service_name] == CircuitBreakerState.CLOSED:
            if stats.failure_rate >= policy["failure_threshold"]:
                self.service_states[service_name] = CircuitBreakerState.OPEN

        elif self.service_states[service_name] == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open sends back to open
            self.service_states[service_name] = CircuitBreakerState.OPEN

    async def perform_health_checks(self):
        """Perform health checks for all registered services."""
        current_time = time.time()

        for service_name, stats in self.service_stats.items():
            policy = self.get_service_policy(service_name)

            # Check if health check is due
            if (stats.last_health_check is None or
                current_time - stats.last_health_check >= policy["health_check_interval"]):

                try:
                    # Perform health check (placeholder - would call actual health endpoint)
                    healthy = await self._perform_health_check(service_name)
                    stats.update_health_status(healthy)

                    # If service recovered and circuit is open, allow testing
                    if healthy and self.service_states[service_name] == CircuitBreakerState.OPEN:
                        if stats.should_attempt_recovery(policy["recovery_timeout"]):
                            self.service_states[service_name] = CircuitBreakerState.HALF_OPEN

                except Exception:
                    stats.update_health_status(False)

    async def _perform_health_check(self, service_name: str) -> bool:
        """Perform a health check for the service."""
        # Placeholder implementation
        # In real implementation, this would call the service's health endpoint
        try:
            # Simulate health check
            await asyncio.sleep(0.1)  # Small delay
            return True  # Assume healthy for demo
        except Exception:
            return False

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get the current status of a service."""
        if service_name not in self.service_stats:
            return {"error": "Service not registered"}

        stats = self.service_stats[service_name]
        state = self.service_states[service_name]
        policy = self.get_service_policy(service_name)

        return {
            "service_name": service_name,
            "state": state.value,
            "stats": {
                "total_requests": stats.total_requests,
                "success_rate": round(stats.success_rate, 3),
                "failure_rate": round(stats.failure_rate, 3),
                "average_response_time": round(stats.average_response_time, 3),
                "consecutive_failures": stats.consecutive_failures,
                "consecutive_successes": stats.consecutive_successes,
                "last_failure_time": stats.last_failure_time,
                "last_success_time": stats.last_success_time
            },
            "policy": policy,
            "health_status": stats.health_status,
            "last_health_check": stats.last_health_check
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        total_services = len(self.service_stats)
        open_circuits = sum(1 for state in self.service_states.values()
                          if state == CircuitBreakerState.OPEN)
        unhealthy_services = sum(1 for stats in self.service_stats.values()
                               if not stats.health_status)

        # Calculate global failure rate
        total_successes = sum(stats.successful_requests for stats in self.service_stats.values())
        total_requests = sum(stats.total_requests for stats in self.service_stats.values())

        if total_requests > 0:
            self.global_failure_rate = 1.0 - (total_successes / total_requests)

        return {
            "total_services": total_services,
            "open_circuits": open_circuits,
            "unhealthy_services": unhealthy_services,
            "global_failure_rate": round(self.global_failure_rate, 3),
            "total_requests": self.total_requests,
            "service_details": {
                name: self.get_service_status(name)
                for name in self.service_stats.keys()
            }
        }

    def reset_service(self, service_name: str):
        """Reset a service to closed state (admin function)."""
        if service_name in self.service_states:
            self.service_states[service_name] = CircuitBreakerState.CLOSED
            # Keep stats for learning, just reset state

    def reset_all(self):
        """Reset all services to closed state."""
        for service_name in self.service_states:
            self.service_states[service_name] = CircuitBreakerState.CLOSED


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker is open for service: {service_name}")