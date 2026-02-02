#!/usr/bin/env python3
"""
Circuit Breaker Implementation with ADHD-aware thresholds
"""

import time
from enum import Enum
from typing import Optional, Callable, Any
from threading import Lock

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 30.0, adhd_aware: bool = True):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.adhd_aware = adhd_aware
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.lock = Lock()
        self.success_threshold = 3  # Successes needed to close from half-open
        self.success_count = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call the function through the circuit breaker."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time < self.timeout:
                    raise Exception(f"Circuit breaker OPEN - call blocked")
                else:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.failure_count = 0
                    self.success_count = 0

            try:
                result = func(*args, **kwargs)
                self.on_success()
                return result
            except Exception as e:
                self.on_failure(e)
                raise e

    def on_success(self):
        """Handle successful call."""
        with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.success_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0

    def on_failure(self, error: Exception):
        """Handle failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN

    def get_state(self) -> CircuitBreakerState:
        """Get current state."""
        with self.lock:
            return self.state

    def set_state(self, state: CircuitBreakerState):
        """Set state manually."""
        with self.lock:
            self.state = state

    def reset(self):
        """Reset circuit breaker."""
        with self.lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

    def __repr__(self):
        return f"CircuitBreaker(state={self.state}, failures={self.failure_count})"