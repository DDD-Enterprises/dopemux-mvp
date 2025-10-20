"""
Minimal test for Component 3: EventBus Subscription

Tests EventBus functionality without requiring full Task-Orchestrator infrastructure.
Validates:
1. EventBus initialization
2. Event subscription
3. Event publication
4. Event reception
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add Integration Bridge path
integration_bridge_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-integration-bridge')
sys.path.insert(0, integration_bridge_path)

from event_bus import EventBus, Event, EventType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestSubscriber:
    """Test subscriber that listens for events."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.event_bus: EventBus = None
        self.received_events = []
        self.running = False

    async def initialize(self):
        """Initialize EventBus."""
        logger.info("🚀 Initializing EventBus...")
        self.event_bus = EventBus(self.redis_url, password=None)
        await self.event_bus.initialize()
        logger.info("✅ EventBus initialized")

    async def subscribe_and_listen(self, duration_seconds: int = 10):
        """Subscribe to events for specified duration."""
        logger.info(f"📡 Subscribing to dopemux:events stream for {duration_seconds} seconds...")

        self.running = True

        # Create subscription task
        subscription_task = asyncio.create_task(self._subscription_worker())

        # Wait for specified duration
        await asyncio.sleep(duration_seconds)

        # Stop subscription
        self.running = False
        subscription_task.cancel()

        try:
            await subscription_task
        except asyncio.CancelledError:
            logger.info("📭 Subscription stopped")

        logger.info(f"📥 Received {len(self.received_events)} events total")

        return self.received_events

    async def _subscription_worker(self):
        """Background worker for event subscription."""
        try:
            async for msg_id, event in self.event_bus.subscribe(
                stream="dopemux:events",
                consumer_group="test-subscriber",
                consumer_name="test-instance-1"
            ):
                if not self.running:
                    break

                logger.info(f"📥 Received event: {event.type} from {event.source}")
                logger.info(f"   Data: {event.data}")
                self.received_events.append(event)

        except Exception as e:
            if self.running:  # Only log if not intentionally stopped
                logger.error(f"Subscription error: {e}")

    async def close(self):
        """Close EventBus connection."""
        if self.event_bus:
            await self.event_bus.close()
            logger.info("📪 EventBus closed")


async def publish_test_events(event_bus: EventBus):
    """Publish test events to verify subscription."""
    logger.info("\n📤 Publishing test events...")

    # Event 1: TASKS_IMPORTED
    event1 = Event(
        type=EventType.TASKS_IMPORTED,
        data={"task_count": 3, "sprint_id": "test-sprint-001"},
        source="test-publisher"
    )
    msg_id1 = await event_bus.publish("dopemux:events", event1)
    logger.info(f"✅ Published TASKS_IMPORTED (ID: {msg_id1})")

    await asyncio.sleep(0.5)

    # Event 2: SESSION_STARTED
    event2 = Event(
        type=EventType.SESSION_STARTED,
        data={"task_id": "test-task-001", "duration_minutes": 25},
        source="test-publisher"
    )
    msg_id2 = await event_bus.publish("dopemux:events", event2)
    logger.info(f"✅ Published SESSION_STARTED (ID: {msg_id2})")

    await asyncio.sleep(0.5)

    # Event 3: PROGRESS_UPDATED
    event3 = Event(
        type=EventType.PROGRESS_UPDATED,
        data={"task_id": "test-task-001", "status": "in_progress", "progress": 0.5},
        source="test-publisher"
    )
    msg_id3 = await event_bus.publish("dopemux:events", event3)
    logger.info(f"✅ Published PROGRESS_UPDATED (ID: {msg_id3})")

    await asyncio.sleep(0.5)

    # Event 4: ADHD_STATE_CHANGED
    event4 = Event(
        type=EventType.ADHD_STATE_CHANGED,
        data={"state": "focused", "energy_level": "high", "attention_level": "focused"},
        source="test-publisher"
    )
    msg_id4 = await event_bus.publish("dopemux:events", event4)
    logger.info(f"✅ Published ADHD_STATE_CHANGED (ID: {msg_id4})")

    logger.info("✅ All test events published")


async def main():
    """Main test execution."""
    logger.info("=" * 70)
    logger.info("Component 3: EventBus Subscription Test")
    logger.info("=" * 70)

    # Create subscriber
    subscriber = TestSubscriber()

    # Create publisher EventBus
    publisher_bus = EventBus("redis://localhost:6379", password=None)

    try:
        # Initialize both
        await subscriber.initialize()
        await publisher_bus.initialize()

        # Start subscription in background
        subscription_task = asyncio.create_task(
            subscriber.subscribe_and_listen(duration_seconds=15)
        )

        # Wait for subscription to start
        await asyncio.sleep(2)

        # Publish test events
        await publish_test_events(publisher_bus)

        # Wait for subscription to complete
        received_events = await subscription_task

        # Verify results
        logger.info("\n" + "=" * 70)
        logger.info("📊 Test Results")
        logger.info("=" * 70)

        if len(received_events) >= 4:
            logger.info(f"✅ SUCCESS: Received {len(received_events)} events")
            logger.info("\nEvent details:")
            for i, event in enumerate(received_events, 1):
                logger.info(f"  {i}. {event.type} from {event.source}")
                logger.info(f"     Data: {event.data}")
        else:
            logger.warning(f"⚠️  PARTIAL: Only received {len(received_events)}/4 events")
            if received_events:
                logger.info("\nReceived events:")
                for event in received_events:
                    logger.info(f"  - {event.type}")

        logger.info("\n" + "=" * 70)
        logger.info("✅ Test complete!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)

    finally:
        # Cleanup
        await subscriber.close()
        await publisher_bus.close()


if __name__ == "__main__":
    asyncio.run(main())
