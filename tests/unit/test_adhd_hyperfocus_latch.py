import pytest


USER_ID = "operator-local-001"


@pytest.mark.asyncio
async def test_hyperfocus_latches_through_lone_idle_signal(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()
    engine.current_attention_states[USER_ID] = AttentionState.HYPERFOCUSED

    result = await engine.record_activity_update(
        USER_ID,
        {
            "idle_detected": True,
            "idle_minutes": 18,
        },
    )

    assert result["attention_state"] == AttentionState.HYPERFOCUSED
    assert engine.current_attention_states[USER_ID] == AttentionState.HYPERFOCUSED


@pytest.mark.asyncio
async def test_hyperfocus_exit_requires_two_degradation_signals(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()
    engine.current_attention_states[USER_ID] = AttentionState.HYPERFOCUSED

    single_signal = await engine.record_activity_update(
        USER_ID,
        {
            "context_switches": 14,
            "completion_rate": 0.7,
            "break_compliance": 0.9,
            "minutes_since_break": 35,
        },
    )

    assert single_signal["attention_state"] == AttentionState.HYPERFOCUSED

    corroborated = await engine.record_activity_update(
        USER_ID,
        {
            "context_switches": 14,
            "tool_failures": 4,
            "completion_rate": 0.7,
            "break_compliance": 0.9,
            "minutes_since_break": 35,
        },
    )

    assert corroborated["attention_state"] == AttentionState.OVERWHELMED


@pytest.mark.asyncio
async def test_work_boundary_releases_hyperfocus_latch(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()
    engine.current_attention_states[USER_ID] = AttentionState.HYPERFOCUSED

    await engine.record_activity_update(
        USER_ID,
        {
            "hook_event_name": "PostToolUse",
            "status": "success",
            "tool_name": "Bash",
            "boundary_type": "test",
        },
    )
    result = await engine.record_activity_update(
        USER_ID,
        {
            "context_switches": 14,
            "completion_rate": 0.7,
            "break_compliance": 0.9,
            "minutes_since_break": 35,
        },
    )

    assert result["attention_state"] == AttentionState.SCATTERED
