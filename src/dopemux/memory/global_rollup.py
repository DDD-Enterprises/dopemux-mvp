"""Read-only global rollup index over per-project chronicle ledgers."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .capture_client import CaptureError, resolve_repo_root_strict

DEFAULT_GLOBAL_INDEX_PATH = Path.home() / ".dopemux" / "global_index.sqlite"
SUMMARY_MAX_CHARS = 500


class GlobalRollupError(RuntimeError):
    """Raised when global rollup cannot proceed safely."""


@dataclass(frozen=True)
class ProjectPointer:
    """Pointer record materialized into the global rollup index."""

    project_id: str
    event_id: str
    ts_utc: str
    event_type: str
    summary: str
    importance_score: Optional[int]
    entry_type: Optional[str]
    category: Optional[str]
    instance_id: Optional[str]



def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def _schema_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
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



def _normalize_repo_root(path: Path) -> Path:
    return path.expanduser().resolve()



def _chronicle_path_for_repo_root(repo_root: Path) -> Path:
    return (_normalize_repo_root(repo_root) / ".dopemux" / "chronicle.sqlite").resolve()



def _infer_repo_root_from_chronicle_path(chronicle_path: Path) -> Path:
    resolved = chronicle_path.expanduser().resolve()
    if resolved.name != "chronicle.sqlite":
        raise GlobalRollupError(f"Expected chronicle.sqlite file path, got: {chronicle_path}")
    if resolved.parent.name == ".dopemux":
        return resolved.parent.parent
    return resolved.parent



def _load_projects_from_file(projects_file: Path) -> list[Path]:
    path = projects_file.expanduser().resolve()
    if not path.exists():
        raise GlobalRollupError(f"Projects file does not exist: {path}")

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    roots: list[Path] = []

    # Accept JSON list of strings or objects, otherwise newline-delimited paths.
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, str):
                candidate = Path(item)
                if not candidate.is_absolute():
                    candidate = (path.parent / candidate).resolve()
                if candidate.name == "chronicle.sqlite":
                    roots.append(_infer_repo_root_from_chronicle_path(candidate))
                else:
                    roots.append(_normalize_repo_root(candidate))
                continue
            if isinstance(item, dict):
                if "repo_root" in item and isinstance(item["repo_root"], str):
                    candidate = Path(item["repo_root"])
                    if not candidate.is_absolute():
                        candidate = (path.parent / candidate).resolve()
                    roots.append(_normalize_repo_root(candidate))
                    continue
                if "chronicle_path" in item and isinstance(item["chronicle_path"], str):
                    candidate = Path(item["chronicle_path"])
                    if not candidate.is_absolute():
                        candidate = (path.parent / candidate).resolve()
                    roots.append(_infer_repo_root_from_chronicle_path(candidate))
                    continue
                raise GlobalRollupError(
                    "Projects JSON item must include 'repo_root' or 'chronicle_path'"
                )
            raise GlobalRollupError("Projects JSON list must contain strings or objects")
        return roots

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        candidate = Path(stripped)
        if not candidate.is_absolute():
            candidate = (path.parent / candidate).resolve()
        if candidate.name == "chronicle.sqlite":
            roots.append(_infer_repo_root_from_chronicle_path(candidate))
        else:
            roots.append(_normalize_repo_root(candidate))

    return roots



def resolve_rollup_projects(projects_file: Optional[Path] = None) -> list[Path]:
    """Resolve project roots for rollup build in deterministic order."""
    roots: list[Path] = []

    if projects_file:
        roots.extend(_load_projects_from_file(projects_file))

    env_list = os.getenv("DOPEMUX_ROLLUP_PROJECTS", "").strip()
    if env_list:
        for raw in env_list.split(","):
            token = raw.strip()
            if not token:
                continue
            candidate = Path(token)
            if candidate.name == "chronicle.sqlite":
                roots.append(_infer_repo_root_from_chronicle_path(candidate))
            else:
                roots.append(_normalize_repo_root(candidate))

    if not roots:
        try:
            roots.append(resolve_repo_root_strict())
        except CaptureError as exc:
            raise GlobalRollupError(
                "No projects provided and current directory is not inside a repo"
            ) from exc

    deduped: list[Path] = []
    seen: set[str] = set()
    for root in sorted(_normalize_repo_root(r) for r in roots):
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(root)

    return deduped


class GlobalRollupIndexer:
    """Builds and queries the global rollup index from project ledgers."""

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = (index_path or DEFAULT_GLOBAL_INDEX_PATH).expanduser().resolve()

    def _connect_index(self) -> sqlite3.Connection:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.index_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _connect_project_read_only(chronicle_path: Path) -> sqlite3.Connection:
        uri = f"file:{chronicle_path.resolve()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self) -> None:
        with self._connect_index() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                  project_id TEXT PRIMARY KEY,
                  repo_root TEXT NOT NULL UNIQUE,
                  chronicle_path TEXT NOT NULL,
                  last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS promoted_pointers (
                  project_id TEXT NOT NULL,
                  event_id TEXT NOT NULL,
                  ts_utc TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  summary TEXT NOT NULL,
                  importance_score INTEGER,
                  entry_type TEXT,
                  category TEXT,
                  instance_id TEXT,
                  created_at_utc TEXT NOT NULL,
                  PRIMARY KEY (project_id, event_id),
                  FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_rollup_pointers_ts
                  ON promoted_pointers(ts_utc DESC, event_id ASC);

                CREATE INDEX IF NOT EXISTS idx_rollup_pointers_event_type
                  ON promoted_pointers(event_type);

                CREATE INDEX IF NOT EXISTS idx_rollup_pointers_summary
                  ON promoted_pointers(summary);
                """
            )
            conn.commit()

    def _load_project_pointers(self, project_id: str, chronicle_path: Path) -> list[ProjectPointer]:
        if not chronicle_path.exists():
            return []

        with self._connect_project_read_only(chronicle_path) as conn:
            if not _schema_table_exists(conn, "work_log_entries"):
                return []

            rows = conn.execute(
                """
                SELECT
                  id,
                  ts_utc,
                  entry_type,
                  category,
                  summary,
                  importance_score,
                  instance_id,
                  created_at_utc
                FROM work_log_entries
                ORDER BY ts_utc DESC, id ASC
                """
            ).fetchall()

        pointers: list[ProjectPointer] = []
        for row in rows:
            summary = (row["summary"] or "").strip()
            if len(summary) > SUMMARY_MAX_CHARS:
                summary = summary[:SUMMARY_MAX_CHARS]

            entry_type = row["entry_type"]
            pointers.append(
                ProjectPointer(
                    project_id=project_id,
                    event_id=row["id"],
                    ts_utc=row["ts_utc"],
                    event_type=entry_type or "work_log",
                    summary=summary,
                    importance_score=row["importance_score"],
                    entry_type=entry_type,
                    category=row["category"],
                    instance_id=row["instance_id"],
                )
            )

        return pointers

    def build(self, project_roots: Iterable[Path]) -> dict[str, object]:
        self.initialize_schema()

        roots = [_normalize_repo_root(root) for root in project_roots]
        if not roots:
            raise GlobalRollupError("No project roots provided for rollup build")

        now = _now_utc_iso()
        total_upserted = 0
        per_project: list[dict[str, object]] = []

        with self._connect_index() as conn:
            for repo_root in sorted(roots):
                project_id = str(repo_root)
                chronicle_path = _chronicle_path_for_repo_root(repo_root)

                conn.execute(
                    """
                    INSERT INTO projects (project_id, repo_root, chronicle_path, last_seen_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(project_id) DO UPDATE SET
                      repo_root = excluded.repo_root,
                      chronicle_path = excluded.chronicle_path,
                      last_seen_at = excluded.last_seen_at
                    """,
                    (project_id, str(repo_root), str(chronicle_path), now),
                )

                pointers = self._load_project_pointers(project_id, chronicle_path)
                upserted = 0
                for pointer in pointers:
                    conn.execute(
                        """
                        INSERT INTO promoted_pointers (
                          project_id, event_id, ts_utc, event_type, summary,
                          importance_score, entry_type, category, instance_id, created_at_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(project_id, event_id) DO UPDATE SET
                          ts_utc = excluded.ts_utc,
                          event_type = excluded.event_type,
                          summary = excluded.summary,
                          importance_score = excluded.importance_score,
                          entry_type = excluded.entry_type,
                          category = excluded.category,
                          instance_id = excluded.instance_id,
                          created_at_utc = excluded.created_at_utc
                        """,
                        (
                            pointer.project_id,
                            pointer.event_id,
                            pointer.ts_utc,
                            pointer.event_type,
                            pointer.summary,
                            pointer.importance_score,
                            pointer.entry_type,
                            pointer.category,
                            pointer.instance_id,
                            now,
                        ),
                    )
                    upserted += 1

                total_upserted += upserted
                per_project.append(
                    {
                        "project_id": project_id,
                        "repo_root": str(repo_root),
                        "chronicle_path": str(chronicle_path),
                        "pointers_upserted": upserted,
                    }
                )

            conn.commit()

        return {
            "index_path": str(self.index_path),
            "projects_registered": len(per_project),
            "pointers_upserted": total_upserted,
            "projects": per_project,
        }

    def list_projects(self) -> list[dict[str, str]]:
        self.initialize_schema()
        with self._connect_index() as conn:
            rows = conn.execute(
                """
                SELECT project_id, repo_root, chronicle_path, last_seen_at
                FROM projects
                ORDER BY last_seen_at DESC, project_id ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, object]]:
        self.initialize_schema()
        bounded_limit = min(max(1, limit), 100)
        query_text = query.strip()

        with self._connect_index() as conn:
            if query_text:
                pattern = f"%{query_text}%"
                rows = conn.execute(
                    """
                    SELECT
                      project_id,
                      event_id,
                      ts_utc,
                      event_type,
                      summary,
                      importance_score,
                      entry_type,
                      category,
                      instance_id
                    FROM promoted_pointers
                    WHERE summary LIKE ?
                       OR event_type LIKE ?
                       OR category LIKE ?
                       OR entry_type LIKE ?
                    ORDER BY ts_utc DESC, event_id ASC
                    LIMIT ?
                    """,
                    (pattern, pattern, pattern, pattern, bounded_limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT
                      project_id,
                      event_id,
                      ts_utc,
                      event_type,
                      summary,
                      importance_score,
                      entry_type,
                      category,
                      instance_id
                    FROM promoted_pointers
                    ORDER BY ts_utc DESC, event_id ASC
                    LIMIT ?
                    """,
                    (bounded_limit,),
                ).fetchall()

        return [dict(row) for row in rows]
