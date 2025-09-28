#!/usr/bin/env python3
"""
MCP Event Integration Demo

Demonstrates how to integrate event producers with real MCP tool calls.
This script shows the integration pattern without modifying the MCP infrastructure.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
from dopemux.producers.mcp_producer import MCPEventProducer
from dopemux.producers.conport_producer import ConPortEventProducer


class MCPEventIntegrator:
    """
    Integration layer that wraps MCP tool calls with event emission.

    This demonstrates the pattern for integrating event producers
    with existing MCP infrastructure without modification.
    """

    def __init__(self, event_bus: RedisStreamsAdapter, instance_id: str):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.mcp_producer = MCPEventProducer(event_bus, instance_id)
        self.conport_producer = ConPortEventProducer(event_bus, instance_id, "/Users/hue/code/dopemux-mvp")

    async def start(self):
        """Initialize the integration layer."""
        await self.event_bus.connect()
        print(f"🔗 MCP Event Integrator started for instance {self.instance_id}")

    async def stop(self):
        """Cleanup the integration layer."""
        await self.event_bus.disconnect()
        print(f"🔗 MCP Event Integrator stopped for instance {self.instance_id}")

    async def call_mcp_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper for MCP tool calls that emits events.

        This is the integration pattern - wrap existing tool calls
        with event emission before and after.
        """
        # Emit start event
        call_id = await self.mcp_producer.on_tool_call_start(tool_name, args)

        start_time = time.time()
        result = None
        error = None

        try:
            # Simulate the actual MCP tool call
            # In real integration, this would call the actual MCP service
            result = await self._simulate_mcp_call(tool_name, args)

        except Exception as e:
            error = str(e)
            result = {"error": error}

        finally:
            # Emit completion event
            await self.mcp_producer.on_tool_call_complete(
                call_id, tool_name, args, result, error
            )

        return result

    async def _simulate_mcp_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MCP tool calls for demonstration."""

        # Simulate processing time
        await asyncio.sleep(0.1)

        if tool_name == "mcp__conport__log_decision":
            return await self._simulate_conport_decision(args)
        elif tool_name == "mcp__conport__log_progress":
            return await self._simulate_conport_progress(args)
        elif tool_name == "mcp__conport__get_active_context":
            return await self._simulate_conport_get_context()
        else:
            return {"status": "success", "tool": tool_name, "timestamp": datetime.utcnow().isoformat()}

    async def _simulate_conport_decision(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate ConPort decision logging with event emission."""
        decision_id = 12345

        # Emit ConPort-specific event
        await self.conport_producer.on_decision_logged(
            decision_id=decision_id,
            summary=args.get("summary", "Demo decision"),
            rationale=args.get("rationale", "For demonstration purposes"),
            tags=args.get("tags", ["demo", "integration"]),
            implementation_details=args.get("implementation_details", "Event integration demo")
        )

        return {
            "id": decision_id,
            "summary": args.get("summary"),
            "status": "logged",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _simulate_conport_progress(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate ConPort progress logging with event emission."""
        progress_id = 67890

        # Emit ConPort-specific event
        await self.conport_producer.on_progress_updated(
            progress_id=progress_id,
            description=args.get("description", "Demo progress"),
            old_status="pending",
            new_status=args.get("status", "in_progress")
        )

        return {
            "id": progress_id,
            "description": args.get("description"),
            "status": args.get("status"),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _simulate_conport_get_context(self) -> Dict[str, Any]:
        """Simulate ConPort context retrieval."""
        # This would emit a context access event
        await self.conport_producer.on_context_accessed(
            context_type="active_context",
            access_reason="integration_demo"
        )

        return {
            "context": {
                "phase": "Phase 2: Integration",
                "current_focus": "MCP event integration",
                "instance_id": self.instance_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }


class EventListener:
    """Listens for events and displays them."""

    def __init__(self, event_bus: RedisStreamsAdapter, instance_id: str):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.events_received = 0

    async def start_listening(self):
        """Start listening for events."""
        subscription_id = await self.event_bus.subscribe(
            f"instance.{self.instance_id}.*",
            self.handle_event
        )
        print(f"👂 Event listener started for instance {self.instance_id}")
        return subscription_id

    def handle_event(self, event: DopemuxEvent):
        """Handle received events."""
        self.events_received += 1

        print(f"📨 [{self.instance_id}] Received event: {event.envelope.type}")
        print(f"   Namespace: {event.envelope.namespace}")
        print(f"   Priority: {event.envelope.priority.value}")

        # Parse payload for specific event types
        if "mcp.tool_call" in event.envelope.type:
            tool_name = event.payload.get("tool_name", "unknown")
            if event.envelope.type.endswith(".started"):
                print(f"   🔧 Tool Call Started: {tool_name}")
            elif event.envelope.type.endswith(".completed"):
                duration = event.payload.get("duration_ms", 0)
                print(f"   ✅ Tool Call Completed: {tool_name} ({duration}ms)")

        elif "conport" in event.envelope.type:
            if "decision.logged" in event.envelope.type:
                summary = event.payload.get("summary", "")
                print(f"   📝 Decision Logged: {summary}")
            elif "progress.updated" in event.envelope.type:
                description = event.payload.get("description", "")
                status = event.payload.get("new_status", "")
                print(f"   📈 Progress Updated: {description} → {status}")

        print()


async def demo_mcp_integration():
    """Demonstrate MCP tool call integration with events."""
    print("🔗 Demo: MCP Event Integration")
    print("=" * 50)

    # Setup
    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    integrator = MCPEventIntegrator(event_bus, "INTEGRATION_DEMO")
    listener = EventListener(event_bus, "INTEGRATION_DEMO")

    await integrator.start()
    subscription_id = await listener.start_listening()

    # Demo tool calls with event emission
    print("🔧 Simulating MCP tool calls with event integration:")
    print()

    # 1. ConPort decision logging
    print("1. ConPort decision logging:")
    result = await integrator.call_mcp_tool(
        "mcp__conport__log_decision",
        {
            "summary": "Integrate event system with MCP tools",
            "rationale": "Enable real-time coordination across instances",
            "tags": ["integration", "events", "mcp"]
        }
    )
    print(f"   Result: {result}")
    print()

    # 2. ConPort progress tracking
    print("2. ConPort progress tracking:")
    result = await integrator.call_mcp_tool(
        "mcp__conport__log_progress",
        {
            "description": "MCP event integration implementation",
            "status": "in_progress"
        }
    )
    print(f"   Result: {result}")
    print()

    # 3. ConPort context access
    print("3. ConPort context access:")
    result = await integrator.call_mcp_tool(
        "mcp__conport__get_active_context",
        {}
    )
    print(f"   Result: {result}")
    print()

    # 4. Generic MCP tool
    print("4. Generic MCP tool call:")
    result = await integrator.call_mcp_tool(
        "mcp__zen__chat",
        {
            "prompt": "How is the event integration working?",
            "model": "flash"
        }
    )
    print(f"   Result: {result}")
    print()

    # Give events time to process
    await asyncio.sleep(2)

    print(f"📊 Integration Summary:")
    print(f"   Events received: {listener.events_received}")
    print(f"   Integration pattern demonstrated successfully!")

    # Cleanup
    await event_bus.unsubscribe(subscription_id)
    await integrator.stop()


async def demo_multi_instance_coordination():
    """Demonstrate coordination between multiple instances."""
    print("\n🏢 Demo: Multi-Instance Coordination via Events")
    print("=" * 50)

    event_bus = RedisStreamsAdapter("redis://localhost:6379")

    # Create integrators for multiple instances
    integrator_a = MCPEventIntegrator(event_bus, "A")
    integrator_b = MCPEventIntegrator(event_bus, "B")

    # Create cross-instance listener for coordination
    class CoordinationListener:
        def __init__(self):
            self.coordination_events = 0

        def handle_coordination_event(self, event: DopemuxEvent):
            self.coordination_events += 1
            print(f"🔄 Coordination: {event.envelope.type}")
            print(f"   From: {event.envelope.namespace}")
            print(f"   Data: {event.payload}")
            print()

    coord_listener = CoordinationListener()

    await integrator_a.start()
    await integrator_b.start()

    # Subscribe to shared coordination namespace
    coord_subscription = await event_bus.subscribe(
        "shared.coordination.*",
        coord_listener.handle_coordination_event
    )

    print("🚀 Simulating cross-instance coordination:")
    print()

    # Instance A logs a decision
    await integrator_a.call_mcp_tool(
        "mcp__conport__log_decision",
        {
            "summary": "Use Redis Streams for event coordination",
            "rationale": "Provides exactly-once delivery with persistence"
        }
    )

    # Instance B responds with progress
    await integrator_b.call_mcp_tool(
        "mcp__conport__log_progress",
        {
            "description": "Implementing Redis Streams integration",
            "status": "active"
        }
    )

    # Emit explicit coordination event
    coordination_event = DopemuxEvent.create(
        event_type="coordination.session_handoff",
        namespace="shared.coordination.instances",
        payload={
            "from_instance": "A",
            "to_instance": "B",
            "context": "Event system integration work",
            "reason": "Scheduled break"
        },
        priority=Priority.HIGH,
        adhd_metadata=ADHDMetadata(
            cognitive_load=CognitiveLoad.LOW,
            attention_required=True,
            interruption_safe=False,
            focus_context="coordination"
        )
    )

    await event_bus.publish(coordination_event)

    await asyncio.sleep(1)

    print(f"📊 Coordination Summary:")
    print(f"   Coordination events: {coord_listener.coordination_events}")
    print(f"   Multi-instance coordination working!")

    # Cleanup
    await event_bus.unsubscribe(coord_subscription)
    await integrator_a.stop()
    await integrator_b.stop()


async def main():
    """Run the MCP integration demonstration."""
    print("🎪 MCP Event Integration Demonstration")
    print("======================================")
    print()
    print("This demo shows how to integrate event producers with MCP tools:")
    print("• Wrap MCP tool calls with event emission")
    print("• Emit ConPort-specific events for decisions and progress")
    print("• Coordinate between multiple instances via events")
    print("• Maintain ADHD-optimized event filtering")
    print()

    try:
        await demo_mcp_integration()
        await demo_multi_instance_coordination()

        print("\n🎉 MCP Integration Demo Complete!")
        print()
        print("Integration Pattern Summary:")
        print("• MCPEventIntegrator wraps tool calls with event emission")
        print("• ConPortEventProducer emits domain-specific events")
        print("• Events enable real-time coordination across instances")
        print("• No modification to existing MCP infrastructure required")
        print()
        print("Next Steps:")
        print("• Deploy this pattern to production MCP services")
        print("• Add event integration to Claude Code MCP wrapper")
        print("• Enable real-time instance coordination")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Ensure Redis is running: docker-compose -f docker/docker-compose.event-bus.yml up -d")


if __name__ == "__main__":
    asyncio.run(main())