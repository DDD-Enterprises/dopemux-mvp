"""
DNDManager - Do Not Disturb automation for macOS and Slack.

Handles:
- macOS Focus Mode activation/deactivation via AppleScript
- Slack status updates ("In focus mode until...")
- Window management via Desktop Commander
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class DNDManager:
    """
    Manages Do Not Disturb across macOS and Slack.

    Phase 1: macOS Focus Mode + Slack status
    Phase 2: Desktop Commander window management
    """

    def __init__(
        self,
        slack_client=None,         # TODO: Import SlackClient
        desktop_commander=None,    # TODO: Import DesktopCommanderClient
        config=None
    ):
        self.slack = slack_client
        self.desktop = desktop_commander
        self.config = config

        # State
        self.focus_mode_enabled = False
        self.slack_status_set = False

    async def enable_macos_focus_mode(self):
        """Enable macOS Focus Mode via AppleScript."""
        logger.info("Enabling macOS Focus Mode...")

        # TODO: Test AppleScript on actual macOS system
        script = """
        tell application "System Events"
            tell process "ControlCenter"
                set focusMode to menu bar item "Focus" of menu bar 1
                click focusMode
                click menu item "Work" of menu 1 of focusMode
            end tell
        end tell
        """

        try:
            result = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error(f"Failed to enable macOS Focus Mode: {stderr.decode()}")

                # Fallback: Use Desktop Commander to minimize windows
                if self.desktop:
                    await self.desktop.minimize_non_essential_windows()
            else:
                self.focus_mode_enabled = True
                logger.info("✅ macOS Focus Mode enabled")

        except Exception as e:
            logger.error(f"Exception enabling Focus Mode: {e}", exc_info=True)

    async def disable_macos_focus_mode(self):
        """Disable macOS Focus Mode."""
        if not self.focus_mode_enabled:
            return

        logger.info("Disabling macOS Focus Mode...")

        script = """
        tell application "System Events"
            tell process "ControlCenter"
                set focusMode to menu bar item "Focus" of menu bar 1
                click focusMode
                click menu item "Off" of menu 1 of focusMode
            end tell
        end tell
        """

        try:
            await self._run_applescript(script)
            self.focus_mode_enabled = False
            logger.info("✅ macOS Focus Mode disabled")

        except Exception as e:
            logger.error(f"Exception disabling Focus Mode: {e}", exc_info=True)

    async def set_slack_status(self, status: str, until: datetime):
        """Set Slack status with expiration."""
        if not self.slack:
            logger.warning("Slack client not configured, skipping status update")
            return

        logger.info(f"Setting Slack status: '{status}' until {until}")

        try:
            expiration_timestamp = int(until.timestamp())

            # TODO: Implement with actual Slack client
            # await self.slack.users_profile_set(
            #     profile={
            #         "status_text": status,
            #         "status_emoji": ":no_entry_sign:",
            #         "status_expiration": expiration_timestamp
            #     }
            # )

            # Also set presence to "away"
            # await self.slack.users_setPresence(presence="away")

            self.slack_status_set = True
            logger.info("✅ Slack status updated")

        except Exception as e:
            logger.error(f"Failed to set Slack status: {e}", exc_info=True)

    async def clear_slack_status(self):
        """Clear Slack status and set presence to active."""
        if not self.slack or not self.slack_status_set:
            return

        logger.info("Clearing Slack status...")

        try:
            # TODO: Implement with actual Slack client
            # await self.slack.users_profile_set(
            #     profile={
            #         "status_text": "",
            #         "status_emoji": "",
            #         "status_expiration": 0
            #     }
            # )

            # await self.slack.users_setPresence(presence="auto")

            self.slack_status_set = False
            logger.info("✅ Slack status cleared")

        except Exception as e:
            logger.error(f"Failed to clear Slack status: {e}", exc_info=True)

    async def _run_applescript(self, script: str):
        """Execute AppleScript and return result."""
        result = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await result.communicate()

        if result.returncode != 0:
            raise Exception(f"AppleScript failed: {stderr.decode()}")

        return stdout.decode()
