#!/usr/bin/env python3
"""
Automatic Snapshots Service for Working Memory Assistant

Implements intelligent background snapshot triggers based on:
- Attention shifts (ADHD Engine monitoring)
- Manual requests (API endpoints)
- Scheduled intervals (time-based policies)

Provides proactive context preservation for ADHD-optimized interrupt recovery.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import signal
import sys

from adhd_engine_client import get_adhd_client, ADHDEngineClient
import redis.asyncio as redis
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool

logger = logging.getLogger(__name__)

@dataclass
class SnapshotTrigger:
    """Represents a snapshot trigger configuration."""
    trigger_type: str  # 'attention_shift', 'manual', 'scheduled'
    user_id: str
    session_id: Optional[str] = None
    priority_threshold: float = 0.5  # Minimum priority score to trigger
    cooldown_seconds: int = 300  # Minimum time between snapshots
    enabled: bool = True

    def should_trigger(self, priority_score: float, last_snapshot_time: Optional[datetime]) -> bool:
        """Check if this trigger should activate."""
        if not self.enabled:
            return False

        # Check priority threshold
        if priority_score < self.priority_threshold:
            return False

        # Check cooldown
        if last_snapshot_time:
            time_since_last = (datetime.now() - last_snapshot_time).total_seconds()
            if time_since_last < self.cooldown_seconds:
                return False

        return True

@dataclass
class SnapshotContext:
    """Context data for snapshot creation."""
    user_id: str
    session_id: str
    trigger_type: str
    priority_score: float
    adhd_context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AutomaticSnapshotsService:
    """Service for automatic context snapshot creation."""

    def __init__(self, db_pool, redis_client: redis.Redis, adhd_client: ADHDEngineClient):
        self.db_pool = db_pool
        self.redis = redis_client
        self.adhd_client = adhd_client

        # Monitoring state
        self.active_triggers: Dict[str, SnapshotTrigger] = {}
        self.last_snapshot_times: Dict[str, datetime] = {}
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Configuration
        self.monitoring_interval = 30  # seconds between checks
        self.max_concurrent_snapshots = 3

    async def start_monitoring(self):
        """Start the automatic snapshot monitoring service."""
        if self.monitoring_active:
            logger.warning("Automatic snapshots monitoring already active")
            return

        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Automatic snapshots monitoring started")

    async def stop_monitoring(self):
        """Stop the automatic snapshot monitoring service."""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Automatic snapshots monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop for automatic snapshots."""
        while self.monitoring_active:
            try:
                await self._check_all_triggers()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _check_all_triggers(self):
        """Check all active triggers for snapshot opportunities."""
        if not self.active_triggers:
            return

        # Get unique user IDs to monitor
        user_ids = set(trigger.user_id for trigger in self.active_triggers.values())

        # Check ADHD metrics for each user
        for user_id in user_ids:
            try:
                # Get ADHD-based snapshot decision
                adhd_decision = await self.adhd_client.should_snapshot_based_on_adhd(user_id)

                if adhd_decision.get("should_snapshot"):
                    priority_score = adhd_decision.get("priority_score", 0.0)
                    await self._evaluate_triggers_for_user(user_id, priority_score, "attention_shift")

            except Exception as e:
                logger.warning(f"Failed to check ADHD triggers for {user_id}: {e}")

        # Check scheduled triggers
        await self._check_scheduled_triggers()

    async def _evaluate_triggers_for_user(self, user_id: str, priority_score: float, trigger_type: str):
        """Evaluate all triggers for a user and create snapshots if needed."""
        user_triggers = [
            trigger for trigger in self.active_triggers.values()
            if trigger.user_id == user_id and trigger.trigger_type == trigger_type
        ]

        for trigger in user_triggers:
            last_snapshot = self.last_snapshot_times.get(f"{user_id}:{trigger.trigger_type}")

            if trigger.should_trigger(priority_score, last_snapshot):
                # Create automatic snapshot
                await self._create_automatic_snapshot(trigger, priority_score)
                break  # Only one snapshot per trigger evaluation

    async def _create_automatic_snapshot(self, trigger: SnapshotTrigger, priority_score: float):
        """Create an automatic snapshot for the given trigger."""
        try:
            # Get comprehensive context
            adhd_context = await self.adhd_client.get_comprehensive_adhd_context(trigger.user_id)

            # Create snapshot context
            context = SnapshotContext(
                user_id=trigger.user_id,
                session_id=trigger.session_id or f"auto_{int(time.time())}",
                trigger_type=trigger.trigger_type,
                priority_score=priority_score,
                adhd_context=adhd_context,
                metadata={
                    "automatic": True,
                    "trigger_type": trigger.trigger_type,
                    "priority_score": priority_score,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Create the snapshot
            snapshot_id = await self._execute_snapshot_creation(context)

            # Update last snapshot time
            self.last_snapshot_times[f"{trigger.user_id}:{trigger.trigger_type}"] = datetime.now()

            logger.info(f"Created automatic snapshot {snapshot_id} for {trigger.user_id} "
                       f"(trigger: {trigger.trigger_type}, priority: {priority_score:.2f})")

        except Exception as e:
            logger.error(f"Failed to create automatic snapshot for {trigger.user_id}: {e}")

    async def _execute_snapshot_creation(self, context: SnapshotContext) -> str:
        """Execute the actual snapshot creation via API call."""
        # This would make an internal API call to the WMA snapshot endpoint
        # For now, we'll simulate by directly calling the database

        snapshot_data = {
            'mental_model': f'Automatic snapshot triggered by {context.trigger_type}',
            'active_focus': {'trigger': context.trigger_type, 'priority': context.priority_score},
            'current_task': f'Context preservation due to {context.trigger_type} trigger'
        }

        # Prepare metadata
        metadata = context.metadata or {}
        if context.adhd_context:
            metadata['adhd_snapshot_priority'] = context.adhd_context.get('snapshot_priority', {})
            metadata['attention_state'] = context.adhd_context.get('metrics', {}).get('attention_state', {})

        # Create snapshot in database
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cursor:
                # Insert into wma_context_snapshots table
                cursor.execute("""
                    INSERT INTO wma_context_snapshots (
                        workspace_id, snapshot_id, user_id, session_id,
                        context_type, emotional_weight, complexity_score,
                        snapshot_data, snapshot_size_bytes,
                        attention_state, energy_level, cognitive_load,
                        metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    "default_workspace",
                    f"snapshot_auto_{int(time.time())}_{context.trigger_type[:8]}",
                    context.user_id,
                    context.session_id,
                    context.trigger_type,
                    0.5,  # neutral emotional weight
                    0.5,  # neutral complexity
                    json.dumps(snapshot_data),
                    len(json.dumps(snapshot_data)),
                    metadata.get('attention_state', {}).get('current_state', 'unknown'),
                    0.5,  # neutral energy level
                    0.5,  # neutral cognitive load
                    json.dumps(metadata)
                ))

                result = cursor.fetchone()
                conn.commit()
                return str(result[0])

        finally:
            self.db_pool.putconn(conn)

    async def _check_scheduled_triggers(self):
        """Check and execute scheduled snapshot triggers."""
        # This would implement time-based triggers
        # For now, we'll implement a simple time-based check

        current_hour = datetime.now().hour

        # Check for users with scheduled triggers
        for trigger_key, trigger in self.active_triggers.items():
            if trigger.trigger_type == 'scheduled':
                # Simple hourly trigger for demo
                if current_hour in [9, 12, 15, 18]:  # Every 3 hours during work hours
                    last_snapshot = self.last_snapshot_times.get(trigger_key)
                    if not last_snapshot or (datetime.now() - last_snapshot).total_seconds() > 3600:  # 1 hour cooldown
                        await self._create_automatic_snapshot(trigger, 0.6)  # Medium priority for scheduled

    # Public API methods

    async def register_trigger(self, trigger: SnapshotTrigger):
        """Register a new snapshot trigger."""
        trigger_key = f"{trigger.user_id}:{trigger.trigger_type}"
        self.active_triggers[trigger_key] = trigger
        logger.info(f"Registered {trigger.trigger_type} trigger for {trigger.user_id}")

    async def unregister_trigger(self, user_id: str, trigger_type: str):
        """Unregister a snapshot trigger."""
        trigger_key = f"{user_id}:{trigger_type}"
        if trigger_key in self.active_triggers:
            del self.active_triggers[trigger_key]
            logger.info(f"Unregistered {trigger_type} trigger for {user_id}")

    async def list_triggers(self, user_id: Optional[str] = None) -> List[SnapshotTrigger]:
        """List all active triggers, optionally filtered by user."""
        triggers = list(self.active_triggers.values())
        if user_id:
            triggers = [t for t in triggers if t.user_id == user_id]
        return triggers

    async def manual_trigger_snapshot(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Manually trigger a snapshot creation."""
        trigger = SnapshotTrigger(
            trigger_type="manual",
            user_id=user_id,
            session_id=session_id,
            priority_threshold=0.0,  # Always trigger for manual
            cooldown_seconds=0  # No cooldown for manual
        )

        return await self._create_automatic_snapshot(trigger, 1.0)  # High priority for manual

    async def get_snapshot_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get snapshot statistics for a user."""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get snapshot counts by trigger type
                cursor.execute("""
                    SELECT
                        context_type as trigger_type,
                        COUNT(*) as count,
                        AVG(CAST(metadata->>'priority_score' AS FLOAT)) as avg_priority,
                        MAX(created_at) as last_snapshot
                    FROM wma_context_snapshots
                    WHERE user_id = %s
                    GROUP BY context_type
                """, (user_id,))

                stats = cursor.fetchall()

                # Get total snapshots
                cursor.execute("""
                    SELECT COUNT(*) as total_snapshots
                    FROM wma_context_snapshots
                    WHERE user_id = %s
                """, (user_id,))

                total = cursor.fetchone()

                return {
                    "user_id": user_id,
                    "total_snapshots": total["total_snapshots"] if total else 0,
                    "trigger_stats": stats,
                    "active_triggers": len([t for t in self.active_triggers.values() if t.user_id == user_id])
                }

        finally:
            self.db_pool.putconn(conn)

# Global service instance
_automatic_snapshots_service = None

async def get_automatic_snapshots_service() -> AutomaticSnapshotsService:
    """Get or create the automatic snapshots service instance."""
    global _automatic_snapshots_service
    if _automatic_snapshots_service is None:
        # Initialize service with connections
        # This would be done in the main application startup
        pass
    return _automatic_snapshots_service

def create_automatic_snapshots_service(db_pool, redis_client, adhd_client) -> AutomaticSnapshotsService:
    """Factory function to create the automatic snapshots service."""
    return AutomaticSnapshotsService(db_pool, redis_client, adhd_client)

# Convenience functions for external use
async def register_snapshot_trigger(trigger: SnapshotTrigger):
    """Register a snapshot trigger."""
    service = await get_automatic_snapshots_service()
    await service.register_trigger(trigger)

async def manual_snapshot_trigger(user_id: str, session_id: Optional[str] = None) -> str:
    """Manually trigger a snapshot."""
    service = await get_automatic_snapshots_service()
    return await service.manual_trigger_snapshot(user_id, session_id)

async def start_automatic_snapshots():
    """Start the automatic snapshots monitoring."""
    service = await get_automatic_snapshots_service()
    await service.start_monitoring()

async def stop_automatic_snapshots():
    """Stop the automatic snapshots monitoring."""
    service = await get_automatic_snapshots_service()
    await service.stop_monitoring()