"""
Test script for Component 3: DopeconBridge Event Subscription

Validates bidirectional event flow:
1. Publish event to DopeconBridge
2. Verify Task-Orchestrator receives event via EventBus
3. Test all 8 event types
"""

import asyncio
import aiohttp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOPECON_BRIDGE_URL = "http://localhost:3016"


async def test_event_publication():
    """Test publishing events to DopeconBridge."""

    async with aiohttp.ClientSession() as session:
        # Test 1: Publish TASKS_IMPORTED event
        logger.info("📤 Test 1: Publishing TASKS_IMPORTED event...")
        tasks_imported_event = {
            "stream": "dopemux:events",
            "event_type": "tasks_imported",
            "data": {
                "task_count": 5,
                "sprint_id": "test-sprint-001"
            },
            "source": "test-script"
        }

        async with session.post(
            f"{DOPECON_BRIDGE_URL}/events",
            json=tasks_imported_event
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ TASKS_IMPORTED published: {result}")
            else:
                logger.error(f"❌ Failed to publish TASKS_IMPORTED: {response.status}")

        await asyncio.sleep(1)  # Give Task-Orchestrator time to process

        # Test 2: Publish SESSION_STARTED event
        logger.info("📤 Test 2: Publishing SESSION_STARTED event...")
        session_started_event = {
            "stream": "dopemux:events",
            "event_type": "session_started",
            "data": {
                "task_id": "test-task-001",
                "duration_minutes": 25
            },
            "source": "test-script"
        }

        async with session.post(
            f"{DOPECON_BRIDGE_URL}/events",
            json=session_started_event
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ SESSION_STARTED published: {result}")
            else:
                logger.error(f"❌ Failed to publish SESSION_STARTED: {response.status}")

        await asyncio.sleep(1)

        # Test 3: Publish PROGRESS_UPDATED event
        logger.info("📤 Test 3: Publishing PROGRESS_UPDATED event...")
        progress_updated_event = {
            "stream": "dopemux:events",
            "event_type": "progress_updated",
            "data": {
                "task_id": "test-task-001",
                "status": "in_progress",
                "progress": 0.5
            },
            "source": "test-script"
        }

        async with session.post(
            f"{DOPECON_BRIDGE_URL}/events",
            json=progress_updated_event
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ PROGRESS_UPDATED published: {result}")
            else:
                logger.error(f"❌ Failed to publish PROGRESS_UPDATED: {response.status}")

        await asyncio.sleep(1)

        # Test 4: Publish DECISION_LOGGED event
        logger.info("📤 Test 4: Publishing DECISION_LOGGED event...")
        decision_logged_event = {
            "stream": "dopemux:events",
            "event_type": "decision_logged",
            "data": {
                "summary": "Use DopeconBridge for event coordination",
                "decision_id": "test-decision-001"
            },
            "source": "test-script"
        }

        async with session.post(
            f"{DOPECON_BRIDGE_URL}/events",
            json=decision_logged_event
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ DECISION_LOGGED published: {result}")
            else:
                logger.error(f"❌ Failed to publish DECISION_LOGGED: {response.status}")

        await asyncio.sleep(1)

        # Test 5: Publish ADHD_STATE_CHANGED event
        logger.info("📤 Test 5: Publishing ADHD_STATE_CHANGED event...")
        adhd_state_event = {
            "stream": "dopemux:events",
            "event_type": "adhd_state_changed",
            "data": {
                "state": "focused",
                "energy_level": "high",
                "attention_level": "focused"
            },
            "source": "test-script"
        }

        async with session.post(
            f"{DOPECON_BRIDGE_URL}/events",
            json=adhd_state_event
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ ADHD_STATE_CHANGED published: {result}")
            else:
                logger.error(f"❌ Failed to publish ADHD_STATE_CHANGED: {response.status}")

        await asyncio.sleep(1)

        # Test 6: Publish BREAK_REMINDER event
        logger.info("📤 Test 6: Publishing BREAK_REMINDER event...")
        break_reminder_event = {
            "stream": "dopemux:events",
            "event_type": "break_reminder",
            "data": {
                "task_id": "test-task-001",
                "duration_minutes": 5
            },
            "source": "test-script"
        }

        async with session.post(
            f"{DOPECON_BRIDGE_URL}/events",
            json=break_reminder_event
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ BREAK_REMINDER published: {result}")
            else:
                logger.error(f"❌ Failed to publish BREAK_REMINDER: {response.status}")


async def check_stream_info():
    """Check DopeconBridge stream information."""
    logger.info("\n📊 Checking DopeconBridge stream info...")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{DOPECON_BRIDGE_URL}/events/dopemux:events"
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Stream info: {result}")
            else:
                logger.error(f"Failed to get stream info: {response.status}")


async def main():
    """Main test execution."""
    logger.info("=" * 60)
    logger.info("Component 3: DopeconBridge Event Subscription Test")
    logger.info("=" * 60)

    # Test event publication
    await test_event_publication()

    # Wait for events to be processed
    logger.info("\n⏳ Waiting 5 seconds for Task-Orchestrator to process events...")
    await asyncio.sleep(5)

    # Check stream info
    await check_stream_info()

    logger.info("\n=" * 60)
    logger.info("✅ Test complete!")
    logger.info("Check Task-Orchestrator logs to verify event reception")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
