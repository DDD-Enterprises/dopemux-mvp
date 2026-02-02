"""
ADHD Monitor - Break and Hyperfocus Detection

Monitors ADHD Engine for break recommendations and hyperfocus state.
Triggers desktop notifications via Notifier.

ADHD Benefits:
- Automatic break reminders
- Hyperfocus burnout prevention
- No manual timer needed
"""

import asyncio
import logging
import aiohttp
from typing import Optional

from notify import Notifier
from mobile_push import MobilePushNotifier, PushConfig, NotificationPriority

logger = logging.getLogger(__name__)


class ADHDMonitor:
    """
    Monitors ADHD Engine and sends notifications for breaks/hyperfocus.

    Polls ADHD Engine every 60 seconds to check:
    - Break needed (25+ minutes of work)
    - Hyperfocus detected (60+ minutes)
    """

    def __init__(
        self,
        adhd_engine_url: str = "http://localhost:8095",
        user_id: str = "hue",
        check_interval: int = 60,
        enable_notifications: bool = True
    ):
        """
        Initialize ADHD monitor.

        Args:
            adhd_engine_url: ADHD Engine base URL
            user_id: User ID to monitor
            check_interval: Seconds between checks (default: 60)
            enable_notifications: Enable desktop notifications (default: True)
        """
        self.adhd_engine_url = adhd_engine_url.rstrip("/")
        self.user_id = user_id
        self.check_interval = check_interval
        self.enable_notifications = enable_notifications

        # Notifiers
        self.notifier = Notifier()
        
        # Mobile Push Configuration (Phase 10.7)
        import os
        push_provider = os.getenv("PUSH_PROVIDER", "ntfy")
        push_config = PushConfig(
            provider=push_provider,
            ntfy_topic=os.getenv("NTFY_TOPIC", "adhd-alerts-hue"),
            ntfy_server=os.getenv("NTFY_SERVER", "https://ntfy.sh"),
            pushover_api_key=os.getenv("PUSHOVER_API_KEY"),
            pushover_user_key=os.getenv("PUSHOVER_USER_KEY"),
            enabled=os.getenv("ENABLE_MOBILE_PUSH", "true").lower() == "true"
        )
        self.mobile_push = MobilePushNotifier(push_config)

        # State tracking
        self.last_break_notification: Optional[float] = None
        self.last_hyperfocus_notification: Optional[float] = None
        self.running = False

        # Metrics
        self.checks_performed = 0
        self.break_notifications_sent = 0
        self.hyperfocus_notifications_sent = 0

    async def subscribe_to_break_suggestions(self):
        """
        Subscribe to break.suggestion events from F-NEW-8.

        Integrates intelligent break detection with notification delivery.
        """
        try:
            import sys
            from pathlib import Path
            bridge_path = Path(__file__).parent.parent.parent / "services" / "mcp-dopecon-bridge"
            if str(bridge_path) not in sys.path:
                sys.path.insert(0, str(bridge_path))

            from event_bus import EventBus

            event_bus = EventBus(redis_url="redis://localhost:6379")
            await event_bus.initialize()

            logger.info("📡 Subscribed to break.suggestion events from F-NEW-8")

            # Subscribe to break suggestions
            async for message_id, event in event_bus.subscribe(
                stream="dopemux:events",
                consumer_group="adhd-notifier-breaks",
                consumer_name="adhd-notifier-1"
            ):
                if event.type == "break.suggestion":
                    await self._handle_break_suggestion(event.data)

        except Exception as e:
            logger.error(f"Break suggestion subscription failed: {e}")

    async def _handle_break_suggestion(self, event_data: dict):
        """
        Handle intelligent break suggestion from F-NEW-8.

        Args:
            event_data: Event payload with priority, message, duration
        """
        priority = event_data.get("priority", "medium")
        message = event_data.get("message", "Time for a break")
        duration = event_data.get("suggested_duration", 5)

        logger.info(f"📥 Received break suggestion: {priority} - {message[:50]}")

        # Map F-NEW-8 priority to notification urgency
        urgency = "urgent" if priority in ["critical", "high"] else "normal"

        # Send notification + voice
        self.notifier.send_break_reminder(duration, urgency)
        self.notifier.speak_break_reminder(duration, urgency)

        logger.info(f"✅ Break suggestion delivered via notification + voice")

    async def start_monitoring(self):
        """Start monitoring loop + event subscription"""
        self.running = True
        logger.info("ADHD monitor started")
        logger.info(f"Checking every {self.check_interval}s for break/hyperfocus")
        logger.info("")

        # Start F-NEW-8 subscription in background
        asyncio.create_task(self.subscribe_to_break_suggestions())

        while self.running:
            try:
                await self._perform_checks()
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                logger.info("Monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _perform_checks(self):
        """Perform break and hyperfocus checks"""
        self.checks_performed += 1

        try:
            # Get current session info from Activity Capture
            session_info = await self._get_session_info()

            if not session_info:
                logger.debug("No active session")
                return

            session_duration = session_info.get("current_session_duration_minutes", 0)
            session_active = session_info.get("session_active", False)

            if not session_active or session_duration == 0:
                logger.debug("No active session or duration is 0")
                return

            # Check for hyperfocus (60+ minutes)
            if session_duration >= 60:
                await self._check_hyperfocus(session_duration)

            # Check for break needed (25+ minutes)
            elif session_duration >= 25:
                await self._check_break_needed(session_duration)

        except Exception as e:
            logger.error(f"Check failed: {e}")

    async def _get_session_info(self) -> Optional[dict]:
        """
        Get current session info from Activity Capture.

        Returns:
            Session info dict or None if unavailable
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8096/metrics",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None

        except Exception as e:
            logger.debug(f"Failed to get session info: {e}")
            return None

    async def _check_break_needed(self, duration_minutes: int):
        """
        Check if break is needed and send notification.

        Args:
            duration_minutes: Current session duration
        """
        if not self.enable_notifications:
            return

        # Don't spam notifications (wait 10 min between reminders)
        import time
        if self.last_break_notification:
            time_since_last = time.time() - self.last_break_notification
            if time_since_last < 600:  # 10 minutes
                return

        logger.info(f"Break recommended: {duration_minutes} min session")

        # Send notification + voice
        urgency = "urgent" if duration_minutes >= 45 else "normal"
        success = self.notifier.send_break_reminder(duration_minutes, urgency)

        if success:
            self.break_notifications_sent += 1
            self.last_break_notification = time.time()

            # Also speak the reminder (more effective for ADHD)
            self.notifier.speak_break_reminder(duration_minutes, urgency)
            
            # Send mobile push (Phase 10.7)
            async with self.mobile_push as pusher:
                await pusher.send_break_reminder(
                    message=f"You've been focused for {duration_minutes} minutes. Time for a break!",
                    priority=NotificationPriority.HIGH if urgency == "urgent" else NotificationPriority.NORMAL
                )

    async def _check_hyperfocus(self, duration_minutes: int):
        """
        Check for hyperfocus and send urgent alert.

        Args:
            duration_minutes: Current session duration
        """
        if not self.enable_notifications:
            return

        # Don't spam notifications (wait 15 min between hyperfocus alerts)
        import time
        if self.last_hyperfocus_notification:
            time_since_last = time.time() - self.last_hyperfocus_notification
            if time_since_last < 900:  # 15 minutes
                return

        logger.warning(f"HYPERFOCUS DETECTED: {duration_minutes} min session!")

        # Send urgent notification + voice
        success = self.notifier.send_hyperfocus_alert(duration_minutes)

        if success:
            self.hyperfocus_notifications_sent += 1
            self.last_hyperfocus_notification = time.time()

            # Also speak the alert (critical for hyperfocus interruption)
            self.notifier.speak_hyperfocus_alert(duration_minutes)
            
            # Send mobile push (Phase 10.7)
            async with self.mobile_push as pusher:
                await pusher.send_hyperfocus_alert(
                    message=f"HYPERFOCUS DETECTED: {duration_minutes} minutes! Take a break now."
                )

    def stop(self):
        """Stop monitoring"""
        self.running = False

    def get_metrics(self) -> dict:
        """Get monitor metrics"""
        return {
            "checks_performed": self.checks_performed,
            "break_notifications_sent": self.break_notifications_sent,
            "hyperfocus_notifications_sent": self.hyperfocus_notifications_sent,
            "notifications_enabled": self.enable_notifications
        }
