"""
ADHD Notifier Service - Notification Management for ADHD Events

Handles notifications for ADHD-related events (break reminders, attention alerts, etc.).
Supports multiple notification methods: terminal, voice, system notifications.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ADHDNotifier:
    """
    Manages notifications for ADHD accommodation events.

    Supports multiple notification channels and prioritizes based on urgency.
    """

    def __init__(self, redis_url: str, user_id: str):
        self.redis_url = redis_url
        self.user_id = user_id
        self.redis: redis.Redis = None

        # Notification methods
        self.notification_methods = os.getenv("NOTIFICATION_METHODS", "terminal").split(",")

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.redis_url)
        logger.info("ADHD Notifier initialized")

    async def send_notification(self, notification: Dict[str, Any]):
        """
        Send notification through configured channels.

        Args:
            notification: Notification data with type, message, priority
        """
        try:
            notification_type = notification.get("type", "general")
            message = notification.get("message", "")
            priority = notification.get("priority", "medium")

            logger.info(f"Sending {priority} priority notification: {message}")

            # Send through each configured method
            for method in self.notification_methods:
                await self._send_via_method(method.strip(), notification)

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def _send_via_method(self, method: str, notification: Dict[str, Any]):
        """
        Send notification via specific method.

        Args:
            method: Notification method (terminal, voice, system)
            notification: Notification data
        """
        message = notification.get("message", "")

        if method == "terminal":
            # Terminal notification (works in tmux/screen)
            print(f"\n🔔 ADHD Notification: {message}\n")

        elif method == "voice":
            # Voice notification (macOS say command)
            try:
                import subprocess
                subprocess.run(["say", "-v", "Samantha", message[:100]],
                             capture_output=True, timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Voice notification not available")

        elif method == "system":
            # System notification (platform-dependent)
            try:
                if os.name == 'posix':
                    # Try notify-send on Linux
                    import subprocess
                    subprocess.run(["notify-send", "ADHD Assistant", message],
                                 capture_output=True, timeout=2)
                # Add macOS notification support if needed
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("System notification not available")

        else:
            logger.warning(f"Unknown notification method: {method}")


async def start_adhd_notifier(user_id: str = "default"):
    """
    Start ADHD notifier service.

    Subscribes to notification events and sends them through configured channels.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")
    notification_methods = os.getenv("NOTIFICATION_METHODS", "terminal")

    notifier = ADHDNotifier(redis_url, user_id)
    await notifier.initialize()

    redis_client = redis.from_url(redis_url)

    logger.info(f"ADHD Notifier started - methods: {notification_methods}")

    while True:
        try:
            # Listen for notification events
            messages = await redis_client.xread(
                {"dopemux:notifications": "$"},
                block=1000,
                count=10
            )

            for stream, message_list in messages:
                for message_id, message_data in message_list:
                    try:
                        # Process notification
                        if message_data.get("user_id") == user_id:
                            await notifier.send_notification(message_data)

                        # Acknowledge message
                        await redis_client.xack("dopemux:notifications", f"notifier-{user_id}", message_id)

                    except Exception as e:
                        logger.error(f"Error processing notification: {e}")

        except Exception as e:
            logger.error(f"Notification service error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    user_id = os.getenv("USER_ID", "default")
    asyncio.run(start_adhd_notifier(user_id))