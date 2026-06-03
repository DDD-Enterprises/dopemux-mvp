from types import SimpleNamespace

import pytest


USER_ID = "operator-local-001"


@pytest.mark.asyncio
async def test_boundary_events_drive_activity_metrics_without_wall_clock(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    for boundary_type in ("test", "build", "commit"):
        await engine.record_activity_update(
            USER_ID,
            {
                "hook_event_name": "PostToolUse",
                "status": "success",
                "tool_name": "Bash",
                "boundary_type": boundary_type,
                "minutes_since_break": 95,
            },
        )

    activity = engine.recent_activity_updates[USER_ID]

    assert activity["boundary_events"] == 3
    assert activity["work_boundary_events"] == 3
    assert activity["completion_rate"] == 1.0
    assert activity["minutes_since_break"] < 30


@pytest.mark.asyncio
async def test_boundary_events_stabilize_prompt_switch_state(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    for _ in range(8):
        await engine.record_activity_update(
            USER_ID,
            {"hook_event_name": "UserPromptSubmit", "status": "attempt"},
        )
    for _ in range(4):
        result = await engine.record_activity_update(
            USER_ID,
            {
                "hook_event_name": "PostToolUse",
                "status": "success",
                "tool_name": "Bash",
                "boundary_type": "test",
            },
        )

    activity = engine.recent_activity_updates[USER_ID]

    assert activity["prompt_events"] == 8
    assert activity["boundary_events"] == 4
    assert activity["context_switches"] < activity["prompt_events"]
    assert result["attention_state"] != AttentionState.SCATTERED


@pytest.mark.asyncio
async def test_listener_forwards_boundary_type_but_not_content():
    from services.adhd_engine.event_listener import ADHDEventListener

    calls = []

    class FakeEngine:
        async def record_activity_update(self, user_id, activity_data):
            calls.append((user_id, activity_data))
            return {"energy_updated": True, "attention_updated": True}

    listener = ADHDEventListener(event_bus=None, adhd_engine=FakeEngine())
    listener._current_user_id = USER_ID

    event = SimpleNamespace(
        type="native_hook_activity",
        data={
            "hook_event_name": "PostToolUse",
            "status": "success",
            "tool_name": "Bash",
            "boundary_type": "commit",
            "prompt": "must not be forwarded",
            "tool_input": {"command": "git commit -m secret"},
            "path": "/Users/hue/code/dopemux-mvp/secret.py",
        },
    )

    await listener._dispatch(event)

    assert calls == [
        (
            USER_ID,
            {
                "hook_event_name": "PostToolUse",
                "status": "success",
                "tool_name": "Bash",
                "boundary_type": "commit",
                "source_event": "native_hook_activity",
            },
        )
    ]


@pytest.mark.asyncio
async def test_listener_turns_file_closed_into_content_free_boundary():
    from services.adhd_engine.event_listener import ADHDEventListener

    calls = []

    class FakeEngine:
        async def record_activity_update(self, user_id, activity_data):
            calls.append((user_id, activity_data))
            return {"energy_updated": True, "attention_updated": True}

    listener = ADHDEventListener(event_bus=None, adhd_engine=FakeEngine())
    listener._current_user_id = USER_ID

    event = SimpleNamespace(
        type="file_closed",
        data={
            "file": "/Users/hue/code/dopemux-mvp/private.py",
            "action": "closed",
        },
    )

    await listener._dispatch(event)

    assert calls == [
        (
            USER_ID,
            {
                "boundary_type": "file_close",
                "source_event": "file_closed",
            },
        )
    ]


@pytest.mark.asyncio
async def test_unknown_boundary_type_is_not_retained(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    await engine.record_activity_update(
        USER_ID,
        {
            "hook_event_name": "PostToolUse",
            "status": "success",
            "tool_name": "Bash",
            "boundary_type": "raw_command",
        },
    )

    assert engine.recent_activity_samples[USER_ID][0].get("boundary_type") is None
    assert engine.recent_activity_updates[USER_ID]["boundary_events"] == 0
