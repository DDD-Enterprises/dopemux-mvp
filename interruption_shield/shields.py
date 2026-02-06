"""Shield implementations for environmental interruption control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class BaseShield:
    """Minimal async shield interface with in-memory state."""

    name: str
    active: bool = False
    last_reason: str = ""
    last_changed_at: str = ""

    async def activate(self, reason: str) -> Dict[str, Any]:
        self.active = True
        self.last_reason = reason
        self.last_changed_at = datetime.now().isoformat()
        return {
            "success": True,
            "shield": self.name,
            "active": self.active,
            "reason": reason,
            "timestamp": self.last_changed_at,
        }

    async def deactivate(self, reason: str) -> Dict[str, Any]:
        self.active = False
        self.last_reason = reason
        self.last_changed_at = datetime.now().isoformat()
        return {
            "success": True,
            "shield": self.name,
            "active": self.active,
            "reason": reason,
            "timestamp": self.last_changed_at,
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "success": True,
            "shield": self.name,
            "active": self.active,
            "last_reason": self.last_reason,
            "last_changed_at": self.last_changed_at or None,
        }


class DNDShield(BaseShield):
    """Do-not-disturb shield."""

    def __init__(self) -> None:
        super().__init__(name="dnd")


class SlackShield(BaseShield):
    """Slack-status shield."""

    def __init__(self) -> None:
        super().__init__(name="slack")


class NotificationShield(BaseShield):
    """Notification-filter shield."""

    def __init__(self) -> None:
        super().__init__(name="notifications")

