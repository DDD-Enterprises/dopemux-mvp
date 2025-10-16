"""
Dopemux Event Bus - ADHD-optimized reactive event system.

Provides type-safe event dispatching with async handlers for real-time
UI updates and cross-component coordination.
"""

from .types import (
    Event,
    WorktreeEvent,
    ContextEvent,
    ADHDEvent,
    ThemeEvent,
    SessionEvent,
)
from .bus import EventBus, EventHandler

__all__ = [
    "Event",
    "WorktreeEvent",
    "ContextEvent",
    "ADHDEvent",
    "ThemeEvent",
    "SessionEvent",
    "EventBus",
    "EventHandler",
]
