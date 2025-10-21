#!/usr/bin/env python3
"""
Individual Shield Implementations

Each shield handles a specific type of interruption protection:
- DNDShield: System Do Not Disturb mode
- SlackShield: Slack status updates and notifications
- NotificationShield: System notification filtering
"""

import asyncio
import logging
import platform
import subprocess
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseShield(ABC):
    """Base class for all interruption shields"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def activate(self, reason: str) -> Dict[str, Any]:
        """Activate this shield"""
        pass

    @abstractmethod
    async def deactivate(self, reason: str) -> Dict[str, Any]:
        """Deactivate this shield"""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of this shield"""
        pass

    async def _run_command(self, cmd: list, timeout: int = 10) -> tuple[bool, str]:
        """Run a system command safely"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0, stdout.decode().strip()
        except Exception as e:
            return False, str(e)

class DNDShield(BaseShield):
    """System Do Not Disturb mode shield"""

    def __init__(self):
        super().__init__("dnd")
        self.system = platform.system()

    async def activate(self, reason: str) -> Dict[str, Any]:
        """Activate system Do Not Disturb mode"""
        self.logger.info(f"Activating DND shield: {reason}")

        if self.system == "Darwin":  # macOS
            success, output = await self._run_command([
                "defaults", "write", "com.apple.notificationcenterui",
                "doNotDisturb", "-bool", "true"
            ])
            if success:
                # Also activate through Notification Center
                await self._run_command([
                    "osascript", "-e",
                    'tell application "System Events" to tell process "NotificationCenter" to set the value of menu bar item 1 to true'
                ])

        elif self.system == "Linux":
            # Try various Linux notification systems
            commands = [
                ["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "false"],
                ["notify-send", "--urgency=low", "DND Activated", reason],
            ]
            success = False
            for cmd in commands:
                cmd_success, _ = await self._run_command(cmd)
                if cmd_success:
                    success = True
                    break

        elif self.system == "Windows":
            # Windows Focus Assist/Do Not Disturb
            success, output = await self._run_command([
                "powershell", "-Command",
                "Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 0"
            ])

        else:
            self.logger.warning(f"DND not supported on {self.system}")
            return {"success": False, "error": f"Unsupported system: {self.system}"}

        if success:
            self.logger.info("DND shield activated successfully")
            return {"success": True, "system": self.system}
        else:
            self.logger.error("Failed to activate DND shield")
            return {"success": False, "error": "Command failed"}

    async def deactivate(self, reason: str) -> Dict[str, Any]:
        """Deactivate system Do Not Disturb mode"""
        self.logger.info(f"Deactivating DND shield: {reason}")

        if self.system == "Darwin":  # macOS
            success, output = await self._run_command([
                "defaults", "write", "com.apple.notificationcenterui",
                "doNotDisturb", "-bool", "false"
            ])

        elif self.system == "Linux":
            commands = [
                ["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", "true"],
                ["notify-send", "--urgency=normal", "DND Deactivated", reason],
            ]
            success = False
            for cmd in commands:
                cmd_success, _ = await self._run_command(cmd)
                if cmd_success:
                    success = True
                    break

        elif self.system == "Windows":
            success, output = await self._run_command([
                "powershell", "-Command",
                "Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 1"
            ])

        else:
            return {"success": False, "error": f"Unsupported system: {self.system}"}

        if success:
            self.logger.info("DND shield deactivated successfully")
            return {"success": True, "system": self.system}
        else:
            self.logger.error("Failed to deactivate DND shield")
            return {"success": False, "error": "Command failed"}

    async def get_status(self) -> Dict[str, Any]:
        """Get current DND status"""
        if self.system == "Darwin":
            success, output = await self._run_command([
                "defaults", "read", "com.apple.notificationcenterui", "doNotDisturb"
            ])
            if success:
                active = output.strip() == "1"
                return {"active": active, "system": self.system}

        elif self.system == "Linux":
            success, output = await self._run_command([
                "gsettings", "get", "org.gnome.desktop.notifications", "show-banners"
            ])
            if success:
                active = output.strip() == "false"
                return {"active": active, "system": self.system}

        elif self.system == "Windows":
            success, output = await self._run_command([
                "powershell", "-Command",
                "Get-ItemPropertyValue -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED'"
            ])
            if success:
                active = output.strip() == "0"
                return {"active": active, "system": self.system}

        return {"active": False, "system": self.system, "error": "Unable to determine status"}

class SlackShield(BaseShield):
    """Slack status and notification shield"""

    def __init__(self, token: Optional[str] = None):
        super().__init__("slack")
        self.token = token or self._get_slack_token()

    def _get_slack_token(self) -> Optional[str]:
        """Get Slack token from environment"""
        import os
        return os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_USER_TOKEN")

    async def activate(self, reason: str) -> Dict[str, Any]:
        """Set Slack status to busy/focused"""
        self.logger.info(f"Activating Slack shield: {reason}")

        if not self.token:
            return {"success": False, "error": "No Slack token configured"}

        try:
            # This would integrate with Slack API
            # For now, return success for demonstration
            self.logger.info("Slack shield activated (mock implementation)")
            return {
                "success": True,
                "status": "busy",
                "message": f"Focused work: {reason}",
                "emoji": ":no_entry_sign:"
            }
        except Exception as e:
            self.logger.error(f"Failed to activate Slack shield: {e}")
            return {"success": False, "error": str(e)}

    async def deactivate(self, reason: str) -> Dict[str, Any]:
        """Reset Slack status to available"""
        self.logger.info(f"Deactivating Slack shield: {reason}")

        if not self.token:
            return {"success": False, "error": "No Slack token configured"}

        try:
            # This would integrate with Slack API
            self.logger.info("Slack shield deactivated (mock implementation)")
            return {
                "success": True,
                "status": "available",
                "message": "",
                "emoji": ""
            }
        except Exception as e:
            self.logger.error(f"Failed to deactivate Slack shield: {e}")
            return {"success": False, "error": str(e)}

    async def get_status(self) -> Dict[str, Any]:
        """Get current Slack status"""
        if not self.token:
            return {"configured": False, "error": "No Slack token"}

        try:
            # This would check Slack API for current status
            return {
                "configured": True,
                "active": False,  # Would check if status is set to busy
                "status": "unknown"
            }
        except Exception as e:
            return {"configured": True, "error": str(e)}

class NotificationShield(BaseShield):
    """System notification filtering shield"""

    def __init__(self):
        super().__init__("notifications")
        self.system = platform.system()

    async def activate(self, reason: str) -> Dict[str, Any]:
        """Filter system notifications"""
        self.logger.info(f"Activating notification shield: {reason}")

        if self.system == "Darwin":  # macOS
            # Use Notification Center settings
            success, output = await self._run_command([
                "defaults", "write", "com.apple.notificationcenterui",
                "dndStart", "-date", "`date -u +'%Y-%m-%d %H:%M:%S +000'`"
            ])

        elif self.system == "Linux":
            # Try to pause notifications
            success, output = await self._run_command([
                "dunstctl", "set-paused", "true"
            ])

        elif self.system == "Windows":
            # Windows notification settings
            success, output = await self._run_command([
                "powershell", "-Command",
                "New-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications' -Name 'ToastEnabled' -Value 0 -PropertyType DWord -Force"
            ])

        else:
            return {"success": False, "error": f"Unsupported system: {self.system}"}

        if success:
            self.logger.info("Notification shield activated successfully")
            return {"success": True, "system": self.system}
        else:
            self.logger.error("Failed to activate notification shield")
            return {"success": False, "error": "Command failed"}

    async def deactivate(self, reason: str) -> Dict[str, Any]:
        """Restore system notifications"""
        self.logger.info(f"Deactivating notification shield: {reason}")

        if self.system == "Darwin":  # macOS
            success, output = await self._run_command([
                "defaults", "delete", "com.apple.notificationcenterui", "dndStart"
            ])

        elif self.system == "Linux":
            success, output = await self._run_command([
                "dunstctl", "set-paused", "false"
            ])

        elif self.system == "Windows":
            success, output = await self._run_command([
                "powershell", "-Command",
                "New-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications' -Name 'ToastEnabled' -Value 1 -PropertyType DWord -Force"
            ])

        else:
            return {"success": False, "error": f"Unsupported system: {self.system}"}

        if success:
            self.logger.info("Notification shield deactivated successfully")
            return {"success": True, "system": self.system}
        else:
            self.logger.error("Failed to deactivate notification shield")
            return {"success": False, "error": "Command failed"}

    async def get_status(self) -> Dict[str, Any]:
        """Get current notification filtering status"""
        if self.system == "Darwin":
            success, output = await self._run_command([
                "defaults", "read", "com.apple.notificationcenterui", "dndStart"
            ])
            active = success and output.strip()
            return {"active": bool(active), "system": self.system}

        elif self.system == "Linux":
            success, output = await self._run_command(["dunstctl", "is-paused"])
            if success:
                active = output.strip().lower() == "true"
                return {"active": active, "system": self.system}

        elif self.system == "Windows":
            success, output = await self._run_command([
                "powershell", "-Command",
                "Get-ItemPropertyValue -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications' -Name 'ToastEnabled'"
            ])
            if success:
                active = output.strip() == "0"
                return {"active": active, "system": self.system}

        return {"active": False, "system": self.system, "error": "Unable to determine status"}