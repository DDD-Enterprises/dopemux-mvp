from unittest.mock import AsyncMock, patch

import pytest

from activity_tracker import ActivityTracker


@pytest.mark.asyncio
async def test_break_event_sends_engine_compatible_payload():
    adhd_client = AsyncMock()
    tracker = ActivityTracker(adhd_client=adhd_client)
    tracker.workspace_switches = 4

    await tracker.handle_break_taken({"duration_minutes": 10})

    adhd_client.send_activity_data.assert_awaited_once_with({
        "completion_rate": None,
        "context_switches": 4,
        "break_compliance": 1.0,
        "minutes_since_break": 0,
    })


@pytest.mark.asyncio
async def test_aggregate_summary_uses_engine_schema():
    adhd_client = AsyncMock()
    tracker = ActivityTracker(adhd_client=adhd_client)
    tracker.current_session = "session-1"
    tracker.session_start_time = 1000
    tracker.workspace_switches = 2
    tracker.task_updates = 3
    tracker.break_events = 1
    tracker.pending_activities = [
        {"type": "progress_update", "timestamp": 1100},
        {"type": "break_taken", "timestamp": 1150},
    ]

    with patch("activity_tracker.time.time", return_value=1300):
        await tracker._aggregate_and_send()

    adhd_client.send_activity_data.assert_awaited_once_with({
        "completion_rate": 0.5,
        "context_switches": 2,
        "break_compliance": 1.0,
        "minutes_since_break": 2,
    })
    assert tracker.summaries_sent == 1
    assert tracker.pending_activities == []
