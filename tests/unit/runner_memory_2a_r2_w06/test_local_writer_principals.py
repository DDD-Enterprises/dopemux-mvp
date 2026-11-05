"""Wave 2A R2 W06: local writers record self-asserted internal principals.

Covers design 5.3 / operator ruling 3: capture_client.py (SQLite ledger) and
native_hooks.py (Redis XADD) carry no token, so they record ``internal:cli`` or
``internal:hooks`` with the self-asserted marker. All state lives in tmp dirs;
Redis is a fake client.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

from dopemux.claude import native_hooks
from dopemux.memory import capture_client as capture_client_module
from dopemux.memory.capture_client import (
    CaptureError,
    emit_capture_event,
    emit_promotable_capture_event,
    try_emit_promotable_capture_event,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PRINCIPAL_RE = re.compile(r"^(runner|internal):[a-z0-9][a-z0-9_.-]{0,63}$")


def _row(ledger: Path, event_id: str) -> tuple:
    conn = sqlite3.connect(str(ledger))
    try:
        return conn.execute(
            "SELECT write_principal, write_principal_self_asserted "
            "FROM raw_activity_events WHERE id = ?",
            (event_id,),
        ).fetchone()
    finally:
        conn.close()


def _columns(ledger: Path) -> set[str]:
    conn = sqlite3.connect(str(ledger))
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(raw_activity_events)")}
    finally:
        conn.close()


@pytest.fixture()
def ledger(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(path))
    monkeypatch.delenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", raising=False)
    return path


def _event(text: str) -> dict:
    return {"event_type": "manual.note", "payload": {"summary": text}}


def test_default_capture_records_internal_cli_self_asserted(ledger):
    result = emit_capture_event(_event("cli default"), mode="cli", repo_root=REPO_ROOT)

    assert _row(ledger, result.event_id) == ("internal:cli", 1)


def test_explicit_hooks_principal_is_recorded_self_asserted(ledger):
    result = emit_capture_event(
        _event("from hooks"),
        mode="plugin",
        repo_root=REPO_ROOT,
        principal="internal:hooks",
    )

    assert _row(ledger, result.event_id) == ("internal:hooks", 1)


def test_promotable_wrappers_forward_principal(ledger):
    direct = emit_promotable_capture_event(
        "error.encountered",
        {"message": "direct"},
        source="dopemux.native_hooks",
        mode="plugin",
        repo_root=REPO_ROOT,
        principal="internal:hooks",
    )
    best_effort = try_emit_promotable_capture_event(
        "error.encountered",
        {"message": "best effort"},
        source="dopemux.native_hooks",
        mode="plugin",
        repo_root=REPO_ROOT,
        principal="internal:hooks",
    )
    default = emit_promotable_capture_event(
        "error.encountered",
        {"message": "default"},
        source="cli",
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert best_effort is not None
    assert _row(ledger, direct.event_id) == ("internal:hooks", 1)
    assert _row(ledger, best_effort.event_id) == ("internal:hooks", 1)
    assert _row(ledger, default.event_id) == ("internal:cli", 1)


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "unverified",
        "hooks",
        "internal:",
        "internal:Hooks",
        "internal:" + "a" * 65,
        "runner:claude",  # local writers may only self-assert an internal principal
        "internal:hooks; DROP TABLE raw_activity_events",
    ],
)
def test_invalid_principal_is_rejected_and_writes_nothing(ledger, bad):
    with pytest.raises(CaptureError):
        emit_capture_event(
            _event("bad principal"), mode="cli", repo_root=REPO_ROOT, principal=bad
        )

    assert not ledger.exists()


def test_invalid_principal_makes_best_effort_wrapper_return_none(ledger):
    result = try_emit_promotable_capture_event(
        "error.encountered",
        {"message": "x"},
        source="dopemux.native_hooks",
        mode="plugin",
        repo_root=REPO_ROOT,
        principal="not a principal",
    )

    assert result is None


def test_event_dict_cannot_smuggle_a_principal(ledger):
    event = _event("smuggle")
    event["write_principal"] = "runner:claude"
    event["write_principal_self_asserted"] = 0

    result = emit_capture_event(event, mode="cli", repo_root=REPO_ROOT)

    assert _row(ledger, result.event_id) == ("internal:cli", 1)


def test_principal_stored_is_valid_per_ledger_contract(ledger):
    result = emit_capture_event(_event("shape"), mode="cli", repo_root=REPO_ROOT)

    principal, _ = _row(ledger, result.event_id)
    assert PRINCIPAL_RE.match(principal)


def test_event_stream_envelope_carries_principal(ledger, monkeypatch):
    emitted: list[dict] = []
    monkeypatch.setattr(capture_client_module, "_emit_to_event_stream", emitted.append)

    emit_capture_event(
        _event("bus"),
        mode="plugin",
        repo_root=REPO_ROOT,
        emit_event_bus=True,
        principal="internal:hooks",
    )

    assert len(emitted) == 1
    assert emitted[0]["write_principal"] == "internal:hooks"


def test_event_stream_xadd_has_principal_fields(ledger, monkeypatch):
    class _Redis:
        calls: list[tuple] = []

        @classmethod
        def from_url(cls, *_a, **_k):
            return cls()

        def xadd(self, stream, fields):
            self.calls.append((stream, fields))

    class _Module:
        Redis = _Redis

    monkeypatch.setitem(__import__("sys").modules, "redis", _Module)

    emit_capture_event(
        _event("xadd"), mode="cli", repo_root=REPO_ROOT, emit_event_bus=True
    )

    assert len(_Redis.calls) == 1
    fields = _Redis.calls[0][1]
    assert fields["write_principal"] == "internal:cli"
    assert fields["write_principal_self_asserted"] == "1"


# --- B03: ledger written before and after W01's migration -------------------


def _make_pre_migration_ledger(path: Path) -> None:
    """A ledger as written before W01: no principal columns, v1.2.1 recorded."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(
            """
            CREATE TABLE raw_activity_events (
              id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
              instance_id TEXT NOT NULL, session_id TEXT,
              ts_utc TEXT NOT NULL, event_type TEXT NOT NULL,
              source TEXT NOT NULL, payload_json TEXT NOT NULL,
              redaction_level TEXT NOT NULL DEFAULT 'strict',
              ttl_days INTEGER NOT NULL DEFAULT 7,
              created_at_utc TEXT NOT NULL
            );
            CREATE TABLE schema_migrations (
              version TEXT PRIMARY KEY, applied_at_utc TEXT NOT NULL
            );
            INSERT INTO schema_migrations VALUES ('v1.2.1', datetime('now'));
            INSERT INTO raw_activity_events VALUES
              ('legacy-1', 'ws', 'A', NULL, '2026-01-01T00:00:00+00:00',
               'manual.note', 'cli', '{}', 'strict', 7, '2026-01-01T00:00:00+00:00');
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_pre_migration_ledger_is_migrated_and_new_row_carries_principal(ledger):
    _make_pre_migration_ledger(ledger)
    assert "write_principal" not in _columns(ledger)

    result = emit_capture_event(
        _event("after migration"),
        mode="plugin",
        repo_root=REPO_ROOT,
        principal="internal:hooks",
    )

    assert {"write_principal", "write_principal_self_asserted"} <= _columns(ledger)
    assert _row(ledger, result.event_id) == ("internal:hooks", 1)
    # Existing rows are not rewritten: they read as unverified and not self-asserted.
    assert _row(ledger, "legacy-1") == ("unverified", 0)


def test_ledger_written_after_migration_stays_writable_by_default_principal(ledger):
    first = emit_capture_event(_event("one"), mode="cli", repo_root=REPO_ROOT)
    capture_client_module._SCHEMA_READY_LEDGER_PATHS.discard(str(ledger.resolve()))
    second = emit_capture_event(_event("two"), mode="cli", repo_root=REPO_ROOT)

    assert _row(ledger, first.event_id) == ("internal:cli", 1)
    assert _row(ledger, second.event_id) == ("internal:cli", 1)


# --- native_hooks: Redis event + capture call -------------------------------


class _FakeRedis:
    def __init__(self):
        self.xadd_calls = []

    def xadd(self, stream, fields, maxlen=None, approximate=True):
        self.xadd_calls.append({"stream": stream, "fields": fields})
        return "1-0"

    def close(self):
        return None


def test_native_hook_redis_event_carries_internal_hooks_principal(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: fake)
    monkeypatch.setattr(native_hooks, "should_emit_heartbeat", lambda *a, **k: True)

    emitted = native_hooks._emit_activity_event(
        hook_event_name="PreToolUse", status="attempt", tool_name="Read"
    )

    assert emitted is True
    fields = fake.xadd_calls[0]["fields"]
    assert fields["write_principal"] == "internal:hooks"
    assert fields["write_principal_self_asserted"] == "1"
    # Content-free payload is unchanged: the principal is an envelope field.
    assert set(json.loads(fields["data"])) == {"hook_event_name", "status", "tool_name"}
    assert "token" not in json.dumps(fields).lower()


def test_native_hook_error_capture_passes_internal_hooks_principal(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(
        native_hooks,
        "try_emit_promotable_capture_event",
        lambda event_type, payload, **kwargs: captured.append(kwargs),
    )

    native_hooks._emit_bounded_hook_error_capture(
        project_root=tmp_path,
        session_id=None,
        hook_event_name="PostToolUseFailure",
        tool_name="Bash",
    )

    assert captured and captured[0]["principal"] == "internal:hooks"


def test_native_hook_error_capture_writes_hooks_principal_to_ledger(ledger, monkeypatch):
    """End to end through the real capture_client (tmp ledger, no Redis)."""
    monkeypatch.setattr(capture_client_module, "_emit_to_event_stream", lambda e: None)

    native_hooks._emit_bounded_hook_error_capture(
        project_root=REPO_ROOT,
        session_id=None,
        hook_event_name="PostToolUseFailure",
        tool_name="Bash",
    )

    conn = sqlite3.connect(str(ledger))
    try:
        rows = conn.execute(
            "SELECT write_principal, write_principal_self_asserted "
            "FROM raw_activity_events WHERE event_type = 'error.encountered'"
        ).fetchall()
    finally:
        conn.close()
    assert rows == [("internal:hooks", 1)]


# --- B02: fail-open is unchanged --------------------------------------------


def test_native_hook_redis_failure_still_fails_open(monkeypatch):
    class _Failing:
        def xadd(self, *_a, **_k):
            raise RuntimeError("redis unavailable")

        def close(self):
            return None

    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: _Failing())
    monkeypatch.setattr(native_hooks, "should_emit_heartbeat", lambda *a, **k: True)

    assert (
        native_hooks._emit_activity_event(hook_event_name="PreToolUse", status="attempt")
        is False
    )


def test_native_hook_invalid_principal_capture_failure_is_swallowed(tmp_path, monkeypatch):
    def boom(*_a, **_k):
        raise CaptureError("bad principal")

    monkeypatch.setattr(native_hooks, "try_emit_promotable_capture_event", boom)

    native_hooks._emit_bounded_hook_error_capture(
        project_root=tmp_path,
        session_id=None,
        hook_event_name="PostToolUseFailure",
        tool_name="Bash",
    )
