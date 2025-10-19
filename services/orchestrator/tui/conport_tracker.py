"""
ConPort Progress Tracker for Orchestrator TUI

ADHD-Optimized Features:
- Automatic progress logging for all AI command executions
- Real-time progress updates to ConPort via Integration Bridge
- Session context preservation for interrupt recovery
- Visual progress feedback integration

Architecture:
- Uses Integration Bridge HTTP API (port 3016) for ConPort operations
- Tracks progress_entry items for each command
- Links commands to active TUI session
- Provides progress data for ProgressTrackerPane display
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CommandProgress:
    """Progress tracking for a single AI command execution"""
    progress_id: Optional[int] = None
    ai_name: str = ""
    command: str = ""
    status: str = "TODO"  # TODO, IN_PROGRESS, DONE, BLOCKED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


class ConPortProgressTracker:
    """
    Tracks TUI command execution progress in ConPort.

    Features:
    - Automatic progress_entry creation for commands
    - Real-time status updates (TODO → IN_PROGRESS → DONE)
    - Session context preservation
    - Progress statistics for ProgressTrackerPane
    """

    def __init__(self, workspace_id: str, integration_bridge_url: str = None):
        """
        Initialize ConPort progress tracker.

        Args:
            workspace_id: Absolute path to workspace (/Users/hue/code/dopemux-mvp)
            integration_bridge_url: Integration Bridge URL (default: http://localhost:3016)
        """
        self.workspace_id = workspace_id
        self.integration_bridge_url = integration_bridge_url or os.getenv(
            "INTEGRATION_BRIDGE_URL", "http://localhost:3016"
        )

        # Session tracking
        self.session_id: Optional[str] = None
        self.session_start: datetime = datetime.now()

        # Command tracking
        self.active_commands: Dict[str, CommandProgress] = {}  # ai_name -> CommandProgress
        self.command_history: List[CommandProgress] = []

        # HTTP session
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

        logger.info(f"📊 ConPort Progress Tracker initialized for {workspace_id}")

    async def initialize(self):
        """Initialize HTTP session and load session context."""
        if not self._initialized:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.http_session = aiohttp.ClientSession(timeout=timeout)

            # Load active context from ConPort
            await self._load_active_context()

            # Create session progress entry
            await self._create_session_entry()

            self._initialized = True
            logger.info("✅ ConPort tracker initialized and session context loaded")

    async def close(self):
        """Clean up resources and finalize session."""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None

        # Mark session as complete
        if self.session_id:
            await self._complete_session()

        self._initialized = False
        logger.info("🔒 ConPort tracker closed, session finalized")

    async def log_command_start(self, ai_name: str, command: str) -> Optional[int]:
        """
        Log command execution start to ConPort.

        Args:
            ai_name: AI executing the command (claude/gemini/grok)
            command: Command being executed

        Returns:
            progress_id from ConPort or None on failure
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Create progress_entry in ConPort
            description = f"[{ai_name.upper()}] {command[:100]}"  # Truncate long commands

            url = f"{self.integration_bridge_url}/conport/progress"
            payload = {
                "workspace_id": self.workspace_id,
                "status": "IN_PROGRESS",
                "description": description,
                "linked_item_id": self.session_id,
                "linked_item_type": "custom_data",
                "link_relationship_type": "relates_to_session"
            }

            async with self.http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    progress_id = result.get("id")

                    # Track locally
                    cmd_progress = CommandProgress(
                        progress_id=progress_id,
                        ai_name=ai_name,
                        command=command,
                        status="IN_PROGRESS",
                        started_at=datetime.now()
                    )
                    self.active_commands[ai_name] = cmd_progress

                    logger.info(f"📝 Logged command start: {ai_name} - {command[:50]}... (ID: {progress_id})")
                    return progress_id
                else:
                    logger.warning(f"⚠️ Failed to log command start: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error logging command start: {e}")
            return None

    async def update_command_progress(self, ai_name: str, status: str, exit_code: Optional[int] = None, error_message: Optional[str] = None):
        """
        Update command execution status in ConPort.

        Args:
            ai_name: AI that was executing
            status: New status (IN_PROGRESS/DONE/BLOCKED)
            exit_code: Command exit code (0 = success, non-zero = failure)
            error_message: Error message if command failed
        """
        if not self._initialized:
            return

        cmd_progress = self.active_commands.get(ai_name)
        if not cmd_progress or not cmd_progress.progress_id:
            logger.warning(f"⚠️ No active command found for {ai_name}")
            return

        try:
            # Update progress_entry in ConPort
            url = f"{self.integration_bridge_url}/conport/progress/{cmd_progress.progress_id}"
            payload = {
                "workspace_id": self.workspace_id,
                "status": status
            }

            async with self.http_session.patch(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    # Update local tracking
                    cmd_progress.status = status
                    cmd_progress.exit_code = exit_code
                    cmd_progress.error_message = error_message

                    if status in ["DONE", "BLOCKED"]:
                        cmd_progress.completed_at = datetime.now()
                        self.command_history.append(cmd_progress)
                        del self.active_commands[ai_name]

                    logger.info(f"✅ Updated command status: {ai_name} → {status}")
                else:
                    logger.warning(f"⚠️ Failed to update command: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ Error updating command progress: {e}")

    async def get_progress_stats(self) -> Dict[str, Any]:
        """
        Get current progress statistics for UI display.

        Returns:
            Dictionary with progress stats:
            - active_commands: Number of commands in progress
            - completed_commands: Total completed this session
            - success_rate: Percentage of successful commands
            - session_duration_minutes: Time since session start
        """
        session_duration = (datetime.now() - self.session_start).total_seconds() / 60

        completed = len(self.command_history)
        successful = sum(1 for cmd in self.command_history if cmd.exit_code == 0)
        success_rate = (successful / completed * 100) if completed > 0 else 0.0

        return {
            "active_commands": len(self.active_commands),
            "completed_commands": completed,
            "successful_commands": successful,
            "success_rate": success_rate,
            "session_duration_minutes": int(session_duration),
            "session_start": self.session_start.isoformat()
        }

    async def _load_active_context(self):
        """Load active context from ConPort for session restoration."""
        try:
            url = f"{self.integration_bridge_url}/conport/active_context"
            params = {"workspace_id": self.workspace_id}

            async with self.http_session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    context = await response.json()
                    logger.info(f"🧠 Loaded active context: {context.get('current_focus', 'Unknown')}")
                    # Could restore previous session state here if needed
                else:
                    logger.info("📝 No previous active context found (new session)")

        except Exception as e:
            logger.warning(f"⚠️ Could not load active context: {e}")

    async def _create_session_entry(self):
        """Create custom_data entry for this TUI session."""
        try:
            url = f"{self.integration_bridge_url}/conport/custom_data"

            # Use timestamp as session ID
            self.session_id = f"tui_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            payload = {
                "workspace_id": self.workspace_id,
                "category": "tui_sessions",
                "key": self.session_id,
                "value": {
                    "started_at": self.session_start.isoformat(),
                    "workspace": self.workspace_id,
                    "status": "active"
                }
            }

            async with self.http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status in [200, 201]:
                    logger.info(f"📝 Created TUI session entry: {self.session_id}")

        except Exception as e:
            logger.warning(f"⚠️ Could not create session entry: {e}")

    async def _complete_session(self):
        """Mark TUI session as complete in ConPort."""
        if not self.session_id:
            return

        try:
            # Update session with completion info
            stats = await self.get_progress_stats()

            url = f"{self.integration_bridge_url}/conport/custom_data"
            payload = {
                "workspace_id": self.workspace_id,
                "category": "tui_sessions",
                "key": self.session_id,
                "value": {
                    "started_at": self.session_start.isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "workspace": self.workspace_id,
                    "status": "completed",
                    "statistics": stats
                }
            }

            async with self.http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Session completed: {stats['completed_commands']} commands executed")

        except Exception as e:
            logger.warning(f"⚠️ Could not complete session: {e}")


# Singleton instance
_tracker: Optional[ConPortProgressTracker] = None


def get_progress_tracker(workspace_id: str = None) -> ConPortProgressTracker:
    """Get singleton progress tracker instance."""
    global _tracker

    if _tracker is None:
        if workspace_id is None:
            workspace_id = os.getcwd()
        _tracker = ConPortProgressTracker(workspace_id)

    return _tracker
