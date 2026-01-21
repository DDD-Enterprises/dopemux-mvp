#!/usr/bin/env python3
"""
Test Workspace Switch Events - Emit test events to verify Activity Capture flow

This script emits workspace.switched events to Redis Streams to test the complete
ADHD activity tracking flow:

Redis Streams → Activity Capture → ADHD Engine → Statusline

Usage:
    python scripts/test-workspace-events.py          # Emit test events
    python scripts/test-workspace-events.py --loop   # Continuous test (every 30s)
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import sys
import argparse
from pathlib import Path

# Add DopeconBridge to path for EventBus
bridge_path = Path(__file__).parent.parent / "services" / "mcp-dopecon-bridge"
sys.path.insert(0, str(bridge_path))

from event_bus import Event, EventBus


async def emit_workspace_switch(
    event_bus: EventBus,
    from_workspace: str,
    to_workspace: str,
    switch_type: str = "manual"
):
    """
    Emit a workspace.switched event.

    Args:
        event_bus: EventBus instance
        from_workspace: Previous workspace
        to_workspace: New workspace
        switch_type: Type of switch (manual/automatic)
    """
    import time
    event = Event(
        type="workspace.switched",
        data={
            "from_workspace": from_workspace,
            "to_workspace": to_workspace,
            "switch_type": switch_type,
            "context_data": {},
            "workspace_id": to_workspace,
            "adhd_context_capture": {
                "timestamp": f"{time.time()}",  # Unique timestamp to avoid deduplication
                "recovery_priority": "medium"
            }
        },
        source="test-script"
    )

    try:
        msg_id = await event_bus.publish("dopemux:events", event)
        logger.info(f"✅ Published workspace.switched: {from_workspace.split('/')[-1]} → {to_workspace.split('/')[-1]}")
        logger.info(f"   Message ID: {msg_id}")
        return msg_id
    except Exception as e:
        logger.error(f"❌ Failed to publish event: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_workspace_flow():
    """Test complete workspace tracking flow"""

    # Connect to Redis
    logger.info("🔌 Connecting to Redis Streams...")
    event_bus = EventBus(redis_url="redis://localhost:6379")
    await event_bus.initialize()
    logger.info("✅ Connected to Redis")
    logger.info()

    logger.info("=" * 60)
    logger.info("🧪 Testing Workspace Switch Event Flow")
    logger.info("=" * 60)
    logger.info()

    # Scenario: Switch TO dopemux workspace (start session)
    logger.info("📍 Test 1: Switch TO dopemux workspace (should start session)")
    await emit_workspace_switch(
        event_bus,
        from_workspace="/Users/hue/other-project",
        to_workspace="/Users/hue/code/dopemux-mvp",
        switch_type="manual"
    )
    logger.info()

    # Wait 2 seconds
    logger.info("⏳ Waiting 2 seconds...")
    await asyncio.sleep(2)

    # Scenario: Switch away briefly (interruption)
    logger.info("🔄 Test 2: Switch away briefly (should count as interruption)")
    await emit_workspace_switch(
        event_bus,
        from_workspace="/Users/hue/code/dopemux-mvp",
        to_workspace="/Users/hue/browser-tab",
        switch_type="manual"
    )
    logger.info()

    # Wait 1 second
    await asyncio.sleep(1)

    # Scenario: Switch back to dopemux
    logger.info("📍 Test 3: Switch back to dopemux (new session)")
    await emit_workspace_switch(
        event_bus,
        from_workspace="/Users/hue/browser-tab",
        to_workspace="/Users/hue/code/dopemux-mvp",
        switch_type="manual"
    )
    logger.info()

    # Close connection
    await event_bus.close()

    logger.info("=" * 60)
    logger.info("✅ Test events published successfully!")
    logger.info("=" * 60)
    logger.info()
    logger.info("🔍 Check Activity Capture logs:")
    logger.info("   docker logs dopemux-activity-capture --tail 30")
    logger.info()
    logger.info("🔍 Check Activity Capture metrics:")
    logger.info("   curl -s http://localhost:8096/metrics | jq '.'")
    logger.info()
    logger.info("🔍 Check ADHD Engine state:")
    logger.info("   curl -s http://localhost:8095/health | jq '.current_state'")
    logger.info()


async def continuous_test_loop():
    """Emit test events every 30 seconds"""

    event_bus = EventBus(redis_url="redis://localhost:6379")
    await event_bus.initialize()

    logger.info("🔄 Starting continuous test mode (Ctrl+C to stop)")
    logger.info("   Emitting workspace switches every 30 seconds")
    logger.info()

    iteration = 0

    try:
        while True:
            iteration += 1
            logger.info(f"--- Iteration {iteration} ---")

            # Switch TO dopemux
            await emit_workspace_switch(
                event_bus,
                from_workspace="/Users/hue/other-project",
                to_workspace="/Users/hue/code/dopemux-mvp"
            )

            await asyncio.sleep(15)

            # Switch AWAY from dopemux (end session)
            await emit_workspace_switch(
                event_bus,
                from_workspace="/Users/hue/code/dopemux-mvp",
                to_workspace="/Users/hue/browser"
            )

            logger.info(f"   ⏳ Waiting 15 seconds until next iteration...")
            logger.info()
            await asyncio.sleep(15)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Stopped continuous test")
        await event_bus.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test workspace switch event flow")
    parser.add_argument("--loop", action="store_true", help="Run continuous test (every 30s)")
    args = parser.parse_args()

    if args.loop:
        asyncio.run(continuous_test_loop())
    else:
        asyncio.run(test_workspace_flow())
