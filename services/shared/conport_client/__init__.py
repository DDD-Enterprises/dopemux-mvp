"""
@dopemux/conport-client - Unified ConPort Client

Single canonical interface for ConPort access across all Dopemux systems.
"""

from .client import ConPortClient, ConPortConfig
from .models import Decision, ProgressEntry, SystemPattern, CustomData
from .backends import BackendType

__version__ = "1.0.0"

__all__ = [
    "ConPortClient",
    "ConPortConfig",
    "Decision",
    "ProgressEntry",
    "SystemPattern",
    "CustomData",
    "BackendType",
]
