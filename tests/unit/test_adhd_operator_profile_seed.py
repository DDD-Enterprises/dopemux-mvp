import json

import pytest


class FakeRedisProfiles:
    def __init__(self, profiles=None):
        self.profiles = dict(profiles or {})
        self.set_calls = []

    async def keys(self, pattern):
        assert pattern == "adhd:profile:*"
        return list(self.profiles.keys())

    async def get(self, key):
        return self.profiles.get(key)

    async def set(self, key, value):
        self.set_calls.append((key, value))
        self.profiles[key] = value
        return True


@pytest.mark.asyncio
async def test_load_user_profiles_seeds_default_operator_profile_when_redis_is_empty(monkeypatch):
    from services.adhd_engine.core import engine as engine_module
    from services.adhd_engine.core.models import ADHDProfile

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")

    engine = engine_module.ADHDAccommodationEngine()
    engine.redis_client = FakeRedisProfiles()

    await engine._load_user_profiles()

    profile = engine.user_profiles["operator-local-001"]
    assert isinstance(profile, ADHDProfile)
    assert profile.user_id == "operator-local-001"
    assert "adhd:profile:/Users/hue/code/dopemux-mvp" not in engine.redis_client.profiles

    assert len(engine.redis_client.set_calls) == 1
    key, payload = engine.redis_client.set_calls[0]
    assert key == "adhd:profile:operator-local-001"
    assert json.loads(payload)["user_id"] == "operator-local-001"


@pytest.mark.asyncio
async def test_load_user_profiles_preserves_existing_operator_profile(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    existing_profile = {
        "user_id": "operator-local-001",
        "optimal_task_duration": 45,
        "peak_hours": [11, 15],
        "crash_indicators": ["late_day_drift"],
    }

    engine = engine_module.ADHDAccommodationEngine()
    engine.redis_client = FakeRedisProfiles(
        {"adhd:profile:operator-local-001": json.dumps(existing_profile)}
    )

    await engine._load_user_profiles()

    assert engine.user_profiles["operator-local-001"].optimal_task_duration == 45
    assert engine.user_profiles["operator-local-001"].peak_hours == [11, 15]
    assert engine.redis_client.set_calls == []


@pytest.mark.asyncio
async def test_load_user_profiles_decodes_redis_byte_keys_and_seeds_operator(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    existing_profile = {"user_id": "other-user", "optimal_task_duration": 30}

    engine = engine_module.ADHDAccommodationEngine()
    engine.redis_client = FakeRedisProfiles(
        {b"adhd:profile:other-user": json.dumps(existing_profile).encode("utf-8")}
    )

    await engine._load_user_profiles()

    assert engine.user_profiles["other-user"].optimal_task_duration == 30
    assert engine.user_profiles["operator-local-001"].user_id == "operator-local-001"
    assert engine.redis_client.set_calls[0][0] == "adhd:profile:operator-local-001"
