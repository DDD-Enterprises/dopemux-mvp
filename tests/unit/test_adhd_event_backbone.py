import importlib
from datetime import datetime, timedelta, timezone

import pytest

from services.adhd_engine.event_emitter import ADHDEventEmitter, Event, EventTypes
from services.adhd_engine.event_listener import ADHDEventListener
from services.adhd_engine.external_activity import DesktopActivityMonitor, MeetingEvent, CalendarIntegration
from services.adhd_engine.workspace_watcher import WorkspaceEventEmitter


class FakeCanonicalEmitter:
    def __init__(self):
        self.calls = []

    async def emit(self, event_type, data, source="adhd_engine_api"):
        self.calls.append(
            {
                "event_type": event_type,
                "data": data,
                "source": source,
            }
        )
        return True


class FakeRedis:
    def __init__(self):
        self.xadd_calls = []

    async def xadd(self, stream, fields, maxlen=None):
        self.xadd_calls.append(
            {
                "stream": stream,
                "fields": fields,
                "maxlen": maxlen,
            }
        )
        return b"1-0"


@pytest.mark.asyncio
async def test_adhd_event_emitter_publish_bridges_event_objects_to_redis_stream():
    emitter = ADHDEventEmitter("redis://unit-test")
    emitter._redis = FakeRedis()
    emitter._connected = True

    event = Event(
        type=EventTypes.FILE_SAVED,
        data={"relative_path": "src/app.py", "action": "saved"},
        source="workspace_watcher",
    )

    assert await emitter.publish("dopemux:events", event) is True
    assert emitter._redis.xadd_calls == [
        {
            "stream": "dopemux:events",
            "fields": event.to_redis_dict(),
            "maxlen": 10000,
        }
    ]


@pytest.mark.asyncio
async def test_workspace_watcher_uses_canonical_emitter_for_file_activity(tmp_path):
    source_file = tmp_path / "src" / "app.py"
    source_file.parent.mkdir()
    source_file.write_text("print('ok')\n")
    emitter = FakeCanonicalEmitter()
    watcher = WorkspaceEventEmitter(emitter, str(tmp_path))

    await watcher.emit_file_event(str(source_file), "saved")

    assert emitter.calls == [
        {
            "event_type": EventTypes.FILE_SAVED,
            "data": {
                "file": str(source_file),
                "relative_path": "src/app.py",
                "action": "saved",
                "timestamp": emitter.calls[0]["data"]["timestamp"],
                "extension": ".py",
            },
            "source": "workspace_watcher",
        }
    ]


@pytest.mark.asyncio
async def test_desktop_activity_uses_canonical_emitter_for_window_events():
    emitter = FakeCanonicalEmitter()
    monitor = DesktopActivityMonitor(emitter)

    await monitor._on_window_switch(
        from_app="Code",
        to_app="Slack",
        from_window="repo.py",
        to_window="DM",
    )

    assert emitter.calls[0]["event_type"] == EventTypes.WINDOW_SWITCHED
    assert emitter.calls[0]["source"] == "desktop_activity_monitor"
    assert emitter.calls[0]["data"]["is_distraction"] is True
    assert emitter.calls[0]["data"]["is_leaving_work"] is True


@pytest.mark.asyncio
async def test_calendar_activity_uses_canonical_emitter_for_meeting_events():
    emitter = FakeCanonicalEmitter()
    calendar = CalendarIntegration(emitter)
    now = datetime.now(timezone.utc)
    meeting = MeetingEvent(
        title="Planning",
        start_time=now,
        end_time=now + timedelta(hours=1),
        attendees=3,
    )

    await calendar._on_meeting_started(meeting)

    assert emitter.calls[0]["event_type"] == EventTypes.MEETING_STARTED
    assert emitter.calls[0]["source"] == "calendar_integration"
    assert emitter.calls[0]["data"]["meeting_type"] == "video"


@pytest.mark.asyncio
async def test_listener_handles_claude_tool_completed_events():
    listener = ADHDEventListener(event_bus=FakeCanonicalEmitter())

    assert EventTypes.CLAUDE_TOOL_COMPLETED in listener._handlers

    await listener._dispatch(
        Event(
            type=EventTypes.CLAUDE_TOOL_COMPLETED,
            data={"tool": "Edit", "success": True, "user_id": "operator"},
            source="log_progress_hook",
        )
    )


def test_routes_enable_event_emission_with_package_relative_imports():
    routes = importlib.import_module("services.adhd_engine.api.routes")
    routes = importlib.reload(routes)

    assert routes.EVENT_EMISSION_AVAILABLE is True
