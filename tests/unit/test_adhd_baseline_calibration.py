import pytest


USER_ID = "operator-local-001"


def _metrics(context_switches, *, completion_rate=0.65, minutes_since_break=20):
    return {
        "completion_rate": completion_rate,
        "context_switches": context_switches,
        "break_compliance": 0.8,
        "minutes_since_break": minutes_since_break,
    }


async def _seed_switch_baseline(engine, switches):
    for count in switches:
        await engine.record_activity_update(USER_ID, _metrics(count))


@pytest.mark.asyncio
async def test_activity_baseline_reports_calibrating_until_minimum_samples(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    await _seed_switch_baseline(engine, [1, 2, 3, 4])

    status = engine.get_activity_baseline_status(USER_ID)

    assert status["status"] == "calibrating"
    assert status["sample_count"] == 4
    assert status["min_samples"] == 5
    assert status["ready"] is False


@pytest.mark.asyncio
async def test_energy_assessment_uses_ready_user_switch_percentile(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import EnergyLevel

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    await _seed_switch_baseline(engine, [8, 10, 12, 14, 16])
    result = await engine.record_activity_update(USER_ID, _metrics(8))

    status = engine.get_activity_baseline_status(USER_ID)
    assert status["status"] == "ready"
    assert status["thresholds"]["high_context_switches"] > 8
    assert result["energy_level"] == EnergyLevel.MEDIUM


@pytest.mark.asyncio
async def test_attention_assessment_uses_low_switch_user_relative_threshold(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    await _seed_switch_baseline(engine, [1, 2, 2, 3, 3])
    result = await engine.record_activity_update(USER_ID, _metrics(6))

    status = engine.get_activity_baseline_status(USER_ID)
    assert status["status"] == "ready"
    assert status["thresholds"]["high_context_switches"] < 6
    assert result["attention_state"] == AttentionState.SCATTERED


@pytest.mark.asyncio
async def test_attention_assessment_avoids_scattered_for_normal_high_switch_user(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: USER_ID)
    engine = engine_module.ADHDAccommodationEngine()

    await _seed_switch_baseline(engine, [8, 10, 12, 14, 16])
    result = await engine.record_activity_update(USER_ID, _metrics(12))

    assert result["attention_state"] != AttentionState.SCATTERED
