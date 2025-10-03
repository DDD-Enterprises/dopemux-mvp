"""
Activity Tracker - ConPort Integration via Direct SQLite

Day 3-4: Direct SQLite read-only access to ConPort database
Week 7+: Migrate to ConPort HTTP API service (technical debt)

Provides real user activity data for ADHD assessments from:
- Recent task completion data (progress_entries table)
- Context switch tracking (custom_data table)
- Break compliance metrics (Redis + custom_data)
- User activity patterns (custom_data activity_log)
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .config import settings
from .conport_client import ConPortSQLiteClient

logger = logging.getLogger(__name__)


class ActivityTracker:
    """
    Activity tracking component for ADHD engine.

    Integrates with ConPort SQLite database (read-only) to get real
    task completion and activity data for accurate ADHD assessments.
    """

    def __init__(
        self,
        redis_client,
        conport_db_path: str
    ):
        """
        Initialize activity tracker.

        Args:
            redis_client: Redis client for local state and break tracking
            conport_db_path: Path to ConPort SQLite database
        """
        self.redis = redis_client
        self.conport = ConPortSQLiteClient(
            db_path=conport_db_path,
            workspace_id=settings.workspace_id
        )

        # In-memory cache (5min TTL) to prevent excessive SQLite queries
        self._activity_cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 minutes

    async def get_recent_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Get recent user activity metrics from ConPort + Redis.

        Queries ConPort SQLite for task completion data and combines
        with Redis break tracking for comprehensive activity picture.

        Returns:
            Dict with completion_rate, context_switches, break_compliance, minutes_since_break
        """
        # Check cache first
        cache_key = f"activity:{user_id}"
        if cache_key in self._activity_cache:
            cached_time, cached_data = self._activity_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                logger.debug(f"📦 Cache hit for {user_id} activity")
                return cached_data

        # Query ConPort for recent progress entries (last hour)
        progress_entries = self.conport.get_progress_entries(
            limit=20,
            hours_ago=1
        )

        # Calculate completion rate from real data
        if progress_entries:
            completed = [p for p in progress_entries if p['status'] == 'DONE']
            completion_rate = len(completed) / len(progress_entries)
        else:
            completion_rate = 0.5  # Default if no recent activity

        # Get context switches from custom_data
        activity_log = self.conport.get_custom_data(
            category="activity_log",
            key=f"user_{user_id}"
        )
        context_switches = activity_log.get('context_switches', 0) if activity_log else 0

        # Get last break from Redis
        last_break_str = await self.redis.get(f"adhd:last_break:{user_id}")
        minutes_since_break = self._calculate_minutes_since(last_break_str)

        # Calculate break compliance from Redis break history
        break_history = await self.redis.lrange(f"adhd:breaks:{user_id}", 0, 10)
        break_compliance = self._calculate_break_compliance(break_history)

        result = {
            "completion_rate": completion_rate,
            "context_switches": context_switches,
            "break_compliance": break_compliance,
            "minutes_since_break": minutes_since_break
        }

        # Cache result
        self._activity_cache[cache_key] = (time.time(), result)
        logger.debug(f"📊 Activity metrics for {user_id}: {completion_rate:.1%} completion, {context_switches} switches")

        return result

    async def get_attention_indicators(self, user_id: str) -> Dict[str, Any]:
        """
        Get attention state indicators from activity patterns.

        Analyzes ConPort activity log and task patterns to detect:
        - Context switching frequency
        - Task abandonment patterns
        - Focus duration trends
        - Distraction events

        Returns:
            Dict with context_switches_per_hour, abandoned_tasks, average_focus_duration, distraction_events
        """
        # Get activity log from ConPort
        activity_log = self.conport.get_custom_data(
            category="activity_log",
            key=f"user_{user_id}"
        )

        if activity_log:
            # Parse real activity data
            return {
                "context_switches_per_hour": activity_log.get('context_switches_per_hour', 5),
                "abandoned_tasks": activity_log.get('abandoned_tasks', 1),
                "average_focus_duration": activity_log.get('average_focus_duration', 22),
                "distraction_events": activity_log.get('distraction_events', 3)
            }
        else:
            # Default indicators if no activity log exists yet
            logger.debug(f"No activity log found for {user_id}, using defaults")
            return {
                "context_switches_per_hour": 5,
                "abandoned_tasks": 1,
                "average_focus_duration": 22,
                "distraction_events": 3
            }

    def _calculate_minutes_since(self, timestamp_str: Optional[str]) -> int:
        """Calculate minutes since timestamp."""
        if not timestamp_str:
            return 60  # Default: assume overdue for break

        try:
            last_time = datetime.fromisoformat(timestamp_str)
            delta = datetime.now(timezone.utc) - last_time
            return int(delta.total_seconds() / 60)
        except Exception:
            return 60

    def _calculate_break_compliance(self, break_history: list) -> float:
        """
        Calculate break compliance rate from Redis history.

        Args:
            break_history: List of break event JSON strings

        Returns:
            Compliance rate (0.0-1.0)
        """
        if not break_history:
            return 0.8  # Default compliance

        try:
            import json

            # Parse break events
            breaks = [json.loads(b) for b in break_history if b]

            # Calculate: breaks_taken / breaks_recommended
            if len(breaks) > 0:
                # Simplified: if breaks exist in history, compliance is good
                return 0.9
            return 0.7

        except Exception as e:
            logger.warning(f"Failed to calculate break compliance: {e}")
            return 0.8
