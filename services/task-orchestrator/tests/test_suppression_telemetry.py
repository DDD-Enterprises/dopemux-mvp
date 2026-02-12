"""
Tests for Event Coordinator Suppression Telemetry.

Validates that all 6 suppression rules are tracked correctly,
per-event-type and per-priority breakdowns work, and the
suppression report provides actionable signal/noise data.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from event_coordinator import (
    EventCoordinator,
    CoordinationEvent,
    EventType,
    EventPriority,
    SuppressionTelemetry
)


@pytest.fixture
async def coordinator():
    """Create EventCoordinator with mocked Redis for testing."""
    coord = EventCoordinator(redis_url="redis://localhost:6379")

    # Mock Redis to avoid actual connections
    coord.redis_client = AsyncMock()
    coord.redis_client.ping = AsyncMock(return_value=True)

    # Initialize queues and state without starting workers
    for priority in EventPriority:
        import asyncio
        coord.event_queues[priority] = asyncio.PriorityQueue()

    return coord


def create_test_event(
    event_type: EventType = EventType.TASK_CREATED,
    priority: EventPriority = EventPriority.MEDIUM,
    cognitive_load: float = 0.5,
    interruption_allowed: bool = True,
    expires_at = None
) -> CoordinationEvent:
    """Create a test event with specified parameters."""
    return CoordinationEvent(
        id=f"test_{datetime.now().timestamp()}",
        event_type=event_type,
        priority=priority,
        source_system="test",
        target_systems=["test"],
        cognitive_load=cognitive_load,
        interruption_allowed=interruption_allowed,
        expires_at=expires_at
    )


@pytest.mark.asyncio
async def test_baseline_pass_through(coordinator):
    """Test that events pass through when no suppression rules are triggered."""
    event = create_test_event()

    # Mock flood detection to return 0 (no flooding)
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    result = await coordinator._should_process_event(event)

    assert result is True
    assert coordinator.suppression_telemetry.events_received == 1
    assert coordinator.suppression_telemetry.events_passed == 1
    assert coordinator.suppression_telemetry.events_suppressed == 0


@pytest.mark.asyncio
async def test_custom_filter_suppression(coordinator):
    """Test that custom filters are tracked correctly."""
    # Register a custom filter that rejects all events
    async def reject_all_filter(event):
        return False

    coordinator.register_filter(reject_all_filter)
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    event = create_test_event()
    result = await coordinator._should_process_event(event)

    assert result is False
    assert coordinator.suppression_telemetry.events_received == 1
    assert coordinator.suppression_telemetry.events_passed == 0
    assert coordinator.suppression_telemetry.events_suppressed == 1
    assert coordinator.suppression_telemetry.suppressed_by_custom_filter == 1


@pytest.mark.asyncio
async def test_deep_focus_priority_suppression(coordinator):
    """Test that low-priority events are suppressed in deep focus mode."""
    coordinator.current_focus_mode = "deep"
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Low priority event should be suppressed in deep focus
    event = create_test_event(priority=EventPriority.LOW)
    result = await coordinator._should_process_event(event)

    assert result is False
    assert coordinator.suppression_telemetry.suppressed_by_deep_focus_priority == 1

    # High priority event should pass
    event2 = create_test_event(priority=EventPriority.HIGH)
    result2 = await coordinator._should_process_event(event2)

    assert result2 is True
    assert coordinator.suppression_telemetry.events_passed == 1


@pytest.mark.asyncio
async def test_deep_focus_interrupt_suppression(coordinator):
    """Test that non-interrupting events are suppressed in deep focus unless critical."""
    coordinator.current_focus_mode = "deep"
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # High priority but interruption_allowed=False should be suppressed
    event = create_test_event(
        priority=EventPriority.HIGH,
        interruption_allowed=False
    )
    result = await coordinator._should_process_event(event)

    assert result is False
    assert coordinator.suppression_telemetry.suppressed_by_deep_focus_interrupt == 1

    # Critical priority with interruption_allowed=False should pass
    event2 = create_test_event(
        priority=EventPriority.CRITICAL,
        interruption_allowed=False
    )
    result2 = await coordinator._should_process_event(event2)

    assert result2 is True


@pytest.mark.asyncio
async def test_energy_level_suppression(coordinator):
    """Test that high cognitive load events are suppressed when energy is low."""
    coordinator.current_energy_level = "low"
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # High cognitive load event should be suppressed
    event = create_test_event(cognitive_load=0.8)
    result = await coordinator._should_process_event(event)

    assert result is False
    assert coordinator.suppression_telemetry.suppressed_by_energy_level == 1

    # Low cognitive load event should pass
    event2 = create_test_event(cognitive_load=0.5)
    result2 = await coordinator._should_process_event(event2)

    assert result2 is True


@pytest.mark.asyncio
async def test_flood_suppression(coordinator):
    """Test that event flooding is detected and suppressed."""
    # Mock flood detection to return >10 events
    coordinator._get_recent_event_count = AsyncMock(return_value=15)

    event = create_test_event()
    result = await coordinator._should_process_event(event)

    assert result is False
    assert coordinator.suppression_telemetry.suppressed_by_flood == 1


@pytest.mark.asyncio
async def test_expiry_suppression(coordinator):
    """Test that expired events are tracked in suppression telemetry."""
    # Create an expired event
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    event = create_test_event(expires_at=expired_time)

    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Process the event (should hit expiry check in _process_event)
    await coordinator._process_event(event, "test-worker")

    assert coordinator.suppression_telemetry.suppressed_by_expiry == 1


@pytest.mark.asyncio
async def test_per_event_type_tracking(coordinator):
    """Test that per-event-type breakdown is tracked correctly."""
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Process different event types
    event1 = create_test_event(event_type=EventType.TASK_CREATED)
    event2 = create_test_event(event_type=EventType.TASK_UPDATED)
    event3 = create_test_event(event_type=EventType.TASK_CREATED)

    await coordinator._should_process_event(event1)
    await coordinator._should_process_event(event2)
    await coordinator._should_process_event(event3)

    # Check per-event-type counts
    assert coordinator.suppression_telemetry.per_event_type["task_created"]["received"] == 2
    assert coordinator.suppression_telemetry.per_event_type["task_updated"]["received"] == 1

    # Now suppress one TASK_CREATED event
    coordinator.current_energy_level = "low"
    event4 = create_test_event(
        event_type=EventType.TASK_CREATED,
        cognitive_load=0.8
    )
    await coordinator._should_process_event(event4)

    assert coordinator.suppression_telemetry.per_event_type["task_created"]["received"] == 3
    assert coordinator.suppression_telemetry.per_event_type["task_created"]["suppressed"] == 1


@pytest.mark.asyncio
async def test_per_priority_tracking(coordinator):
    """Test that per-priority breakdown is tracked correctly."""
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Process different priorities
    event1 = create_test_event(priority=EventPriority.CRITICAL)
    event2 = create_test_event(priority=EventPriority.HIGH)
    event3 = create_test_event(priority=EventPriority.MEDIUM)

    await coordinator._should_process_event(event1)
    await coordinator._should_process_event(event2)
    await coordinator._should_process_event(event3)

    assert coordinator.suppression_telemetry.per_priority["CRITICAL"]["received"] == 1
    assert coordinator.suppression_telemetry.per_priority["HIGH"]["received"] == 1
    assert coordinator.suppression_telemetry.per_priority["MEDIUM"]["received"] == 1

    # Suppress a LOW priority event in deep focus
    coordinator.current_focus_mode = "deep"
    event4 = create_test_event(priority=EventPriority.LOW)
    await coordinator._should_process_event(event4)

    assert coordinator.suppression_telemetry.per_priority["LOW"]["received"] == 1
    assert coordinator.suppression_telemetry.per_priority["LOW"]["suppressed"] == 1


@pytest.mark.asyncio
async def test_suppression_report_structure(coordinator):
    """Test that get_suppression_report returns correct structure."""
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Process some events
    event1 = create_test_event()
    event2 = create_test_event(cognitive_load=0.8)

    await coordinator._should_process_event(event1)

    coordinator.current_energy_level = "low"
    await coordinator._should_process_event(event2)

    report = coordinator.get_suppression_report()

    # Check structure
    assert "summary" in report
    assert "per_rule_breakdown" in report
    assert "per_event_type" in report
    assert "per_priority" in report
    assert "adhd_state" in report

    # Check summary fields
    assert report["summary"]["events_received"] == 2
    assert report["summary"]["events_passed"] == 1
    assert report["summary"]["events_suppressed"] == 1
    assert "signal_noise_ratio" in report["summary"]
    assert "suppression_rate_pct" in report["summary"]

    # Check per_rule_breakdown has all 6 rules
    assert len(report["per_rule_breakdown"]) == 6
    assert "custom_filter" in report["per_rule_breakdown"]
    assert "deep_focus_priority" in report["per_rule_breakdown"]
    assert "deep_focus_interrupt" in report["per_rule_breakdown"]
    assert "energy_level" in report["per_rule_breakdown"]
    assert "flood" in report["per_rule_breakdown"]
    assert "expiry" in report["per_rule_breakdown"]


@pytest.mark.asyncio
async def test_signal_noise_ratio_calculation(coordinator):
    """Test that signal/noise ratio is calculated correctly."""
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Pass 3 events, suppress 1 event
    for _ in range(3):
        event = create_test_event()
        await coordinator._should_process_event(event)

    coordinator.current_energy_level = "low"
    suppressed_event = create_test_event(cognitive_load=0.8)
    await coordinator._should_process_event(suppressed_event)

    report = coordinator.get_suppression_report()

    # Signal/noise ratio = passed / received = 3 / 4 = 0.75
    assert report["summary"]["signal_noise_ratio"] == 0.75
    assert report["summary"]["suppression_rate_pct"] == 25.0


@pytest.mark.asyncio
async def test_zero_events_no_division_error(coordinator):
    """Test that report doesn't crash with zero events."""
    report = coordinator.get_suppression_report()

    assert report["summary"]["events_received"] == 0
    assert report["summary"]["events_passed"] == 0
    assert report["summary"]["events_suppressed"] == 0
    assert report["summary"]["signal_noise_ratio"] == 0.0
    assert report["summary"]["suppression_rate_pct"] == 0.0


