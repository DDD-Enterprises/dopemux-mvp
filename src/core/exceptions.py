"""
Dopemux Core Exceptions

Custom exception classes for Dopemux integrations and operations.
"""


class DopemuxError(Exception):
    """Base exception for all Dopemux-related errors."""
    pass


class DopemuxIntegrationError(DopemuxError):
    """Exception raised when integration operations fail."""
    pass


class AuthenticationError(DopemuxError):
    """Exception raised when authentication fails."""
    pass


class ConfigurationError(DopemuxError):
    """Exception raised when configuration is invalid."""
    pass


class ADHDOptimizationError(DopemuxError):
    """Exception raised when ADHD optimization operations fail."""
    pass