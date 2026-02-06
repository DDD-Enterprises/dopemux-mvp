"""
Activity Tracker for ADHD Engine Integration

Tracks development activity and sends to ADHD Engine for accommodation adjustments.
"""

import asyncio
import json
import logging
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

    async def handle_workspace_switch(self, event_data: dict):
        """Handle workspace switch event."""
        logger.info(f"Workspace switch: {event_data}")

        self.workspace_switches += 1

        # Record activity
        activity = {
            "type": "workspace_switch",
            "timestamp": time.time(),
            "from_workspace": event_data.get("from_workspace"),
            "to_workspace": event_data.get("to_workspace"),
            "from_app": event_data.get("from_app"),
            "to_app": event_data.get("to_app"),
            "file_activity": event_data.get("file_activity", {})
        }

        self.pending_activities.append(activity)

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

    async def handle_session_start(self, event_data: dict):
        """Handle session start event."""
        logger.info(f"Session started: {event_data}")

        self.current_session = event_data.get("session_id", "unknown")
        self.session_start_time = time.time()

        # Reset counters for new session
        self.workspace_switches = 0
        self.task_updates = 0
        self.break_events = 0
        self.pending_activities = []

    async def handle_break_taken(self, event_data: dict):
        """Handle break taken event."""
        logger.info(f"Break taken: {event_data}")

        self.break_events += 1

        # Record break activity
        activity = {
            "type": "break_taken",
            "timestamp": time.time(),
            "duration_minutes": event_data.get("duration_minutes", 5),
            "reason": event_data.get("reason", "scheduled")
        }

        self.pending_activities.append(activity)

        # Send break data to ADHD Engine immediately
        await self.adhd_client.send_activity_data({
            "type": "break_taken",
            "session_id": self.current_session,
            "break_duration": activity["duration_minutes"],
            "timestamp": activity["timestamp"]
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
            "session_id": self.current_session,
            "time_window_seconds": self.aggregation_window_seconds,
            "session_duration_minutes": session_duration / 60,
            "workspace_switches": self.workspace_switches,
            "task_updates": self.task_updates,
            "break_events": self.break_events,
            "total_activities": len(self.pending_activities),
            "timestamp": time.time()
        }

        # Send to ADHD Engine
        try:
            await self.adhd_client.send_activity_data(activity_summary)
            logger.info(f"Sent activity summary: {activity_summary}")

            # Clear pending activities after successful send
            self.pending_activities = []

        except Exception as e:
            logger.error(f"Failed to send activity data: {e}")

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
            "last_aggregation_time": self.last_aggregation_time
        }