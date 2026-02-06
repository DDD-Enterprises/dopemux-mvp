#!/usr/bin/env python3
"""
Export ConPort SQLite databases into structured JSONL snapshots.

Default behavior:
- Scans known local ConPort SQLite locations inside this repo
- Exports all non-FTS tables
- Writes outputs under reports/conport_sqlite_exports/<timestamp>/
- Emits a manifest with row counts and output file hashes
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_CANDIDATES = [
    REPO_ROOT / "context_portal" / "context.db",
    REPO_ROOT / ".dopemux" / "context.db",
]
DEFAULT_OUTPUT_BASE = REPO_ROOT / "reports" / "conport_sqlite_exports"


@dataclass
class TableExportResult:
    table: str
    row_count: int
    output_file: Path
    sha256: str


def now_utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sanitize_db_label(db_path: Path) -> str:
    rel = db_path.resolve().relative_to(REPO_ROOT.resolve())
    return rel.as_posix().replace("/", "__").replace(".", "_")


def is_fts_shadow_table(table_name: str) -> bool:
    # FTS virtual tables and backing shadow tables frequently contain generated
    # structures that are not ideal for payload exports and can fail normal SELECTs.
    markers = [
        "_fts",
        "_fts_data",
        "_fts_idx",
        "_fts_docsize",
        "_fts_config",
    ]
    name = table_name.lower()
    return any(marker in name for marker in markers)


def looks_like_json(value: str) -> bool:
    value = value.strip()
    return bool(value) and value[0] in ("{", "[")


def normalize_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"_type": "bytes", "base64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, str) and looks_like_json(value):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_dbs(explicit_paths: list[Path] | None) -> list[Path]:
    if explicit_paths:
        return [p for p in explicit_paths if p.exists()]
    return [p for p in DEFAULT_DB_CANDIDATES if p.exists()]


def list_tables(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name ASC"
    )
    return [row[0] for row in cursor.fetchall()]


def export_table_jsonl(
    conn: sqlite3.Connection, table: str, output_file: Path
) -> TableExportResult:
    cursor = conn.execute(f"SELECT * FROM '{table}'")
    columns = [col[0] for col in cursor.description]

    row_count = 0
    with output_file.open("w", encoding="utf-8") as handle:
        for row in cursor:
            row_count += 1
            normalized = {
                columns[idx]: normalize_value(row[idx]) for idx in range(len(columns))
            }
            handle.write(json.dumps(normalized, ensure_ascii=True) + "\n")

    return TableExportResult(
        table=table,
        row_count=row_count,
        output_file=output_file,
        sha256=hash_file(output_file),
    )


def export_db(
    db_path: Path,
    output_root: Path,
    include_fts: bool,
) -> dict[str, Any]:
    db_label = sanitize_db_label(db_path)
    db_out = output_root / db_label
    db_out.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        tables = list_tables(conn)
        table_results: list[TableExportResult] = []
        skipped: list[str] = []

        for table in tables:
            if not include_fts and is_fts_shadow_table(table):
                skipped.append(table)
                continue

            try:
                result = export_table_jsonl(
                    conn=conn,
                    table=table,
                    output_file=db_out / f"{table}.jsonl",
                )
                table_results.append(result)
            except sqlite3.Error as exc:
                skipped.append(f"{table} (sqlite_error: {exc})")

        return {
            "db_path": str(db_path),
            "db_size_bytes": db_path.stat().st_size,
            "export_dir": str(db_out),
            "tables_exported": len(table_results),
            "tables_skipped": skipped,
            "rows_exported_total": sum(r.row_count for r in table_results),
            "tables": [
                {
                    "name": r.table,
                    "rows": r.row_count,
                    "output_file": str(r.output_file),
                    "sha256": r.sha256,
                }
                for r in table_results
            ],
        }
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export ConPort SQLite DBs into JSONL snapshots."
    )
    parser.add_argument(
        "--db",
        action="append",
        type=Path,
        help="SQLite DB path (can be provided multiple times). Defaults to known ConPort DB paths.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to reports/conport_sqlite_exports/<timestamp>/",
    )
    parser.add_argument(
        "--include-fts",
        action="store_true",
        help="Include FTS shadow/virtual tables in export.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    db_paths = discover_dbs(args.db)
    if not db_paths:
        print("No SQLite databases found to export.")
        return 1

    output_root = (
        args.output_dir
        if args.output_dir
        else DEFAULT_OUTPUT_BASE / now_utc_stamp()
    )
    output_root.mkdir(parents=True, exist_ok=True)

    db_exports = []
    for db_path in db_paths:
        db_exports.append(
            export_db(
                db_path=db_path,
                output_root=output_root,
                include_fts=args.include_fts,
            )
        )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_root": str(output_root),
        "include_fts": bool(args.include_fts),
        "db_count": len(db_exports),
        "rows_exported_total": sum(entry["rows_exported_total"] for entry in db_exports),
        "databases": db_exports,
    }

    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    summary = {
        "output_root": str(output_root),
        "manifest": str(manifest_path),
        "db_count": manifest["db_count"],
        "rows_exported_total": manifest["rows_exported_total"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
