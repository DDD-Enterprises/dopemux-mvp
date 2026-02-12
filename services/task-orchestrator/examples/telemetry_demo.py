#!/usr/bin/env python3
"""
Demo: Event Coordinator Suppression Telemetry

Shows how to use the new telemetry features to measure signal/noise ratio
and understand which suppression rules are most active.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from event_coordinator import (
    EventCoordinator,
    CoordinationEvent,
    EventType,
    EventPriority
)


async def demo():
    """Demonstrate suppression telemetry."""
    print("🚀 Event Coordinator Suppression Telemetry Demo\n")

    # Create coordinator (won't actually connect to Redis in demo)
    coordinator = EventCoordinator(redis_url="redis://localhost:6379")

    # Simulate different scenarios

    # Scenario 1: Normal operation (high signal/noise)
    print("📊 Scenario 1: Normal operation")
    coordinator.current_focus_mode = "normal"
    coordinator.current_energy_level = "medium"
    coordinator._get_recent_event_count = lambda _: asyncio.create_task(
        asyncio.coroutine(lambda: 0)()
    )

    for i in range(10):
        event = CoordinationEvent(
            id=f"normal_{i}",
            event_type=EventType.TASK_CREATED,
            priority=EventPriority.MEDIUM,
            source_system="demo",
            target_systems=["test"],
            cognitive_load=0.5
        )
        await coordinator._should_process_event(event)

    report = coordinator.get_suppression_report()
    print(f"  Events received: {report['summary']['events_received']}")
    print(f"  Events passed: {report['summary']['events_passed']}")
    print(f"  Signal/Noise ratio: {report['summary']['signal_noise_ratio']:.2f}")
    print(f"  Suppression rate: {report['summary']['suppression_rate_pct']:.1f}%\n")

    # Scenario 2: Deep focus mode (lower signal/noise)
    print("📊 Scenario 2: Deep focus mode - suppress low priority")
    coordinator.current_focus_mode = "deep"

    for i in range(5):
        event = CoordinationEvent(
            id=f"deep_low_{i}",
            event_type=EventType.TASK_UPDATED,
            priority=EventPriority.LOW,  # Will be suppressed
            source_system="demo",
            target_systems=["test"]
        )
        await coordinator._should_process_event(event)

    report = coordinator.get_suppression_report()
    print(f"  Events received: {report['summary']['events_received']}")
    print(f"  Events passed: {report['summary']['events_passed']}")
    print(f"  Signal/Noise ratio: {report['summary']['signal_noise_ratio']:.2f}")
    print(f"  Suppression rate: {report['summary']['suppression_rate_pct']:.1f}%")
    print(f"  Suppressed by deep_focus_priority: {report['per_rule_breakdown']['deep_focus_priority']}\n")

    # Scenario 3: Low energy mode (suppress high cognitive load)
    print("📊 Scenario 3: Low energy - suppress complex events")
    coordinator.current_focus_mode = "normal"
    coordinator.current_energy_level = "low"

    for i in range(3):
        event = CoordinationEvent(
            id=f"low_energy_{i}",
            event_type=EventType.SPRINT_STARTED,
            priority=EventPriority.MEDIUM,
            source_system="demo",
            target_systems=["test"],
            cognitive_load=0.9  # High cognitive load - will be suppressed
        )
        await coordinator._should_process_event(event)

    report = coordinator.get_suppression_report()
    print(f"  Events received: {report['summary']['events_received']}")
    print(f"  Events passed: {report['summary']['events_passed']}")
    print(f"  Signal/Noise ratio: {report['summary']['signal_noise_ratio']:.2f}")
    print(f"  Suppression rate: {report['summary']['suppression_rate_pct']:.1f}%")
    print(f"  Suppressed by energy_level: {report['per_rule_breakdown']['energy_level']}\n")

    # Full report
    print("📊 Full Suppression Report:")
    print("=" * 60)

    print("\n📈 Summary:")
    for key, value in report['summary'].items():
        print(f"  {key}: {value}")

    print("\n🎯 Per-Rule Breakdown:")
    for rule, count in report['per_rule_breakdown'].items():
        if count > 0:
            print(f"  {rule}: {count}")

    print("\n📋 Per-Event-Type:")
    for event_type, stats in report['per_event_type'].items():
        print(f"  {event_type}: received={stats['received']}, suppressed={stats['suppressed']}")

    print("\n🎚️ Per-Priority:")
    for priority, stats in report['per_priority'].items():
        print(f"  {priority}: received={stats['received']}, suppressed={stats['suppressed']}")

    print("\n🧠 ADHD State:")
    for key, value in report['adhd_state'].items():
        print(f"  {key}: {value}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo())
