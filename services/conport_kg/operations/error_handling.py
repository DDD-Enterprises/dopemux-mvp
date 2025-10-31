#!/usr/bin/env python3
"""
ConPort-KG Operational Error Handling Patterns
Production-ready error handling, recovery, and resilience patterns.

This module defines comprehensive error handling strategies for:
- Application errors (business logic, validation)
- Infrastructure errors (database, network, external services)
- Security errors (authentication, authorization)
- Recovery patterns (retry, fallback, circuit breaker)
- Logging and monitoring integration
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Any, Dict, Optional, Callable, Awaitable, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
import functools

# Configure logging
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels for classification and handling"""
    LOW = "low"         # Minor issues, log and continue
    MEDIUM = "medium"   # Notable issues, alert but continue
    HIGH = "high"       # Serious issues, alert and may degrade
    CRITICAL = "critical"  # System-threatening, immediate action required

class ErrorCategory(Enum):
    """Error categories for routing and handling"""
    VALIDATION = "validation"       # Input validation errors
    AUTHENTICATION = "auth"         # Login/auth failures
    AUTHORIZATION = "authz"         # Permission/access errors
    DATABASE = "database"          # DB connection/query errors
    NETWORK = "network"            # External service/API errors
    BUSINESS_LOGIC = "business"     # Application logic errors
    INFRASTRUCTURE = "infra"        # Server/hardware errors
    SECURITY = "security"           # Security-related errors
    EXTERNAL = "external"           # Third-party service errors

@dataclass
class ErrorContext:
    """Rich error context for debugging and monitoring"""
    category: ErrorCategory
    severity: ErrorSeverity
    operation: str
    user_id: Optional[int] = None
    workspace_id: Optional[str] = None
    resource_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ErrorResponse:
    """Standardized error response format"""
    error_code: str
    message: str
    category: str
    severity: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None
    request_id: Optional[str] = None

class ConPortException(Exception):
    """Base exception class for ConPort-KG"""

    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable

    def to_response(self, request_id: Optional[str] = None) -> ErrorResponse:
        """Convert to standardized error response"""
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            category=self.category.value,
            severity=self.severity.value,
            details=self.details,
            retry_after=30 if self.retryable else None,
            request_id=request_id
        )

# Specific exception classes
class ValidationError(ConPortException):
    """Input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            status_code=400,
            details={"field": field, **(details or {})}
        )

class AuthenticationError(ConPortException):
    """Authentication failures"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            status_code=401,
            details=details
        )

class AuthorizationError(ConPortException):
    """Authorization/permission errors"""
    def __init__(self, message: str = "Insufficient permissions", resource: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_FAILED",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            status_code=403,
            details={"resource": resource}
        )

class DatabaseError(ConPortException):
    """Database-related errors"""
    def __init__(self, message: str, operation: str, retryable: bool = True):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            status_code=500,
            details={"operation": operation},
            retryable=retryable
        )

class ExternalServiceError(ConPortException):
    """External service/API errors"""
    def __init__(self, service: str, operation: str, status_code: int = 502, retryable: bool = True):
        super().__init__(
            message=f"External service error: {service}",
            error_code="EXTERNAL_SERVICE_ERROR",
            category=ErrorCategory.EXTERNAL,
            severity=ErrorSeverity.MEDIUM,
            status_code=status_code,
            details={"service": service, "operation": operation},
            retryable=retryable
        )

class CircuitBreakerOpenError(ConPortException):
    """Circuit breaker prevents operation"""
    def __init__(self, service: str):
        super().__init__(
            message=f"Service temporarily unavailable: {service}",
            error_code="CIRCUIT_BREAKER_OPEN",
            category=ErrorCategory.EXTERNAL,
            severity=ErrorSeverity.MEDIUM,
            status_code=503,
            details={"service": service},
            retryable=True
        )

# Retry and Circuit Breaker Implementation
@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 0.1
    max_delay: float = 10.0
    backoff_factor: float = 2.0
    jitter: bool = True

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: tuple = (Exception,)

class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half_open

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = "half_open"
                else:
                    raise CircuitBreakerOpenError(func.__name__)

            try:
                result = await func(*args, **kwargs)
                if self.state == "half_open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except self.config.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.config.failure_threshold:
                    self.state = "open"

                raise e

        return wrapper

