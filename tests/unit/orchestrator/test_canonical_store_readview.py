"""Tests for the canonical-store read-only operator view.

Covers:
  (a) flag off   -> inspect command fails closed (non-zero + 'disabled' message)
  (b) flag on + nonexistent --db -> non-zero, clear message
  (c) flag on + fixture db -> exit 0, valid_as_of + provenance fields present
  (d) read-only enforced: INSERT via _connect_ro raises sqlite3.OperationalError
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from dopemux.commands.orchestrator_commands import orchestrator_group
from dopemux.orchestrator.canonical_readview import _connect_ro, read_canonical_view

# ──────────────────────────────────────────────────────────────────────────────
# Fixture helpers
# ──────────────────────────────────────────────────────────────────────────────

_SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "services"
    / "task-orchestrator"
    / "app"
    / "storage"
    / "canonical_store_schema.sql"
)

_KNOWN_SLUG = "wt-test-slug"
_KNOWN_MTIME = "2026-01-15T10:00:00Z"
_KNOWN_IDENTITY = "canon-id-001"


@pytest.fixture()
def canonical_db(tmp_path: Path) -> Path:
    """Build a minimal canonical reconciliation SQLite fixture in *tmp_path*.

    Inserts exactly one row into each required table, satisfying all FK and
    NOT NULL constraints so the reader can exercise the full query path.
    """
    db_path = tmp_path / "canonical_test.sqlite"
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_sql)

    # 1. source_databases — parent of all FK chains
    conn.execute(
        """
        INSERT INTO source_databases (
            source_db_slug,
            source_database_path,
            source_schema_hash,
            source_schema_class,
            source_mtime_utc,
            source_table,
            source_row_id,
            archive_sha256,
            import_run_id,
            bytes,
            table_count,
            work_items_count,
            dependencies_count,
            notes_count,
            role_transitions_count,
            queue_count,
            work_count,
            review_count,
            blocked_count,
            terminal_count,
            adjudication_class,
            canonical_treatment,
            imported_at_utc
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0,
            ?, ?, ?
        )
        """,
        (
            _KNOWN_SLUG,
            "/fake/path/wt-test.db",
            "sha256-schema-hash-abc",
            "modern",
            _KNOWN_MTIME,
            "DATABASE_INDEX.csv",
            "row-001",
            "sha256-archive-abc",
            "run-001",
            "include",
            "canonical",
            "2026-01-15T10:01:00Z",
        ),
    )

    # 2. reconciliation_decisions — referenced by canonical_current_work_items.decision_id
    conn.execute(
        """
        INSERT INTO reconciliation_decisions (
            source_db_slug,
            source_database_path,
            source_schema_hash,
            source_table,
            source_row_id,
            source_mtime_utc,
            import_run_id,
            archive_sha256,
            decision_type,
            decision,
            reason,
            created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _KNOWN_SLUG,
            "/fake/path/wt-test.db",
            "sha256-schema-hash-abc",
            "work_items",
            "row-001",
            _KNOWN_MTIME,
            "run-001",
            "sha256-archive-abc",
            "include",
            "canonical",
            "item is unique across sources",
            "2026-01-15T10:01:00Z",
        ),
    )
    decision_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 3. canonical_current_work_items — references both parents above
    conn.execute(
        """
        INSERT INTO canonical_current_work_items (
            source_db_slug,
            source_database_path,
            source_schema_hash,
            source_table,
            source_row_id,
            source_mtime_utc,
            import_run_id,
            archive_sha256,
            canonical_identity,
            role,
            status_label,
            title,
            decision_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _KNOWN_SLUG,
            "/fake/path/wt-test.db",
            "sha256-schema-hash-abc",
            "work_items",
            "row-001",
            _KNOWN_MTIME,
            "run-001",
            "sha256-archive-abc",
            _KNOWN_IDENTITY,
            "work",
            "IN_PROGRESS",
            "Test work item",
            decision_id,
        ),
    )
    conn.commit()
    conn.close()
    return db_path


# ──────────────────────────────────────────────────────────────────────────────
# (a) Flag off → inspect fails closed
# ──────────────────────────────────────────────────────────────────────────────


def test_inspect_fails_closed_when_flag_off(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Command must exit non-zero with a 'disabled' message when flag is unset."""
    monkeypatch.delenv("CANONICAL_STORE_READ_VIEW_ENABLED", raising=False)
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        ["canonical-store", "inspect", "--db", str(tmp_path / "any.sqlite")],
    )
    assert result.exit_code != 0
    assert "disabled" in (result.output or "").lower() or "disabled" in str(
        result.exception or ""
    ).lower()


