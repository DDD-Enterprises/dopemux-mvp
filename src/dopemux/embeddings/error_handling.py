"""
Error Handling for Embeddings Module.

Re-exports the global error handling framework for use within the embeddings
module. This provides a consistent interface while allowing the embeddings
module to import from a relative path.
"""

# Re-export all error handling components from the main dopemux error handling
from dopemux.error_handling import (
    # Core types
    ErrorType,
    ErrorSeverity,
    
    # Error classes
    DopemuxError,
    
    # Circuit breaker
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerStats,
    
    # Retry policy
    RetryPolicy,
    
    # Global handler
    GlobalErrorHandler,
    get_global_error_handler,
    
    # Convenience functions
    with_error_handling,
    create_dopemux_error,
)

__all__ = [
    # Core types
    "ErrorType",
    "ErrorSeverity",
    
    # Error classes
    "DopemuxError",
    
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "CircuitBreakerStats",
    
    # Retry policy
    "RetryPolicy",
    
    # Global handler
    "GlobalErrorHandler",
    "get_global_error_handler",
    
    # Convenience functions
    "with_error_handling",
    "create_dopemux_error",
]
