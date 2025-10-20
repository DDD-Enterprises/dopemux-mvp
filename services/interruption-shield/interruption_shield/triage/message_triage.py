"""
MessageTriage - Orchestrates urgency scoring and message queuing.

Coordinates UrgencyScorer and MessageQueue for intelligent message filtering.
"""

import asyncio
import logging
from typing import Optional

from .message_queue import MessageQueue
from .models import QueuedSummary, SlackMessage, UrgencyLevel
from .urgency_scorer import UrgencyScorer

logger = logging.getLogger(__name__)


class MessageTriage:
    """
    Urgency-based message filtering and queuing orchestration.

    Workflow:
    1. Incoming message → score urgency
    2. If CRITICAL → deliver immediately
    3. Else → queue for break delivery
    4. On shield deactivation → deliver all queued
    """

    def __init__(
        self, urgency_scorer: UrgencyScorer, message_queue: MessageQueue, enable_ai_summary: bool = False
    ):
        self.scorer = urgency_scorer
        self.queue = message_queue
        self.enable_ai_summary = enable_ai_summary
        self.queuing_active = False

        # Callbacks
        self.on_critical_message = None  # Callback for critical interruptions

    async def start(self):
        """Start message triage system."""
        await self.queue.connect()
        logger.info("MessageTriage started")

    async def stop(self):
        """Stop message triage system."""
        await self.queue.disconnect()
        logger.info("MessageTriage stopped")

    async def start_queuing(self):
        """Start queuing incoming messages (shields activated)."""
        self.queuing_active = True
        logger.info("📥 Message queuing activated")

    async def stop_queuing_and_deliver(self):
        """Stop queuing and deliver all queued messages."""
        self.queuing_active = False

        # Get summary
        summary = await self.queue.get_summary()

        logger.info(
            f"📤 Message queuing deactivated. Queued: {summary.total_count} messages "
            f"({summary.critical_count} critical, {summary.high_count} high)"
        )

        # Show summary (via Desktop Commander notification)
        await self._show_summary(summary)

        # Mark all as delivered (they're now accessible)
        await self.queue.clear()

    async def handle_incoming_message(self, message: SlackMessage):
        """
        Process incoming Slack message.

        If shields active:
        - Score urgency
        - If CRITICAL → deliver immediately (callback)
        - Else → queue for later

        If shields inactive:
        - Pass through (no filtering)
        """
        if not self.queuing_active:
            # Shields not active, no filtering
            logger.debug(f"Shields inactive, passing through message from {message.user}")
            return

        # Score urgency
        urgency = await self.scorer.score(message)

        if urgency == UrgencyLevel.CRITICAL:
            # Allow critical interruptions
            logger.warning(
                f"🚨 CRITICAL message from {message.user}: '{message.text[:50]}...'. "
                f"Interrupting focus session."
            )

            # Trigger callback (deliver to user immediately)
            if self.on_critical_message:
                await self.on_critical_message(message)

        else:
            # Queue for later
            await self.queue.add(message, urgency)

    async def get_queued_summary(self) -> QueuedSummary:
        """Get summary of currently queued messages."""
        summary = await self.queue.get_summary()

        # Optionally generate AI summary
        if self.enable_ai_summary and summary.total_count > 0:
            summary.ai_summary = await self._generate_ai_summary()

        return summary

    async def _show_summary(self, summary: QueuedSummary):
        """
        Display queued message summary to user.

        TODO: Integrate with Desktop Commander for notification
        """
        if summary.total_count == 0:
            logger.info("💬 No messages queued during focus session")
            return

        # Build human-readable summary
        msg = (
            f"💬 {summary.total_count} messages queued during focus session\n"
            f"   Critical: {summary.critical_count}, "
            f"High: {summary.high_count}, "
            f"Medium: {summary.medium_count}, "
            f"Low: {summary.low_count}\n"
        )

        if summary.top_senders:
            top = ", ".join(f"{user} ({count})" for user, count in summary.top_senders[:3])
            msg += f"   Top senders: {top}\n"

        if summary.ai_summary:
            msg += f"\n   📝 Summary: {summary.ai_summary}"

        logger.info(msg)

        # TODO: Send to Desktop Commander for user notification
        # await desktop_commander.notify(
        #     title="Focus Session Complete",
        #     message=msg
        # )

    async def _generate_ai_summary(self) -> str:
        """
        Generate AI summary of queued messages using OpenAI.

        Phase 2 feature - requires user consent.
        """
        # TODO: Implement OpenAI summarization
        # queued = await self.queue.get_all()
        # Group by channel, send to OpenAI for summarization
        return "AI summarization not yet implemented"

    def set_critical_callback(self, callback):
        """
        Set callback for critical message delivery.

        Callback signature: async def on_critical(message: SlackMessage)
        """
        self.on_critical_message = callback
        logger.info("Critical message callback registered")
