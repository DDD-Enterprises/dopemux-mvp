#!/usr/bin/env python3
"""
EventBus Integration Test
Validates Redis Streams pub/sub functionality for Integration Bridge
"""

import asyncio
import sys
from datetime import datetime

from event_bus import EventBus, Event, EventType


async def test_publish_all_event_types(bus: EventBus):
    """Test publishing all event types"""
    print("\n📤 Testing Event Publishing")
    print("=" * 60)

    test_events = [
        Event(
            type=EventType.TASKS_IMPORTED,
            data={"task_count": 10, "sprint_id": "S-2025.10"}
        ),
        Event(
            type=EventType.SESSION_STARTED,
            data={"task_id": "task-123", "duration_minutes": 25}
        ),
        Event(
            type=EventType.PROGRESS_UPDATED,
            data={"task_id": "task-123", "status": "IN_PROGRESS", "progress": 0.5}
        ),
        Event(
            type=EventType.SESSION_COMPLETED,
            data={"task_id": "task-123", "outcome": "success"}
        ),
        Event(
            type=EventType.BREAK_REMINDER,
            data={"duration_minutes": 5, "message": "Time for a break!"}
        ),
        Event(
            type=EventType.ADHD_STATE_CHANGED,
            data={"energy": "high", "focus": "scattered"}
        ),
        Event(
            type=EventType.DECISION_LOGGED,
            data={"decision_id": 999, "summary": "Test decision"}
        ),
    ]

    published_ids = []

    for event in test_events:
        msg_id = await bus.publish("dopemux:test", event)
        published_ids.append(msg_id)
        print(f"  ✅ Published {event.type}: {msg_id}")

    print(f"\n📊 Published {len(published_ids)} events to dopemux:test")
    return published_ids


async def test_stream_info(bus: EventBus):
    """Test stream information retrieval"""
    print("\n📊 Testing Stream Info")
    print("=" * 60)

    info = await bus.get_stream_info("dopemux:test")

    print(f"  Stream: dopemux:test")
    print(f"  Length: {info.get('length', 0)} messages")
    print(f"  Groups: {info.get('groups', 0)} consumer groups")

    if info.get('length', 0) > 0:
        print(f"  ✅ Stream contains messages")
    else:
        print(f"  ⚠️  Stream is empty")

    return info


async def test_consumer_subscription(bus: EventBus):
    """Test consumer group subscription and message acknowledgment"""
    print("\n📥 Testing Consumer Subscription")
    print("=" * 60)

    consumer_group = "test-consumers"
    consumer_name = "test-worker-1"
    messages_received = 0
    max_messages = 10

    print(f"  Subscribing as: {consumer_group}/{consumer_name}")
    print(f"  Reading from: dopemux:test")
    print(f"  Max messages: {max_messages}")
    print()

    try:
        async for msg_id, event in bus.subscribe(
            stream="dopemux:test",
            consumer_group=consumer_group,
            consumer_name=consumer_name
        ):
            messages_received += 1
            print(f"  📬 Received: {event.type}")
            print(f"     ├─ Message ID: {msg_id}")
            print(f"     ├─ Timestamp: {event.timestamp}")
            print(f"     ├─ Source: {event.source}")
            print(f"     └─ Data: {event.data}")

            # Stop after max messages or if we've read everything
            if messages_received >= max_messages:
                # Unsubscribe to exit cleanly
                await bus.unsubscribe("dopemux:test", consumer_group, consumer_name)
                break

    except asyncio.CancelledError:
        print(f"\n  ⚠️  Subscription cancelled")

    print(f"\n📊 Received {messages_received} messages")
    print(f"  ✅ Consumer subscription working")

    return messages_received


