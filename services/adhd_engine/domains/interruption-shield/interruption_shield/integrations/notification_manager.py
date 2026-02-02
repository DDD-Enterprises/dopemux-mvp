"""
NotificationManager - macOS notification batching and delivery.

Handles:
- Batching notifications during focus sessions
- Delivering summary during breaks
- Filtering low-priority notifications
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    """macOS notification metadata."""

    title: str
    message: str
    timestamp: datetime
    source: str = "unknown"


class NotificationManager:
    """
    macOS notification batching and filtering.

    Phase 1: Basic batching
    Phase 2: App-specific filtering, priority detection
    """

    def __init__(self):
        self.batching_active = False
        self.batched: List[Notification] = []

        # App-specific filtering rules (Phase 2)
        self.blocked_apps = ["Slack", "Discord", "Teams"]  # Handled by shield
        self.allowed_apps = ["Calendar"]  # Always allow calendar notifications

    async def enable_batching(self):
        """Start batching notifications."""
        self.batching_active = True
        self.batched = []
        logger.info("🔕 Notification batching enabled")

        # TODO: Phase 2 - Hook into macOS Notification Center API
        # For now, this is a placeholder for manual notification handling

    async def disable_batching_and_deliver(self):
        """Stop batching and deliver summary notification."""
        self.batching_active = False

        if len(self.batched) > 0:
            await self._deliver_summary()

        self.batched = []
        logger.info("🔔 Notification batching disabled")

    async def handle_notification(self, title: str, message: str, source: str = "unknown"):
        """
        Handle incoming notification.

        If batching active:
        - Add to batch
        If batching inactive:
        - Deliver immediately via pync
        """
        notification = Notification(
            title=title, message=message, timestamp=datetime.now(), source=source
        )

        if self.batching_active:
            # Check if source is allowed (always deliver)
            if source in self.allowed_apps:
                await self._deliver_immediately(notification)
            # Check if source is blocked (handle via shield)
            elif source in self.blocked_apps:
                logger.debug(f"Blocked notification from {source} (handled by shield)")
            # Otherwise batch
            else:
                self.batched.append(notification)
                logger.debug(
                    f"Batched notification from {source}: '{title}' "
                    f"(total: {len(self.batched)})"
                )
        else:
            # Not batching, deliver immediately
            await self._deliver_immediately(notification)

    async def _deliver_immediately(self, notification: Notification):
        """Deliver notification immediately via pync."""
        try:
            # TODO: Install pync for macOS notifications
            # import pync
            # pync.notify(notification.message, title=notification.title)

            logger.info(f"🔔 Delivered: [{notification.title}] {notification.message}")

        except ImportError:
            logger.warning("pync not installed, skipping notification delivery")
        except Exception as e:
            logger.error(f"Failed to deliver notification: {e}")

    async def _deliver_summary(self):
        """Deliver summary of batched notifications."""
        if len(self.batched) == 0:
            return

        # Group by source
        by_source = defaultdict(list)
        for notif in self.batched:
            by_source[notif.source].append(notif)

        # Build summary message
        summary_lines = [
            f"📬 {len(self.batched)} notifications during focus session:",
            "",
        ]

        for source, notifs in by_source.items():
            summary_lines.append(f"  {source}: {len(notifs)} notifications")

        summary = "\n".join(summary_lines)

        try:
            # TODO: Install pync
            # import pync
            # pync.notify(summary, title="Dopemux - Focus Session Complete")

            logger.info(f"🔔 Notification summary:\n{summary}")

        except ImportError:
            logger.warning("pync not installed, logging summary instead")
        except Exception as e:
            logger.error(f"Failed to deliver notification summary: {e}")

    def get_batched_count(self) -> int:
        """Get count of batched notifications."""
        return len(self.batched)

    def clear_batch(self):
        """Clear batched notifications without delivering."""
        count = len(self.batched)
        self.batched = []
        logger.info(f"Cleared {count} batched notifications")
