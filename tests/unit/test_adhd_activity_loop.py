from types import SimpleNamespace

import pytest


class FakeCache:
    def __init__(self):
        self.values = {}

    async def get(self, key, default=None):
        return self.values.get(key, default)

    async def set(self, key, value, ttl=None):
        self.values[key] = value
        return True


@pytest.mark.asyncio
async def test_engine_activity_update_writes_current_state(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import AttentionState, EnergyLevel

    async def fake_energy(self, user_id):
        assert user_id == "operator-local-001"
        return EnergyLevel.LOW

    async def fake_attention(self, user_id):
        assert user_id == "operator-local-001"
        return AttentionState.SCATTERED

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    monkeypatch.setattr(engine_module.ADHDAccommodationEngine, "_assess_current_energy_level", fake_energy)
    monkeypatch.setattr(engine_module.ADHDAccommodationEngine, "_assess_attention_state", fake_attention)

    engine = engine_module.ADHDAccommodationEngine()

    result = await engine.record_activity_update(
        "operator-local-001",
        {"completion_rate": 0.25, "context_switches": 12, "prompt": "must not be retained"},
    )

    assert result["energy_level"] == EnergyLevel.LOW
    assert result["attention_state"] == AttentionState.SCATTERED
    assert result["energy_updated"] is True
    assert result["attention_updated"] is True
    assert engine.current_energy_levels["operator-local-001"] == EnergyLevel.LOW
    assert engine.current_attention_states["operator-local-001"] == AttentionState.SCATTERED
    assert "prompt" not in engine.recent_activity_updates["operator-local-001"]


@pytest.mark.asyncio
async def test_recent_activity_update_takes_precedence_for_immediate_assessment(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    class StaleActivityTracker:
        async def get_recent_activity(self, user_id):
            return {"completion_rate": 1.0, "context_switches": 0}

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    engine = engine_module.ADHDAccommodationEngine()
    engine.activity_tracker = StaleActivityTracker()
    engine.recent_activity_updates["operator-local-001"] = {
        "completion_rate": 0.2,
        "context_switches": 14,
    }

    assert await engine._get_recent_activity("operator-local-001") == {
        "completion_rate": 0.2,
        "context_switches": 14,
    }


@pytest.mark.asyncio
async def test_listener_native_hook_activity_updates_engine_state():
    from services.adhd_engine.core.models import AttentionState, EnergyLevel
    from services.adhd_engine.event_listener import ADHDEventListener

    calls = []

    class FakeEngine:
        def __init__(self):
            self.current_energy_levels = {}
            self.current_attention_states = {}

        async def record_activity_update(self, user_id, activity_data):
            calls.append((user_id, activity_data))
            self.current_energy_levels[user_id] = EnergyLevel.MEDIUM
            self.current_attention_states[user_id] = AttentionState.FOCUSED
            return {
                "energy_level": EnergyLevel.MEDIUM,
                "attention_state": AttentionState.FOCUSED,
                "energy_updated": True,
                "attention_updated": True,
            }

    engine = FakeEngine()
    listener = ADHDEventListener(event_bus=None, adhd_engine=engine)
    listener._current_user_id = "operator-local-001"

    event = SimpleNamespace(
        type="native_hook_activity",
        data={
            "hook_event_name": "PostToolUse",
            "status": "success",
            "tool_name": "Edit",
            "prompt": "must not be forwarded",
        },
    )

    await listener._dispatch(event)

    assert calls == [
        (
            "operator-local-001",
            {
                "hook_event_name": "PostToolUse",
                "status": "success",
                "tool_name": "Edit",
                "source_event": "native_hook_activity",
            },
        )
    ]
    assert engine.current_energy_levels["operator-local-001"] == EnergyLevel.MEDIUM
    assert engine.current_attention_states["operator-local-001"] == AttentionState.FOCUSED


@pytest.mark.asyncio
async def test_activity_route_updates_engine_and_emits_bounded_event(monkeypatch):
    from services.adhd_engine.api import routes
    from services.adhd_engine.api.schemas import ActivityUpdateRequest
    from services.adhd_engine.core.models import AttentionState, EnergyLevel

    emitted = []

    class FakeEmitter:
        @classmethod
        async def get_instance(cls):
            return cls()

        async def emit(self, event_type, data, source):
            emitted.append((event_type, data, source))
            return True

    class FakeEngine:
        def __init__(self):
            self.user_profiles = {"operator-local-001": object()}
            self.current_energy_levels = {}
            self.current_attention_states = {}
            self.predictive_engine = None

        async def record_activity_update(self, user_id, activity_data):
            self.current_energy_levels[user_id] = EnergyLevel.HIGH
            self.current_attention_states[user_id] = AttentionState.FOCUSED
            return {
                "energy_level": EnergyLevel.HIGH,
                "attention_state": AttentionState.FOCUSED,
                "energy_updated": True,
                "attention_updated": True,
            }

    cache = FakeCache()

    async def fake_cache_instance():
        return cache

    monkeypatch.setattr(routes, "get_cache_instance", fake_cache_instance)
    monkeypatch.setattr(routes, "EVENT_EMISSION_AVAILABLE", True)
    monkeypatch.setattr(routes, "ADHDEventEmitter", FakeEmitter)

    response = await routes.update_activity(
        user_id="operator-local-001",
        request=ActivityUpdateRequest(
            user_id="operator-local-001",
            completion_rate=0.9,
            context_switches=2,
            minutes_since_break=12,
        ),
        engine=FakeEngine(),
    )

    assert response.recorded is True
    assert response.energy_updated is True
    assert response.attention_updated is True
    assert emitted == [
        (
            "activity_updated",
            {
                "user_id": "operator-local-001",
                "metrics": {
                    "completion_rate": 0.9,
                    "context_switches": 2,
                    "minutes_since_break": 12,
                },
            },
            "adhd_activity_api",
        )
    ]


@pytest.mark.asyncio
async def test_activity_route_processes_update_even_when_response_cache_exists(monkeypatch):
    from services.adhd_engine.api import routes
    from services.adhd_engine.api.schemas import ActivityUpdateRequest

    calls = []

    class FakeEngine:
        user_profiles = {"operator-local-001": object()}
        current_energy_levels = {}
        current_attention_states = {}
        predictive_engine = None

        async def record_activity_update(self, user_id, activity_data):
            calls.append((user_id, activity_data))
            return {
                "energy_updated": True,
                "attention_updated": True,
            }

    cache = FakeCache()
    cache.values[routes._make_cache_key("activity", "operator-local-001")] = (
        '{"recorded":true,"energy_updated":false,"attention_updated":false,"message":"cached"}'
    )

    async def fake_cache_instance():
        return cache

    monkeypatch.setattr(routes, "get_cache_instance", fake_cache_instance)
    monkeypatch.setattr(routes, "EVENT_EMISSION_AVAILABLE", False)

    response = await routes.update_activity(
        user_id="operator-local-001",
        request=ActivityUpdateRequest(
            user_id="operator-local-001",
            completion_rate=0.4,
        ),
        engine=FakeEngine(),
    )

    assert response.energy_updated is True
    assert calls == [("operator-local-001", {"completion_rate": 0.4})]
