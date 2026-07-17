"""Unit tests for the producer-side activity heartbeat rate limiter.

Packet MCPINT-FND-HYG-007 / ADR-mcpint-004: session heartbeats are
coalesced/dropped client-side; high-signal (promotion-allowlist) events are
never rate-limited; cache failures always fail open.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from dopemux.claude import activity_ratelimit, native_hooks
from dopemux.claude.activity_ratelimit import (
    DEFAULT_COOLDOWN_SECONDS,
    ENV_COOLDOWN_SECONDS,
    is_high_signal_event_type,
    should_emit_heartbeat,
)
from dopemux.claude.native_hooks import handle_event
from dopemux.memory.capture_client import PROMOTABLE_CAPTURE_EVENT_TYPES


class FakeClock:
    """Deterministic stand-in for the module's `time` import."""

    def __init__(self, start: float = 1_000_000.0):
        self.now = start

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture()
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(activity_ratelimit, "time", fake)
    return fake


def _cache_file(root: Path) -> Path:
    return root / ".claude" / ".activity-heartbeat-cache.json"


# ---------------------------------------------------------------------------
# Cooldown honored
# ---------------------------------------------------------------------------


def test_first_emission_allowed_and_cached(tmp_path, clock):
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    cache = json.loads(_cache_file(tmp_path).read_text())
    assert len(cache) == 1
    (key,) = cache.keys()
    assert key.startswith("s1::")


def test_identical_event_suppressed_within_cooldown(tmp_path, clock):
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    clock.advance(DEFAULT_COOLDOWN_SECONDS - 1)
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_emission_allowed_after_cooldown_expires(tmp_path, clock):
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    clock.advance(DEFAULT_COOLDOWN_SECONDS + 1)
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_sessions_have_independent_buckets(tmp_path, clock):
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    assert should_emit_heartbeat("session-active", session_id="s2", project_root=tmp_path)
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    assert not should_emit_heartbeat("session-active", session_id="s2", project_root=tmp_path)


def test_missing_session_id_uses_shared_unknown_bucket(tmp_path, clock):
    assert should_emit_heartbeat("session-active", project_root=tmp_path)
    assert not should_emit_heartbeat("session-active", project_root=tmp_path)


def test_distinct_event_types_independent(tmp_path, clock):
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    assert should_emit_heartbeat(
        "native_hook_activity:PreToolUse:attempt:Read",
        session_id="s1",
        project_root=tmp_path,
    )
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_str_project_root_accepted_and_limits(tmp_path, clock):
    # monitor_daemon assigns str watched_paths; str roots must still key the
    # cache (a silent fail-open here would disable limiting for the daemon).
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=str(tmp_path))
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=str(tmp_path))
    assert _cache_file(tmp_path).exists()


# ---------------------------------------------------------------------------
# High-signal bypass — promotion allowlist is NEVER rate-limited
# ---------------------------------------------------------------------------


def test_every_promotable_event_type_bypasses_rate_limit(tmp_path, clock):
    for event_type in sorted(PROMOTABLE_CAPTURE_EVENT_TYPES):
        for _ in range(3):  # repeated identical emissions, zero suppression
            assert should_emit_heartbeat(
                event_type, session_id="s1", project_root=tmp_path
            ), f"high-signal event {event_type} must never be rate-limited"
    # High-signal events never touch the cooldown cache.
    assert not _cache_file(tmp_path).exists()


def test_high_signal_underscore_variant_bypasses(tmp_path, clock):
    # capture_client normalizes decision_logged -> decision.logged; the
    # limiter must apply the same normalization before the allowlist check.
    assert is_high_signal_event_type("decision_logged")
    assert is_high_signal_event_type("DECISION.LOGGED")
    for _ in range(3):
        assert should_emit_heartbeat("decision_logged", session_id="s1", project_root=tmp_path)
    assert not _cache_file(tmp_path).exists()


