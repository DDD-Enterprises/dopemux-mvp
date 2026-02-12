"""SQLite chronicle migration applicator.

Applies versioned SQL files from ``chronicle/migrations`` against an existing
SQLite connection. Migrations are idempotent and ordered by semantic version
parsed from migration filenames.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path


SCHEMA_PATH = Path(__file__).parent / "schema.sql"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_FILENAME_VERSION_RE = re.compile(r"^v(\d+)_(\d+)_(\d+)_.*\.sql$")
_APPLIED_VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
_BEGIN_RE = re.compile(r"(?im)^\s*BEGIN(?:\s+TRANSACTION)?\s*;")
_COMMIT_RE = re.compile(r"(?im)^\s*COMMIT\s*;")


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return bool(row)


def _parse_applied_version(version: str) -> tuple[int, int, int] | None:
    match = _APPLIED_VERSION_RE.match(version.strip())
    if not match:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def _migration_entries(migrations_dir: Path) -> list[tuple[tuple[int, int, int], str, Path]]:
    entries: list[tuple[tuple[int, int, int], str, Path]] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        match = _FILENAME_VERSION_RE.match(path.name)
        if not match:
            continue
        major, minor, patch = match.groups()
        version_tuple = (int(major), int(minor), int(patch))
        version_str = f"v{major}.{minor}.{patch}"
        entries.append((version_tuple, version_str, path))
    entries.sort(key=lambda item: item[0])
    return entries


def _script_has_explicit_transaction(script: str) -> bool:
    return bool(_BEGIN_RE.search(script) and _COMMIT_RE.search(script))


def _execute_script_transactional(conn: sqlite3.Connection, script: str) -> None:
    # Some migrations already manage their own transaction boundaries.
    if _script_has_explicit_transaction(script):
        conn.executescript(script)
        return

    wrapped_script = f"BEGIN IMMEDIATE;\n{script.rstrip()}\nCOMMIT;\n"
    conn.executescript(wrapped_script)


def apply_chronicle_migrations(
    conn: sqlite3.Connection,
    *,
    schema_path: Path = SCHEMA_PATH,
    migrations_dir: Path = MIGRATIONS_DIR,
    logger: logging.Logger | None = None,
) -> list[str]:
    """Apply pending chronicle SQLite migrations.

    Returns a list of applied migration filenames in the order executed.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    # Bootstrap schema if this is a blank database.
    if not _table_exists(conn, "schema_migrations"):
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()

    applied_version_rows = conn.execute(
        "SELECT version FROM schema_migrations"
    ).fetchall()
    applied_versions = {str(row[0]) for row in applied_version_rows}
    parsed_applied_versions = [
        parsed
        for parsed in (_parse_applied_version(version) for version in applied_versions)
        if parsed is not None
    ]
    current_max = max(parsed_applied_versions) if parsed_applied_versions else None

    applied_files: list[str] = []
    for version_tuple, version_str, migration_path in _migration_entries(migrations_dir):
        if version_str in applied_versions:
            continue
        if current_max is not None and version_tuple <= current_max:
            # Support bootstrap paths where schema.sql already seeded a newer version.
            continue

        migration_sql = migration_path.read_text(encoding="utf-8")
        try:
            _execute_script_transactional(conn, migration_sql)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise RuntimeError(
                f"Failed applying chronicle migration {migration_path.name}: {exc}"
            ) from exc

        version_row = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ? LIMIT 1",
            (version_str,),
        ).fetchone()
        if not version_row:
            raise RuntimeError(
                f"Migration {migration_path.name} did not record version {version_str}"
            )

        logger.info("APPLIED %s", migration_path.name)
        applied_versions.add(version_str)
        current_max = version_tuple
        applied_files.append(migration_path.name)

    return applied_files
