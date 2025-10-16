"""
Event type definitions for Dopemux event bus.

All events are Pydantic models for type safety and validation.
Based on UI Design Research Synthesis (Decision #25).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventPriority(str, Enum):
    """Event priority levels for ADHD-optimized filtering."""

    LOW = "low"           # Background updates, non-critical
    MEDIUM = "medium"     # Normal updates
    HIGH = "high"         # Important state changes
    CRITICAL = "critical" # Requires immediate attention


class Event(BaseModel):
    """Base event class for all Dopemux events."""

    type: str = Field(..., description="Event type identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: EventPriority = Field(default=EventPriority.MEDIUM)
    data: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = Field(default=None, description="Component that emitted event")

    class Config:
        frozen = True  # Events are immutable


class WorktreeEvent(Event):
    """Events related to git worktree operations."""

    type: str = "worktree"

    class Action(str, Enum):
        CREATED = "created"
        SWITCHED = "switched"
        REMOVED = "removed"
        CLEANED = "cleaned"

    action: Action = Field(..., description="Worktree action performed")
    branch: str = Field(..., description="Branch name")
    path: Optional[str] = Field(default=None, description="Worktree path")


class ContextEvent(Event):
    """Events related to ConPort context changes."""

    type: str = "context"

    class Action(str, Enum):
        UPDATED = "updated"
        RESTORED = "restored"
        DECISION_LOGGED = "decision_logged"
        PROGRESS_UPDATED = "progress_updated"

    action: Action = Field(..., description="Context action performed")
    workspace_id: str = Field(..., description="ConPort workspace ID")
    context_type: str = Field(..., description="product_context or active_context")


class ADHDEvent(Event):
    """Events related to ADHD state changes from ADHD Engine."""

    type: str = "adhd"

    class StateType(str, Enum):
        ENERGY = "energy"
        ATTENTION = "attention"
        BREAK_REMINDER = "break_reminder"
        CONTEXT_SWITCH = "context_switch"

    state_type: StateType = Field(..., description="Type of ADHD state")
    previous_value: Optional[str] = Field(default=None)
    current_value: str = Field(..., description="New state value")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ThemeEvent(Event):
    """Events related to theme changes."""

    type: str = "theme"

    class Action(str, Enum):
        SWITCHED = "switched"
        UPDATED = "updated"
        INTERPOLATED = "interpolated"  # Energy state transition

    action: Action = Field(..., description="Theme action")
    theme_name: str = Field(..., description="Theme identifier")
    previous_theme: Optional[str] = Field(default=None)


class SessionEvent(Event):
    """Events related to tmux session lifecycle."""

    type: str = "session"

    class Action(str, Enum):
        CREATED = "created"
        ATTACHED = "attached"
        DETACHED = "detached"
        DESTROYED = "destroyed"
        PANE_CREATED = "pane_created"
        LAYOUT_CHANGED = "layout_changed"

    action: Action = Field(..., description="Session action")
    session_id: str = Field(..., description="Tmux session ID")
    session_name: Optional[str] = Field(default=None)
