from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = "dopemux-mvp-2e346e2084bca021"
RECOVERY = "dnh_crm__recovery_20260504t060227z-364b7472ece807d7"
CANONICAL_DATASTORE_SCHEMA = (
    ROOT / "schemas" / "task-orchestrator" / "canonical-datastore.schema.json"
)


def _run_import(pack: Path, output: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.task_orchestrator_reconcile.import_pack",
            "--input",
            str(pack),
            "--output",
            str(output),
            *extra,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _unredact_note(pack: Path) -> None:
    notes = pack / "dbs" / ACTIVE / "all_tables_safe" / "notes.csv"
    text = notes.read_text(encoding="utf-8")
    notes.write_text(text.replace("[REDACTED len=", "raw note ", 1), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "pack"
    active_dir = pack / "dbs" / ACTIVE
    recovery_dir = pack / "dbs" / RECOVERY
    active_dir.mkdir(parents=True)
    recovery_dir.mkdir(parents=True)
    (active_dir / "schema.sql").write_text("CREATE TABLE work_items(id TEXT);\n")
    (recovery_dir / "schema.sql").write_text("CREATE TABLE work_items(id TEXT);\n")

    index_fields = [
        "db_slug",
        "database_path",
        "bytes",
        "mtime_utc",
        "work_items",
        "dependencies",
        "notes",
        "role_transitions",
        "queue",
        "work",
        "review",
        "blocked",
        "terminal",
        "table_count",
    ]
    _write_csv(
        pack / "DATABASE_INDEX.csv",
        index_fields,
        [
            {
                "db_slug": ACTIVE,
                "database_path": f"/tmp/{ACTIVE}/current-tasks.db",
                "bytes": 1,
                "mtime_utc": "2026-06-22T00:00:00Z",
                "work_items": 4,
                "dependencies": 1,
                "notes": 1,
                "role_transitions": 1,
                "queue": 1,
                "work": 1,
                "review": 0,
                "blocked": 1,
                "terminal": 1,
                "table_count": 25,
            },
            {
                "db_slug": RECOVERY,
                "database_path": f"/tmp/{RECOVERY}/current-tasks.db",
                "bytes": 1,
                "mtime_utc": "2026-05-01T00:00:00Z",
                "work_items": 1,
                "dependencies": 0,
                "notes": 1,
                "role_transitions": 0,
                "queue": 1,
                "work": 0,
                "review": 0,
                "blocked": 0,
                "terminal": 0,
                "table_count": 5,
            },
        ],
    )

    work_fields = [
        "db_slug",
        "id",
        "parent_id",
        "depth",
        "role",
        "status_label",
        "priority",
        "complexity",
        "tags",
        "type",
        "claimed_by",
        "claim_expires_at",
        "created_at",
        "modified_at",
        "role_changed_at",
        "title",
        "summary",
        "description_redacted",
    ]
    work_rows = [
        {
            "db_slug": ACTIVE,
            "id": "root",
            "parent_id": "",
            "depth": 0,
            "role": "work",
            "status_label": "in-progress",
            "priority": "high",
            "complexity": "",
            "tags": "dmx-coldstart",
            "type": "",
            "claimed_by": "",
            "claim_expires_at": "",
            "created_at": "2026-06-22",
            "modified_at": "2026-06-22",
            "role_changed_at": "2026-06-22",
            "title": "DMX-COLDSTART task-packet series",
            "summary": "root",
            "description_redacted": "[REDACTED len=1 sha256=a]",
        },
        {
            "db_slug": ACTIVE,
            "id": "100",
            "parent_id": "root",
            "depth": 1,
            "role": "terminal",
            "status_label": "in-progress",
            "priority": "high",
            "complexity": "",
            "tags": "dmx-coldstart",
            "type": "",
            "claimed_by": "",
            "claim_expires_at": "",
            "created_at": "2026-06-22",
            "modified_at": "2026-06-22",
            "role_changed_at": "2026-06-22",
            "title": "TP-DMX-COLDSTART-L0-DEP-AUDIT-100",
            "summary": "done",
            "description_redacted": "[REDACTED len=1 sha256=b]",
        },
        {
            "db_slug": ACTIVE,
            "id": "102",
            "parent_id": "root",
            "depth": 1,
            "role": "blocked",
            "status_label": "blocked",
            "priority": "medium",
            "complexity": "",
            "tags": "dmx-coldstart",
            "type": "",
            "claimed_by": "",
            "claim_expires_at": "",
            "created_at": "2026-06-22",
            "modified_at": "2026-06-22",
            "role_changed_at": "2026-06-22",
            "title": "TP-DMX-COLDSTART-INIT-UNIFY-102",
            "summary": "blocked",
            "description_redacted": "[REDACTED len=1 sha256=c]",
        },
        {
            "db_slug": ACTIVE,
            "id": "dup-active",
            "parent_id": "",
            "depth": 0,
            "role": "queue",
            "status_label": "",
            "priority": "medium",
            "complexity": "",
            "tags": "",
            "type": "",
            "claimed_by": "",
            "claim_expires_at": "",
            "created_at": "2026-06-22",
            "modified_at": "2026-06-22",
            "role_changed_at": "2026-06-22",
            "title": "Duplicate Lane",
            "summary": "active duplicate",
            "description_redacted": "[REDACTED len=1 sha256=d]",
        },
        {
            "db_slug": RECOVERY,
            "id": "dup-recovery",
            "parent_id": "",
            "depth": 0,
            "role": "queue",
            "status_label": "",
            "priority": "medium",
            "complexity": "",
            "tags": "",
            "type": "",
            "claimed_by": "",
            "claim_expires_at": "",
            "created_at": "2026-05-01",
            "modified_at": "2026-05-01",
            "role_changed_at": "2026-05-01",
            "title": "Duplicate Lane",
            "summary": "recovery duplicate",
            "description_redacted": "[REDACTED len=1 sha256=e]",
        },
    ]
    _write_csv(pack / "COMBINED_WORK_ITEMS.csv", work_fields, work_rows)
    _write_csv(
        pack / "COMBINED_COLDSTART_ITEMS.csv",
        work_fields,
        [row for row in work_rows if "COLDSTART" in str(row["title"])],
    )
    _write_csv(pack / "EXPORT_ERRORS.csv", ["db_slug", "table", "error"], [])

    root_fields = [
        "db_slug",
        "root_id",
        "root_role",
        "root_status_label",
        "priority",
        "tags",
        "title",
        "child_queue",
        "child_work",
        "child_review",
        "child_blocked",
        "child_terminal",
        "direct_children",
    ]
    _write_csv(
        pack / "COMBINED_ROOT_OVERVIEW.csv",
        root_fields,
        [
            {
                "db_slug": ACTIVE,
                "root_id": "root",
                "root_role": "work",
                "root_status_label": "in-progress",
                "priority": "high",
                "tags": "dmx-coldstart",
                "title": "DMX-COLDSTART task-packet series",
                "child_queue": 1,
                "child_work": 0,
                "child_review": 0,
                "child_blocked": 1,
                "child_terminal": 1,
                "direct_children": 3,
            }
        ],
    )

    dep_fields = [
        "id",
        "from_item_id",
        "from_title",
        "to_item_id",
        "to_title",
        "type",
        "unblock_at",
        "created_at",
    ]
    note_fields = [
        "id",
        "item_id",
        "item_title",
        "key",
        "role",
        "body_len",
        "body_sha256",
        "actor_id",
        "actor_kind",
        "actor_proof",
        "verification_status",
        "created_at",
        "modified_at",
    ]
    transition_fields = [
        "id",
        "item_id",
        "item_title",
        "from_role",
        "to_role",
        "from_status_label",
        "to_status_label",
        "trigger",
        "summary",
        "actor_id",
        "actor_kind",
        "actor_proof",
        "verification_status",
        "transitioned_at",
    ]
    for db_dir in [active_dir, recovery_dir]:
        _write_csv(db_dir / "core_dependencies.csv", dep_fields, [])
        _write_csv(
            db_dir / "core_notes_index.csv",
            note_fields,
            [
                {
                    "id": f"{db_dir.name}-note",
                    "item_id": "root",
                    "item_title": "root",
                    "key": "analysis",
                    "role": "work",
                    "body_len": 4,
                    "body_sha256": "abcd",
                    "actor_id": "codex",
                    "actor_kind": "orchestrator",
                    "actor_proof": "",
                    "verification_status": "",
                    "created_at": "2026-06-22",
                    "modified_at": "2026-06-22",
                }
            ],
        )
        _write_csv(db_dir / "core_role_transitions.csv", transition_fields, [])
        _write_csv(
            db_dir / "root_overview.csv",
            root_fields[1:],
            [
                {
                    "root_id": "root",
                    "root_role": "work",
                    "root_status_label": "in-progress",
                    "priority": "high",
                    "tags": "dmx-coldstart",
                    "title": "DMX-COLDSTART task-packet series",
                    "child_queue": 1,
                    "child_work": 0,
                    "child_review": 0,
                    "child_blocked": 1,
                    "child_terminal": 1,
                    "direct_children": 3,
                }
            ],
        )
        _write_csv(
            db_dir / "all_tables_safe" / "notes.csv",
            ["id", "body"],
            [{"id": "note-1", "body": "[REDACTED len=4 sha256=abcd]"}],
        )
    return pack


def test_import_pack_preserves_source_provenance(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)
    output = tmp_path / "canonical.sqlite"
    report = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.task_orchestrator_reconcile.import_pack",
            "--input",
            str(pack),
            "--output",
            str(output),
            "--archive-sha256",
            "archive-test",
            "--redacted-only",
            "--emit-report",
            str(report),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["source_databases"] == 2
    assert payload["imported_counts"]["work_items"] == 5
    assert payload["imported_counts"]["note_indexes"] == 2
    assert payload["canonical_current_work_items"] == 0

    conn = sqlite3.connect(output)
    conn.row_factory = sqlite3.Row
    try:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        row = conn.execute(
            """
            SELECT source_db_slug, source_database_path, source_schema_hash,
                   source_table, source_row_id, archive_sha256
            FROM source_work_items
            LIMIT 1
            """
        ).fetchone()
        assert row["source_db_slug"]
        assert row["source_database_path"].endswith("current-tasks.db")
        assert row["source_schema_hash"]
        assert row["source_table"] == "COMBINED_WORK_ITEMS.csv"
        assert row["source_row_id"]
        assert row["archive_sha256"] == "archive-test"
    finally:
        conn.close()


def test_import_pack_resolve_current_and_coldstart(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)
    output = tmp_path / "canonical.sqlite"
    report = tmp_path / "report.json"
    coldstart = tmp_path / "coldstart.json"
    conflicts = tmp_path / "conflicts.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.task_orchestrator_reconcile.import_pack",
            "--input",
            str(pack),
            "--output",
            str(output),
            "--archive-sha256",
            "archive-test",
            "--redacted-only",
            "--resolve-current",
            "--emit-report",
            str(report),
            "--emit-coldstart",
            str(coldstart),
            "--emit-conflicts",
            str(conflicts),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["canonical_current_work_items"] == 4
    assert payload["resolve"]["database_decisions"] == {
        "promote_to_current": 1,
        "provenance_only": 1,
    }

    cold = json.loads(coldstart.read_text(encoding="utf-8"))
    by_title = {item["title"]: item for item in cold["items"]}
    assert by_title["TP-DMX-COLDSTART-L0-DEP-AUDIT-100"]["decision"] == (
        "accepted_do_not_rerun"
    )
    assert by_title["TP-DMX-COLDSTART-INIT-UNIFY-102"]["decision"] == (
        "keep_blocked_until_repo_packet_allowlist_exists"
    )
    assert by_title["DMX-COLDSTART task-packet series"]["decision"] == (
        "remain_active_in_progress"
    )

    collision = json.loads(conflicts.read_text(encoding="utf-8"))
    assert collision["total"] == 1
    assert collision["duplicate_title_conflicts"][0]["decision"] == (
        "conflict_not_identity"
    )


def test_import_pack_rejects_unredacted_note_body(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)
    notes = pack / "dbs" / ACTIVE / "all_tables_safe" / "notes.csv"
    text = notes.read_text(encoding="utf-8")
    notes.write_text(text.replace("[REDACTED len=", "raw note ", 1), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.task_orchestrator_reconcile.import_pack",
            "--input",
            str(pack),
            "--output",
            str(tmp_path / "canonical.sqlite"),
            "--redacted-only",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unredacted note body value" in result.stderr


def test_import_pack_emits_schema_valid_manifest_when_requested(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)
    output = tmp_path / "canonical.sqlite"
    manifest_path = tmp_path / "manifest.json"

    result = _run_import(
        pack,
        output,
        "--archive-sha256",
        "archive-test",
        "--redacted-only",
        "--resolve-current",
        "--emit-manifest",
        str(manifest_path),
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(CANONICAL_DATASTORE_SCHEMA.read_text(encoding="utf-8"))
    # The emitted manifest must validate against the committed contract.
    Draft202012Validator(schema).validate(manifest)

    assert manifest["schema_version"] == "task-orchestrator.canonical-datastore.v0"
    assert manifest["source_pack"]["archive_sha256"] == "archive-test"
    assert manifest["source_pack"]["redacted_only"] is True
    # generated_at_utc is deterministic (newest source mtime), never wall-clock.
    assert manifest["source_pack"]["generated_at_utc"] == "2026-06-22T00:00:00Z"
    assert len(manifest["source_databases"]) == 2
    entity_types = {e["entity_type"] for e in manifest["imported_entities"]}
    assert entity_types == {"canonical_current_work_item"}
    assert len(manifest["imported_entities"]) == 4


def test_import_pack_redaction_check_is_default_or_requires_explicit_opt_out(
    tmp_path: Path,
) -> None:
    pack = _make_pack(tmp_path)
    _unredact_note(pack)

    # No --redacted-only and no opt-out: verification must still run by default
    # and reject the unredacted note body.
    result = _run_import(pack, tmp_path / "canonical.sqlite")

    assert result.returncode == 2, result.stdout
    assert "unredacted note body value" in result.stderr


def test_import_pack_records_unredacted_opt_out_warning_when_used(
    tmp_path: Path,
) -> None:
    pack = _make_pack(tmp_path)
    _unredact_note(pack)
    report = tmp_path / "report.json"

    result = _run_import(
        pack,
        tmp_path / "canonical.sqlite",
        "--allow-unredacted-safe-pack-input",
        "--emit-report",
        str(report),
    )

    assert result.returncode == 0, result.stderr
    assert "WARNING" in result.stderr
    assert "skipping safe-pack" in result.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["unredacted_opt_out"] is True
    assert payload["redacted_only"] is False


def test_import_pack_uses_pinned_import_run_id_in_reports(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)
    report = tmp_path / "report.json"
    coldstart = tmp_path / "coldstart.json"

    result = _run_import(
        pack,
        tmp_path / "canonical.sqlite",
        "--archive-sha256",
        "archive-test",
        "--import-run-id",
        "to-canon-pinned-001",
        "--redacted-only",
        "--resolve-current",
        "--emit-report",
        str(report),
        "--emit-coldstart",
        str(coldstart),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["import_run_id"] == "to-canon-pinned-001"
    # Re-running with the same pinned id yields the same id (byte-stable evidence).
    rerun = _run_import(
        pack,
        tmp_path / "canonical2.sqlite",
        "--archive-sha256",
        "archive-test",
        "--import-run-id",
        "to-canon-pinned-001",
        "--redacted-only",
        "--resolve-current",
        "--emit-report",
        str(tmp_path / "report2.json"),
    )
    assert rerun.returncode == 0, rerun.stderr
    payload2 = json.loads((tmp_path / "report2.json").read_text(encoding="utf-8"))
    assert payload2["import_run_id"] == "to-canon-pinned-001"

    cold = json.loads(coldstart.read_text(encoding="utf-8"))
    assert cold["schema_version"] == "task-orchestrator.reconciliation-decision.v0"
    assert "point_in_time" in cold
