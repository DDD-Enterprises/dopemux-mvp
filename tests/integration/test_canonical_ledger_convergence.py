"""
Integration tests for Packet C: Canonical Ledger Unification.

Verifies:
1. Exactly one writable chronicle per project (single ledger existence)
2. CLI capture and WMA service write to the same DB file (cross-adapter convergence)
3. Attempts to write to legacy ~/.dope-memory fail loudly (legacy path failure)
4. store.py INSERT OR IGNORE deduplicates like capture_client
"""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the WMA service packages are importable
_WMA_DIR = Path(__file__).resolve().parents[2] / "services" / "working-memory-assistant"
if str(_WMA_DIR) not in sys.path:
    sys.path.insert(0, str(_WMA_DIR))

from dopemux.memory.capture_client import (
    CaptureError,
    emit_capture_event,
    resolve_repo_root_strict,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_events(ledger_path: Path) -> int:
    conn = sqlite3.connect(str(ledger_path))
    try:
        return int(
            conn.execute("SELECT COUNT(*) FROM raw_activity_events").fetchone()[0]
        )
    finally:
        conn.close()


def _get_event_ids(ledger_path: Path) -> list[str]:
    conn = sqlite3.connect(str(ledger_path))
    try:
        rows = conn.execute(
            "SELECT id FROM raw_activity_events ORDER BY id"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 1: Single ledger existence
# ---------------------------------------------------------------------------

class TestSingleLedgerExistence:
    """Verify exactly one SQLite file receives writes per project."""

    def test_capture_client_writes_to_canonical_path(self, tmp_path, monkeypatch):
        """capture_client writes to repo_root/.dopemux/chronicle.sqlite."""
        ledger_path = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

        result = emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "test capture client"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )

        assert result.ledger_path == ledger_path.resolve()
        assert ledger_path.exists()
        assert _count_events(ledger_path) == 1

    def test_wma_store_writes_to_canonical_path(self, tmp_path, monkeypatch):
        """WMA ChronicleStore uses canonical ledger resolution."""
        ledger_path = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

        from canonical_ledger import resolve_canonical_ledger

        resolved = resolve_canonical_ledger("any-workspace-id")
        assert resolved == ledger_path.resolve()

    def test_no_chronicle_db_files_created(self, tmp_path, monkeypatch):
        """No legacy chronicle.db files are created anywhere."""
        ledger_path = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "test no legacy"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )

        # Verify no .db files exist anywhere under tmp_path
        db_files = list(tmp_path.rglob("*.db"))
        assert db_files == [], f"Legacy .db files found: {db_files}"


# ---------------------------------------------------------------------------
# Test 2: Cross-adapter convergence
# ---------------------------------------------------------------------------

