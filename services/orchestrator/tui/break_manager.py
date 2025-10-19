"""
Pomodoro Break Manager for Orchestrator TUI

ADHD-Optimized Break System:
- Elapsed timer (count up) instead of countdown (reduces anxiety)
- Color-coded status: green → yellow → red
- Gentle break suggestions (not enforcement)
- ConPort logging for pattern learning
- Configurable work/break durations

Research-Backed Design:
- Elapsed timers reduce ADHD deadline anxiety vs countdown
- Visual progression creates positive momentum
- Autonomy-respecting (suggests, doesn't force)
- Pattern tracking enables personalized optimization

Architecture:
- Uses Integration Bridge HTTP API for ConPort logging
- Tracks break compliance for self-awareness
- Provides state for ProgressTrackerPane display
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class BreakSession:
    """Record of a single work/break cycle."""
    session_id: str
    work_start: datetime
    work_end: Optional[datetime] = None
    work_duration_minutes: Optional[int] = None
    break_start: Optional[datetime] = None
    break_end: Optional[datetime] = None
    break_duration_minutes: Optional[int] = None
    completed: bool = False
    interrupted: bool = False


class PomodoroBreakManager:
    """
    Manages Pomodoro-style break reminders with ADHD optimizations.

    Features:
    - Elapsed timer (positive framing)
    - Color-coded progress (green/yellow/red)
    - Gentle break suggestions
    - Break compliance tracking
    - ConPort pattern learning
    """

    def __init__(self, workspace_id: str, integration_bridge_url: str = None):
        """
        Initialize break manager.

        Args:
            workspace_id: Absolute path to workspace
            integration_bridge_url: Integration Bridge URL (default: http://localhost:3016)
        """
        self.workspace_id = workspace_id
        self.integration_bridge_url = integration_bridge_url or os.getenv(
            "INTEGRATION_BRIDGE_URL", "http://localhost:3016"
        )

        # Configuration (Pomodoro standard)
        self.work_duration_minutes = 25
        self.short_break_minutes = 5
        self.long_break_minutes = 15
        self.sessions_until_long_break = 4

        # State tracking
        self.session_start: Optional[datetime] = None
        self.last_break: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None
        self.current_session: Optional[BreakSession] = None
        self.session_count = 0
        self.break_sessions: List[BreakSession] = []

        # HTTP session
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

        logger.info(f"⏰ Pomodoro Break Manager initialized")

    async def initialize(self):
        """Initialize HTTP session and start first work session."""
        if not self._initialized:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.http_session = aiohttp.ClientSession(timeout=timeout)

            # Start first work session
            self.start_work_session()

            self._initialized = True
            logger.info("✅ Break manager initialized, work session started")

    async def close(self):
        """Clean up resources and finalize current session."""
        if self.current_session and not self.current_session.completed:
            await self.end_work_session(interrupted=True)

        if self.http_session:
            await self.http_session.close()
            self.http_session = None

        self._initialized = False
        logger.info("🔒 Break manager closed")

    def start_work_session(self):
        """Start a new work session."""
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        self.session_count += 1

        session_id = f"work_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = BreakSession(
            session_id=session_id,
            work_start=self.session_start
        )

        logger.info(f"▶️  Work session {self.session_count} started")

    async def end_work_session(self, interrupted: bool = False):
        """End current work session and log to ConPort."""
        if not self.current_session:
            return

        self.current_session.work_end = datetime.now()
        duration = (self.current_session.work_end - self.current_session.work_start).total_seconds() / 60
        self.current_session.work_duration_minutes = int(duration)
        self.current_session.interrupted = interrupted

        # Log to ConPort
        await self._log_break_session()

        self.break_sessions.append(self.current_session)
        self.current_session = None

    def record_activity(self):
        """Record user activity (resets idle detection)."""
        self.last_activity = datetime.now()

    def get_elapsed_minutes(self) -> int:
        """Get minutes elapsed in current work session."""
        if not self.session_start:
            return 0

        elapsed = (datetime.now() - self.session_start).total_seconds() / 60
        return int(elapsed)

    def get_elapsed_seconds(self) -> int:
        """Get seconds elapsed in current work session."""
        if not self.session_start:
            return 0

        elapsed = (datetime.now() - self.session_start).total_seconds()
        return int(elapsed)

    def get_status_color(self) -> str:
        """
        Get color code based on elapsed time.

        Returns:
            "green" (0-20min) | "yellow" (20-25min) | "red" (25+min)
        """
        elapsed = self.get_elapsed_minutes()

        if elapsed < 20:
            return "green"
        elif elapsed < 25:
            return "yellow"
        else:
            return "red"

    def should_suggest_break(self) -> bool:
        """
        Check if break should be suggested.

        Returns:
            True if >= 25 minutes elapsed
        """
        return self.get_elapsed_minutes() >= self.work_duration_minutes

    def should_mandate_break(self) -> bool:
        """
        Check if break should be mandatory (hyperfocus protection).

        Returns:
            True if >= 50 minutes elapsed (2x Pomodoro)
        """
        return self.get_elapsed_minutes() >= (self.work_duration_minutes * 2)

    def get_break_duration_minutes(self) -> int:
        """
        Get recommended break duration.

        Returns:
            5 minutes (short) or 15 minutes (long, every 4th session)
        """
        if self.session_count % self.sessions_until_long_break == 0:
            return self.long_break_minutes
        else:
            return self.short_break_minutes

    async def get_state_async(self) -> Dict[str, Any]:
        """
        Get current break manager state for UI display.

        Returns:
            Dictionary with timer state, colors, suggestions
        """
        elapsed_minutes = self.get_elapsed_minutes()
        elapsed_seconds = self.get_elapsed_seconds()
        status_color = self.get_status_color()
        break_needed = self.should_suggest_break()
        break_mandatory = self.should_mandate_break()

        return {
            "elapsed_seconds": elapsed_seconds,
            "elapsed_minutes": elapsed_minutes,
            "elapsed_formatted": self._format_elapsed(elapsed_seconds),
            "status_color": status_color,
            "break_suggested": break_needed,
            "break_mandatory": break_mandatory,
            "break_duration_minutes": self.get_break_duration_minutes(),
            "session_count": self.session_count,
            "message": self._get_status_message(elapsed_minutes, status_color)
        }

    def _format_elapsed(self, seconds: int) -> str:
        """Format elapsed time as MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def _get_status_message(self, elapsed: int, color: str) -> str:
        """Get user-friendly status message."""
        if color == "green":
            return f"✅ Focused for {elapsed} min"
        elif color == "yellow":
            return f"⚠️  {elapsed} min - break soon?"
        else:
            return f"🔴 {elapsed} min - break recommended!"

    async def start_break(self, duration_minutes: int = None):
        """Start break period and log to ConPort."""
        if self.current_session:
            await self.end_work_session(interrupted=False)

        self.last_break = datetime.now()

        if duration_minutes is None:
            duration_minutes = self.get_break_duration_minutes()

        logger.info(f"☕ Break started ({duration_minutes} minutes)")

        # After break, start new work session
        # (This would be triggered by user action or timer in real implementation)

    async def _log_break_session(self):
        """Log break session to ConPort for pattern learning."""
        if not self.current_session or not self.http_session:
            return

        try:
            url = f"{self.integration_bridge_url}/conport/custom_data"
            payload = {
                "workspace_id": self.workspace_id,
                "category": "break_sessions",
                "key": self.current_session.session_id,
                "value": {
                    "work_start": self.current_session.work_start.isoformat(),
                    "work_end": self.current_session.work_end.isoformat() if self.current_session.work_end else None,
                    "work_duration_minutes": self.current_session.work_duration_minutes,
                    "completed": self.current_session.completed,
                    "interrupted": self.current_session.interrupted,
                    "session_number": self.session_count
                }
            }

            async with self.http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status in [200, 201]:
                    logger.info(f"💾 Break session logged: {self.current_session.work_duration_minutes} min")
                else:
                    logger.warning(f"⚠️  Failed to log break session: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ Error logging break session: {e}")


# Singleton instance
_break_manager: Optional[PomodoroBreakManager] = None


def get_break_manager(workspace_id: str = None) -> PomodoroBreakManager:
    """Get singleton break manager instance."""
    global _break_manager

    if _break_manager is None:
        if workspace_id is None:
            workspace_id = os.getcwd()
        _break_manager = PomodoroBreakManager(workspace_id)

    return _break_manager
