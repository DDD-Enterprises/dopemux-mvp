import sqlite3
from pathlib import Path

import pytest

from dopemux.memory.global_rollup import (
    GlobalRollupError,
    GlobalRollupIndexer,
    resolve_rollup_projects,
)


def _create_project_chronicle(project_root: Path, rows: list[dict]) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)
    chronicle_path = project_root / ".dopemux" / "chronicle.sqlite"
    chronicle_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(chronicle_path))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS work_log_entries (
              id TEXT PRIMARY KEY,
              workspace_id TEXT NOT NULL,
              instance_id TEXT NOT NULL,
              session_id TEXT,
              ts_utc TEXT NOT NULL,
              duration_sec INTEGER,
              category TEXT NOT NULL,
              entry_type TEXT NOT NULL,
              workflow_phase TEXT,
              summary TEXT NOT NULL,
              details_json TEXT,
              reasoning TEXT,
              outcome TEXT NOT NULL,
              importance_score INTEGER NOT NULL,
              tags_json TEXT NOT NULL,
              linked_decisions_json TEXT,
              linked_files_json TEXT,
              linked_commits_json TEXT,
              linked_chat_range_json TEXT,
              parent_entry_id TEXT,
              created_at_utc TEXT NOT NULL,
              updated_at_utc TEXT NOT NULL
            );
            """
        )

        for row in rows:
            conn.execute(
                """
                INSERT INTO work_log_entries (
                  id, workspace_id, instance_id, session_id,
                  ts_utc, duration_sec, category, entry_type,
                  workflow_phase, summary, details_json, reasoning,
                  outcome, importance_score, tags_json,
                  linked_decisions_json, linked_files_json, linked_commits_json,
                  linked_chat_range_json, parent_entry_id,
                  created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row.get("workspace_id", str(project_root)),
                    row.get("instance_id", "A"),
                    row.get("session_id"),
                    row["ts_utc"],
                    row.get("duration_sec"),
                    row.get("category", "implementation"),
                    row.get("entry_type", "resolution"),
                    row.get("workflow_phase"),
                    row["summary"],
                    row.get("details_json"),
                    row.get("reasoning"),
                    row.get("outcome", "success"),
                    row.get("importance_score", 7),
                    row.get("tags_json", "[]"),
                    row.get("linked_decisions_json"),
                    row.get("linked_files_json"),
                    row.get("linked_commits_json"),
                    row.get("linked_chat_range_json"),
                    row.get("parent_entry_id"),
                    row.get("created_at_utc", row["ts_utc"]),
                    row.get("updated_at_utc", row["ts_utc"]),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    return chronicle_path


def _project_schema_tables(chronicle_path: Path) -> set[str]:
    conn = sqlite3.connect(str(chronicle_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def _project_row_count(chronicle_path: Path) -> int:
    conn = sqlite3.connect(str(chronicle_path))
    try:
        return int(conn.execute("SELECT COUNT(*) FROM work_log_entries").fetchone()[0])
    finally:
        conn.close()


def test_rollup_build_registers_project_and_indexes_pointers(tmp_path):
    project_root = tmp_path / "project-a"
    chronicle_path = _create_project_chronicle(
        project_root,
        [
            {
                "id": "e-2",
                "ts_utc": "2026-02-08T18:05:00+00:00",
                "summary": "Fixed flaky memory capture test",
                "entry_type": "resolution",
                "category": "debugging",
            },
            {
                "id": "e-1",
                "ts_utc": "2026-02-08T18:00:00+00:00",
                "summary": "Investigated event dedupe behavior",
                "entry_type": "decision",
                "category": "implementation",
            },
        ],
    )

    before_tables = _project_schema_tables(chronicle_path)
    before_count = _project_row_count(chronicle_path)

    index_path = tmp_path / "global_index.sqlite"
    indexer = GlobalRollupIndexer(index_path=index_path)

    result = indexer.build([project_root])

    assert result["projects_registered"] == 1
    assert result["pointers_upserted"] == 2

    projects = indexer.list_projects()
    assert len(projects) == 1
    assert projects[0]["repo_root"] == str(project_root.resolve())
    assert projects[0]["chronicle_path"] == str((project_root / ".dopemux" / "chronicle.sqlite").resolve())

    rows = indexer.search("memory capture", limit=5)
    assert len(rows) == 1
    assert rows[0]["event_id"] == "e-2"

    after_tables = _project_schema_tables(chronicle_path)
    after_count = _project_row_count(chronicle_path)
    assert before_tables == after_tables
    assert before_count == after_count


def test_rollup_search_uses_deterministic_tie_breaker(tmp_path):
    project_root = tmp_path / "project-b"
    _create_project_chronicle(
        project_root,
        [
            {
                "id": "b-id",
                "ts_utc": "2026-02-08T19:00:00+00:00",
                "summary": "Same timestamp entry b",
                "entry_type": "resolution",
                "category": "debugging",
            },
            {
                "id": "a-id",
                "ts_utc": "2026-02-08T19:00:00+00:00",
                "summary": "Same timestamp entry a",
                "entry_type": "resolution",
                "category": "debugging",
            },
        ],
    )

    indexer = GlobalRollupIndexer(index_path=tmp_path / "global_index.sqlite")
    indexer.build([project_root])

    rows = indexer.search("same timestamp", limit=10)
    assert [row["event_id"] for row in rows] == ["a-id", "b-id"]


def test_resolve_rollup_projects_from_file(tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)

    projects_file = tmp_path / "projects.txt"
    projects_file.write_text(f"{repo_root}\n", encoding="utf-8")

    roots = resolve_rollup_projects(projects_file=projects_file)
    assert roots == [repo_root.resolve()]


def test_resolve_rollup_projects_fails_outside_repo_without_inputs(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)
    monkeypatch.chdir(outside)

    with pytest.raises(GlobalRollupError, match="No projects provided"):
        resolve_rollup_projects(projects_file=None)
