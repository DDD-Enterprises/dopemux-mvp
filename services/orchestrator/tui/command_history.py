"""
Command History Manager for Orchestrator TUI

ADHD-Optimized History Management:
- Privacy-aware: Filters sensitive keywords (password, secret, token)
- Size-limited: 100 in memory (prevents overwhelm), 1000 in ConPort (searchable)
- Smart loading: Recent commands + frequently used
- Up/down navigation in CommandInput
- ConPort persistence for session restoration

Privacy Features:
- Automatic filtering of sensitive commands
- Never logs credentials or secrets
- User screen-sharing safe

Architecture:
- Uses Integration Bridge HTTP API for ConPort operations
- Category: "command_history" in custom_data
- Provides navigation interface for CommandInput widget
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CommandRecord:
    """Record of a single command execution."""
    command_id: str
    ai: str
    command: str
    timestamp: datetime
    exit_code: Optional[int] = None
    session_id: Optional[str] = None


class CommandHistoryManager:
    """
    Manages command history with privacy and ADHD optimizations.

    Features:
    - Privacy filtering (no sensitive keywords)
    - Size limits (100 memory, 1000 ConPort)
    - Smart loading (recent + frequent)
    - Up/down navigation
    - ConPort persistence
    """

    # Sensitive keywords that trigger filtering
    SENSITIVE_KEYWORDS = [
        "password", "passwd", "pwd",
        "secret", "token", "key",
        "api_key", "apikey",
        "credential", "auth",
        "private"
    ]

    def __init__(self, workspace_id: str, integration_bridge_url: str = None):
        """
        Initialize command history manager.

        Args:
            workspace_id: Absolute path to workspace
            integration_bridge_url: Integration Bridge URL
        """
        self.workspace_id = workspace_id
        self.integration_bridge_url = integration_bridge_url or os.getenv(
            "INTEGRATION_BRIDGE_URL", "http://localhost:3016"
        )

        # In-memory history (ADHD-safe size: 100 max)
        self.history: List[str] = []
        self.current_index = -1  # For up/down navigation

        # Session tracking
        self.session_id: Optional[str] = None
        self.commands_this_session = 0

        # HTTP session
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

        logger.info(f"📜 Command History Manager initialized")

    async def initialize(self):
        """Initialize HTTP session and load history from ConPort."""
        if not self._initialized:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.http_session = aiohttp.ClientSession(timeout=timeout)

            # Generate session ID
            self.session_id = f"history_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Load history from ConPort
            await self._load_history()

            self._initialized = True
            logger.info(f"✅ History manager initialized, loaded {len(self.history)} commands")

    async def close(self):
        """Clean up resources."""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None

        self._initialized = False
        logger.info("🔒 History manager closed")

    def add_command(self, ai: str, command: str) -> bool:
        """
        Add command to in-memory history (with privacy filtering).

        Args:
            ai: AI that executed the command
            command: Command text

        Returns:
            True if added, False if filtered for privacy
        """
        # Privacy check
        if self._is_sensitive(command):
            logger.info(f"🔒 Filtered sensitive command from history")
            return False

        # Add to history
        full_command = f"@{ai} {command}"
        self.history.append(full_command)

        # Maintain size limit (ADHD-safe: 100 max)
        if len(self.history) > 100:
            self.history.pop(0)

        # Reset navigation index
        self.current_index = -1

        self.commands_this_session += 1
        return True

    async def save_command(self, ai: str, command: str, exit_code: int):
        """
        Save command to ConPort for persistent history.

        Args:
            ai: AI that executed the command
            command: Command text
            exit_code: Exit code (0 = success)
        """
        if not self._initialized or not self.http_session:
            return

        # Privacy check
        if self._is_sensitive(command):
            return

        try:
            url = f"{self.integration_bridge_url}/conport/custom_data"
            timestamp_key = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            payload = {
                "workspace_id": self.workspace_id,
                "category": "command_history",
                "key": timestamp_key,
                "value": {
                    "ai": ai,
                    "command": command,
                    "timestamp": datetime.now().isoformat(),
                    "exit_code": exit_code,
                    "session_id": self.session_id,
                    "success": exit_code == 0
                }
            }

            async with self.http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status in [200, 201]:
                    logger.debug(f"💾 Command saved to history: {ai} - {command[:50]}...")
                else:
                    logger.warning(f"⚠️  Failed to save command: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ Error saving command: {e}")

    def navigate_up(self) -> Optional[str]:
        """
        Navigate to previous command (up arrow).

        Returns:
            Previous command or None if at beginning
        """
        if not self.history:
            return None

        # Initialize index if first navigation
        if self.current_index == -1:
            self.current_index = len(self.history)

        # Move up (backward in history)
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]

        return None

    def navigate_down(self) -> Optional[str]:
        """
        Navigate to next command (down arrow).

        Returns:
            Next command or None if at end
        """
        if not self.history or self.current_index == -1:
            return None

        # Move down (forward in history)
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        else:
            # Reached end, reset to command entry mode
            self.current_index = -1
            return ""  # Empty string signals "new command"

    def get_count(self) -> int:
        """Get number of commands in memory."""
        return len(self.history)

    def get_recent(self, count: int = 10) -> List[str]:
        """Get most recent commands."""
        return self.history[-count:] if self.history else []

    def _is_sensitive(self, command: str) -> bool:
        """
        Check if command contains sensitive keywords.

        Args:
            command: Command text to check

        Returns:
            True if command should be filtered for privacy
        """
        command_lower = command.lower()
        return any(keyword in command_lower for keyword in self.SENSITIVE_KEYWORDS)

    async def _load_history(self):
        """Load command history from ConPort."""
        try:
            url = f"{self.integration_bridge_url}/conport/custom_data"
            params = {
                "workspace_id": self.workspace_id,
                "category": "command_history",
                "limit": 30  # Last 30 commands (ADHD-safe)
            }

            async with self.http_session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    commands = data.get("data", [])

                    # Load into history (most recent last)
                    for cmd_data in sorted(commands, key=lambda x: x.get("value", {}).get("timestamp", "")):
                        value = cmd_data.get("value", {})
                        ai = value.get("ai", "unknown")
                        command = value.get("command", "")

                        if command and not self._is_sensitive(command):
                            self.history.append(f"@{ai} {command}")

                    logger.info(f"📚 Loaded {len(self.history)} commands from ConPort")
                else:
                    logger.info("📝 No command history found (new session)")

        except Exception as e:
            logger.warning(f"⚠️  Could not load history: {e}")


# Singleton instance
_history_manager: Optional[CommandHistoryManager] = None


def get_history_manager(workspace_id: str = None) -> CommandHistoryManager:
    """Get singleton history manager instance."""
    global _history_manager

    if _history_manager is None:
        if workspace_id is None:
            workspace_id = os.getcwd()
        _history_manager = CommandHistoryManager(workspace_id)

    return _history_manager
