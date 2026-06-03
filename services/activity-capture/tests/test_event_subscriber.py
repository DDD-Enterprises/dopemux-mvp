from unittest.mock import AsyncMock

import pytest

from event_subscriber import EventSubscriber


@pytest.mark.asyncio
async def test_process_message_routes_normalized_progress_event():
    tracker = AsyncMock()
    subscriber = EventSubscriber(
        redis_url="redis://localhost:6379",
        stream_name="dopemux:events",
        consumer_group="activity-capture",
        consumer_name="test-consumer",
        activity_tracker=tracker,
    )

    await subscriber._process_message({
        "type": "progress_updated",
        "data": '{"task_id":"task-1","status":"IN_PROGRESS","progress":55}',
    })

    tracker.handle_progress_update.assert_awaited_once_with({
        "task_id": "task-1",
        "status": "IN_PROGRESS",
        "progress": 55,
    })


@pytest.mark.asyncio
async def test_process_message_routes_workspace_switch_with_nested_file_activity():
    tracker = AsyncMock()
    subscriber = EventSubscriber(
        redis_url="redis://localhost:6379",
        stream_name="dopemux:events",
        consumer_group="activity-capture",
        consumer_name="test-consumer",
        activity_tracker=tracker,
    )

    await subscriber._process_message({
        "type": "workspace.switched",
        "data": {
            "from_workspace": "/tmp/one",
            "to_workspace": "/tmp/two",
            "adhd_context_capture": {
                "file_activity": {
                    "files_modified": 1,
                }
            },
        },
    })

    tracker.handle_workspace_switch.assert_awaited_once_with({
        "from_workspace": "/tmp/one",
        "to_workspace": "/tmp/two",
        "file_activity": {
            "has_recent_activity": True,
            "files_modified": 1,
            "seconds_since_last_save": None,
        },
        "from_app": None,
        "to_app": None,
        "switch_type": None,
        "workspace_id": "/tmp/two",
    })
