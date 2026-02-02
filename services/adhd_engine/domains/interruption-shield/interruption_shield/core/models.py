"""Data models for interruption shield system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class ShieldMode(Enum):
    """Shield operation modes."""
    ASSIST = "assist"      # Suggestions only, user can override
    ENFORCE = "enforce"    # Strict filtering, limited overrides


class AttentionState(Enum):
    """ADHD Engine attention states (mirrored for type safety)."""
    SCATTERED = "scattered"
    TRANSITIONING = "transitioning"
    FOCUSED = "focused"
    HYPERFOCUS = "hyperfocus"
    FATIGUED = "fatigued"


@dataclass
class ShieldState:
    """Current state of interruption shields."""

    user_id: str
    active: bool
    attention_state: AttentionState
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    duration_seconds: int = 0

    # Metrics
    messages_queued: int = 0
    messages_critical: int = 0
    notifications_batched: int = 0
    interruptions_prevented: int = 0

    # Configuration
    mode: ShieldMode = ShieldMode.ASSIST
    auto_deactivate_after: int = 25  # minutes


@dataclass
class ShieldConfig:
    """User-configurable shield settings."""

    # Shield activation
    auto_activate: bool = True
    default_duration: int = 25  # minutes

    # Urgency scoring
    critical_keywords: List[str] = field(default_factory=lambda: [
        "urgent", "asap", "emergency", "critical", "p0", "sev0",
        "production down", "outage", "incident", "all hands"
    ])
    high_keywords: List[str] = field(default_factory=lambda: [
        "important", "p1", "sev1", "blocker", "high priority",
        "deadline", "today", "this morning"
    ])
    vip_users: List[str] = field(default_factory=list)

    # Mode
    mode: ShieldMode = ShieldMode.ASSIST

    # Overrides
    allow_manual_override: bool = True
    override_cooldown: int = 10  # minutes

    # Privacy
    enable_ai_summarization: bool = True
    store_message_content: bool = False

    # Integration endpoints
    adhd_engine_url: str = "http://localhost:8095"
    conport_url: str = "http://localhost:5455"
    desktop_commander_url: str = "http://localhost:8099"

    # Workspace
    workspace_id: str = "/Users/hue/code/dopemux-mvp"


@dataclass
class ShieldMetrics:
    """Metrics for shield effectiveness tracking."""

    session_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int

    # Interruption prevention
    total_messages_received: int
    messages_queued: int
    messages_delivered_immediately: int
    critical_interruptions: int

    # Accuracy
    false_positives: int = 0  # Important messages queued
    false_negatives: int = 0  # Unimportant messages delivered

    # User engagement
    manual_overrides: int = 0
    user_satisfaction: Optional[int] = None  # 1-5 scale