def test_low_signal_types_are_not_high_signal():
    assert not is_high_signal_event_type("session-active")
    assert not is_high_signal_event_type("native_hook_activity:PreToolUse:attempt:Read")
    assert not is_high_signal_event_type("files-modified")


# ---------------------------------------------------------------------------
# Cache corruption / IO failure — fail open, never block emission
# ---------------------------------------------------------------------------


def test_corrupt_cache_json_fails_open(tmp_path, clock):
    cache_path = _cache_file(tmp_path)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text("{not json at all")
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    # The corrupt cache was replaced with valid state and limiting resumed.
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_cache_wrong_shape_fails_open(tmp_path, clock):
    cache_path = _cache_file(tmp_path)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps(["not", "a", "dict"]))
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_cache_non_numeric_timestamp_fails_open(tmp_path, clock):
    cache_path = _cache_file(tmp_path)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(json.dumps({"s1::session.active": "yesterday"}))
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_unwritable_cache_dir_fails_open(tmp_path, clock):
    # A regular file where the .claude dir should be makes every cache write
    # fail; emission must still be allowed on every call.
    (tmp_path / ".claude").write_text("i am a file, not a directory")
    for _ in range(3):
        assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_unexpected_internal_error_fails_open(tmp_path, clock, monkeypatch):
    def boom(_root):
        raise RuntimeError("cache layer exploded")

    monkeypatch.setattr(activity_ratelimit, "_load_cache", boom)
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


# ---------------------------------------------------------------------------
# Env override
# ---------------------------------------------------------------------------


def test_env_override_shortens_cooldown(tmp_path, clock, monkeypatch):
    monkeypatch.setenv(ENV_COOLDOWN_SECONDS, "10")
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    clock.advance(9)
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    clock.advance(2)
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_env_zero_disables_limiting(tmp_path, clock, monkeypatch):
    monkeypatch.setenv(ENV_COOLDOWN_SECONDS, "0")
    for _ in range(3):
        assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_env_invalid_falls_back_to_default(tmp_path, clock, monkeypatch):
    monkeypatch.setenv(ENV_COOLDOWN_SECONDS, "not-a-number")
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    clock.advance(DEFAULT_COOLDOWN_SECONDS - 1)
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_env_negative_falls_back_to_default(tmp_path, clock, monkeypatch):
    monkeypatch.setenv(ENV_COOLDOWN_SECONDS, "-5")
    assert should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)
    assert not should_emit_heartbeat("session-active", session_id="s1", project_root=tmp_path)


def test_explicit_cooldown_kwarg_beats_env(tmp_path, clock, monkeypatch):
    monkeypatch.setenv(ENV_COOLDOWN_SECONDS, "10000")
    assert should_emit_heartbeat(
        "session-active", session_id="s1", project_root=tmp_path, cooldown_seconds=5
    )
    clock.advance(6)
    assert should_emit_heartbeat(
        "session-active", session_id="s1", project_root=tmp_path, cooldown_seconds=5
    )


# ---------------------------------------------------------------------------
# Cache growth bound
# ---------------------------------------------------------------------------


def test_cache_size_is_bounded(tmp_path, clock):
    for i in range(activity_ratelimit._MAX_CACHE_ENTRIES + 10):
        clock.advance(1)
        should_emit_heartbeat(f"ping-{i}", session_id="s1", project_root=tmp_path)
    cache = json.loads(_cache_file(tmp_path).read_text())
    assert len(cache) <= activity_ratelimit._MAX_CACHE_ENTRIES


# ---------------------------------------------------------------------------
# native_hooks call-site integration (dopemux:events producer)
# ---------------------------------------------------------------------------


class RecordingRedisClient:
    def __init__(self):
        self.xadd_calls = []

    def xadd(self, stream, fields, maxlen=None, approximate=True):
        self.xadd_calls.append({"stream": stream, "fields": fields})
        return "1-0"

    def close(self):
        return None


