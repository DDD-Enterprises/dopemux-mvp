"""Tests for ADHD Engine Redis key instance namespacing."""

import json

import pytest

from ..adhd_config_service import ADHDConfigService
from ..redis_keys import redis_key, redis_key_prefix, redis_pattern


def test_redis_key_preserves_legacy_key_without_prefix(monkeypatch):
    monkeypatch.delenv("ADHD_ENGINE_REDIS_PREFIX", raising=False)
    monkeypatch.delenv("ADHD_ENGINE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("DOPEMUX_INSTANCE_ID", raising=False)

    assert redis_key_prefix() == ""
    assert redis_key("adhd:energy_level:user1") == "adhd:energy_level:user1"
    assert redis_pattern("adhd:profile:*") == "adhd:profile:*"


def test_redis_key_uses_explicit_prefix_before_instance_ids(monkeypatch):
    monkeypatch.setenv("ADHD_ENGINE_REDIS_PREFIX", "explicit")
    monkeypatch.setenv("ADHD_ENGINE_INSTANCE_ID", "adhd-instance")
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "dopemux-instance")

    assert redis_key_prefix() == "explicit"
    assert redis_key("adhd:attention_state:user1") == "explicit:adhd:attention_state:user1"
    assert redis_pattern("adhd:profile:*") == "explicit:adhd:profile:*"


@pytest.mark.asyncio
async def test_config_service_reads_prefixed_attention_energy_and_profile(monkeypatch, redis_client):
    monkeypatch.setenv("ADHD_ENGINE_REDIS_PREFIX", "worktree-a")
    service = ADHDConfigService(redis_url="redis://localhost:6379/5", workspace_id="/tmp/worktree-a")
    service.redis_client = redis_client

    await redis_client.set("adhd:attention_state:user1", "overwhelmed")
    await redis_client.set("worktree-a:adhd:attention_state:user1", "focused")
    await redis_client.set("worktree-a:adhd:energy_level:user1", "high")
    await redis_client.set(
        "worktree-a:adhd:profile:user1",
        json.dumps({"optimal_task_duration": 25, "max_task_duration": 90}),
    )

    assert await service.get_max_results("user1") == 15
    assert await service.get_complexity_threshold("user1") == 0.9
    summary = await service.get_current_state_summary("user1")
    assert summary["profile"]["max_task_duration"] == 90
