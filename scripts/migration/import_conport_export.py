#!/usr/bin/env python3
"""Import a legacy ConPort SQLite export bundle into a project-walled Postgres DB.

WHY THIS EXISTS
---------------
docs/archive/generated/conport-migration/conport_export.json was exported on
2025-10-25 from /Users/hue/code/dopemux-mvp/context_portal/context.db (a SQLite
store that no longer exists). It holds 294 decisions, 209 progress entries, 111
context links and 3 system patterns spanning 2025-10-05..2025-10-25. Its own
active_context says "Migration scripts complete - ready to migrate ConPort to
PostgreSQL AGE" -- and that migration was never run. The corpus has been sitting
in an archive directory ever since while the live database held 3 decisions.

WHY NOT scripts/deploy/migration/import_to_postgresql_age.py
-----------------------------------------------------------
That script reads exactly this bundle shape and was the obvious thing to reuse,
but it has four defects that matter here:
  1. updated_at falls back to datetime.utcnow() (import time) rather than
     created_at, destroying the timestamps this import exists to preserve.
  2. implementation_details is written to `alternatives`. Wrong semantics --
     alternatives means "roads not taken", not "how it was built". 283 of the
     294 decisions carry this field.
  3. system_patterns is detected and skipped, because no such table exists.
  4. It is not idempotent: every run mints fresh UUIDs and re-inserts everything.
This script fixes all four.

IDEMPOTENCY
-----------
Every source row gets a ledger row in custom_data under category
'_migration_ledger', keyed 'decision:<old_id>', 'progress_entry:<old_id>', etc.
custom_data already has UNIQUE(workspace_id, category, key), so the ledger both
deduplicates and stores the old_id -> new_uuid mapping in value.new_id.

That mapping is also how context_links and progress parent_id are resolved.
Deliberately NOT by content-matching summaries the way
backfill_conport_relationships.py does -- with 294+209 rows, near-duplicate
summaries would silently mis-link. Reading our own ledger is exact.

The ledger's value.raw holds the complete original row, which is where
context_links.description survives (entity_relationships has no description
column, so that field would otherwise be lost).

Usage:
  python scripts/migration/import_conport_export.py \
      --json-path docs/archive/generated/conport-migration/conport_export.json \
      --db-url postgresql://conport_dopemux_mvp:PW@127.0.0.1:5432/conport_dopemux_mvp \
      --workspace-id /Users/hue/code/dopemux-mvp \
      --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import asyncpg

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

LEDGER_CATEGORY = "_migration_ledger"
IMPORT_TAG = "legacy-import:conport-2025-10-25"

# Old SQLite statuses -> the CHECK constraint on progress_entries.status.
# Observed in this bundle: TODO=132, DONE=76, BLOCKED=1.
STATUS_MAP = {
    "TODO": "PLANNED",
    "DONE": "COMPLETED",
    "BLOCKED": "BLOCKED",
    "IN_PROGRESS": "IN_PROGRESS",
    "CANCELLED": "CANCELLED",
}


def parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def as_list(value: Any) -> list[str]:
    """Tags arrive as a real list here, but older exports used a JSON string."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return [str(v) for v in parsed] if isinstance(parsed, list) else [value]
        except json.JSONDecodeError:
            return [value]
    return [str(value)]


def as_jsonb(value: Any) -> str:
    """custom_data.value is jsonb NOT NULL; old rows stored JSON-encoded strings."""
    if isinstance(value, str):
        try:
            return json.dumps(json.loads(value))
        except json.JSONDecodeError:
            return json.dumps(value)
    return json.dumps(value)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_") or "unnamed"


