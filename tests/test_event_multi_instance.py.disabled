"""
Integration Tests for Dopemux Event-Driven Multi-Instance Architecture

Tests isolation, coordination, and ADHD filtering across multiple instances.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from dopemux.event_bus import (
    EventBus, DopemuxEvent, RedisStreamsAdapter, InMemoryAdapter,
    Priority, CognitiveLoad, ADHDMetadata
)
from dopemux.attention_mediator import AttentionMediator, FocusState, InterruptionTolerance
from dopemux.instance_registry import InstanceRegistry, InstanceStatus
from dopemux.producers.mcp_producer import MCPEventProducer
from dopemux.producers.conport_producer import ConPortEventProducer


class TestEventCollector:
    """Helper class to collect events for testing."""

    def __init__(self):
        self.events: List[DopemuxEvent] = []
        self.batches: List[Any] = []

    def collect_event(self, event: DopemuxEvent):
        """Collect individual events."""
        self.events.append(event)

    def collect_batch(self, batch: Any):
        """Collect event batches."""
        self.batches.append(batch)

    def reset(self):
        """Reset collected events."""
        self.events.clear()
        self.batches.clear()


@pytest.fixture
async def redis_event_bus():
    """Redis event bus fixture."""
    adapter = RedisStreamsAdapter("redis://localhost:6379")
    await adapter.connect()
    yield adapter
    await adapter.disconnect()


@pytest.fixture
def memory_event_bus():
    """In-memory event bus fixture."""
    return InMemoryAdapter()


@pytest.fixture
def event_collector():
    """Event collector fixture."""
    return TestEventCollector()


class TestBasicEventBus:
    """Test basic event bus functionality."""

    @pytest.mark.asyncio
    async def test_memory_adapter_basic_flow(self, memory_event_bus, event_collector):
        """Test basic publish/subscribe with memory adapter."""
        # Subscribe to events
        subscription_id = await memory_event_bus.subscribe(
            "instance.A.*",
            event_collector.collect_event
        )

        # Create and publish event
        event = DopemuxEvent.create(
            event_type="test.event",
            namespace="instance.A.test",
            payload={"message": "Hello World"},
            priority=Priority.NORMAL
        )

        success = await memory_event_bus.publish(event)
        assert success

        # Allow async processing
        await asyncio.sleep(0.1)

        # Verify event was received
        assert len(event_collector.events) == 1
        received_event = event_collector.events[0]
        assert received_event.envelope.type == "test.event"
        assert received_event.payload["message"] == "Hello World"

        # Cleanup
        await memory_event_bus.unsubscribe(subscription_id)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_redis_adapter_basic_flow(self, redis_event_bus, event_collector):
        """Test basic publish/subscribe with Redis adapter."""
        # Subscribe to events
        subscription_id = await redis_event_bus.subscribe(
            "instance.B.*",
            event_collector.collect_event
        )

        # Allow subscription to initialize
        await asyncio.sleep(0.5)

        # Create and publish event
        event = DopemuxEvent.create(
            event_type="test.redis.event",
            namespace="instance.B.test",
            payload={"redis": True, "timestamp": datetime.now().isoformat()},
            priority=Priority.HIGH
        )

        success = await redis_event_bus.publish(event)
        assert success

        # Allow Redis processing
        await asyncio.sleep(1.0)

        # Verify event was received
        assert len(event_collector.events) >= 1
        received_event = event_collector.events[0]
        assert received_event.envelope.type == "test.redis.event"
        assert received_event.payload["redis"] is True

        # Cleanup
        await redis_event_bus.unsubscribe(subscription_id)


class TestMultiInstanceIsolation:
    """Test isolation between multiple instances."""

    @pytest.mark.asyncio
    async def test_instance_event_isolation(self, memory_event_bus):
        """Test that instances only receive their own events."""
        collector_a = TestEventCollector()
        collector_b = TestEventCollector()

        # Subscribe each instance to its own namespace
        sub_a = await memory_event_bus.subscribe("instance.A.*", collector_a.collect_event)
        sub_b = await memory_event_bus.subscribe("instance.B.*", collector_b.collect_event)

        # Publish events to each instance
        event_a = DopemuxEvent.create(
            event_type="task.started",
            namespace="instance.A.task",
            payload={"task": "A-specific task"}
        )

        event_b = DopemuxEvent.create(
            event_type="task.started",
            namespace="instance.B.task",
            payload={"task": "B-specific task"}
        )

        await memory_event_bus.publish(event_a)
        await memory_event_bus.publish(event_b)
        await asyncio.sleep(0.1)

        # Verify isolation
        assert len(collector_a.events) == 1
        assert len(collector_b.events) == 1
        assert collector_a.events[0].payload["task"] == "A-specific task"
        assert collector_b.events[0].payload["task"] == "B-specific task"

        # Cleanup
        await memory_event_bus.unsubscribe(sub_a)
        await memory_event_bus.unsubscribe(sub_b)

    @pytest.mark.asyncio
    async def test_shared_namespace_coordination(self, memory_event_bus):
        """Test that shared events reach multiple instances."""
        collector_a = TestEventCollector()
        collector_b = TestEventCollector()

        # Subscribe both instances to shared namespace
        sub_a = await memory_event_bus.subscribe("shared.team.*", collector_a.collect_event)
        sub_b = await memory_event_bus.subscribe("shared.team.*", collector_b.collect_event)

        # Publish shared event
        shared_event = DopemuxEvent.create(
            event_type="team.decision.logged",
            namespace="shared.team.decisions",
            payload={"decision": "Use microservices architecture"}
        )

        await memory_event_bus.publish(shared_event)
        await asyncio.sleep(0.1)

        # Verify both instances received the event
        assert len(collector_a.events) == 1
        assert len(collector_b.events) == 1
        assert collector_a.events[0].payload["decision"] == collector_b.events[0].payload["decision"]

        # Cleanup
        await memory_event_bus.unsubscribe(sub_a)
        await memory_event_bus.unsubscribe(sub_b)


class TestADHDAttentionFiltering:
    """Test ADHD-specific attention filtering."""

    @pytest.mark.asyncio
    async def test_deep_focus_filtering(self, memory_event_bus, event_collector):
        """Test that deep focus mode filters out non-critical events."""
        # Create attention mediator in deep focus mode
        mediator = AttentionMediator(
            event_bus=memory_event_bus,
            instance_id="A",
            delivery_callback=event_collector.collect_event,
            batch_callback=event_collector.collect_batch
        )

        await mediator.start()

        # Set deep focus mode
        mediator.update_focus_state(
            FocusState.DEEP,
            task_context="implementation",
            interruption_tolerance=InterruptionTolerance.CRITICAL
        )

        # Create events with different priorities
        critical_event = DopemuxEvent.create(
            event_type="system.error.critical",
            namespace="instance.A.system",
            payload={"error": "Database connection lost"},
            priority=Priority.CRITICAL
        )

        normal_event = DopemuxEvent.create(
            event_type="task.progress.updated",
            namespace="instance.A.task",
            payload={"task": "Feature implementation", "progress": 50},
            priority=Priority.NORMAL
        )

        low_event = DopemuxEvent.create(
            event_type="celebration.task.completed",
            namespace="instance.A.celebration",
            payload={"message": "Great job!"},
            priority=Priority.LOW
        )

        # Publish events
        await memory_event_bus.publish(critical_event)
        await memory_event_bus.publish(normal_event)
        await memory_event_bus.publish(low_event)

        await asyncio.sleep(0.2)

        # Only critical event should be delivered immediately
        assert len(event_collector.events) == 1
        assert event_collector.events[0].envelope.priority == Priority.CRITICAL

        # Other events should be queued
        assert len(mediator.event_queue) >= 2

        await mediator.stop()

    @pytest.mark.asyncio
    async def test_break_time_batch_delivery(self, memory_event_bus, event_collector):
        """Test that batched events are delivered during break time."""
        mediator = AttentionMediator(
            event_bus=memory_event_bus,
            instance_id="B",
            delivery_callback=event_collector.collect_event,
            batch_callback=event_collector.collect_batch
        )

        await mediator.start()

        # Start in deep focus to queue events
        mediator.update_focus_state(FocusState.DEEP)

        # Create low-priority events
        for i in range(3):
            event = DopemuxEvent.create(
                event_type="info.update",
                namespace="instance.B.info",
                payload={"update": f"Update {i}"},
                priority=Priority.LOW
            )
            await memory_event_bus.publish(event)

        await asyncio.sleep(0.1)

        # Events should be queued, not delivered
        initial_delivered = len(event_collector.events)

        # Switch to break mode
        mediator.update_focus_state(FocusState.BREAK)
        await asyncio.sleep(0.2)

        # Should have received batched events
        assert len(event_collector.events) > initial_delivered or len(event_collector.batches) > 0

        await mediator.stop()


class TestInstanceRegistry:
    """Test instance registry functionality."""

    @pytest.mark.asyncio
    async def test_instance_registration(self, memory_event_bus, event_collector):
        """Test instance registration and discovery."""
        registry = InstanceRegistry(memory_event_bus)

        # Subscribe to instance events
        sub_id = await memory_event_bus.subscribe("global.instance.*", event_collector.collect_event)

        await registry.start()

        # Register an instance
        instance = await registry.register_instance(
            instance_id="TEST",
            port_base=3000,
            git_branch="feature/test",
            user="testuser"
        )

        await asyncio.sleep(0.1)

        # Verify instance was registered
        assert instance.instance_id == "TEST"
        assert instance.port_base == 3000
        assert instance.git_branch == "feature/test"

        # Verify registration event was emitted
        registration_events = [
            e for e in event_collector.events
            if "registered" in e.envelope.type
        ]
        assert len(registration_events) >= 1

        # Test instance lookup
        found_instance = registry.get_instance("TEST")
        assert found_instance is not None
        assert found_instance.instance_id == "TEST"

        # Test port allocation
        assert 3000 in registry.port_allocations

        # Cleanup
        await registry.unregister_instance("TEST")
        await registry.stop()
        await memory_event_bus.unsubscribe(sub_id)

    @pytest.mark.asyncio
    async def test_session_handoff(self, memory_event_bus, event_collector):
        """Test session handoff between instances."""
        registry = InstanceRegistry(memory_event_bus)

        # Subscribe to handoff events
        sub_id = await memory_event_bus.subscribe("shared.session.*", event_collector.collect_event)

        await registry.start()

        # Register two instances
        await registry.register_instance("FROM", 3000)
        await registry.register_instance("TO", 3030)

        # Update status to active
        await registry.update_instance_status("FROM", InstanceStatus.ACTIVE)
        await registry.update_instance_status("TO", InstanceStatus.ACTIVE)

        # Request session handoff
        session_data = {
            "current_task": "Feature implementation",
            "focus_context": "coding",
            "progress": 75
        }

        success = await registry.request_session_handoff("FROM", "TO", session_data)
        assert success

        await asyncio.sleep(0.1)

        # Verify handoff event was emitted
        handoff_events = [
            e for e in event_collector.events
            if "handoff" in e.envelope.type
        ]
        assert len(handoff_events) >= 1

        handoff_event = handoff_events[0]
        assert handoff_event.payload["from_instance"] == "FROM"
        assert handoff_event.payload["to_instance"] == "TO"
        assert handoff_event.payload["session_data"]["current_task"] == "Feature implementation"

        # Cleanup
        await registry.stop()
        await memory_event_bus.unsubscribe(sub_id)


class TestEventProducers:
    """Test event producers functionality."""

    @pytest.mark.asyncio
    async def test_mcp_producer_tool_tracking(self, memory_event_bus, event_collector):
        """Test MCP producer tracks tool calls correctly."""
        producer = MCPEventProducer(memory_event_bus, "TEST")

        # Subscribe to MCP events
        sub_id = await memory_event_bus.subscribe("instance.TEST.mcp.*", event_collector.collect_event)

        # Simulate tool call
        call_id = await producer.on_tool_call_start(
            "mcp__zen__thinkdeep",
            {"prompt": "Think about architecture", "model": "o3"}
        )

        await asyncio.sleep(0.1)

        # Should have start event for long-running tool
        start_events = [e for e in event_collector.events if "started" in e.envelope.type]
        assert len(start_events) >= 1

        # Simulate completion
        await producer.on_tool_call_complete(
            call_id,
            "mcp__zen__thinkdeep",
            {"prompt": "Think about architecture"},
            {"analysis": "Deep thinking completed"},
            error=None
        )

        await asyncio.sleep(0.1)

        # Should have completion event
        completion_events = [e for e in event_collector.events if "completed" in e.envelope.type]
        assert len(completion_events) >= 1

        completion_event = completion_events[0]
        assert completion_event.payload["tool"] == "mcp__zen__thinkdeep"
        assert completion_event.payload["success"] is True

        await memory_event_bus.unsubscribe(sub_id)

    @pytest.mark.asyncio
    async def test_conport_producer_decision_tracking(self, memory_event_bus, event_collector):
        """Test ConPort producer tracks decisions correctly."""
        producer = ConPortEventProducer(memory_event_bus, "TEST", "/test/workspace")

        # Subscribe to ConPort events
        sub_id = await memory_event_bus.subscribe("instance.TEST.conport.*", event_collector.collect_event)

        # Simulate decision logging
        await producer.on_decision_logged(
            decision_id=42,
            summary="Use Redis for event streaming",
            rationale="Redis Streams provide exactly-once semantics and good performance",
            tags=["architecture", "event-driven"],
            implementation_details="Configure Redis with consumer groups"
        )

        await asyncio.sleep(0.1)

        # Should have decision event
        decision_events = [e for e in event_collector.events if "decision" in e.envelope.type]
        assert len(decision_events) >= 1

        decision_event = decision_events[0]
        assert decision_event.payload["decision_id"] == 42
        assert decision_event.payload["summary"] == "Use Redis for event streaming"
        assert "architecture" in decision_event.payload["tags"]

        # Architectural decisions should have high priority
        assert decision_event.envelope.priority == Priority.HIGH

        await memory_event_bus.unsubscribe(sub_id)


class TestPerformanceAndScale:
    """Test performance characteristics and scalability."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_event_throughput(self, memory_event_bus):
        """Test event bus can handle required throughput."""
        collector = TestEventCollector()

        # Subscribe to events
        sub_id = await memory_event_bus.subscribe("perf.test.*", collector.collect_event)

        # Publish many events quickly
        num_events = 1000
        start_time = time.time()

        for i in range(num_events):
            event = DopemuxEvent.create(
                event_type="perf.test.event",
                namespace="perf.test.load",
                payload={"index": i, "timestamp": time.time()},
                priority=Priority.NORMAL
            )
            await memory_event_bus.publish(event)

        publish_time = time.time() - start_time

        # Allow processing
        await asyncio.sleep(1.0)

        # Verify all events were processed
        assert len(collector.events) == num_events

        # Calculate throughput
        throughput = num_events / publish_time
        print(f"Event throughput: {throughput:.0f} events/second")

        # Should handle at least 100 events/second
        assert throughput > 100

        await memory_event_bus.unsubscribe(sub_id)

    @pytest.mark.asyncio
    async def test_multiple_instance_simulation(self, memory_event_bus):
        """Simulate multiple instances working simultaneously."""
        # Create collectors for 3 instances
        collectors = {
            "A": TestEventCollector(),
            "B": TestEventCollector(),
            "C": TestEventCollector()
        }

        # Subscribe each instance
        subscriptions = {}
        for instance_id in collectors.keys():
            subscriptions[instance_id] = await memory_event_bus.subscribe(
                f"instance.{instance_id}.*",
                collectors[instance_id].collect_event
            )

        # Simulate concurrent work across instances
        tasks = []
        for instance_id in ["A", "B", "C"]:
            task = asyncio.create_task(
                self._simulate_instance_work(memory_event_bus, instance_id, num_events=50)
            )
            tasks.append(task)

        # Wait for all instances to complete work
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.5)

        # Verify each instance received only its events
        for instance_id, collector in collectors.items():
            assert len(collector.events) == 50
            # All events should be for this instance
            for event in collector.events:
                assert event.envelope.namespace.startswith(f"instance.{instance_id}")

        # Cleanup
        for sub_id in subscriptions.values():
            await memory_event_bus.unsubscribe(sub_id)

    async def _simulate_instance_work(self, event_bus: EventBus, instance_id: str, num_events: int):
        """Simulate work happening on an instance."""
        for i in range(num_events):
            event = DopemuxEvent.create(
                event_type="work.task.progress",
                namespace=f"instance.{instance_id}.work",
                payload={
                    "instance": instance_id,
                    "task_index": i,
                    "work_type": "simulation"
                },
                priority=Priority.NORMAL
            )
            await event_bus.publish(event)

            # Small delay to simulate real work
            await asyncio.sleep(0.01)


# Utility functions for running tests
def run_integration_tests():
    """Run all integration tests."""
    print("🧪 Running Dopemux Event Architecture Integration Tests")

    # Run with pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not performance"  # Skip performance tests by default
    ])

def run_performance_tests():
    """Run performance tests only."""
    print("⚡ Running Performance Tests")

    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "performance"
    ])

def run_redis_tests():
    """Run Redis integration tests only."""
    print("🔴 Running Redis Integration Tests")

    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "integration"
    ])


if __name__ == "__main__":
    # Run basic tests by default
    run_integration_tests()