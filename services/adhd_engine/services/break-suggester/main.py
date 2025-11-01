"""
F-NEW-8: Proactive Break Suggester

Prevents ADHD burnout by detecting cognitive load patterns and suggesting breaks
BEFORE exhaustion occurs.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class BreakSuggestionEngine:
    """
    Break suggestion engine using cognitive load patterns.

    Monitors activity streams and applies rules to suggest breaks
    before ADHD exhaustion occurs.
    """

    def __init__(self, redis_url: str, user_id: str):
        self.redis_url = redis_url
        self.user_id = user_id
        self.redis: Optional[redis.Redis] = None

        # Rule thresholds
        self.complexity_threshold = float(os.getenv("COMPLEXITY_THRESHOLD", "0.6"))
        self.session_threshold_minutes = int(os.getenv("SESSION_THRESHOLD_MINUTES", "25"))
        self.break_frequency_minutes = int(os.getenv("BREAK_FREQUENCY_MINUTES", "25"))

        # Monitoring state
        self.current_session_start: Optional[float] = None
        self.complexity_events = []
        self.last_break_time: Optional[float] = None

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.redis_url)
        logger.info("Break suggestion engine initialized")

    async def process_event(self, event_type: str, event_data: Dict):
        """
        Process incoming event and check break suggestion rules.

        Args:
            event_type: Type of event (code.complexity.high, cognitive.state.change, etc.)
            event_data: Event data payload
        """
        logger.debug(f"Processing event: {event_type}")

        # Track complexity events
        if event_type == "code.complexity.high":
            complexity_score = event_data.get("complexity_score", 0)
            if complexity_score >= self.complexity_threshold:
                self.complexity_events.append({
                    "timestamp": asyncio.get_event_loop().time(),
                    "complexity": complexity_score
                })

        # Check break rules
        suggestion = await self._evaluate_break_rules()

        if suggestion:
            await self._send_break_suggestion(suggestion)

    async def _evaluate_break_rules(self) -> Optional[Dict]:
        """
        Evaluate break suggestion rules.

        Returns:
            Dict with suggestion details or None if no suggestion needed
        """
        current_time = asyncio.get_event_loop().time()

        # Rule 1: Sustained High Complexity
        recent_complexity = [
            event for event in self.complexity_events
            if current_time - event["timestamp"] < 1500  # Last 25 minutes
        ]

        if len(recent_complexity) >= 3:
            return {
                "reason": "sustained_complexity",
                "priority": "MEDIUM",
                "message": f"High complexity work detected ({len(recent_complexity)} events in 25 minutes)",
                "suggested_break_minutes": 5
            }

        # Rule 2: Session Duration Threshold
        if self.current_session_start:
            session_duration_minutes = (current_time - self.current_session_start) / 60

            if session_duration_minutes >= self.session_threshold_minutes:
                # Check if we've had a recent break
                if not self.last_break_time or (current_time - self.last_break_time) / 60 >= self.break_frequency_minutes:
                    return {
                        "reason": "session_duration",
                        "priority": "MEDIUM",
                        "message": ".0f",
                        "suggested_break_minutes": 5
                    }

        # Rule 3: Critical Session Threshold (60+ minutes)
        if self.current_session_start:
            session_duration_minutes = (current_time - self.current_session_start) / 60

            if session_duration_minutes >= 60:
                return {
                    "reason": "critical_session",
                    "priority": "CRITICAL",
                    "message": ".0f",
                    "suggested_break_minutes": 10
                }

        return None

    async def _send_break_suggestion(self, suggestion: Dict):
        """
        Send break suggestion to notification channels.

        Args:
            suggestion: Suggestion details
        """
        try:
            # Store in Redis for dashboard consumption
            suggestion_data = {
                **suggestion,
                "user_id": self.user_id,
                "timestamp": asyncio.get_event_loop().time(),
                "session_duration_minutes": (
                    (asyncio.get_event_loop().time() - self.current_session_start) / 60
                    if self.current_session_start else 0
                )
            }

            await self.redis.lpush(
                f"adhd:break_suggestions:{self.user_id}",
                json.dumps(suggestion_data)
            )

            # Keep only recent suggestions
            await self.redis.ltrim(f"adhd:break_suggestions:{self.user_id}", 0, 9)

            logger.info(f"Break suggestion sent: {suggestion['reason']} - {suggestion['priority']}")

        except Exception as e:
            logger.error(f"Failed to send break suggestion: {e}")

    async def handle_session_start(self, session_data: Dict):
        """Handle session start event."""
        self.current_session_start = asyncio.get_event_loop().time()
        self.complexity_events = []  # Reset for new session
        logger.info("Session started - break monitoring active")

    async def handle_break_taken(self, break_data: Dict):
        """Handle break taken event."""
        self.last_break_time = asyncio.get_event_loop().time()
        logger.info("Break taken - monitoring paused temporarily")


async def start_break_suggester_service(user_id: str = "default"):
    """
    Start break suggester service.

    Subscribes to Redis streams and monitors for break suggestion triggers.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")

    engine = BreakSuggestionEngine(redis_url, user_id)
    await engine.initialize()

    redis_client = redis.from_url(redis_url)

    # Subscribe to relevant streams
    streams = {
        "dopemux:events": "$"  # All events
    }

    logger.info("Break suggester service started")

    while True:
        try:
            # Read from streams
            messages = await redis_client.xread(streams, block=1000, count=10)

            for stream, message_list in messages:
                for message_id, message_data in message_list:
                    event_type = message_data.get("type", "")
                    event_data = message_data.get("data", {})

                    # Route events to engine
                    if event_type in ["code.complexity.high", "cognitive.state.change", "session.start", "break.taken"]:
                        await engine.process_event(event_type, event_data)

                    # Acknowledge message
                    await redis_client.xack("dopemux:events", f"break-suggester-{user_id}", message_id)

        except Exception as e:
            logger.error(f"Break suggester error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    user_id = os.getenv("USER_ID", "default")
    asyncio.run(start_break_suggester_service(user_id))