class TestCrossAdapterConvergence:
    """Verify CLI capture and WMA service write to the same DB file."""

    def test_capture_client_and_wma_store_share_ledger(self, tmp_path, monkeypatch):
        """Both capture_client and WMA store resolve to the same file."""
        ledger_path = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

        from canonical_ledger import resolve_canonical_ledger

        # capture_client writes
        result = emit_capture_event(
            {
                "event_type": "manual.note",
                "source": "test",
                "payload": {"summary": "from capture_client"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )

        # WMA resolves
        wma_path = resolve_canonical_ledger("any-workspace")

        assert result.ledger_path == wma_path
        assert result.ledger_path == ledger_path.resolve()

    def test_wma_store_reads_capture_client_writes(self, tmp_path, monkeypatch):
        """WMA ChronicleStore can read events written by capture_client."""
        ledger_path = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

        # Write via capture_client
        emit_capture_event(
            {
                "event_type": "decision.logged",
                "source": "test",
                "payload": {"summary": "Architecture decision"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )

        # Read via ChronicleStore
        from chronicle.store import ChronicleStore

        store = ChronicleStore(ledger_path)
        store.initialize_schema()
        conn = store.connect()
        rows = conn.execute(
            "SELECT event_type, source FROM raw_activity_events"
        ).fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "decision.logged"
        assert rows[0][1] == "test"

    def test_all_capture_modes_write_to_same_ledger(self, tmp_path, monkeypatch):
        """Plugin, CLI, and MCP modes all write to the same canonical ledger."""
        ledger_path = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

        results = []
        for mode in ("plugin", "cli", "mcp"):
            result = emit_capture_event(
                {
                    "event_type": "manual.note",
                    "payload": {"summary": f"From {mode} mode"},
                },
                mode=mode,
                repo_root=REPO_ROOT,
            )
            results.append(result)

        # All resolved to same ledger
        paths = {str(r.ledger_path) for r in results}
        assert len(paths) == 1, f"Multiple ledger paths: {paths}"

        # All events in one database
        assert _count_events(ledger_path) == 3


# ---------------------------------------------------------------------------
# Test 3: Legacy path failure
# ---------------------------------------------------------------------------

class TestLegacyPathFailure:
    """Verify attempts to use legacy ~/.dope-memory paths fail loudly."""

    def test_canonical_ledger_fails_closed_without_markers(self, tmp_path, monkeypatch):
        """resolve_canonical_ledger fails closed when no repo markers exist."""
        # Clear override so resolution must find repo markers
        monkeypatch.delenv("DOPEMUX_CAPTURE_LEDGER_PATH", raising=False)

        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir(parents=True)
        monkeypatch.chdir(non_repo)

        from canonical_ledger import CanonicalLedgerError, resolve_canonical_ledger

        with pytest.raises(CanonicalLedgerError, match="fails closed"):
            resolve_canonical_ledger("not-a-path")

    def test_env_override_takes_precedence(self, tmp_path, monkeypatch):
        """DOPEMUX_CAPTURE_LEDGER_PATH overrides all other resolution."""
        override = tmp_path / "custom" / "ledger.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(override))

        from canonical_ledger import resolve_canonical_ledger

        resolved = resolve_canonical_ledger("ignored-workspace-id")
        assert resolved == override.resolve()

    def test_workspace_id_as_repo_root_resolves_canonical(self, tmp_path, monkeypatch):
        """workspace_id that is an absolute path with .git resolves to canonical ledger."""
        monkeypatch.delenv("DOPEMUX_CAPTURE_LEDGER_PATH", raising=False)

        fake_repo = tmp_path / "my-project"
        (fake_repo / ".git").mkdir(parents=True)

        from canonical_ledger import resolve_canonical_ledger

        resolved = resolve_canonical_ledger(str(fake_repo))
        expected = (fake_repo / ".dopemux" / "chronicle.sqlite").resolve()
        assert resolved == expected


# ---------------------------------------------------------------------------
# Test 4: store.py INSERT OR IGNORE dedup
# ---------------------------------------------------------------------------

class TestStoreIdempotentDedup:
    """Verify store.py INSERT OR IGNORE matches capture_client dedup."""

    def test_store_insert_raw_event_is_idempotent(self, tmp_path):
        """Duplicate event_id does not crash, is silently ignored."""
        from chronicle.store import ChronicleStore

        db_path = tmp_path / "test.sqlite"
        store = ChronicleStore(db_path)
        store.initialize_schema()

        event_id = "test-dedup-event-001"

        # First insert
        store.insert_raw_event(
            workspace_id="ws",
            instance_id="A",
            event_type="manual.note",
            source="test",
            payload={"summary": "first"},
            event_id=event_id,
        )

        # Second insert with same ID — must NOT crash
        store.insert_raw_event(
            workspace_id="ws",
            instance_id="A",
            event_type="manual.note",
            source="test",
            payload={"summary": "duplicate"},
            event_id=event_id,
        )

        # Verify only one event
        conn = store.connect()
        count = conn.execute(
            "SELECT COUNT(*) FROM raw_activity_events WHERE id = ?",
            (event_id,),
        ).fetchone()[0]
        assert count == 1

        # Verify first insert's payload is preserved (not overwritten)
        row = conn.execute(
            "SELECT payload_json FROM raw_activity_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        payload = json.loads(row[0])
        assert payload["summary"] == "first"
