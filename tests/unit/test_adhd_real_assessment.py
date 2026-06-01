import pytest


class FakeRedis:
    async def get(self, key):
        return None

    async def lrange(self, key, start, end):
        return []


class FakeConPort:
    def __init__(self, progress_entries=None, activity_log=None):
        self.progress_entries = list(progress_entries or [])
        self.activity_log = activity_log

    def get_progress_entries(self, **kwargs):
        return self.progress_entries

    def get_custom_data(self, **kwargs):
        return self.activity_log


@pytest.mark.asyncio
async def test_high_context_switch_activity_drives_scattered_attention(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState, EnergyLevel

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    engine = engine_module.ADHDAccommodationEngine()

    result = await engine.record_activity_update(
        "operator-local-001",
        {
            "completion_rate": 0.25,
            "context_switches": 14,
            "break_compliance": 0.4,
            "minutes_since_break": 95,
        },
    )

    assert result["energy_level"] in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}
    assert result["attention_state"] == AttentionState.SCATTERED
    assert engine.current_attention_states["operator-local-001"] == AttentionState.SCATTERED


@pytest.mark.asyncio
async def test_repeated_native_hook_failures_drive_low_energy_and_overwhelmed_attention(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState, EnergyLevel

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    engine = engine_module.ADHDAccommodationEngine()

    for _ in range(4):
        result = await engine.record_activity_update(
            "operator-local-001",
            {
                "hook_event_name": "PostToolUseFailure",
                "status": "failure",
                "tool_name": "Edit",
                "prompt": "must not be retained",
            },
        )

    assert result["energy_level"] in {EnergyLevel.LOW, EnergyLevel.VERY_LOW}
    assert result["attention_state"] == AttentionState.OVERWHELMED
    assert "prompt" not in engine.recent_activity_updates["operator-local-001"]
    assert engine.recent_activity_updates["operator-local-001"]["tool_failures"] == 4


@pytest.mark.asyncio
async def test_activity_tracker_marks_fallback_data_as_no_observed_evidence():
    from services.adhd_engine.core.activity_tracker import ActivityTracker

    tracker = ActivityTracker(redis_client=FakeRedis(), conport_db_path="/fake/path.db")
    tracker.conport = FakeConPort(progress_entries=[], activity_log=None)

    result = await tracker.get_recent_activity("operator-local-001")

    assert result["activity_evidence"] is False


@pytest.mark.asyncio
async def test_activity_tracker_marks_real_activity_data_as_observed_evidence():
    from services.adhd_engine.core.activity_tracker import ActivityTracker

    tracker = ActivityTracker(redis_client=FakeRedis(), conport_db_path="/fake/path.db")
    tracker.conport = FakeConPort(
        progress_entries=[
            {"status": "DONE"},
            {"status": "IN_PROGRESS"},
        ],
        activity_log={"context_switches": 3},
    )

    result = await tracker.get_recent_activity("operator-local-001")

    assert result["activity_evidence"] is True
    assert result["completion_rate"] == 0.5
    assert result["context_switches"] == 3