async def retry_async(
    func: Callable[..., Awaitable[Any]],
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """Retry an async function with exponential backoff"""
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt < config.max_attempts - 1:
                delay = min(
                    config.initial_delay * (config.backoff_factor ** attempt),
                    config.max_delay
                )

                if config.jitter:
                    delay = delay * (0.5 + 0.5 * time.time() % 1)  # Add jitter

                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
                )
                await asyncio.sleep(delay)

    logger.error(f"All {config.max_attempts} attempts failed")
    raise last_exception

def with_error_handling(
    category: ErrorCategory,
    severity: ErrorSeverity,
    operation: str
) -> Callable:
    """Decorator for comprehensive error handling"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = kwargs.get('request_id') or str(time.time())

            try:
                # Extract user context from request if available
                user_id = None
                workspace_id = None

                # Try to extract from args/kwargs (FastAPI dependency injection)
                for arg in args:
                    if hasattr(arg, 'user') and hasattr(arg.user, 'id'):
                        user_id = arg.user.id
                    if hasattr(arg, 'workspace_id'):
                        workspace_id = arg.workspace_id

                # Execute function
                result = await func(*args, **kwargs)
                return result

            except ConPortException:
                # Re-raise our custom exceptions as-is
                raise

            except Exception as e:
                # Wrap unexpected exceptions
                error_context = ErrorContext(
                    category=category,
                    severity=severity,
                    operation=operation,
                    user_id=user_id,
                    workspace_id=workspace_id,
                    request_id=request_id,
                    metadata={"original_error": str(e), "error_type": type(e).__name__}
                )

                logger.error(
                    f"Unhandled error in {operation}",
                    extra={
                        "error_context": error_context,
                        "exception": str(e),
                        "stack_trace": True
                    }
                )

                # Convert to appropriate ConPort exception
                if "database" in str(e).lower():
                    raise DatabaseError(f"Database operation failed: {operation}", operation)
                elif "connection" in str(e).lower():
                    raise ExternalServiceError("database", operation)
                elif "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                    raise AuthorizationError("Operation not permitted")
                else:
                    raise ConPortException(
                        message=f"Operation failed: {operation}",
                        error_code="INTERNAL_ERROR",
                        category=category,
                        severity=severity,
                        details={"original_error": str(e)}
                    )

        return wrapper

    return decorator

# Health Check and Monitoring Integration
@dataclass
class HealthStatus:
    """Service health status"""
    service: str
    status: str  # healthy, degraded, unhealthy
    last_check: float
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class HealthChecker:
    """Health check management"""

    def __init__(self):
        self.services: Dict[str, HealthStatus] = {}
        self.check_functions: Dict[str, Callable[[], Awaitable[bool]]] = {}

    def register_service(self, name: str, check_func: Callable[[], Awaitable[bool]]):
        """Register a service health check"""
        self.check_functions[name] = check_func

    async def check_all_services(self) -> Dict[str, HealthStatus]:
        """Check health of all registered services"""
        results = {}

        for service_name, check_func in self.check_functions.items():
            start_time = time.time()

            try:
                is_healthy = await check_func()
                response_time = time.time() - start_time

                status = HealthStatus(
                    service=service_name,
                    status="healthy" if is_healthy else "unhealthy",
                    last_check=time.time(),
                    response_time=response_time
                )

            except Exception as e:
                response_time = time.time() - start_time

                status = HealthStatus(
                    service=service_name,
                    status="unhealthy",
                    last_check=time.time(),
                    response_time=response_time,
                    error_message=str(e)
                )

            self.services[service_name] = status
            results[service_name] = status

        return results

    def get_overall_health(self) -> str:
        """Get overall system health status"""
        if not self.services:
            return "unknown"

        unhealthy_count = sum(1 for s in self.services.values() if s.status != "healthy")

        if unhealthy_count == 0:
            return "healthy"
        elif unhealthy_count < len(self.services) / 2:
            return "degraded"
        else:
            return "unhealthy"

# Global instances
health_checker = HealthChecker()
circuit_breaker_config = CircuitBreakerConfig()
retry_config = RetryConfig()

__all__ = [
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorResponse",
    "ConPortException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError",
    "ExternalServiceError",
    "CircuitBreakerOpenError",
    "RetryConfig",
    "CircuitBreakerConfig",
    "CircuitBreaker",
    "retry_async",
    "with_error_handling",
    "HealthStatus",
    "HealthChecker",
    "health_checker",
    "circuit_breaker_config",
    "retry_config"
]