def test_inspect_fails_closed_when_flag_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Command must exit non-zero when flag is explicitly set to 'false'."""
    monkeypatch.setenv("CANONICAL_STORE_READ_VIEW_ENABLED", "false")
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        ["canonical-store", "inspect", "--db", str(tmp_path / "any.sqlite")],
    )
    assert result.exit_code != 0
    output = result.output or ""
    assert "CANONICAL_STORE_READ_VIEW_ENABLED" in output


# ──────────────────────────────────────────────────────────────────────────────
# (b) Flag on + nonexistent --db → non-zero with clear message
# ──────────────────────────────────────────────────────────────────────────────


def test_inspect_fails_on_missing_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Command must exit non-zero when --db path does not exist."""
    monkeypatch.setenv("CANONICAL_STORE_READ_VIEW_ENABLED", "true")
    missing = tmp_path / "does_not_exist.sqlite"
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        ["canonical-store", "inspect", "--db", str(missing)],
    )
    assert result.exit_code != 0
    output = result.output or ""
    assert "not found" in output.lower() or str(missing) in output


# ──────────────────────────────────────────────────────────────────────────────
# (c) Flag on + fixture db → exit 0, valid_as_of + provenance present
# ──────────────────────────────────────────────────────────────────────────────


def test_inspect_succeeds_with_fixture_db(
    canonical_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Command exits 0 and prints valid_as_of + provenance slug from fixture."""
    monkeypatch.setenv("CANONICAL_STORE_READ_VIEW_ENABLED", "1")
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        ["canonical-store", "inspect", "--db", str(canonical_db)],
    )
    assert result.exit_code == 0, f"unexpected error: {result.output}"
    output = result.output
    assert _KNOWN_MTIME in output
    assert _KNOWN_SLUG in output


def test_inspect_json_output_with_fixture_db(
    canonical_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JSON output contains valid_as_of and items list with provenance fields."""
    import json

    monkeypatch.setenv("CANONICAL_STORE_READ_VIEW_ENABLED", "yes")
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        ["canonical-store", "inspect", "--db", str(canonical_db), "--json-output"],
    )
    assert result.exit_code == 0, f"unexpected error: {result.output}"
    payload = json.loads(result.output)
    assert payload["valid_as_of"] == _KNOWN_MTIME
    assert payload["source_db_count"] == 1
    assert payload["item_count"] == 1
    items = payload["items"]
    assert len(items) == 1
    item = items[0]
    assert item["canonical_identity"] == _KNOWN_IDENTITY
    assert item["source_db_slug"] == _KNOWN_SLUG
    assert "source_row_id" in item
    # summary / note bodies must NOT be present
    assert "summary" not in item


def test_read_canonical_view_returns_correct_structure(
    canonical_db: Path,
) -> None:
    """Unit-level check: read_canonical_view returns expected keys and values."""
    view = read_canonical_view(canonical_db)
    assert view["valid_as_of"] == _KNOWN_MTIME
    assert view["source_db_count"] == 1
    assert view["item_count"] == 1
    assert len(view["items"]) == 1
    item = view["items"][0]
    assert item["canonical_identity"] == _KNOWN_IDENTITY
    assert item["source_db_slug"] == _KNOWN_SLUG


