"""
Dopemux Core Exceptions

Custom exception classes for Dopemux integrations and operations.
"""


class DopemuxError(Exception):
    """Base exception for all Dopemux-related errors."""


class DopemuxIntegrationError(DopemuxError):
    """Exception raised when integration operations fail."""


class AuthenticationError(DopemuxError):
    """Exception raised when authentication fails."""


class ConfigurationError(DopemuxError):
    """Exception raised when configuration is invalid."""


class ADHDOptimizationError(DopemuxError):
    """Exception raised when ADHD optimization operations fail."""
