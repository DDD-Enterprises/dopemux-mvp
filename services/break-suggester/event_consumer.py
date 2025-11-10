"""
F-NEW-8: EventBus Consumer for Break Suggestions

Subscribes to ConPort-KG event stream and feeds BreakSuggestionEngine.

Events Monitored:
- code.complexity.high (Serena)
- cognitive.state.change (ADHD Engine)
- session.start (Task-Orchestrator)
- break.taken (manual tracking)

Integration with F-NEW-6: Suggestions appear in session dashboard
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BreakSuggestionConsumer:
    """
    EventBus consumer for break suggestion engine.

    Subscribes to Redis Streams (dopemux:events) and routes events
    to BreakSuggestionEngine for correlation analysis.
    """

    def __init__(self, user_id: str = "default", redis_url: str = "redis://localhost:6379"):
        """
        Initialize event consumer.

        Args:
            user_id: User identifier
            redis_url: Redis connection URL
        """
        self.user_id = user_id
        self.redis_url = redis_url
        self.redis_client = None
        self.engine = None
        self.running = False

        # Event stream config
        self.stream_name = "dopemux:events"
        self.consumer_group = f"break-suggester-{user_id}"
        self.consumer_name = f"break-suggester-{user_id}-1"

    async def initialize(self):
        """Initialize Redis connection and break engine."""
        try:
            import redis.asyncio as redis

            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info(f"✅ Connected to Redis: {self.redis_url}")

            # Import break engine (relative import)
            from .engine import get_break_suggestion_engine

            self.engine = await get_break_suggestion_engine(self.user_id)
            logger.info(f"✅ BreakSuggestionEngine initialized for user {self.user_id}")

            # Create consumer group (if not exists)
            try:
                await self.redis_client.xgroup_create(
                    self.stream_name,
                    self.consumer_group,
                    mkstream=True
                )
                logger.info(f"✅ Consumer group created: {self.consumer_group}")
            except Exception:
                # Group already exists
                pass

        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    async def start_consuming(self):
        """
        Start consuming events from stream.

        Runs indefinitely until stopped.
        """
        self.running = True
        logger.info(f"🔄 Starting event consumption...")

        while self.running:
            try:
                # Read events from stream
                # XREADGROUP GROUP group consumer BLOCK 1000 STREAMS stream >
                events = await self.redis_client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: '>'},
                    count=10,
                    block=1000  # 1 second timeout in milliseconds
                )

                if not events or len(events) == 0:
                    await asyncio.sleep(0.1)
                    continue

                # Process each event (events is a list of [stream_name, [[msg_id, data], ...]])
                for stream_name, messages in events:
                    for message_id, data in messages:
                        await self._process_event(message_id, data)

                        # Acknowledge message
                        await self.redis_client.xack(
                            self.stream_name,
                            self.consumer_group,
                            message_id
                        )

            except asyncio.CancelledError:
                logger.info("Event consumption cancelled")
                break
            except Exception as e:
                logger.error(f"Error consuming events: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _process_event(self, message_id: str, data: Dict):
        """
        Process single event.

        Routes to appropriate engine method based on event type.

        Args:
            message_id: Redis message ID
            data: Event data dict
        """
        try:
            # Parse event data (redis.asyncio with decode_responses=True returns strings)
            event_type = data.get('event_type', data.get('type', ''))
            event_data_str = data.get('data', '{}')
            event_data = json.loads(event_data_str) if isinstance(event_data_str, str) else event_data_str

            logger.debug(f"Processing event: {event_type}")

            # Route to engine based on type
            if event_type == 'code.complexity.high':
                await self.engine.on_complexity_event(event_data)

            elif event_type == 'cognitive.state.change':
                await self.engine.on_cognitive_state_change(event_data)

            elif event_type == 'session.start':
                timestamp = datetime.fromisoformat(event_data.get('timestamp'))
                await self.engine.on_session_start(timestamp)

            elif event_type == 'break.taken':
                timestamp = datetime.fromisoformat(event_data.get('timestamp'))
                await self.engine.on_break_taken(timestamp)

        except Exception as e:
            logger.error(f"Failed to process event {message_id}: {e}")

    async def stop_consuming(self):
        """Stop event consumption gracefully."""
        self.running = False
        logger.info("Stopping event consumption...")

        if self.redis_client:
            await self.redis_client.aclose()


async def run_break_suggester_service(user_id: str = "default", redis_url: str = "redis://localhost:6379"):
    """
    Run break suggester as background service.

    Args:
        user_id: User identifier
        redis_url: Redis connection URL

    Usage:
        asyncio.create_task(run_break_suggester_service("alice", "redis://redis:6379"))
    """
    consumer = BreakSuggestionConsumer(user_id=user_id, redis_url=redis_url)

    try:
        await consumer.initialize()
        await consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Break suggester service interrupted")
    finally:
        await consumer.stop_consuming()


if __name__ == "__main__":
    # Run as standalone service
    import sys
    import os

    user_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    print(f"🚀 Starting F-NEW-8 Break Suggester for user: {user_id}")
    print(f"   Redis: {redis_url}")
    print(f"   Monitoring events for proactive break suggestions...")

    asyncio.run(run_break_suggester_service(user_id, redis_url))