def test_native_hook_identical_pings_coalesced(tmp_path, clock, monkeypatch):
    fake_redis = RecordingRedisClient()
    monkeypatch.setattr(
        native_hooks, "_open_activity_redis_client", lambda: fake_redis, raising=False
    )

    event = {
        "cwd": str(tmp_path),
        "session_id": "sess-1",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x.py"},
        "env": {"DOPEMUX_INSTANCE_ID": "main"},
    }
    for _ in range(5):
        handle_event("PreToolUse", dict(event))

    assert len(fake_redis.xadd_calls) == 1
    assert fake_redis.xadd_calls[0]["stream"] == "dopemux:events"


def test_native_hook_pings_emit_again_after_cooldown(tmp_path, clock, monkeypatch):
    fake_redis = RecordingRedisClient()
    monkeypatch.setattr(
        native_hooks, "_open_activity_redis_client", lambda: fake_redis, raising=False
    )

    event = {
        "cwd": str(tmp_path),
        "session_id": "sess-1",
        "tool_name": "Read",
        "env": {"DOPEMUX_INSTANCE_ID": "main"},
    }
    handle_event("PreToolUse", dict(event))
    clock.advance(DEFAULT_COOLDOWN_SECONDS + 1)
    handle_event("PreToolUse", dict(event))

    assert len(fake_redis.xadd_calls) == 2


def test_native_hook_distinct_tools_not_coalesced(tmp_path, clock, monkeypatch):
    fake_redis = RecordingRedisClient()
    monkeypatch.setattr(
        native_hooks, "_open_activity_redis_client", lambda: fake_redis, raising=False
    )

    for tool in ("Read", "Edit", "Bash"):
        handle_event(
            "PreToolUse",
            {
                "cwd": str(tmp_path),
                "session_id": "sess-1",
                "tool_name": tool,
                "env": {"DOPEMUX_INSTANCE_ID": "main"},
            },
        )

    assert len(fake_redis.xadd_calls) == 3


def test_native_hook_session_id_not_leaked_to_stream(tmp_path, clock, monkeypatch):
    # session_id keys the local cooldown cache but must never reach Redis.
    fake_redis = RecordingRedisClient()
    monkeypatch.setattr(
        native_hooks, "_open_activity_redis_client", lambda: fake_redis, raising=False
    )

    handle_event(
        "PreToolUse",
        {
            "cwd": str(tmp_path),
            "session_id": "session-secret",
            "tool_name": "Read",
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )

    assert len(fake_redis.xadd_calls) == 1
    assert "session-secret" not in json.dumps(fake_redis.xadd_calls, sort_keys=True)
    # ... while the cooldown cache (local, under .claude/) does key by it.
    cache = json.loads(_cache_file(tmp_path).read_text())
    assert any(key.startswith("session-secret::") for key in cache)


# ---------------------------------------------------------------------------
# claude_code_hooks session-active producer (monitor daemon path)
# ---------------------------------------------------------------------------


def test_session_active_heartbeat_gated(tmp_path, clock, monkeypatch):
    from dopemux.hooks import claude_code_hooks as cch

    hooks = cch.ClaudeCodeHooks()
    hooks.watched_paths = [tmp_path]

    triggered = []

    async def record_trigger(event_type, context):
        triggered.append(event_type)

    class FakeProc:
        async def communicate(self):
            return b"12345\n", b""

    async def fake_subprocess(*_args, **_kwargs):
        return FakeProc()

    monkeypatch.setattr(hooks, "_trigger_hook", record_trigger)
    monkeypatch.setattr(cch.asyncio, "create_subprocess_shell", fake_subprocess)

    # 2s-poll simulation: five consecutive ticks -> exactly one emission.
    for _ in range(5):
        asyncio.run(hooks._check_claude_session())
    assert triggered == ["session-active"]

    # After the cooldown window the next tick emits again.
    clock.advance(DEFAULT_COOLDOWN_SECONDS + 1)
    asyncio.run(hooks._check_claude_session())
    assert triggered == ["session-active", "session-active"]
