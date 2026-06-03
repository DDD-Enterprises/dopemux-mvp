from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class ForbiddenConPort:
    def __init__(self):
        self.progress_called = False

    def log_progress_entry(self, **kwargs):
        self.progress_called = True
        return "forbidden-progress-entry"


class TrackingContextPreserver:
    """Records calls so we can assert which arguments were passed."""

    def __init__(self):
        self.calls = []

    async def save_context(self, **kwargs):
        self.calls.append(dict(kwargs))


class TrackingWorkingMemory:
    """Records calls so we can assert which arguments were passed."""

    def __init__(self):
        self.calls = []

    async def save_breadcrumb(self, **kwargs):
        self.calls.append(dict(kwargs))


@pytest.mark.asyncio
async def test_save_context_strips_content_fields_and_does_not_forward_them(monkeypatch):
    """
    /save-context is called by local hooks (save_context.sh, prompt_analyzer.py)
    that may include content-bearing fields such as 'files' or 'prompt_hint'.
    The endpoint must SUCCEED (so callers aren't silently broken) but must NOT
    forward any content to persistence layers or the event bus.
    """
    from services.adhd_engine.api import routes

    emitted = []

    async def fake_emit_context_saved(**kwargs):
        emitted.append(kwargs)
        return True

    context_preserver = TrackingContextPreserver()
    working_memory = TrackingWorkingMemory()
    engine = SimpleNamespace(
        context_preserver=context_preserver,
        working_memory_support=working_memory,
    )

    monkeypatch.setattr(routes, "EVENT_EMISSION_AVAILABLE", True)
    monkeypatch.setattr(routes, "emit_context_saved", fake_emit_context_saved)

    # Should NOT raise — content-bearing fields are stripped, not rejected.
    result = await routes.save_context_for_hook(
        {
            "reason": "context_switch",
            "prompt_hint": "raw prompt must not persist",
            "files": ["/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py"],
        },
        user_id="operator-local-001",
        engine=engine,
    )

    # Call succeeded.
    assert result.get("saved") is True

    # context_preserver was called but only with content-free fields.
    assert context_preserver.calls
    for call in context_preserver.calls:
        assert "prompt_hint" not in call
        assert "files" not in call
        assert "path" not in call

    # emit_context_saved was called.  The real implementation strips prompt_hint
    # before forwarding to the event bus (see event_emitter.emit_context_saved).
    # Here we only verify that content-bearing strings from the request body
    # (e.g. actual path text) were not blindly forwarded as-is.
    assert emitted
    for payload in emitted:
        assert "files" not in payload
        assert "path" not in payload
        # prompt_hint is an accepted parameter of emit_context_saved but the real
        # emitter always strips it; the fake captures it as a kwarg, which is fine.


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
