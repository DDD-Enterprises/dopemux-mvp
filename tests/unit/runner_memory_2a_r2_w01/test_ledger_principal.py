"""Ledger principal column: migration up/down, store API, older readers,
capture_client compatibility, eventbus_consumer self-asserted principal."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

from chronicle import sqlite_migrations  # noqa: E402

from chronicle.store import ChronicleStore  # noqa: E402

from .helpers import SERVICE_DIR  # noqa: E402

MIGRATION = SERVICE_DIR / "chronicle" / "migrations" / "v1_3_0_add_write_principal.sql"
SCHEMA = SERVICE_DIR / "chronicle" / "schema.sql"
TABLES = ("raw_activity_events", "work_log_entries", "issue_links", "reflection_cards")
COLUMNS = ("write_principal", "write_principal_self_asserted")
NOW = "2026-10-31T00:00:00+00:00"


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _make_pre_migration_ledger(path: Path) -> None:
    """Build a ledger as it looked at v1.2.1 (no principal columns)."""
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA.read_text())
    for table in TABLES:
        for column in COLUMNS:
            conn.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
    conn.execute("DELETE FROM schema_migrations WHERE version = 'v1.3.0'")
    conn.commit()
    conn.close()


def _old_style_insert(conn, entry_id="old-1"):
    """INSERT the way pre-migration writers (capture_client.py) do: no principal."""
    conn.execute(
        """
        INSERT INTO raw_activity_events (
            id, workspace_id, instance_id, session_id, ts_utc, event_type, source,
            payload_json, redaction_level, ttl_days, created_at_utc
        ) VALUES (?, 'ws', 'i', NULL, ?, 'shell.command', 'cli', '{}', 'strict', 7, ?)
        """,
        (entry_id, NOW, NOW),
    )
    conn.commit()


def _apply(conn):
    return sqlite_migrations.apply_chronicle_migrations(
        conn, schema_path=SCHEMA, migrations_dir=MIGRATION.parent
    )


# --- migration -----------------------------------------------------------------


def test_should_ship_migration_file_with_documented_rollback():
    text = MIGRATION.read_text()
    assert re.search(r"(?im)^--\s*ROLLBACK:", text), "rollback statement missing from header"
    assert "v1.3.0" in text
    for table in TABLES:
        assert f"ALTER TABLE {table} ADD COLUMN write_principal" in text


def test_should_add_nullable_defaulted_columns_to_an_older_ledger(tmp_path):
    ledger = tmp_path / "old.sqlite"
    _make_pre_migration_ledger(ledger)
    conn = sqlite3.connect(str(ledger))
    _old_style_insert(conn)
    assert "write_principal" not in _columns(conn, "raw_activity_events")

    applied = _apply(conn)

    assert "v1_3_0_add_write_principal.sql" in applied
    for table in TABLES:
        assert set(COLUMNS) <= _columns(conn, table)
    row = conn.execute(
        "SELECT write_principal, write_principal_self_asserted FROM raw_activity_events"
    ).fetchone()
    assert tuple(row) == ("unverified", 0)  # pre-existing rows read as unverified
    info = {r[1]: r for r in conn.execute("PRAGMA table_info(raw_activity_events)")}
    assert info["write_principal"][4] == "'unverified'"  # default
    assert info["write_principal"][3] == 0  # nullable (notnull flag)
    conn.close()


def test_should_roll_back_with_the_documented_statements_and_reapply(tmp_path):
    ledger = tmp_path / "old.sqlite"
    _make_pre_migration_ledger(ledger)
    conn = sqlite3.connect(str(ledger))
    _old_style_insert(conn)
    _apply(conn)
    conn.execute(
        "UPDATE raw_activity_events SET write_principal = 'runner:codex' WHERE id = 'old-1'"
    )
    conn.commit()

    statements = [
        m.group(1).strip()
        for m in re.finditer(r"(?im)^--\s*ROLLBACK:\s*(.+)$", MIGRATION.read_text())
    ]
    assert statements
    for statement in statements:
        conn.execute(statement)
    conn.commit()

    for table in TABLES:
        assert not (set(COLUMNS) & _columns(conn, table))
    # rows keep their data
    assert conn.execute("SELECT id FROM raw_activity_events").fetchone()[0] == "old-1"
    assert conn.execute("SELECT version FROM schema_migrations WHERE version='v1.3.0'").fetchone() is None

    _apply(conn)  # re-apply after rollback works
    for table in TABLES:
        assert set(COLUMNS) <= _columns(conn, table)
    conn.close()


def test_should_boot_blank_ledger_with_columns_and_record_version(tmp_path):
    store = ChronicleStore(tmp_path / "fresh.sqlite")
    store.initialize_schema()
    conn = store.connect()
    for table in TABLES:
        assert set(COLUMNS) <= _columns(conn, table)
    versions = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    assert "v1.3.0" in versions
    store.initialize_schema()  # second init is a no-op, not a duplicate-column error
    store.close()


def test_should_not_fail_when_columns_already_exist_but_version_unrecorded(tmp_path):
    """First-use race / bootstrap path: another process added the columns."""
    ledger = tmp_path / "raced.sqlite"
    _make_pre_migration_ledger(ledger)
    conn = sqlite3.connect(str(ledger))
    conn.execute("ALTER TABLE raw_activity_events ADD COLUMN write_principal TEXT DEFAULT 'unverified'")
    conn.commit()
    _apply(conn)
    for table in TABLES:
        assert set(COLUMNS) <= _columns(conn, table)
    conn.close()


def test_should_skip_tables_a_legacy_ledger_does_not_have_yet(tmp_path):
    """A v1.0.0-era ledger has no raw_activity_events/issue_links table."""
    conn = sqlite3.connect(str(tmp_path / "legacy.sqlite"))
    conn.executescript(
        """
        CREATE TABLE work_log_entries (id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
          instance_id TEXT NOT NULL, summary TEXT NOT NULL, created_at_utc TEXT NOT NULL);
        CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at_utc TEXT NOT NULL);
        INSERT INTO schema_migrations VALUES ('v1.2.1', datetime('now'));
        """
    )
    _apply(conn)
    assert set(COLUMNS) <= _columns(conn, "work_log_entries")
    assert not _columns(conn, "raw_activity_events")
    conn.close()


def test_should_keep_older_readers_and_writers_working_on_a_migrated_ledger(tmp_path):
    ledger = tmp_path / "old.sqlite"
    _make_pre_migration_ledger(ledger)
    conn = sqlite3.connect(str(ledger))
    _old_style_insert(conn, "before")
    _apply(conn)
    _old_style_insert(conn, "after")  # old INSERT without the new columns
    # old reader: explicit column list, as pre-migration code uses
    rows = conn.execute(
        "SELECT id, workspace_id, instance_id, event_type, payload_json "
        "FROM raw_activity_events ORDER BY id"
    ).fetchall()
    assert [r[0] for r in rows] == ["after", "before"]
    principals = [r[0] for r in conn.execute("SELECT write_principal FROM raw_activity_events")]
    assert principals == ["unverified", "unverified"]
    conn.close()


def test_should_let_capture_client_write_to_a_migrated_ledger(tmp_path, monkeypatch):
    from dopemux.memory.capture_client import emit_capture_event

    ledger = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
    repo_root = SERVICE_DIR.parents[1]
    # An older ledger that the capture client migrates on first use.
    _make_pre_migration_ledger(ledger)
    result = emit_capture_event(
        {"event_type": "shell.command", "payload": {"command": "echo hi"}},
        mode="cli",
        repo_root=repo_root,
    )
    conn = sqlite3.connect(str(result.ledger_path))
    try:
        assert set(COLUMNS) <= _columns(conn, "raw_activity_events")
        row = conn.execute(
            "SELECT write_principal, write_principal_self_asserted"
            " FROM raw_activity_events WHERE id = ?",
            (result.event_id,),
        ).fetchone()
    finally:
        conn.close()
    # W06: the capture client records its self-asserted principal.
    assert tuple(row) == ("internal:cli", 1)


# --- store API -------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    s = ChronicleStore(tmp_path / "s.sqlite")
    s.initialize_schema()
    yield s
    s.close()


def _insert_entry(store, **kwargs):
    return store.insert_work_log_entry(
        workspace_id="ws",
        instance_id="i",
        category="implementation",
        entry_type="decision",
        summary="s",
        source_event_id=f"manual-{kwargs.pop('n', 1)}",
        source_event_type="manual.memory_store",
        source_adapter="mcp-server",
        source_event_ts_utc=NOW,
        promotion_rule="manual",
        **kwargs,
    )


def _row(store, table):
    return tuple(
        store.connect().execute(
            f"SELECT write_principal, write_principal_self_asserted FROM {table}"
        ).fetchone()
    )


def test_should_default_to_unverified_when_no_principal_is_given(store):
    _insert_entry(store)
    assert _row(store, "work_log_entries") == ("unverified", 0)


def test_should_store_principal_on_work_log_entries(store):
    _insert_entry(store, write_principal="runner:claude")
    assert _row(store, "work_log_entries") == ("runner:claude", 0)


def test_should_store_self_asserted_marker(store):
    store.insert_raw_event(
        "ws", "i", "shell.command", "cli", {"a": 1},
        write_principal="internal:wma", principal_self_asserted=True,
    )
    assert _row(store, "raw_activity_events") == ("internal:wma", 1)


def test_should_store_principal_on_issue_links_and_reflections_and_corrections(store):
    a = _insert_entry(store, n=1)
    b = _insert_entry(store, n=2)
    store.insert_issue_link("ws", "i", a, b, write_principal="runner:codex")
    assert _row(store, "issue_links") == ("runner:codex", 0)

    store.insert_corrected_work_log_entry(
        "ws", "i", b, "update", "fixed", write_principal="runner:codex"
    )
    rows = store.connect().execute(
        "SELECT write_principal FROM work_log_entries ORDER BY created_at_utc"
    ).fetchall()
    assert [r[0] for r in rows][-1] == "runner:codex"

    store.insert_reflection_card(
        {
            "reflection_id": "r1", "workspace_id": "ws", "instance_id": "i",
            "window_start": NOW, "window_end": NOW, "trajectory_summary": "t",
            "top_decisions": [], "top_blockers": [], "progress_summary": {},
            "suggested_next": [],
        },
        write_principal="runner:codex",
    )
    assert _row(store, "reflection_cards") == ("runner:codex", 0)


def test_should_store_principal_on_promoted_entries(store):
    from promotion.promotion import PromotionEngine

    entry = PromotionEngine().promote(
        {
            "id": "e1", "event_type": "decision.logged", "type": "decision.logged",
            "source": "x", "ts_utc": NOW, "ts": NOW,
            "payload": {"decision_id": "d", "title": "T", "choice": "C", "rationale": "R"},
            "data": {"decision_id": "d", "title": "T", "choice": "C", "rationale": "R"},
        }
    )
    assert entry is not None
    store.insert_promoted_entry(
        "ws", "i", entry, write_principal="internal:wma", principal_self_asserted=True
    )
    assert _row(store, "work_log_entries") == ("internal:wma", 1)


# --- eventbus_consumer -------------------------------------------------------------


async def test_should_record_internal_wma_principal_with_self_asserted_marker(tmp_path, monkeypatch):
    pytest.importorskip("redis")
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "bus.sqlite"))
    from eventbus_consumer import EventBusConsumer

    consumer = EventBusConsumer(redis_url="redis://localhost:6379")
    msg = {
        b"id": b"event-1",
        b"ts": b"2026-02-02T10:00:00Z",
        b"workspace_id": b"ws",
        b"instance_id": b"i",
        b"type": b"decision.logged",
        b"source": b"dopequery",
        b"data": json.dumps(
            {"decision_id": "d-1", "title": "Use SQLite", "choice": "SQLite", "rationale": "simple"}
        ).encode(),
    }
    await consumer._process_message(b"m-1", msg)

    conn = consumer._get_store("ws").connect()
    raw = conn.execute(
        "SELECT write_principal, write_principal_self_asserted FROM raw_activity_events"
    ).fetchall()
    promoted = conn.execute(
        "SELECT write_principal, write_principal_self_asserted FROM work_log_entries"
    ).fetchall()
    assert raw and promoted
    assert {tuple(r) for r in raw + promoted} == {("internal:wma", 1)}
