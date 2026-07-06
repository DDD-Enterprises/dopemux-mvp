import json

import pytest
from services.adhd_engine.redis_keys import redis_key, redis_pattern


class FakeRedisProfiles:
    def __init__(self, profiles=None):
        self.profiles = dict(profiles or {})
        self.set_calls = []

    async def keys(self, pattern):
        assert pattern == redis_pattern("adhd:profile:*")
        return list(self.profiles.keys())

    async def get(self, key):
        return self.profiles.get(key)

    async def set(self, key, value, **kwargs):
        nx = kwargs.get("nx", False)
        if nx and key in self.profiles:
            # Honour SET NX: do not overwrite if key already exists.
            return None
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
    assert redis_key("adhd:profile:/Users/hue/code/dopemux-mvp") not in engine.redis_client.profiles

    assert len(engine.redis_client.set_calls) == 1
    key, payload = engine.redis_client.set_calls[0]
    assert key == redis_key("adhd:profile:operator-local-001")
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
        {redis_key("adhd:profile:operator-local-001"): json.dumps(existing_profile)}
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
        {redis_key("adhd:profile:other-user").encode("utf-8"): json.dumps(existing_profile).encode("utf-8")}
    )

    await engine._load_user_profiles()

    assert engine.user_profiles["other-user"].optimal_task_duration == 30
    assert engine.user_profiles["operator-local-001"].user_id == "operator-local-001"
    assert engine.redis_client.set_calls[0][0] == redis_key("adhd:profile:operator-local-001")


@pytest.mark.asyncio
async def test_operator_profile_seed_uses_nx_and_does_not_overwrite_concurrent_profile(monkeypatch):
    """Seed must use SET NX so a concurrent write is never overwritten (#776 race)."""
    from services.adhd_engine.core import engine as engine_module

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")

    # Profile is absent from Redis at load time (so _load_user_profiles doesn't
    # find it), but a concurrent process writes it BEFORE the seed SET runs.
    class FakeRedisNXRace:
        """Simulates a key that appears between the load scan and the seed SET."""

        def __init__(self):
            self.profiles = {}
            self.set_calls = []

        async def keys(self, pattern):
            return []  # empty on initial scan

        async def get(self, key):
            return self.profiles.get(key)

        async def set(self, key, value, **kwargs):
            nx = kwargs.get("nx", False)
            if nx and key in self.profiles:
                return None  # key already exists — honour NX, return None
            self.set_calls.append((key, value))
            self.profiles[key] = value
            return True

    fake_redis = FakeRedisNXRace()
    # Simulate the concurrent write before the seed fires.
    concurrent_profile = json.dumps(
        {"user_id": "operator-local-001", "optimal_task_duration": 99}
    )
    fake_redis.profiles[redis_key("adhd:profile:operator-local-001")] = concurrent_profile

    engine = engine_module.ADHDAccommodationEngine()
    engine.redis_client = fake_redis

    await engine._load_user_profiles()

    # In-memory profile is the default (seeded locally — no Redis data was loaded
    # because keys() returned empty, so the concurrent profile was not loaded).
    # The important thing: the SET NX was a no-op, so the concurrent profile in
    # Redis was NOT overwritten.
    assert fake_redis.set_calls == [], "NX should have prevented overwrite of concurrent profile"