def test_read_canonical_view_raises_on_missing_file(tmp_path: Path) -> None:
    """read_canonical_view raises FileNotFoundError for a missing path."""
    with pytest.raises(FileNotFoundError):
        read_canonical_view(tmp_path / "missing.sqlite")


def test_read_canonical_view_raises_on_non_canonical_store(tmp_path: Path) -> None:
    """read_canonical_view raises ValueError for a plain SQLite file."""
    db_path = tmp_path / "plain.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY);")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="not a canonical reconciliation store"):
        read_canonical_view(db_path)


# ──────────────────────────────────────────────────────────────────────────────
# (d) Read-only enforcement via _connect_ro
# ──────────────────────────────────────────────────────────────────────────────


def test_connect_ro_raises_on_write(canonical_db: Path) -> None:
    """_connect_ro must raise sqlite3.OperationalError on any write attempt."""
    conn = _connect_ro(canonical_db)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO source_databases "
                "(source_db_slug, source_database_path, source_schema_hash, "
                "source_schema_class, source_mtime_utc, source_table, "
                "source_row_id, archive_sha256, import_run_id, "
                "adjudication_class, canonical_treatment, imported_at_utc) "
                "VALUES ('x','x','x','modern','x','x','x','x','x','x','x','x');"
            )
    finally:
        conn.close()


def test_connect_ro_raises_file_not_found(tmp_path: Path) -> None:
    """_connect_ro raises FileNotFoundError when the path does not exist."""
    with pytest.raises(FileNotFoundError):
        _connect_ro(tmp_path / "no_such_file.sqlite")


def test_read_view_handles_uri_metacharacters(canonical_db: Path, tmp_path: Path) -> None:
    """A --db path containing '?' / '#' must open the real file read-only.

    Without percent-encoding, SQLite would parse '?'/'#' as query/fragment and
    could open a truncated path read-write instead of the requested store.
    """
    weird_dir = tmp_path / "weird # dir ? x"
    weird_dir.mkdir()
    weird_path = weird_dir / "store #1 ? v.sqlite"
    weird_path.write_bytes(canonical_db.read_bytes())

    # The correct (non-truncated) store opens and yields its real contents.
    view = read_canonical_view(weird_path)
    assert view["item_count"] == 1
    assert view["items"][0]["source_db_slug"] == _KNOWN_SLUG

    # ...and it is still strictly read-only.
    conn = _connect_ro(weird_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO source_databases (source_db_slug) VALUES ('x');"
            )
    finally:
        conn.close()


def test_module_docstring_documents_iso8601_valid_as_of() -> None:
    """valid_as_of lexicographic MAX assumption is documented for operators."""
    import dopemux.orchestrator.canonical_readview as module

    doc = module.read_canonical_view.__doc__ or ""
    assert "ISO-8601" in doc
    assert "import_pack" in doc


def test_inspect_limit_truncates_items_but_not_count(
    canonical_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--limit caps returned items while item_count stays the store total."""
    import json

    monkeypatch.setenv("CANONICAL_STORE_READ_VIEW_ENABLED", "true")
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        [
            "canonical-store",
            "inspect",
            "--db",
            str(canonical_db),
            "--limit",
            "0",
            "--json-output",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["item_count"] == 1
    assert payload["items"] == []


def test_inspect_surfaces_sqlite_database_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Corrupt SQLite files surface a specific sqlite error message."""
    monkeypatch.setenv("CANONICAL_STORE_READ_VIEW_ENABLED", "true")
    corrupt = tmp_path / "corrupt.sqlite"
    corrupt.write_bytes(b"not-a-sqlite-database")
    runner = CliRunner()
    result = runner.invoke(
        orchestrator_group,
        ["canonical-store", "inspect", "--db", str(corrupt)],
    )
    assert result.exit_code != 0
    output = (result.output or "") + str(result.exception or "")
    assert "sqlite error reading canonical store" in output.lower()
