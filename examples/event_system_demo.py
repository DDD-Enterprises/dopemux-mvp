#!/usr/bin/env python3
"""
Dopemux Event-Driven Architecture Demo

Demonstrates multi-instance coordination with ADHD-optimized event filtering.
"""

import asyncio
import time
from datetime import datetime

from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
from dopemux.attention_mediator import AttentionMediator, FocusState, InterruptionTolerance
from dopemux.instance_registry import InstanceRegistry, InstanceStatus
from dopemux.producers.mcp_producer import MCPEventProducer
from dopemux.producers.conport_producer import ConPortEventProducer


class DemoEventHandler:
    """Demo event handler that prints received events."""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.events_received = 0

    def handle_event(self, event: DopemuxEvent):
        """Handle individual events."""
        self.events_received += 1
        print(f"🎯 [{self.instance_id}] Event: {event.envelope.type}")
        print(f"   Payload: {event.payload}")
        print(f"   Priority: {event.envelope.priority.value}")
        print(f"   Cognitive Load: {event.envelope.adhd_metadata.cognitive_load.value}")
        print()

    def handle_batch(self, batch):
        """Handle batched events."""
        print(f"📦 [{self.instance_id}] Batch: {batch.category} ({len(batch.events)} events)")
        for event in batch.events:
            print(f"   - {event.envelope.type}: {event.payload}")
        print()


async def demo_basic_event_flow():
    """Demonstrate basic event publishing and subscription."""
    print("🚀 Demo 1: Basic Event Flow")
    print("=" * 50)

    # Create event bus (use Redis in production, memory for demo)
    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()

    handler = DemoEventHandler("DEMO")

    # Subscribe to events
    subscription_id = await event_bus.subscribe(
        "instance.DEMO.*",
        handler.handle_event
    )

    # Publish some events
    events = [
        DopemuxEvent.create(
            event_type="task.started",
            namespace="instance.DEMO.tasks",
            payload={"task": "Implement event system", "estimated_time": "2 hours"},
            priority=Priority.HIGH
        ),
        DopemuxEvent.create(
            event_type="progress.updated",
            namespace="instance.DEMO.tasks",
            payload={"progress": 25, "milestone": "Architecture complete"},
            priority=Priority.NORMAL
        ),
        DopemuxEvent.create(
            event_type="celebration.achievement",
            namespace="instance.DEMO.motivation",
            payload={"message": "Great progress! 🎉", "achievement": "milestone_reached"},
            priority=Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MINIMAL,
                attention_required=False,
                interruption_safe=True,
                focus_context="positive_reinforcement"
            )
        )
    ]

    for event in events:
        await event_bus.publish(event)
        await asyncio.sleep(0.5)

    print(f"✅ Sent {len(events)} events, received {handler.events_received}")

    await event_bus.unsubscribe(subscription_id)
    await event_bus.disconnect()


async def demo_adhd_attention_filtering():
    """Demonstrate ADHD-optimized attention filtering."""
    print("\n🧠 Demo 2: ADHD Attention Filtering")
    print("=" * 50)

    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()

    handler = DemoEventHandler("FOCUSED")

    # Create attention mediator
    mediator = AttentionMediator(
        event_bus=event_bus,
        instance_id="FOCUSED",
        delivery_callback=handler.handle_event,
        batch_callback=handler.handle_batch
    )

    await mediator.start()

    print("🎯 Setting DEEP FOCUS mode (minimal interruptions)")
    mediator.update_focus_state(
        FocusState.DEEP,
        task_context="implementation",
        interruption_tolerance=InterruptionTolerance.CRITICAL
    )

    # Send events with different priorities
    test_events = [
        ("🚨 Critical system error", Priority.CRITICAL, "Should be delivered immediately"),
        ("📝 Normal progress update", Priority.NORMAL, "Should be queued"),
        ("🎉 Low priority celebration", Priority.LOW, "Should be queued"),
        ("⚠️ High priority warning", Priority.HIGH, "Should be queued (not critical)")
    ]

    print("\nSending events during DEEP FOCUS:")
    for description, priority, expectation in test_events:
        event = DopemuxEvent.create(
            event_type="test.event",
            namespace="instance.FOCUSED.test",
            payload={"description": description, "expectation": expectation},
            priority=priority
        )
        await event_bus.publish(event)
        print(f"  {description} ({priority.value}) - {expectation}")
        await asyncio.sleep(0.2)

    await asyncio.sleep(1)

    print(f"\n📊 During deep focus: {handler.events_received} events delivered immediately")
    print(f"🗃️ Queued events: {len(mediator.event_queue)}")

    print("\n☕ Switching to BREAK mode (deliver queued events)")
    mediator.update_focus_state(FocusState.BREAK)
    await asyncio.sleep(1)

    print(f"📬 After break: Total events delivered: {handler.events_received}")

    await mediator.stop()
    await event_bus.disconnect()


