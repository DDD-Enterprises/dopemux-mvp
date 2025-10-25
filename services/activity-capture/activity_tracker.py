"""
Activity Tracker - Session and Activity Aggregation

Tracks development sessions with 5-minute aggregation windows.
Logs aggregated activity to ADHD Engine for energy/attention assessment.

Session Tracking:
- Start session: When workspace switches TO dopemux
- End session: When workspace switches FROM dopemux (or 5-min window elapses)
- Interruptions: Workspace switches during active session

Activity Logging:
- Every 5 minutes (or on session end)
- Aggregates: duration, interruptions, complexity
- Sends to ADHD Engine via HTTP client

ADHD Optimization:
- Automatic tracking (zero manual overhead)
- Real-time interruption detection
- Focus session duration measurement
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ActivityTracker:
    """
    Tracks development activity sessions and aggregates for ADHD Engine.

    Features:
    - Session start/end tracking
    - 5-minute aggregation windows
    - Interruption counting
    - Automatic ADHD Engine logging
    """

    def __init__(
        self,
        adhd_client: Any,
        aggregation_window_seconds: int = 300  # 5 minutes
    ):
        """
        Initialize activity tracker.

        Args:
            adhd_client: ADHDEngineClient instance
            aggregation_window_seconds: Window size for aggregation (default: 300s = 5min)
        """
        self.adhd_client = adhd_client
        self.aggregation_window_seconds = aggregation_window_seconds

        # Current session state
        self.session_active = False
        self.session_start_time: Optional[float] = None
        self.session_interruptions = 0

        # Metrics
        self.sessions_tracked = 0
        self.activities_logged = 0
        self.logging_errors = 0

        # Background task
        self.window_task: Optional[asyncio.Task] = None
        self.running = False

    async def start_session(self):
        """
        Start a new activity session.

        Called when workspace switches TO dopemux workspace.
        """
        logger.debug(f"start_session() called (active: {self.session_active})")

        if self.session_active:
            # Already in session, might be redundant event
            logger.debug("Session already active, skipping")
            return

        self.session_active = True
        self.session_start_time = time.time()
        self.session_interruptions = 0
        self.sessions_tracked += 1

        logger.info(f"📍 Session started (#{self.sessions_tracked})")

        # Start aggregation window timer if not running
        if not self.running:
            self.running = True
            self.window_task = asyncio.create_task(self._aggregation_window_loop())

    async def end_session(self, interruption: bool = False):
        """
        End current activity session and log to ADHD Engine.

        Called when workspace switches FROM dopemux workspace or window elapses.

        Args:
            interruption: Whether session ended due to interruption
        """
        if not self.session_active:
            logger.debug("No active session to end")
            return

        # Calculate session duration
        duration_seconds = time.time() - self.session_start_time if self.session_start_time else 0
        duration_minutes = int(duration_seconds / 60)

        # Only log if session was meaningful (> 1 minute)
        if duration_minutes >= 1:
            await self._log_activity(
                duration_minutes=duration_minutes,
                interruptions=self.session_interruptions + (1 if interruption else 0),
                complexity=0.5,  # Default for MVP
                activity_type="coding"
            )

            logger.info(
                f"📤 Session ended: {duration_minutes}min, "
                f"{self.session_interruptions} interruptions, "
                f"{'interrupted' if interruption else 'clean exit'}"
            )
        else:
            logger.debug(f"Session too short ({duration_seconds:.0f}s), not logging")

        # Reset session
        self.session_active = False
        self.session_start_time = None
        self.session_interruptions = 0

    async def record_interruption(self):
        """
        Record an interruption during active session.

        Called when workspace switches while session is active.
        """
        if not self.session_active:
            return

        self.session_interruptions += 1
        logger.debug(f"🔔 Interruption #{self.session_interruptions} recorded")

    async def _log_activity(
        self,
        duration_minutes: int,
        interruptions: int,
        complexity: float,
        activity_type: str
    ):
        """
        Log activity to ADHD Engine.

        Args:
            duration_minutes: Session duration
            interruptions: Number of interruptions
            complexity: Task complexity (0.0-1.0)
            activity_type: Type of activity (coding/reviewing/debugging)
        """
        try:
            success = await self.adhd_client.log_activity(
                activity_type=activity_type,
                duration_minutes=duration_minutes,
                complexity=complexity,
                interruptions=interruptions
            )

            if success:
                self.activities_logged += 1
                logger.info(
                    f"✅ Activity logged to ADHD Engine "
                    f"({duration_minutes}min, {interruptions} interruptions)"
                )
            else:
                self.logging_errors += 1
                logger.warning("⚠️ Failed to log activity to ADHD Engine")

        except Exception as e:
            self.logging_errors += 1
            logger.error(f"Activity logging error: {e}")

    async def _aggregation_window_loop(self):
        """
        Background task that logs activity every N seconds if session active.

        This ensures long sessions get logged periodically, not just on end.
        """
        while self.running:
            try:
                await asyncio.sleep(self.aggregation_window_seconds)

                # If session is active and window elapsed, log partial activity
                if self.session_active and self.session_start_time:
                    duration_seconds = time.time() - self.session_start_time
                    duration_minutes = int(duration_seconds / 60)

                    if duration_minutes >= 5:  # Only log if meaningful duration
                        await self._log_activity(
                            duration_minutes=duration_minutes,
                            interruptions=self.session_interruptions,
                            complexity=0.5,
                            activity_type="coding"
                        )

                        # Reset session for next window
                        logger.info(f"🔄 Window completed, starting new window")
                        self.session_start_time = time.time()
                        self.session_interruptions = 0

            except asyncio.CancelledError:
                logger.info("⏹️ Aggregation window loop cancelled")
                break
            except Exception as e:
                logger.error(f"Aggregation window error: {e}")
                await asyncio.sleep(10)

    async def flush_all(self):
        """
        Flush any pending activity on shutdown.

        Ensures no data is lost when service stops.
        """
        if self.session_active:
            logger.info("💾 Flushing pending session on shutdown")
            await self.end_session(interruption=False)

    def get_current_session_duration(self) -> int:
        """
        Get current session duration in minutes.

        Returns:
            Duration in minutes, or 0 if no active session
        """
        if not self.session_active or not self.session_start_time:
            return 0

        duration_seconds = time.time() - self.session_start_time
        return int(duration_seconds / 60)

    def get_metrics(self) -> Dict[str, Any]:
        """Get tracker metrics"""
        return {
            "sessions_tracked": self.sessions_tracked,
            "activities_logged": self.activities_logged,
            "logging_errors": self.logging_errors,
            "session_active": self.session_active,
            "current_session_duration_minutes": self.get_current_session_duration(),
            "current_session_interruptions": self.session_interruptions if self.session_active else 0,
            "aggregation_window_seconds": self.aggregation_window_seconds
        }
