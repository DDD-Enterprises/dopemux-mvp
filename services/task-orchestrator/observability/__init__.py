"""
Component 6: Observability Module

Provides metrics collection and monitoring for ADHD Intelligence Layer.

Created: 2025-10-20
Phase: 1a - Observability Foundation (25% of Component 6)
"""

from .metrics_collector import MetricsCollector
from .adhd_dashboard import ADHDDashboard

__all__ = [
    "MetricsCollector",
    "ADHDDashboard",
]
