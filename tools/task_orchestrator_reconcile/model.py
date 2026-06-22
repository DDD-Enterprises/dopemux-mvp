from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


ACTIVE_DOPEMUX_DB_SLUG = "dopemux-mvp-2e346e2084bca021"


@dataclass(frozen=True)
class SourceDatabase:
    db_slug: str
    database_path: str
    bytes: int
    mtime_utc: str
    work_items: int
    dependencies: int
    notes: int
    role_transitions: int
    queue: int
    work: int
    review: int
    blocked: int
    terminal: int
    table_count: int
    schema_hash: str
    schema_class: str
    adjudication_class: str
    canonical_treatment: str


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def int_field(row: dict[str, str], key: str) -> int:
    value = row.get(key) or "0"
    return int(float(value))


def schema_class(table_count: int) -> str:
    if table_count >= 25:
        return "modern"
    if table_count == 5:
        return "legacy"
    return "unknown"


def classify_database(db_slug: str, schema_kind: str, work_items: int) -> tuple[str, str]:
    if db_slug == ACTIVE_DOPEMUX_DB_SLUG:
        return (
            "active_current_dopemux",
            "current dopemux workflow-memory source for this pack",
        )
    if schema_kind == "modern" and work_items > 0:
        return (
            "modern_project_with_content",
            "project-specific provenance only; do not collapse into dopemux current state",
        )
    if schema_kind == "modern":
        return (
            "modern_empty_shell",
            "register as source DB with empty current-state import",
        )
    if "recovery" in db_slug and work_items > 0:
        return (
            "legacy_recovery_non_empty",
            "historical recovery provenance only; stage and dedupe before current-state use",
        )
    if schema_kind == "legacy" and work_items == 0:
        return ("legacy_empty_shell", "stale or empty provenance only")
    return (
        "legacy_or_unknown_with_content",
        "UNKNOWN until supervised adjudication; do not promote to current state",
    )


def load_source_databases(input_dir: Path) -> list[SourceDatabase]:
    rows = read_csv_rows(input_dir / "DATABASE_INDEX.csv")
    sources: list[SourceDatabase] = []
    for row in rows:
        db_slug = row["db_slug"]
        table_count = int_field(row, "table_count")
        work_items = int_field(row, "work_items")
        schema_kind = schema_class(table_count)
        adjudication_class, treatment = classify_database(
            db_slug, schema_kind, work_items
        )
        schema_path = input_dir / "dbs" / db_slug / "schema.sql"
        schema_hash = sha256_file(schema_path) if schema_path.exists() else ""
        sources.append(
            SourceDatabase(
                db_slug=db_slug,
                database_path=row["database_path"],
                bytes=int_field(row, "bytes"),
                mtime_utc=row["mtime_utc"],
                work_items=work_items,
                dependencies=int_field(row, "dependencies"),
                notes=int_field(row, "notes"),
                role_transitions=int_field(row, "role_transitions"),
                queue=int_field(row, "queue"),
                work=int_field(row, "work"),
                review=int_field(row, "review"),
                blocked=int_field(row, "blocked"),
                terminal=int_field(row, "terminal"),
                table_count=table_count,
                schema_hash=schema_hash,
                schema_class=schema_kind,
                adjudication_class=adjudication_class,
                canonical_treatment=treatment,
            )
        )
    return sources
