from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class ForbiddenConPort:
    def __init__(self):
        self.progress_called = False

    def log_progress_entry(self, **kwargs):
        self.progress_called = True
        return "forbidden-progress-entry"


class ForbiddenContextPreserver:
    async def save_context(self, **kwargs):
        raise AssertionError("context preserver must not receive prompt or path content")


class ForbiddenWorkingMemory:
    async def save_breadcrumb(self, **kwargs):
        raise AssertionError("working memory must not receive prompt content")


@pytest.mark.asyncio
async def test_save_context_rejects_prompt_and_file_content_before_persistence(monkeypatch):
    from services.adhd_engine.api import routes

    emitted = []

    async def fake_emit_context_saved(**kwargs):
        emitted.append(kwargs)
        return True

    engine = SimpleNamespace(
        context_preserver=ForbiddenContextPreserver(),
        working_memory_support=ForbiddenWorkingMemory(),
    )

    monkeypatch.setattr(routes, "EVENT_EMISSION_AVAILABLE", True)
    monkeypatch.setattr(routes, "emit_context_saved", fake_emit_context_saved)

    with pytest.raises(HTTPException) as exc_info:
        await routes.save_context_for_hook(
            {
                "reason": "context_switch",
                "prompt_hint": "raw prompt must not persist",
                "files": ["/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py"],
            },
            user_id="operator-local-001",
            engine=engine,
        )

    assert exc_info.value.status_code == 400
    assert emitted == []
    assert not hasattr(engine, "_context_snapshots")


@pytest.mark.asyncio
async def test_log_intent_rejects_prompt_summary_before_conport_or_event(monkeypatch):
    from services.adhd_engine.api import routes

    class ForbiddenIntentConPort:
        async def log_custom_data(self, **kwargs):
            raise AssertionError("ConPort must not receive prompt summaries")

    emitted = []

    async def fake_emit_claude_prompt(**kwargs):
        emitted.append(kwargs)
        return True

    engine = SimpleNamespace(conport=ForbiddenIntentConPort())

    monkeypatch.setattr(routes, "EVENT_EMISSION_AVAILABLE", True)
    monkeypatch.setattr(routes, "emit_claude_prompt", fake_emit_claude_prompt)

    with pytest.raises(HTTPException) as exc_info:
        await routes.log_user_intent(
            {
                "prompt_summary": "build the secret thing in /tmp/private.py",
                "signals": {"is_context_switch": True},
                "adhd_state": {"energy": "low"},
                "timestamp": "2026-05-31T00:00:00Z",
            },
            engine=engine,
        )

    assert exc_info.value.status_code == 400
    assert emitted == []
    assert not hasattr(engine, "_intent_buffer")


@pytest.mark.asyncio
async def test_event_helpers_emit_content_free_payloads(monkeypatch):
    from services.adhd_engine import event_emitter

    emitted = []

    class FakeEmitter:
        async def emit(self, event_type, data, source):
            emitted.append((event_type, data, source))
            return True

    async def fake_get_instance():
        return FakeEmitter()

    monkeypatch.setattr(event_emitter.ADHDEventEmitter, "get_instance", fake_get_instance)

    assert await event_emitter.emit_claude_prompt(
        "raw prompt content",
        {"is_context_switch": True},
        {"energy": "low", "attention": "scattered"},
    )
    assert await event_emitter.emit_context_saved(
        "operator-local-001",
        "context_switch",
        "raw prompt hint",
    )

    assert emitted == [
        (
            event_emitter.EventTypes.CLAUDE_PROMPT_RECEIVED,
            {
                "signals": {"is_context_switch": True},
                "adhd_state": {"energy": "low", "attention": "scattered"},
            },
            "prompt_analyzer_hook",
        ),
        (
            event_emitter.EventTypes.CONTEXT_SAVED,
            {
                "user_id": "operator-local-001",
                "reason": "context_switch",
            },
            "save_context_hook",
        ),
    ]


@pytest.mark.asyncio
async def test_task_and_unfinished_work_routes_fail_closed_without_engine_reads():
    from services.adhd_engine.api import routes

    class ForbiddenEngine:
        async def get_tasks_completed(self, user_id):
            raise AssertionError("ADHD Engine must not expose task metrics")

        async def get_total_tasks(self, user_id):
            raise AssertionError("ADHD Engine must not expose task metrics")

    with pytest.raises(HTTPException) as task_exc:
        await routes.get_tasks_for_user("operator-local-001", ForbiddenEngine(), api_key="test")

    with pytest.raises(HTTPException) as unfinished_exc:
        await routes.get_unfinished_work("operator-local-001", ForbiddenEngine())

    assert task_exc.value.status_code == 410
    assert unfinished_exc.value.status_code == 410


@pytest.mark.asyncio
async def test_cognitive_overload_does_not_create_conport_progress_task(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    engine = engine_module.ADHDAccommodationEngine()
    conport = ForbiddenConPort()
    engine.conport = conport

    async def overload():
        return 0.95

    monkeypatch.setattr(engine, "_calculate_system_cognitive_load", overload)

    await engine._handle_cognitive_overload()

    assert conport.progress_called is False
    assert engine.accommodation_stats["breaks_suggested"] == 0
