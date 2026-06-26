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

# Roles considered terminal — excluded from the operator view unless requested.
_TERMINAL_ROLES = frozenset({"done", "cancelled", "archived"})


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    """Open *db_path* strictly read-only.

    Raises :exc:`FileNotFoundError` if the path does not exist.
    Raises :exc:`sqlite3.OperationalError` for other open failures.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"canonical store not found: {db_path}")
    # Build the file: URI from a percent-encoded absolute path so URI
    # metacharacters in db_path (e.g. '?' or '#') cannot be parsed as a
    # query/fragment and silently bypass mode=ro (opening read-write or a
    # truncated path). resolve() is safe — existence is checked above.
    uri = db_path.resolve().as_uri() + "?mode=ro"
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
    role: Optional[str] = None,
    status: Optional[str] = None,
    root: Optional[str] = None,
    include_terminal: bool = True,
) -> Dict[str, Any]:
    """Return a read-only point-in-time summary of the canonical reconciliation store.

    The returned dict has the following keys:

    - ``valid_as_of``    – ``MAX(source_mtime_utc)`` from ``source_databases``.
      This is a lexicographic string MAX and equals the true chronological
      maximum only when every producer mtime is zero-padded ISO-8601 UTC
      (as emitted by ``import_pack``).
    - ``source_db_count`` – number of source databases recorded
    - ``item_count``     – total canonical work items
    - ``items``          – list of provenance-tagged item dicts

    Each item dict contains: ``canonical_identity``, ``role``, ``status_label``,
    ``title``, ``import_run_id``, ``archive_sha256``, ``source_mtime_utc``,
    ``source_db_slug``, ``source_row_id``.  ``summary`` / note bodies are
    intentionally excluded.

    All filter values are applied as parameterised ``?`` placeholders; no filter
    value is ever interpolated into SQL.

    Args:
        db_path:          Path to the offline canonical reconciliation SQLite file.
        limit:            Optional cap on items returned (``ORDER BY canonical_identity``).
        role:             Filter to items with this exact ``role``.
        status:           Filter to items with this exact ``status_label``.
        root:             Filter to items whose ``canonical_identity`` starts with
                          this prefix.
        include_terminal: When False, exclude terminal-role rows
                          (``done``/``cancelled``/``archived``). Default True.

    Raises:
        FileNotFoundError: ``db_path`` does not exist.
        ValueError: The file exists but is not a canonical reconciliation store.
        sqlite3.OperationalError: Any other SQLite error.
    """
    conn = _connect_ro(db_path)
    try:
        _verify_canonical_store(conn, db_path)

        # Point-in-time anchor — lexicographic MAX over ISO-8601 UTC mtimes.
        valid_as_of: Optional[str] = conn.execute(
            "SELECT MAX(source_mtime_utc) FROM source_databases;"
        ).fetchone()[0]

        source_db_count: int = conn.execute(
            "SELECT COUNT(*) FROM source_databases;"
        ).fetchone()[0]

        item_count: int = conn.execute(
            "SELECT COUNT(*) FROM canonical_current_work_items;"
        ).fetchone()[0]

        # Parameterised filters — no filter value is interpolated into SQL.
        conditions: List[str] = []
        params: List[Any] = []
        if not include_terminal:
            placeholders = ",".join("?" for _ in _TERMINAL_ROLES)
            conditions.append(f"role NOT IN ({placeholders})")
            params.extend(sorted(_TERMINAL_ROLES))
        if role is not None:
            conditions.append("role = ?")
            params.append(role)
        if status is not None:
            conditions.append("status_label = ?")
            params.append(status)
        if root is not None:
            conditions.append("canonical_identity LIKE ? ESCAPE '\\'")
            params.append(
                root.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            )
        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        query = f"""
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
            {where_clause}
            ORDER BY canonical_identity
        """
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))

        rows = conn.execute(query, params).fetchall()
        items: List[Dict[str, Any]] = [dict(row) for row in rows]
    finally:
        conn.close()

    return {
        "valid_as_of": valid_as_of,
        "source_db_count": source_db_count,
        "item_count": item_count,
        "items": items,
    }