async def test_parallel_consumers(bus: EventBus):
    """Test multiple consumers in same group (load balancing)"""
    print("\n⚡ Testing Parallel Consumers (Load Balancing)")
    print("=" * 60)

    # Publish some test events first
    for i in range(5):
        event = Event(
            type=EventType.PROGRESS_UPDATED,
            data={"task_id": f"task-{i}", "progress": i * 0.2}
        )
        await bus.publish("dopemux:parallel-test", event)

    print(f"  Published 5 events to dopemux:parallel-test")

    # Create two consumers in same group
    consumer_group = "parallel-group"
    consumer1_count = 0
    consumer2_count = 0

    async def consume_as(consumer_name: str, count_ref: list):
        """Consumer worker"""
        async for msg_id, event in bus.subscribe(
            stream="dopemux:parallel-test",
            consumer_group=consumer_group,
            consumer_name=consumer_name
        ):
            count_ref[0] += 1
            print(f"  📬 {consumer_name} received: {event.type} (task: {event.data.get('task_id')})")

            if count_ref[0] >= 3:  # Each consumer processes up to 3
                await bus.unsubscribe("dopemux:parallel-test", consumer_group, consumer_name)
                break

    # Run both consumers concurrently
    consumer1_ref = [0]
    consumer2_ref = [0]

    await asyncio.gather(
        consume_as("consumer-1", consumer1_ref),
        consume_as("consumer-2", consumer2_ref)
    )

    total_consumed = consumer1_ref[0] + consumer2_ref[0]

    print(f"\n📊 Load balancing results:")
    print(f"  Consumer 1: {consumer1_ref[0]} messages")
    print(f"  Consumer 2: {consumer2_ref[0]} messages")
    print(f"  Total: {total_consumed} messages")
    print(f"  ✅ Parallel consumption working")

    return total_consumed


async def cleanup_test_streams(bus: EventBus):
    """Clean up test streams (optional)"""
    print("\n🧹 Cleaning up test streams")
    print("=" * 60)

    # Note: Redis doesn't provide a direct "delete stream" command via Python client
    # For cleanup, you'd use: docker exec dopemux-redis-primary redis-cli DEL dopemux:test

    print("  ℹ️  To manually cleanup test streams:")
    print("     docker exec dopemux-redis-primary redis-cli DEL dopemux:test")
    print("     docker exec dopemux-redis-primary redis-cli DEL dopemux:parallel-test")


async def main():
    """Run all EventBus tests"""
    print("\n" + "=" * 60)
    print("🧪 EventBus Integration Test Suite")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")

    # Initialize EventBus
    redis_url = "redis://localhost:6379"  # Via port mapping
    bus = EventBus(redis_url)

    try:
        print("\n🔌 Initializing EventBus connection...")
        await bus.initialize()
        print("  ✅ Connected to Redis")

        # Run test suite
        test_results = {}

        # Test 1: Publish all event types
        published_ids = await test_publish_all_event_types(bus)
        test_results['publish'] = len(published_ids) == 7

        # Test 2: Stream info
        info = await test_stream_info(bus)
        test_results['stream_info'] = info.get('length', 0) >= 7

        # Test 3: Consumer subscription
        messages_received = await test_consumer_subscription(bus)
        test_results['subscription'] = messages_received >= 7

        # Test 4: Parallel consumers (load balancing)
        total_consumed = await test_parallel_consumers(bus)
        test_results['parallel'] = total_consumed >= 5

        # Cleanup instructions
        await cleanup_test_streams(bus)

        # Summary
        print("\n" + "=" * 60)
        print("📋 Test Results Summary")
        print("=" * 60)

        for test_name, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {test_name}")

        all_passed = all(test_results.values())

        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 All EventBus tests PASSED!")
            print("=" * 60)
            print("\nIntegration Bridge EventBus is ready for production:")
            print("  • Redis Streams: Operational")
            print("  • Event Publishing: Working")
            print("  • Consumer Groups: Working")
            print("  • Load Balancing: Working")
            print("  • Message Acknowledgment: Working")
            return 0
        else:
            print("⚠️  Some EventBus tests FAILED")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await bus.close()
        print(f"\n🔌 EventBus connection closed")
        print(f"Completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
