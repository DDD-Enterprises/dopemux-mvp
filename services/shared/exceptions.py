"""
Shared exception classes for ADHD services.

Provides consistent error handling across all ADHD microservices.
"""


class ADHDServiceError(Exception):
    """Base exception for all ADHD services."""
    pass


class EnergyAssessmentError(ADHDServiceError):
    """Failed to assess energy level."""
    pass


class AttentionDetectionError(ADHDServiceError):
    """Failed to detect attention state."""
    pass


class BreakSuggestionError(ADHDServiceError):
    """Failed to generate break suggestion."""
    pass


class ContextSwitchError(ADHDServiceError):
    """Failed to track context switch."""
    pass


class TaskRecommendationError(ADHDServiceError):
    """Failed to generate task recommendation."""
    pass


class NotificationError(ADHDServiceError):
    """Failed to send notification."""
    pass
