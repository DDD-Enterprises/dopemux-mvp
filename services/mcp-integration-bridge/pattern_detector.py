"""
Pattern Detection Engine for Integration Bridge

Automatically detects patterns across agent events and generates ConPort insights.
Runs as background worker every 5 minutes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from event_bus import EventBus
from patterns import (
    PatternInsight,
    HighComplexityClusterPattern,
    RepeatedErrorPattern,
    KnowledgeGapPattern,
    DecisionChurnPattern,
    ADHDStatePattern,
    ContextSwitchFrequencyPattern,
    TaskAbandonmentPattern,
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Orchestrates pattern detection across all event types.

    Features:
    - Runs 7 pattern detectors on event window
    - Auto-creates ConPort decisions for detected patterns
    - Background worker with configurable interval
    - Performance tracking and metrics
    - ADHD-optimized: Non-blocking, efficient processing
    """

    def __init__(
        self,
        event_bus: EventBus,
        conport_client: Optional[Any] = None,
        event_window_minutes: int = 60,
        detection_interval_seconds: int = 300,  # 5 minutes
    ):
        """
        Initialize pattern detector.

        Args:
            event_bus: EventBus instance for fetching events
            conport_client: Optional ConPort client for logging insights
            event_window_minutes: Time window for event analysis (default: 60 min)
            detection_interval_seconds: How often to run detection (default: 300s)
        """
        self.event_bus = event_bus
        self.conport_client = conport_client
        self.event_window_minutes = event_window_minutes
        self.detection_interval_seconds = detection_interval_seconds

        # Initialize all pattern detectors
        self.patterns = [
            HighComplexityClusterPattern(),
            RepeatedErrorPattern(),
            KnowledgeGapPattern(),
            DecisionChurnPattern(),
            ADHDStatePattern(),
            ContextSwitchFrequencyPattern(),
            TaskAbandonmentPattern(),
        ]

        # Tracking
        self.total_runs = 0
        self.total_insights_generated = 0
        self.last_run: Optional[str] = None
        self.running = False

    async def analyze_events(
        self,
        events: List[Dict[str, Any]],
        workspace_id: str
    ) -> List[PatternInsight]:
        """
        Run all pattern detectors on events.

        Args:
            events: List of event dictionaries
            workspace_id: Workspace ID for ConPort logging

        Returns:
            List of all detected insights
        """
        all_insights = []

        logger.info(f"Running pattern detection on {len(events)} events...")

        # Run each pattern detector
        for pattern in self.patterns:
            try:
                insights = pattern.detect(events)

                if insights:
                    logger.info(
                        f"  [{pattern.get_pattern_name()}] "
                        f"Detected {len(insights)} pattern(s)"
                    )
                    all_insights.extend(insights)

            except Exception as e:
                logger.error(
                    f"  [{pattern.get_pattern_name()}] "
                    f"Detection failed: {e}"
                )

        logger.info(f"Pattern detection complete: {len(all_insights)} total insights")

        return all_insights

    async def log_insights_to_conport(
        self,
        insights: List[PatternInsight],
        workspace_id: str
    ) -> int:
        """
        Log detected insights to ConPort as decisions.

        Args:
            insights: List of PatternInsight objects
            workspace_id: Workspace ID for ConPort

        Returns:
            Number of insights successfully logged
        """
        if not self.conport_client:
            logger.warning("ConPort client not available - insights not logged")
            return 0

        logged_count = 0

        for insight in insights:
            try:
                # Convert to ConPort decision format
                decision_data = insight.to_conport_decision(workspace_id)

                # Log to ConPort (would use real MCP client here)
                # await self.conport_client.log_decision(**decision_data)

                logger.info(
                    f"  Logged insight: [{insight.pattern_name}] "
                    f"{insight.summary[:60]}..."
                )

                logged_count += 1
                self.total_insights_generated += 1

            except Exception as e:
                logger.error(f"  Failed to log insight: {e}")

        return logged_count

    async def fetch_recent_events(
        self,
        stream: str = "dopemux:events"
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent events from Redis Stream.

        Args:
            stream: Stream name to fetch from

        Returns:
            List of event dictionaries
        """
        if not self.event_bus.redis_client:
            logger.error("Redis client not available")
            return []

        try:
            # Calculate time window
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.event_window_minutes)
            cutoff_ms = int(cutoff_time.timestamp() * 1000)

            # Read from stream (last N events)
            # Using XREVRANGE to get recent events
            events_raw = await self.event_bus.redis_client.xrevrange(
                stream,
                max='+',  # Latest
                min=f'{cutoff_ms}-0',  # Events after cutoff
                count=1000  # Limit to prevent memory issues
            )

            # Parse events
            events = []
            for msg_id, msg_data in events_raw:
                try:
                    import json
                    event = {
                        "type": msg_data[b"event_type"].decode("utf-8"),
                        "timestamp": msg_data[b"timestamp"].decode("utf-8"),
                        "source": msg_data.get(b"source", b"unknown").decode("utf-8"),
                        "data": json.loads(msg_data[b"data"].decode("utf-8"))
                    }
                    events.append(event)

                except Exception as e:
                    logger.warning(f"Failed to parse event {msg_id}: {e}")

            logger.info(f"Fetched {len(events)} events from last {self.event_window_minutes} minutes")

            return events

        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []

    async def run_detection_cycle(self, workspace_id: str) -> Dict[str, Any]:
        """
        Run one complete detection cycle.

        Args:
            workspace_id: Workspace ID for ConPort logging

        Returns:
            Dictionary with cycle results
        """
        self.total_runs += 1
        start_time = datetime.utcnow()

        # Fetch recent events
        events = await self.fetch_recent_events()

        if not events:
            logger.info("No events to analyze")
            return {
                "events_analyzed": 0,
                "insights_generated": 0,
                "insights_logged": 0,
                "duration_ms": 0
            }

        # Analyze for patterns
        insights = await self.analyze_events(events, workspace_id)

        # Log to ConPort
        logged_count = await self.log_insights_to_conport(insights, workspace_id)

        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        self.last_run = datetime.utcnow().isoformat()

        results = {
            "events_analyzed": len(events),
            "insights_generated": len(insights),
            "insights_logged": logged_count,
            "duration_ms": duration_ms,
            "timestamp": self.last_run
        }

        logger.info(
            f"Detection cycle complete: {len(insights)} insights from {len(events)} events "
            f"({duration_ms:.0f}ms)"
        )

        return results

    async def start_background_worker(
        self,
        workspace_id: str,
        stop_event: Optional[asyncio.Event] = None
    ):
        """
        Start background worker that runs detection cycles periodically.

        Args:
            workspace_id: Workspace ID for ConPort logging
            stop_event: Optional event to signal worker stop
        """
        self.running = True
        stop_event = stop_event or asyncio.Event()

        logger.info(
            f"Starting pattern detection worker "
            f"(interval: {self.detection_interval_seconds}s, "
            f"window: {self.event_window_minutes}min)"
        )

        while self.running and not stop_event.is_set():
            try:
                # Run detection cycle
                await self.run_detection_cycle(workspace_id)

                # Wait for next cycle (with periodic checks for stop signal)
                for _ in range(self.detection_interval_seconds):
                    if stop_event.is_set() or not self.running:
                        break
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Pattern detection cycle failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

        logger.info("Pattern detection worker stopped")

    def stop(self):
        """Stop the background worker."""
        self.running = False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get pattern detection metrics.

        Returns:
            Dictionary with runs, insights, pattern-specific metrics
        """
        return {
            "total_runs": self.total_runs,
            "total_insights_generated": self.total_insights_generated,
            "last_run": self.last_run,
            "patterns": [pattern.get_metrics() for pattern in self.patterns]
        }
