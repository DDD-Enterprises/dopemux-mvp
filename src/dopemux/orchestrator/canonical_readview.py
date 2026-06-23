"""Read-only view over an offline canonical reconciliation SQLite store.

This module opens a caller-supplied SQLite file strictly in read-only mode
(``file:...?mode=ro`` URI) and returns a point-in-time provenance summary.
It is NEVER a canonical authority.  It never touches a live current-tasks.db.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


_EXPECTED_TABLES = frozenset({"source_databases", "canonical_current_work_items"})


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    """Open *db_path* strictly read-only.

    Raises :exc:`FileNotFoundError` if the path does not exist.
    Raises :exc:`sqlite3.OperationalError` for other open failures.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"canonical store not found: {db_path}")
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _verify_canonical_store(conn: sqlite3.Connection, db_path: Path) -> None:
    """Raise :exc:`ValueError` when expected tables are absent."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )
    present = {row[0] for row in cur.fetchall()}
    missing = _EXPECTED_TABLES - present
    if missing:
        raise ValueError(
            f"not a canonical reconciliation store: {db_path} "
            f"(missing tables: {', '.join(sorted(missing))})"
        )


def read_canonical_view(
    db_path: Path,
    *,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a read-only point-in-time summary of the canonical reconciliation store.

    The returned dict has the following keys:

    - ``valid_as_of``    – ``MAX(source_mtime_utc)`` from ``source_databases``
    - ``source_db_count`` – number of source databases recorded
    - ``item_count``     – total canonical work items
    - ``items``          – list of provenance-tagged item dicts

    Each item dict contains: ``canonical_identity``, ``role``, ``status_label``,
    ``title``, ``import_run_id``, ``archive_sha256``, ``source_mtime_utc``,
    ``source_db_slug``, ``source_row_id``.  ``summary`` / note bodies are
    intentionally excluded.

    Args:
        db_path: Path to the offline canonical reconciliation SQLite file.
        limit:   Optional cap on the number of items returned (``ORDER BY
                 canonical_identity``).

    Raises:
        FileNotFoundError: ``db_path`` does not exist.
        ValueError: The file exists but is not a canonical reconciliation store.
        sqlite3.OperationalError: Any other SQLite error.
    """
    conn = _connect_ro(db_path)
    try:
        _verify_canonical_store(conn, db_path)

        # Point-in-time anchor — deterministic, matches the import manifest.
        valid_as_of: Optional[str] = conn.execute(
            "SELECT MAX(source_mtime_utc) FROM source_databases;"
        ).fetchone()[0]

        source_db_count: int = conn.execute(
            "SELECT COUNT(*) FROM source_databases;"
        ).fetchone()[0]

        item_count: int = conn.execute(
            "SELECT COUNT(*) FROM canonical_current_work_items;"
        ).fetchone()[0]

        query = """
            SELECT
                canonical_identity,
                role,
                status_label,
                title,
                import_run_id,
                archive_sha256,
                source_mtime_utc,
                source_db_slug,
                source_row_id
            FROM canonical_current_work_items
            ORDER BY canonical_identity
        """
        if limit is not None:
            query += f" LIMIT {int(limit)}"

        rows = conn.execute(query).fetchall()
        items: List[Dict[str, Any]] = [dict(row) for row in rows]
    finally:
        conn.close()

    return {
        "valid_as_of": valid_as_of,
        "source_db_count": source_db_count,
        "item_count": item_count,
        "items": items,
    }
