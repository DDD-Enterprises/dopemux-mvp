"""Data models for message triage system."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class UrgencyLevel(Enum):
    """Message urgency levels."""
    CRITICAL = 4  # Production incidents, emergencies (interrupt allowed)
    HIGH = 3      # Important but not urgent (notify at next break)
    MEDIUM = 2    # Standard messages (batch for break)
    LOW = 1       # FYI, can wait (end-of-day summary)


@dataclass
class SlackMessage:
    """Slack message metadata."""

    id: str
    user: str
    channel: str
    channel_type: str  # "channel", "im", "mpim"
    text: str
    timestamp: datetime

    # Optional metadata
    thread_ts: Optional[str] = None
    reactions: List[str] = None
    attachments: List[dict] = None

    def __post_init__(self):
        if self.reactions is None:
            self.reactions = []
        if self.attachments is None:
            self.attachments = []


@dataclass
class QueuedMessage:
    """Message queued during focus session."""

    message: SlackMessage
    urgency: UrgencyLevel
    queued_at: datetime
    delivered: bool = False
    user_corrected_urgency: Optional[UrgencyLevel] = None


@dataclass
class QueuedSummary:
    """Summary of queued messages."""

    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    channels: List[str]
    top_senders: List[tuple]  # [(user, count), ...]
    ai_summary: Optional[str] = None
