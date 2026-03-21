"""
Activity Tracker for ADHD Engine Integration

Tracks development activity and sends to ADHD Engine for accommodation adjustments.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

def _configure_import_paths() -> Path:
    current = Path(__file__).resolve()
    candidates = [current.parent, *current.parents]
    repo_root = next(
        (
            candidate for candidate in candidates
            if (candidate / "services" / "shared").exists() or (candidate / "src" / "dopemux").exists()
        ),
        current.parent,
    )
    for path in (repo_root, repo_root / "src"):
        path_str = str(path)
        if path.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)
    return repo_root


REPO_ROOT = _configure_import_paths()

from services.shared.brand_voice import StatusChip, brand_log
import time
from collections import defaultdict
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ActivityTracker:
    """
    Tracks development activity and aggregates it for ADHD Engine.

    Aggregates activity over configurable time windows and sends
    comprehensive activity reports to the ADHD Accommodation Engine.
    """

    def __init__(self, adhd_client, aggregation_window_seconds: int = 300):
        """
        Initialize activity tracker.

        Args:
            adhd_client: ADHD Engine API client
            aggregation_window_seconds: Time window for activity aggregation
        """
        self.adhd_client = adhd_client
        self.aggregation_window_seconds = aggregation_window_seconds

        # Activity storage
        self.current_session = None
        self.session_start_time = None
        self.pending_activities: List[Dict[str, Any]] = []

        # Aggregation state
        self.last_aggregation_time = time.time()
        self.workspace_switches = 0
        self.task_updates = 0
        self.break_events = 0
        self.activities_logged = 0
        self.summaries_sent = 0

    async def handle_workspace_switch(self, event_data: dict):
        """Handle workspace switch event."""
        logger.info(brand_log(f"Workspace switch: {event_data}", chip=StatusChip.LIVE))

        self.workspace_switches += 1

        # Record activity
        activity = {
            "type": "workspace_switch",
            "timestamp": time.time(),
            "from_workspace": event_data.get("from_workspace"),
            "to_workspace": event_data.get("to_workspace"),
            "from_app": event_data.get("from_app"),
            "to_app": event_data.get("to_app"),
            "file_activity": event_data.get("file_activity", {}),
        }

        self.pending_activities.append(activity)
        self.activities_logged += 1

        # Check if we should aggregate and send
        await self._check_and_aggregate()

    async def handle_progress_update(self, event_data: dict):
        """Handle progress update event."""
        logger.debug(f"Progress update: {event_data}")

        self.task_updates += 1

        # Record activity
        activity = {
            "type": "progress_update",
            "timestamp": time.time(),
            "task_id": event_data.get("task_id"),
            "status": event_data.get("status"),
            "progress": event_data.get("progress", 0)
        }

        self.pending_activities.append(activity)
        self.activities_logged += 1

    async def handle_session_start(self, event_data: dict):
        """Handle session start event."""
        logger.info(brand_log(f"Session started: {event_data}", chip=StatusChip.LIVE))

        self.current_session = event_data.get("session_id", "unknown")
        self.session_start_time = time.time()

        # Reset counters for new session
        self.workspace_switches = 0
        self.task_updates = 0
        self.break_events = 0
        self.pending_activities = []

    async def handle_break_taken(self, event_data: dict):
        """Handle break taken event."""
        logger.info(brand_log(f"Break taken: {event_data}", chip=StatusChip.LIVE))

        self.break_events += 1

        # Record break activity
        activity = {
            "type": "break_taken",
            "timestamp": time.time(),
            "duration_minutes": event_data.get("duration_minutes", 5),
            "reason": event_data.get("reason", "scheduled")
        }

        self.pending_activities.append(activity)
        self.activities_logged += 1

        # Send break data to ADHD Engine immediately
        await self.adhd_client.send_activity_data({
            "completion_rate": None,
            "context_switches": self.workspace_switches,
            "break_compliance": 1.0,
            "minutes_since_break": 0,
        })

    async def _check_and_aggregate(self):
        """Check if it's time to aggregate and send activity data."""
        current_time = time.time()

        if current_time - self.last_aggregation_time >= self.aggregation_window_seconds:
            await self._aggregate_and_send()
            self.last_aggregation_time = current_time

    async def _aggregate_and_send(self):
        """Aggregate pending activities and send to ADHD Engine."""
        if not self.pending_activities:
            return

        # Calculate session duration
        session_duration = 0
        if self.session_start_time:
            session_duration = time.time() - self.session_start_time

        # Aggregate activity data
        activity_summary = {
            "completion_rate": self._calculate_completion_rate(),
            "context_switches": self.workspace_switches,
            "break_compliance": self._calculate_break_compliance(),
            "minutes_since_break": self._calculate_minutes_since_break(),
        }

        # Send to ADHD Engine
        try:
            await self.adhd_client.send_activity_data(activity_summary)
            logger.info(brand_log(f"Sent activity summary: {activity_summary}", chip=StatusChip.LIVE))
            self.summaries_sent += 1

            # Clear pending activities after successful send
            self.pending_activities = []

        except Exception as e:
            logger.error(brand_log(f"Failed to send activity data: {e}", chip=StatusChip.BLOCKER))

    async def flush_all(self):
        """Flush all pending activities (for shutdown)."""
        if self.pending_activities:
            await self._aggregate_and_send()

    def get_metrics(self) -> Dict[str, Any]:
        """Get activity tracking metrics."""
        session_duration = 0
        if self.session_start_time:
            session_duration = (time.time() - self.session_start_time) / 60

        return {
            "sessions_tracked": 1 if self.current_session else 0,
            "current_session_id": self.current_session,
            "current_session_duration_minutes": session_duration,
            "workspace_switches": self.workspace_switches,
            "task_updates": self.task_updates,
            "break_events": self.break_events,
            "pending_activities": len(self.pending_activities),
            "last_aggregation_time": self.last_aggregation_time,
            "activities_logged": self.activities_logged,
            "session_active": self.current_session is not None,
            "summaries_sent": self.summaries_sent,
        }

    def _calculate_completion_rate(self) -> float:
        total_updates = self.task_updates + self.break_events + self.workspace_switches
        if total_updates <= 0:
            return 0.0
        return min(1.0, self.task_updates / total_updates)

    def _calculate_break_compliance(self) -> float:
        if not self.current_session:
            return 1.0
        expected_breaks = max(1, int(((time.time() - (self.session_start_time or time.time())) / 60) // 60) + 1)
        return min(1.0, self.break_events / expected_breaks)

    def _calculate_minutes_since_break(self) -> int:
        for activity in reversed(self.pending_activities):
            if activity.get("type") == "break_taken":
                return int((time.time() - activity["timestamp"]) / 60)
        if self.session_start_time:
            return int((time.time() - self.session_start_time) / 60)
        return 0
