"""
Integration adapters for external systems.

Provides seamless integration with ConPort (context management),
Serena (code navigation), and other dopemux components.
"""

from .base import BaseIntegration
from .conport import ConPortAdapter
from .serena import SerenaAdapter

__all__ = [
    # Base interface
    "BaseIntegration",

    # Specific integrations
    "ConPortAdapter",
    "SerenaAdapter"
]