async def demo_multi_instance_coordination():
    """Demonstrate multi-instance coordination."""
    print("\n🏢 Demo 3: Multi-Instance Coordination")
    print("=" * 50)

    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()

    # Create instance registry
    registry = InstanceRegistry(event_bus)
    await registry.start()

    # Register multiple instances
    instances = ["A", "B", "C"]
    port_bases = [3000, 3030, 3060]

    for instance_id, port_base in zip(instances, port_bases):
        await registry.register_instance(
            instance_id=instance_id,
            port_base=port_base,
            git_branch=f"feature/{instance_id.lower()}",
            user=f"developer_{instance_id.lower()}"
        )
        await registry.update_instance_status(instance_id, InstanceStatus.ACTIVE)

    print(f"📝 Registered {len(instances)} instances")

    # Show instance coordination
    active_instances = registry.get_active_instances()
    for instance in active_instances:
        print(f"  Instance {instance.instance_id}: port {instance.port_base}, branch {instance.git_branch}")

    # Demonstrate session handoff
    print("\n🔄 Demonstrating session handoff from A to B")
    session_data = {
        "current_task": "Event system implementation",
        "focus_context": "deep_work",
        "progress_percent": 85,
        "last_file": "dopemux/event_bus.py"
    }

    success = await registry.request_session_handoff("A", "B", session_data)
    print(f"Session handoff success: {success}")

    # Show registry status
    status = registry.get_registry_status()
    print(f"\n📊 Registry Status:")
    print(f"  Total instances: {status['total_instances']}")
    print(f"  Active instances: {status['active_instances']}")
    print(f"  Port allocations: {status['allocated_ports']}")

    await registry.stop()
    await event_bus.disconnect()


async def demo_producer_integration():
    """Demonstrate event producers for MCP and ConPort."""
    print("\n🔧 Demo 4: Event Producer Integration")
    print("=" * 50)

    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()

    handler = DemoEventHandler("PRODUCERS")

    # Subscribe to producer events
    subscription_id = await event_bus.subscribe(
        "instance.PRODUCERS.*",
        handler.handle_event
    )

    # Create producers
    mcp_producer = MCPEventProducer(event_bus, "PRODUCERS")
    conport_producer = ConPortEventProducer(event_bus, "PRODUCERS", "/demo/workspace")

    print("🔧 Simulating MCP tool call")
    call_id = await mcp_producer.on_tool_call_start(
        "mcp__conport__log_decision",
        {"summary": "Demo decision", "rationale": "For demonstration"}
    )

    await asyncio.sleep(0.5)

    await mcp_producer.on_tool_call_complete(
        call_id,
        "mcp__conport__log_decision",
        {"summary": "Demo decision"},
        {"decision_id": 42},
        error=None
    )

    print("📝 Simulating ConPort decision logging")
    await conport_producer.on_decision_logged(
        decision_id=42,
        summary="Use event-driven architecture for Dopemux",
        rationale="Enables better multi-instance coordination and ADHD accommodations",
        tags=["architecture", "events", "adhd"],
        implementation_details="Redis Streams with hierarchical namespacing"
    )

    print("🎯 Simulating progress update")
    await conport_producer.on_progress_updated(
        progress_id=123,
        description="Implement event system demo",
        old_status="in_progress",
        new_status="done"
    )

    await asyncio.sleep(1)

    print(f"✅ Producer demo complete. Events received: {handler.events_received}")

    await event_bus.unsubscribe(subscription_id)
    await event_bus.disconnect()


async def demo_performance_test():
    """Demonstrate performance characteristics."""
    print("\n⚡ Demo 5: Performance Test")
    print("=" * 50)

    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()

    handler = DemoEventHandler("PERF")
    subscription_id = await event_bus.subscribe("perf.test.*", handler.handle_event)

    # Performance test
    num_events = 100
    print(f"🚀 Sending {num_events} events...")

    start_time = time.time()

    for i in range(num_events):
        event = DopemuxEvent.create(
            event_type="perf.test.event",
            namespace="perf.test.load",
            payload={"index": i, "timestamp": time.time()},
            priority=Priority.NORMAL
        )
        await event_bus.publish(event)

    publish_time = time.time() - start_time

    # Wait for processing
    await asyncio.sleep(2)

    throughput = num_events / publish_time
    print(f"📊 Performance Results:")
    print(f"  Publish rate: {throughput:.0f} events/second")
    print(f"  Events received: {handler.events_received}")
    print(f"  Latency: {(publish_time / num_events) * 1000:.1f}ms per event")

    await event_bus.unsubscribe(subscription_id)
    await event_bus.disconnect()


async def main():
    """Run all demos."""
    print("🎪 Dopemux Event-Driven Architecture Demo")
    print("==========================================")
    print()
    print("This demo showcases:")
    print("• Basic event publishing and subscription")
    print("• ADHD-optimized attention filtering")
    print("• Multi-instance coordination")
    print("• Event producer integration")
    print("• Performance characteristics")
    print()

    try:
        await demo_basic_event_flow()
        await demo_adhd_attention_filtering()
        await demo_multi_instance_coordination()
        await demo_producer_integration()
        await demo_performance_test()

        print("\n🎉 All demos completed successfully!")
        print("\nNext steps:")
        print("• Start Redis: docker-compose -f docker/docker-compose.event-bus.yml up -d")
        print("• Run tests: python -m pytest tests/test_event_multi_instance.py -v")
        print("• Integrate into Dopemux instances")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure Redis is running: docker-compose -f docker/docker-compose.event-bus.yml up -d")


if __name__ == "__main__":
    asyncio.run(main())