class Importer:
    def __init__(self, conn, workspace_id: str, bundle: dict, dry_run: bool):
        self.conn = conn
        self.ws = workspace_id
        self.bundle = bundle
        self.dry_run = dry_run
        # kind -> {old_id: new_uuid}, populated from the ledger and as we insert.
        self.maps: dict[str, dict[str, str]] = {}
        self.stats: dict[str, dict[str, int]] = {}

    def _bump(self, kind: str, field: str) -> None:
        self.stats.setdefault(kind, {"new": 0, "skip": 0, "unresolved": 0})[field] += 1

    async def load_ledger(self) -> None:
        rows = await self.conn.fetch(
            "SELECT key, value FROM custom_data WHERE workspace_id=$1 AND category=$2",
            self.ws, LEDGER_CATEGORY,
        )
        for row in rows:
            key = row["key"]
            if ":" not in key:
                continue
            kind, old_id = key.split(":", 1)
            payload = row["value"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            new_id = (payload or {}).get("new_id")
            if new_id:
                self.maps.setdefault(kind, {})[old_id] = new_id
        if rows:
            logger.info("📒 Existing ledger rows: %d", len(rows))

    def seen(self, kind: str, old_id: Any) -> str | None:
        return self.maps.get(kind, {}).get(str(old_id))

    async def record(self, kind: str, old_id: Any, new_id: str, raw: dict) -> None:
        """Write the ledger row. Also the dedup key, via UNIQUE(ws, category, key)."""
        self.maps.setdefault(kind, {})[str(old_id)] = new_id
        if self.dry_run:
            return
        await self.conn.execute(
            """
            INSERT INTO custom_data (workspace_id, category, key, value)
            VALUES ($1, $2, $3, $4::jsonb)
            ON CONFLICT (workspace_id, category, key) DO NOTHING
            """,
            self.ws, LEDGER_CATEGORY, f"{kind}:{old_id}",
            json.dumps({
                "new_id": new_id,
                "source_export": "conport_export.json",
                "export_timestamp": self.bundle.get("export_timestamp"),
                "raw": raw,
            }, default=str),
        )

    # -- decisions ---------------------------------------------------------
    async def import_decisions(self) -> None:
        for row in self.bundle.get("decisions", []):
            old_id = row.get("id")
            if self.seen("decision", old_id):
                self._bump("decisions", "skip")
                continue

            created = parse_ts(row.get("timestamp"))
            rationale = row.get("rationale") or ""
            impl = row.get("implementation_details")
            if impl:
                # Folded into rationale, NOT alternatives -- see module docstring.
                rationale = (
                    f"{rationale}\n\n---\nImplementation details (legacy):\n{impl}"
                    if rationale else f"Implementation details (legacy):\n{impl}"
                )

            tags = as_list(row.get("tags")) + [IMPORT_TAG, f"legacy-id:{old_id}"]

            if self.dry_run:
                new_id = f"dry-run-decision-{old_id}"
            else:
                new_id = str(await self.conn.fetchval(
                    """
                    INSERT INTO decisions
                        (workspace_id, summary, rationale, tags, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $5)
                    RETURNING id
                    """,
                    self.ws, row.get("summary") or "(no summary)", rationale, tags, created,
                ))
            await self.record("decision", old_id, new_id, row)
            self._bump("decisions", "new")

    # -- progress ----------------------------------------------------------
    async def import_progress(self) -> None:
        for row in self.bundle.get("progress_entries", []):
            old_id = row.get("id")
            if self.seen("progress_entry", old_id):
                self._bump("progress_entries", "skip")
                continue

            created = parse_ts(row.get("timestamp"))
            raw_status = (row.get("status") or "TODO").upper()
            status = STATUS_MAP.get(raw_status, "PLANNED")

            if self.dry_run:
                new_id = f"dry-run-progress-{old_id}"
            else:
                new_id = str(await self.conn.fetchval(
                    """
                    INSERT INTO progress_entries
                        (workspace_id, description, status, percentage, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $5)
                    RETURNING id
                    """,
                    self.ws, row.get("description") or "(no description)", status,
                    100 if status == "COMPLETED" else 0, created,
                ))
            await self.record("progress_entry", old_id, new_id, row)
            self._bump("progress_entries", "new")

    async def import_parent_links(self) -> None:
        """progress_entries.parent_id has no column in the Postgres schema.

        109 of 209 rows carry one. Rather than drop the hierarchy, each becomes
        an entity_relationships row with relationship_type='parent_of'.
        """
        for row in self.bundle.get("progress_entries", []):
            parent_old = row.get("parent_id")
            if not parent_old:
                continue
            old_id = row.get("id")
            if self.seen("parent_link", old_id):
                self._bump("parent_links", "skip")
                continue

            parent_new = self.seen("progress_entry", parent_old)
            child_new = self.seen("progress_entry", old_id)
            if not parent_new or not child_new:
                self._bump("parent_links", "unresolved")
                continue

            if not self.dry_run:
                await self.conn.execute(
                    """
                    INSERT INTO entity_relationships
                        (workspace_id, source_type, source_id, target_type, target_id,
                         relationship_type, created_at)
                    VALUES ($1,'progress_entry',$2,'progress_entry',$3,'parent_of',$4)
                    """,
                    self.ws, parent_new, child_new, parse_ts(row.get("timestamp")),
                )
            await self.record("parent_link", old_id, child_new, {"parent_id": parent_old})
            self._bump("parent_links", "new")

    # -- context links -----------------------------------------------------
    async def import_context_links(self) -> None:
        kind_for = {
            "decision": "decision",
            "progress_entry": "progress_entry",
            "custom_data": "custom_data",
        }
        for row in self.bundle.get("context_links", []):
            old_id = row.get("id")
            if self.seen("context_link", old_id):
                self._bump("context_links", "skip")
                continue

            s_type = row.get("source_item_type")
            t_type = row.get("target_item_type")
            s_new = self.seen(kind_for.get(s_type, s_type or ""), row.get("source_item_id"))
            t_new = self.seen(kind_for.get(t_type, t_type or ""), row.get("target_item_id"))
            if not s_new or not t_new:
                # Never insert a half-resolved edge. But do not silently drop it
                # either: quarantine the full original row in the ledger so its
                # description and endpoints stay auditable.
                #
                # Known case in this bundle: link 33 targets
                # custom_data 'python-tmux-research', a row that was never
                # included in the export. The reference dangles in the SOURCE
                # data; it is not an import failure.
                # Sentinel rather than "" so load_ledger() rehydrates it and a
                # re-run recognises the row as already handled.
                if not self.seen("unresolved_link", old_id):
                    await self.record("unresolved_link", old_id, "unresolved", {
                        "reason": "endpoint not present in export bundle",
                        "source_resolved": bool(s_new),
                        "target_resolved": bool(t_new),
                        "link": row,
                    })
                self._bump("context_links", "unresolved")
                continue

            if not self.dry_run:
                await self.conn.execute(
                    """
                    INSERT INTO entity_relationships
                        (workspace_id, source_type, source_id, target_type, target_id,
                         relationship_type, created_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    """,
                    self.ws, s_type, s_new, t_type, t_new,
                    row.get("relationship_type") or "relates_to",
                    parse_ts(row.get("timestamp")),
                )
            # value.raw preserves `description`, which entity_relationships cannot hold.
            await self.record("context_link", old_id, t_new, row)
            self._bump("context_links", "new")

    # -- custom data + system patterns + contexts --------------------------
    async def _put_custom(self, kind: str, old_id: Any, category: str, key: str,
                          value: Any, created: datetime | None, raw: dict) -> None:
        if self.seen(kind, old_id):
            self._bump(kind + "s", "skip")
            return
        if self.dry_run:
            await self.record(kind, old_id, f"dry-run-{kind}-{old_id}", raw)
            self._bump(kind + "s", "new")
            return

        # UNIQUE(workspace_id, category, key): the bundle has duplicate keys
        # (session_summary, research_in_progress) under one category.
        new_id = await self.conn.fetchval(
            """
            INSERT INTO custom_data (workspace_id, category, key, value, created_at, updated_at)
            VALUES ($1,$2,$3,$4::jsonb,$5,$5)
            ON CONFLICT (workspace_id, category, key) DO NOTHING
            RETURNING id
            """,
            self.ws, category, key, as_jsonb(value), created,
        )
        if new_id is None:
            new_id = await self.conn.fetchval(
                """
                INSERT INTO custom_data (workspace_id, category, key, value, created_at, updated_at)
                VALUES ($1,$2,$3,$4::jsonb,$5,$5)
                RETURNING id
                """,
                self.ws, category, f"{key}-legacy-{old_id}", as_jsonb(value), created,
            )
        await self.record(kind, old_id, str(new_id), raw)
        self._bump(kind + "s", "new")

    async def import_custom_data(self) -> None:
        for row in self.bundle.get("custom_data", []):
            await self._put_custom(
                "custom_data", row.get("id"), row.get("category") or "uncategorized",
                row.get("key") or f"key-{row.get('id')}", row.get("value"),
                parse_ts(row.get("timestamp")), row,
            )

    async def import_system_patterns(self) -> None:
        """No system_patterns table exists; route to custom_data."""
        for row in self.bundle.get("system_patterns", []):
            await self._put_custom(
                "system_pattern", row.get("id"), "system_pattern",
                f"pattern_{slugify(row.get('name') or row.get('id'))}",
                {
                    "name": row.get("name"),
                    "description": row.get("description"),
                    "tags": as_list(row.get("tags")),
                    "legacy_id": row.get("id"),
                },
                parse_ts(row.get("timestamp")), row,
            )

    async def import_contexts(self) -> None:
        """Archive the 2025-10-24 contexts rather than overwriting live state.

        workspace_contexts already holds a current row for this workspace; the
        bundle's active_context is nine months stale.
        """
        for name in ("active_context", "product_context"):
            payload = self.bundle.get(name)
            if not payload:
                continue
            await self._put_custom(
                "legacy_context", name, "legacy_context_archive",
                f"{name}_2025-10-25", payload.get("content", payload), None, payload,
            )

    async def run(self) -> None:
        await self.load_ledger()
        await self.import_decisions()
        await self.import_progress()
        await self.import_parent_links()
        await self.import_context_links()
        await self.import_custom_data()
        await self.import_system_patterns()
        await self.import_contexts()

    def report(self) -> int:
        logger.info("")
        logger.info("%-22s %8s %8s %12s", "ENTITY", "NEW", "SKIPPED", "UNRESOLVED")
        logger.info("%s", "-" * 54)
        unresolved_total = 0
        for kind, s in sorted(self.stats.items()):
            logger.info("%-22s %8d %8d %12d", kind, s["new"], s["skip"], s["unresolved"])
            unresolved_total += s["unresolved"]
        return unresolved_total


async def main_async(args) -> int:
    bundle = json.loads(Path(args.json_path).read_text())
    logger.info("🚀 ConPort legacy export import")
    logger.info("   source      : %s", args.json_path)
    logger.info("   exported    : %s", bundle.get("export_timestamp"))
    logger.info("   source_db   : %s", bundle.get("source_db"))
    logger.info("   workspace   : %s", args.workspace_id)
    logger.info("   dry run     : %s", args.dry_run)
    for k in ("decisions", "progress_entries", "custom_data", "context_links", "system_patterns"):
        logger.info("   %-15s %d", k, len(bundle.get(k) or []))

    conn = await asyncpg.connect(args.db_url)
    try:
        importer = Importer(conn, args.workspace_id, bundle, args.dry_run)
        if args.dry_run:
            await importer.run()
        else:
            # One transaction: a partial import is worse than none.
            async with conn.transaction():
                await importer.run()
        unresolved = importer.report()
    finally:
        await conn.close()

    if unresolved:
        logger.warning("")
        logger.warning("⚠️  %d relationship rows could not be resolved to both endpoints "
                       "and were skipped (not inserted half-formed).", unresolved)
    logger.info("")
    logger.info("✅ %s", "Dry run complete - nothing written" if args.dry_run else "Import complete")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json-path", required=True)
    p.add_argument("--db-url", required=True)
    p.add_argument("--workspace-id", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
