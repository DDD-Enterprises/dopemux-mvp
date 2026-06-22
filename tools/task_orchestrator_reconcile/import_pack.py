from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .dedupe import build_collision_report
from .model import (
    ACTIVE_DOPEMUX_DB_SLUG,
    SourceDatabase,
    load_source_databases,
    read_csv_rows,
    sha256_file,
)
from .resolve import (
    build_canonical_datastore_manifest,
    build_resolve_report,
    insert_database_decisions,
    manifest_generated_at_utc,
    materialize_current_work_items,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = (
    REPO_ROOT
    / "services"
    / "task-orchestrator"
    / "app"
    / "storage"
    / "canonical_store_schema.sql"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


def _int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _require_pack(input_dir: Path) -> None:
    required = [
        "DATABASE_INDEX.csv",
        "COMBINED_WORK_ITEMS.csv",
        "COMBINED_ROOT_OVERVIEW.csv",
        "COMBINED_COLDSTART_ITEMS.csv",
        "EXPORT_ERRORS.csv",
    ]
    missing = [name for name in required if not (input_dir / name).is_file()]
    if missing:
        raise ValueError(f"missing required pack file(s): {', '.join(missing)}")
    errors = read_csv_rows(input_dir / "EXPORT_ERRORS.csv")
    if errors:
        raise ValueError("EXPORT_ERRORS.csv contains data rows")


def _verify_redacted_only(input_dir: Path) -> None:
    fts_exports = [
        path
        for path in input_dir.glob("dbs/*/all_tables_safe/*.csv")
        if "fts" in path.name.lower()
    ]
    if fts_exports:
        raise ValueError(f"FTS row exports are not allowed: {fts_exports[0]}")
    for notes_csv in input_dir.glob("dbs/*/all_tables_safe/notes.csv"):
        with notes_csv.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                body = row.get("body") or ""
                if body and not body.startswith("[REDACTED len="):
                    raise ValueError(f"unredacted note body value in {notes_csv}")


def _provenance(source: SourceDatabase, import_run_id: str, archive_sha256: str) -> tuple:
    return (
        source.db_slug,
        source.database_path,
        source.schema_hash,
        source.mtime_utc,
        import_run_id,
        archive_sha256,
    )


def _create_database(output: Path) -> sqlite3.Connection:
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(output)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _insert_sources(
    conn: sqlite3.Connection,
    sources: Iterable[SourceDatabase],
    *,
    import_run_id: str,
    archive_sha256: str,
    imported_at_utc: str,
) -> None:
    for source in sources:
        conn.execute(
            """
            INSERT INTO source_databases (
                source_db_slug, source_database_path, source_schema_hash,
                source_schema_class, source_mtime_utc, source_table, source_row_id,
                archive_sha256, import_run_id, bytes, table_count, work_items_count,
                dependencies_count, notes_count, role_transitions_count, queue_count,
                work_count, review_count, blocked_count, terminal_count,
                adjudication_class, canonical_treatment, imported_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source.db_slug,
                source.database_path,
                source.schema_hash,
                source.schema_class,
                source.mtime_utc,
                "DATABASE_INDEX.csv",
                source.db_slug,
                archive_sha256,
                import_run_id,
                source.bytes,
                source.table_count,
                source.work_items,
                source.dependencies,
                source.notes,
                source.role_transitions,
                source.queue,
                source.work,
                source.review,
                source.blocked,
                source.terminal,
                source.adjudication_class,
                source.canonical_treatment,
                imported_at_utc,
            ),
        )


def _insert_work_items(
    conn: sqlite3.Connection,
    rows: Iterable[dict[str, str]],
    sources: dict[str, SourceDatabase],
    *,
    import_run_id: str,
    archive_sha256: str,
) -> int:
    count = 0
    for row in rows:
        source = sources[row["db_slug"]]
        conn.execute(
            """
            INSERT INTO source_work_items (
                source_db_slug, source_database_path, source_schema_hash,
                source_table, source_row_id, source_mtime_utc, import_run_id,
                archive_sha256, parent_source_row_id, depth, role, status_label,
                priority, complexity, tags, item_type, claimed_by, claim_expires_at,
                created_at, modified_at, role_changed_at, title, summary,
                description_redacted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                *_provenance(source, import_run_id, archive_sha256)[:3],
                "COMBINED_WORK_ITEMS.csv",
                row["id"],
                source.mtime_utc,
                import_run_id,
                archive_sha256,
                _clean(row.get("parent_id")),
                _int_or_none(row.get("depth")) or 0,
                row["role"],
                _clean(row.get("status_label")),
                _clean(row.get("priority")),
                _clean(row.get("complexity")),
                _clean(row.get("tags")),
                _clean(row.get("type")),
                _clean(row.get("claimed_by")),
                _clean(row.get("claim_expires_at")),
                _clean(row.get("created_at")),
                _clean(row.get("modified_at")),
                _clean(row.get("role_changed_at")),
                row["title"],
                _clean(row.get("summary")),
                _clean(row.get("description_redacted")),
            ),
        )
        count += 1
    return count


def _insert_per_db_exports(
    conn: sqlite3.Connection,
    input_dir: Path,
    sources: dict[str, SourceDatabase],
    *,
    import_run_id: str,
    archive_sha256: str,
) -> dict[str, int]:
    counts = Counter()
    for db_slug, source in sources.items():
        db_dir = input_dir / "dbs" / db_slug
        for row in read_csv_rows(db_dir / "core_dependencies.csv"):
            conn.execute(
                """
                INSERT INTO source_dependencies (
                    source_db_slug, source_database_path, source_schema_hash,
                    source_table, source_row_id, source_mtime_utc, import_run_id,
                    archive_sha256, from_source_row_id, from_title, to_source_row_id,
                    to_title, dependency_type, unblock_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.db_slug,
                    source.database_path,
                    source.schema_hash,
                    "core_dependencies.csv",
                    row["id"],
                    source.mtime_utc,
                    import_run_id,
                    archive_sha256,
                    row["from_item_id"],
                    _clean(row.get("from_title")),
                    row["to_item_id"],
                    _clean(row.get("to_title")),
                    _clean(row.get("type")),
                    _clean(row.get("unblock_at")),
                    _clean(row.get("created_at")),
                ),
            )
            counts["dependencies"] += 1
        for row in read_csv_rows(db_dir / "core_notes_index.csv"):
            conn.execute(
                """
                INSERT INTO source_note_indexes (
                    source_db_slug, source_database_path, source_schema_hash,
                    source_table, source_row_id, source_mtime_utc, import_run_id,
                    archive_sha256, item_source_row_id, item_title, note_key,
                    note_role, body_len, body_sha256, actor_id, actor_kind,
                    actor_proof, verification_status, created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.db_slug,
                    source.database_path,
                    source.schema_hash,
                    "core_notes_index.csv",
                    row["id"],
                    source.mtime_utc,
                    import_run_id,
                    archive_sha256,
                    row["item_id"],
                    _clean(row.get("item_title")),
                    row["key"],
                    _clean(row.get("role")),
                    _int_or_none(row.get("body_len")),
                    _clean(row.get("body_sha256")),
                    _clean(row.get("actor_id")),
                    _clean(row.get("actor_kind")),
                    _clean(row.get("actor_proof")),
                    _clean(row.get("verification_status")),
                    _clean(row.get("created_at")),
                    _clean(row.get("modified_at")),
                ),
            )
            counts["note_indexes"] += 1
        for row in read_csv_rows(db_dir / "core_role_transitions.csv"):
            conn.execute(
                """
                INSERT INTO source_role_transitions (
                    source_db_slug, source_database_path, source_schema_hash,
                    source_table, source_row_id, source_mtime_utc, import_run_id,
                    archive_sha256, item_source_row_id, item_title, from_role,
                    to_role, from_status_label, to_status_label, trigger, summary,
                    actor_id, actor_kind, actor_proof, verification_status,
                    transitioned_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.db_slug,
                    source.database_path,
                    source.schema_hash,
                    "core_role_transitions.csv",
                    row["id"],
                    source.mtime_utc,
                    import_run_id,
                    archive_sha256,
                    row["item_id"],
                    _clean(row.get("item_title")),
                    _clean(row.get("from_role")),
                    _clean(row.get("to_role")),
                    _clean(row.get("from_status_label")),
                    _clean(row.get("to_status_label")),
                    _clean(row.get("trigger")),
                    _clean(row.get("summary")),
                    _clean(row.get("actor_id")),
                    _clean(row.get("actor_kind")),
                    _clean(row.get("actor_proof")),
                    _clean(row.get("verification_status")),
                    _clean(row.get("transitioned_at")),
                ),
            )
            counts["role_transitions"] += 1
        for row in read_csv_rows(db_dir / "root_overview.csv"):
            conn.execute(
                """
                INSERT INTO source_root_overviews (
                    source_db_slug, source_database_path, source_schema_hash,
                    source_table, source_row_id, source_mtime_utc, import_run_id,
                    archive_sha256, root_source_row_id, root_role, root_status_label,
                    priority, tags, title, child_queue, child_work, child_review,
                    child_blocked, child_terminal, direct_children
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.db_slug,
                    source.database_path,
                    source.schema_hash,
                    "root_overview.csv",
                    row["root_id"],
                    source.mtime_utc,
                    import_run_id,
                    archive_sha256,
                    row["root_id"],
                    _clean(row.get("root_role")),
                    _clean(row.get("root_status_label")),
                    _clean(row.get("priority")),
                    _clean(row.get("tags")),
                    row["title"],
                    _int_or_none(row.get("child_queue")) or 0,
                    _int_or_none(row.get("child_work")) or 0,
                    _int_or_none(row.get("child_review")) or 0,
                    _int_or_none(row.get("child_blocked")) or 0,
                    _int_or_none(row.get("child_terminal")) or 0,
                    _int_or_none(row.get("direct_children")) or 0,
                ),
            )
            counts["root_overviews"] += 1
    return dict(counts)


def _write_json(path: Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def import_pack(args: argparse.Namespace) -> dict:
    input_dir = args.input.resolve()
    _require_pack(input_dir)
    # Redaction verification is fail-safe by default (opt-out, not opt-in). The
    # legacy --redacted-only flag is still accepted but is no longer required.
    unredacted_opt_out = bool(args.allow_unredacted_safe_pack_input)
    redacted_only = not unredacted_opt_out
    if redacted_only:
        _verify_redacted_only(input_dir)
    else:
        print(
            "WARNING: --allow-unredacted-safe-pack-input set; skipping safe-pack "
            "redaction verification. Note bodies and imported titles/summaries are "
            "NOT checked for redaction.",
            file=sys.stderr,
        )

    if args.archive_sha256:
        archive_sha256 = args.archive_sha256
    elif args.archive:
        archive_sha256 = sha256_file(args.archive)
    else:
        archive_sha256 = "UNKNOWN"
    import_run_id = args.import_run_id or f"to-canon-{uuid.uuid4().hex}"
    imported_at = utc_now()
    sources_list = load_source_databases(input_dir)
    sources = {source.db_slug: source for source in sources_list}
    if ACTIVE_DOPEMUX_DB_SLUG not in sources:
        raise ValueError(f"active dopemux source missing: {ACTIVE_DOPEMUX_DB_SLUG}")

    conn = _create_database(args.output)
    try:
        with conn:
            _insert_sources(
                conn,
                sources_list,
                import_run_id=import_run_id,
                archive_sha256=archive_sha256,
                imported_at_utc=imported_at,
            )
            work_item_count = _insert_work_items(
                conn,
                read_csv_rows(input_dir / "COMBINED_WORK_ITEMS.csv"),
                sources,
                import_run_id=import_run_id,
                archive_sha256=archive_sha256,
            )
            import_counts = _insert_per_db_exports(
                conn,
                input_dir,
                sources,
                import_run_id=import_run_id,
                archive_sha256=archive_sha256,
            )
            import_counts["work_items"] = work_item_count
            current_count = 0
            if args.resolve_current:
                insert_database_decisions(
                    conn,
                    import_run_id=import_run_id,
                    archive_sha256=archive_sha256,
                )
                current_count = materialize_current_work_items(conn)
        report = {
            "import_run_id": import_run_id,
            "archive_sha256": archive_sha256,
            "redacted_only": redacted_only,
            "unredacted_opt_out": unredacted_opt_out,
            "source_databases": len(sources_list),
            "schema_counts": dict(
                Counter(source.schema_class for source in sources_list)
            ),
            "adjudication_counts": dict(
                Counter(source.adjudication_class for source in sources_list)
            ),
            "active_db_slug": ACTIVE_DOPEMUX_DB_SLUG,
            "imported_counts": import_counts,
            "canonical_current_work_items": current_count,
            "output": str(args.output),
        }
        if args.resolve_current:
            resolve_report = build_resolve_report(conn, REPO_ROOT)
            report["resolve"] = resolve_report
            _write_json(args.emit_coldstart, resolve_report["coldstart"])
            _write_json(args.emit_conflicts, build_collision_report(conn))
        if args.emit_manifest:
            manifest = build_canonical_datastore_manifest(
                conn,
                archive_sha256=archive_sha256,
                redacted_only=redacted_only,
                generated_at_utc=manifest_generated_at_utc(conn),
            )
            _write_json(args.emit_manifest, manifest)
        _write_json(args.emit_report, report)
        return report
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a safe Task Orchestrator evidence pack into an offline canonical SQLite store."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--archive-sha256")
    parser.add_argument("--import-run-id")
    parser.add_argument(
        "--redacted-only",
        action="store_true",
        help="(legacy/no-op) safe-pack redaction verification now runs by default",
    )
    parser.add_argument(
        "--allow-unredacted-safe-pack-input",
        action="store_true",
        help="opt out of safe-pack redaction verification (warns loudly, recorded in report)",
    )
    parser.add_argument("--resolve-current", action="store_true")
    parser.add_argument("--emit-report", type=Path)
    parser.add_argument("--emit-coldstart", type=Path)
    parser.add_argument("--emit-conflicts", type=Path)
    parser.add_argument(
        "--emit-manifest",
        type=Path,
        help="emit a canonical-datastore.schema.json-conforming provenance manifest",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = import_pack(args)
    except Exception as exc:
        parser.exit(2, f"ERROR: {exc}\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