@pytest.mark.asyncio
async def test_rule_short_circuit_ordering(coordinator):
    """Test that first matching rule gets the count (short-circuit)."""
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Set up deep focus mode + low energy (multiple rules could apply)
    coordinator.current_focus_mode = "deep"
    coordinator.current_energy_level = "low"

    # Create event that would match BOTH deep_focus_priority AND energy_level
    event = create_test_event(
        priority=EventPriority.LOW,  # Would trigger deep_focus_priority
        cognitive_load=0.8           # Would trigger energy_level
    )

    result = await coordinator._should_process_event(event)

    assert result is False
    # Only the FIRST matching rule should be counted (deep_focus_priority)
    assert coordinator.suppression_telemetry.suppressed_by_deep_focus_priority == 1
    assert coordinator.suppression_telemetry.suppressed_by_energy_level == 0


@pytest.mark.asyncio
async def test_telemetry_in_health_endpoint(coordinator):
    """Test that suppression telemetry is included in health check."""
    coordinator._get_recent_event_count = AsyncMock(return_value=0)

    # Process some events
    event = create_test_event()
    await coordinator._should_process_event(event)

    # Get health status
    health = await coordinator.get_coordination_health()

    assert "suppression_telemetry" in health
    assert "summary" in health["suppression_telemetry"]
    assert health["suppression_telemetry"]["summary"]["events_received"] == 1
