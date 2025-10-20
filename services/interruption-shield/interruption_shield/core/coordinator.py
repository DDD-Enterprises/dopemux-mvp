"""
ShieldCoordinator - Core orchestration for interruption shield.

Subscribes to ADHD Engine attention state changes and coordinates
shield activation/deactivation across all integrated services.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from .models import ShieldState, ShieldMode, ShieldConfig, AttentionState

logger = logging.getLogger(__name__)


class ShieldCoordinator:
    """
    Coordinates interruption shield activation based on ADHD Engine state.

    Subscribes to ADHD Engine attention state changes and activates/deactivates
    shields across all integrated services (macOS, Slack, notifications).
    """

    def __init__(
        self,
        config: ShieldConfig,
        adhd_engine_client=None,  # TODO: Import ADHDEngineClient
        dnd_manager=None,         # TODO: Import DNDManager
        message_triage=None,      # TODO: Import MessageTriage
        notification_manager=None # TODO: Import NotificationManager
    ):
        self.config = config
        self.adhd_engine = adhd_engine_client
        self.dnd = dnd_manager
        self.triage = message_triage
        self.notifications = notification_manager

        # State tracking
        self.state = ShieldState(
            user_id="current_user",  # TODO: Get from auth
            active=False,
            attention_state=AttentionState.SCATTERED,
            mode=config.mode
        )

    async def start(self):
        """Start monitoring ADHD Engine and coordinating shields."""
        logger.info("Starting ShieldCoordinator...")

        # TODO: Subscribe to ADHD Engine attention state changes
        # await self.adhd_engine.subscribe_attention_state(
        #     callback=self.on_attention_state_changed
        # )

        # Start background monitoring tasks
        asyncio.create_task(self._monitor_productivity())
        asyncio.create_task(self._periodic_metrics_log())

        logger.info("ShieldCoordinator started successfully")

    async def on_attention_state_changed(
        self,
        new_state: AttentionState,
        user_id: str
    ):
        """
        Handle attention state changes from ADHD Engine.

        FOCUSED/HYPERFOCUS → Activate shields
        SCATTERED/TRANSITIONING/FATIGUED → Deactivate shields
        """
        logger.info(f"Attention state changed: {new_state.value} for user {user_id}")

        self.state.attention_state = new_state

        if new_state in [AttentionState.FOCUSED, AttentionState.HYPERFOCUS]:
            if self.config.auto_activate:
                await self.activate_shields(user_id)
        else:
            await self.deactivate_shields(user_id)

    async def activate_shields(self, user_id: str):
        """Activate all interruption shields."""
        if self.state.active:
            logger.debug("Shields already active, skipping activation")
            return

        logger.info(f"🛡️ Activating interruption shields for user {user_id}")

        try:
            # Activate all components in parallel
            tasks = []

            if self.dnd:
                tasks.append(self.dnd.enable_macos_focus_mode())
                tasks.append(self.dnd.set_slack_status(
                    status="In focus mode",
                    until=self._calculate_end_time()
                ))

            if self.notifications:
                tasks.append(self.notifications.enable_batching())

            if self.triage:
                tasks.append(self.triage.start_queuing())

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Update state
            self.state.active = True
            self.state.activated_at = datetime.now()

            # Log to ConPort
            await self._log_to_conport(user_id, "shields_activated")

            logger.info("✅ Shields activated successfully")

        except Exception as e:
            logger.error(f"Failed to activate shields: {e}", exc_info=True)
            # Graceful degradation - continue even if some components fail

    async def deactivate_shields(self, user_id: str):
        """Deactivate shields and deliver queued messages."""
        if not self.state.active:
            logger.debug("Shields already inactive, skipping deactivation")
            return

        logger.info(f"🔓 Deactivating interruption shields for user {user_id}")

        try:
            # Deactivate all components in parallel
            tasks = []

            if self.dnd:
                tasks.append(self.dnd.disable_macos_focus_mode())
                tasks.append(self.dnd.clear_slack_status())

            if self.notifications:
                tasks.append(self.notifications.disable_batching_and_deliver())

            if self.triage:
                tasks.append(self.triage.stop_queuing_and_deliver())

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Update state
            self.state.active = False
            self.state.deactivated_at = datetime.now()

            if self.state.activated_at:
                self.state.duration_seconds = int(
                    (self.state.deactivated_at - self.state.activated_at).total_seconds()
                )

            # Show summary of what was queued
            await self._show_queued_summary(user_id)

            # Log to ConPort
            await self._log_to_conport(
                user_id,
                "shields_deactivated",
                metadata={"duration_seconds": self.state.duration_seconds}
            )

            logger.info("✅ Shields deactivated successfully")

        except Exception as e:
            logger.error(f"Failed to deactivate shields: {e}", exc_info=True)

    async def manual_override(self, user_id: str, duration_minutes: int = 10):
        """
        Manually override shields for N minutes.

        Used when user needs to check messages urgently.
        """
        logger.info(f"Manual override requested for {duration_minutes} minutes")

        if not self.config.allow_manual_override:
            logger.warning("Manual override not allowed in current configuration")
            return

        # Temporarily deactivate
        await self.deactivate_shields(user_id)

        # Schedule reactivation after cooldown
        await asyncio.sleep(duration_minutes * 60)

        # Reactivate if still in FOCUSED/HYPERFOCUS
        if self.state.attention_state in [AttentionState.FOCUSED, AttentionState.HYPERFOCUS]:
            await self.activate_shields(user_id)

    async def _monitor_productivity(self):
        """
        Monitor for false positive focus states.

        If no code changes in 15 minutes during FOCUSED state,
        downgrade to SCATTERED to prevent blocking communications.
        """
        while True:
            await asyncio.sleep(60)  # Check every minute

            if not self.state.active:
                continue

            if not self.state.activated_at:
                continue

            duration = (datetime.now() - self.state.activated_at).total_seconds()

            if duration > 900:  # 15 minutes
                has_activity = await self._check_code_activity()

                if not has_activity:
                    logger.warning(
                        "⚠️ No code activity in 15min during FOCUSED state. "
                        "Deactivating shields to prevent communication blockage."
                    )
                    await self.deactivate_shields(self.state.user_id)

    async def _check_code_activity(self) -> bool:
        """
        Check if user has made code changes recently.

        TODO: Query Serena for recent file modifications
        TODO: Query git for uncommitted changes
        """
        # Placeholder - always return True for now
        return True

    async def _periodic_metrics_log(self):
        """Log metrics to ConPort every 5 minutes."""
        while True:
            await asyncio.sleep(300)  # 5 minutes

            if self.state.active:
                await self._log_metrics()

    def _calculate_end_time(self) -> datetime:
        """Calculate when to auto-deactivate shields."""
        return datetime.now() + timedelta(minutes=self.config.default_duration)

    async def _show_queued_summary(self, user_id: str):
        """Show user a summary of queued communications."""
        if not self.triage:
            return

        summary = await self.triage.get_queued_summary()

        # TODO: Display via Desktop Commander notification
        logger.info(f"Queued summary: {summary}")

    async def _log_to_conport(
        self,
        user_id: str,
        event: str,
        metadata: dict = None
    ):
        """Log shield events to ConPort for analytics."""
        # TODO: Implement ConPort integration
        logger.debug(f"ConPort log: {event} - {metadata}")

    async def _log_metrics(self):
        """Log current shield metrics."""
        # TODO: Implement metrics logging
        logger.debug(f"Metrics: {self.state}")
