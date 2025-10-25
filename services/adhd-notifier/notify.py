"""
Desktop Notifier - OS-Specific Notification Sender

Sends desktop notifications for ADHD break reminders and hyperfocus alerts.
Supports macOS (osascript) and Linux (notify-send).

ADHD Benefits:
- Visual break reminders (prevents hyperfocus burnout)
- Urgent alerts for extended sessions
- Non-intrusive (can be dismissed)
- Persistent until acknowledged
"""

import subprocess
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


class Notifier:
    """
    Cross-platform desktop notification sender.

    Sends break reminders and hyperfocus alerts via native OS notifications.
    """

    def __init__(self):
        """Initialize notifier with OS detection"""
        self.os_type = platform.system()
        logger.info(f"Notifier initialized for {self.os_type}")

    def send_break_reminder(self, duration_minutes: int, urgency: str = "normal") -> bool:
        """
        Send break reminder notification.

        Args:
            duration_minutes: How long user has been working
            urgency: "normal" or "urgent"

        Returns:
            True if notification sent successfully
        """
        if urgency == "urgent":
            title = "Break Needed NOW"
            message = f"You've been coding for {duration_minutes} minutes. Take a 10-minute break!"
            sound = "Basso"  # Alert sound
        else:
            title = "Time for a Break"
            message = f"You've been focused for {duration_minutes} minutes. Take a 5-minute break."
            sound = "default"

        return self._send_notification(title, message, sound)

    def send_hyperfocus_alert(self, duration_minutes: int) -> bool:
        """
        Send urgent hyperfocus protection alert.

        Args:
            duration_minutes: How long user has been in hyperfocus

        Returns:
            True if notification sent successfully
        """
        title = "HYPERFOCUS ALERT"
        message = (
            f"You've been coding for {duration_minutes} minutes without a break!\n\n"
            f"This can lead to burnout. Take a 15-minute break NOW."
        )
        sound = "Sosumi"  # Urgent alert sound

        return self._send_notification(title, message, sound)

    def send_test_notification(self) -> bool:
        """Send test notification to verify system works"""
        return self._send_notification(
            "ADHD Notifier",
            "Desktop notifications are working!",
            "default"
        )

    def speak_break_reminder(self, duration_minutes: int, urgency: str = "normal") -> bool:
        """
        Speak break reminder using text-to-speech (macOS only).

        Args:
            duration_minutes: How long user has been working
            urgency: "normal" or "urgent"

        Returns:
            True if speech sent successfully
        """
        if not IS_MACOS:
            logger.debug("Voice notifications only supported on macOS")
            return False

        if urgency == "urgent":
            message = f"Break needed now. You have been coding for {duration_minutes} minutes. Please take a ten minute break."
        else:
            message = f"Time for a break. You have been focused for {duration_minutes} minutes. Take a five minute break."

        return self._speak_macos(message)

    def speak_hyperfocus_alert(self, duration_minutes: int) -> bool:
        """
        Speak urgent hyperfocus alert using TTS.

        Args:
            duration_minutes: How long user has been in hyperfocus

        Returns:
            True if speech sent successfully
        """
        if not IS_MACOS:
            return False

        message = (
            f"Hyperfocus alert! You have been coding for {duration_minutes} minutes without a break. "
            f"This can lead to burnout. Take a fifteen minute break immediately."
        )

        return self._speak_macos(message, rate=180)  # Slightly faster for urgency

    def _speak_macos(self, message: str, rate: int = 175) -> bool:
        """
        Speak text on macOS using 'say' command.

        Args:
            message: Text to speak
            rate: Words per minute (default: 175)

        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                ["say", "-r", str(rate), message],
                capture_output=True,
                timeout=30.0  # Max 30 seconds to speak
            )

            if result.returncode == 0:
                logger.info(f"Spoke: {message[:50]}...")
                return True
            else:
                logger.warning(f"say command failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Speech timeout")
            return False
        except Exception as e:
            logger.error(f"macOS speech error: {e}")
            return False

    def _send_notification(
        self,
        title: str,
        message: str,
        sound: str = "default"
    ) -> bool:
        """
        Send notification using OS-specific method.

        Args:
            title: Notification title
            message: Notification message
            sound: Sound to play (macOS only)

        Returns:
            True if sent successfully
        """
        try:
            if IS_MACOS:
                return self._send_notification_macos(title, message, sound)
            elif IS_LINUX:
                return self._send_notification_linux(title, message)
            else:
                logger.warning(f"Notifications not supported on {self.os_type}")
                return False

        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return False

    def _send_notification_macos(
        self,
        title: str,
        message: str,
        sound: str = "default"
    ) -> bool:
        """
        Send notification on macOS using osascript (AppleScript).

        Args:
            title: Notification title
            message: Notification message
            sound: Sound name (default, Basso, Sosumi, etc.)

        Returns:
            True if sent successfully
        """
        try:
            # Build AppleScript command
            if sound == "default":
                script = f'display notification "{message}" with title "{title}"'
            else:
                script = f'display notification "{message}" with title "{title}" sound name "{sound}"'

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2.0
            )

            if result.returncode == 0:
                logger.info(f"Sent notification: {title}")
                return True
            else:
                logger.warning(f"osascript failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Notification timeout")
            return False
        except Exception as e:
            logger.error(f"macOS notification error: {e}")
            return False

    def _send_notification_linux(self, title: str, message: str) -> bool:
        """
        Send notification on Linux using notify-send.

        Requires: apt-get install libnotify-bin

        Args:
            title: Notification title
            message: Notification message

        Returns:
            True if sent successfully
        """
        try:
            result = subprocess.run(
                ["notify-send", title, message],
                capture_output=True,
                text=True,
                timeout=2.0
            )

            if result.returncode == 0:
                logger.info(f"Sent notification: {title}")
                return True
            else:
                logger.warning(f"notify-send failed: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.error("notify-send not installed (apt-get install libnotify-bin)")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Notification timeout")
            return False
        except Exception as e:
            logger.error(f"Linux notification error: {e}")
            return False
