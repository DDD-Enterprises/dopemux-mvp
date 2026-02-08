#!/usr/bin/env python3
"""
Backfill ConPort relationships from an import bundle into PostgreSQL.

This script is designed for post-import recovery when context_links were skipped
because legacy ID mappings were unavailable at import time.
"""

import argparse
import asyncio
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

try:
    import asyncpg
except ModuleNotFoundError:  # pragma: no cover - runtime dependency
    asyncpg = None

try:
    from dateutil import parser as dateparser
except ModuleNotFoundError:  # pragma: no cover - fallback parser below
    dateparser = None


def parse_timestamp(value: Optional[str]) -> datetime:
    """Best-effort timestamp parsing with UTC fallback."""
    if not value:
        return datetime.utcnow()
    if dateparser is not None:
        try:
            return dateparser.parse(value)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


def normalize_type(raw: str) -> str:
    """Normalize SQLite type labels to runtime labels."""
    value = (raw or "").strip().lower()
    if value in {"progress_entry", "progress_entries", "progress"}:
        return "progress_entry"
    if value in {"decision", "decisions"}:
        return "decision"
    return value


class RelationshipBackfill:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn: Optional[Any] = None
        self.schema: Optional[str] = None
        self.table_columns: Dict[str, Set[str]] = {}

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg is not installed; cannot run relationship backfill.")
        self.conn = await asyncpg.connect(self.db_url)

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()

    async def detect_schema(self) -> str:
        if self.schema is not None:
            return self.schema
        for candidate in ("ag_catalog", "public"):
            exists = await self.conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = $1
                    AND table_name = 'entity_relationships'
                )
                """,
                candidate,
            )
            if exists:
                self.schema = candidate
                return candidate
        raise RuntimeError("Unable to detect target schema with entity_relationships table.")

    async def table_exists(self, table_name: str) -> bool:
        schema = await self.detect_schema()
        return await self.conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = $1
                AND table_name = $2
            )
            """,
            schema,
            table_name,
        )

    async def load_table_columns(self, table_name: str) -> Set[str]:
        if table_name in self.table_columns:
            return self.table_columns[table_name]
        schema = await self.detect_schema()
        rows = await self.conn.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = $1
            AND table_name = $2
            """,
            schema,
            table_name,
        )
        cols = {row["column_name"] for row in rows}
        self.table_columns[table_name] = cols
        return cols

    def qname(self, table_name: str) -> str:
        if self.schema is None:
            raise RuntimeError("Schema not initialized.")
        return f'"{self.schema}"."{table_name}"'

    async def fetch_lookup_maps(self, workspace_id: str) -> Dict[str, Dict[str, str]]:
        """Build summary/description/key -> UUID lookup maps from existing DB records."""
        decision_rows = await self.conn.fetch(
            f"""
            SELECT id, summary, created_at
            FROM {self.qname('decisions')}
            WHERE workspace_id = $1
            ORDER BY created_at DESC NULLS LAST, id DESC
            """,
            workspace_id,
        )
        progress_rows = await self.conn.fetch(
            f"""
            SELECT id, description, created_at
            FROM {self.qname('progress_entries')}
            WHERE workspace_id = $1
            ORDER BY created_at DESC NULLS LAST, id DESC
            """,
            workspace_id,
        )
        custom_data_rows = await self.conn.fetch(
            f"""
            SELECT id, key, category, updated_at
            FROM {self.qname('custom_data')}
            WHERE workspace_id = $1
            ORDER BY updated_at DESC NULLS LAST, id DESC
            """,
            workspace_id,
        )

        decision_by_summary: Dict[str, str] = {}
        progress_by_description: Dict[str, str] = {}
        custom_data_by_key: Dict[str, str] = {}
        decision_collisions = 0
        progress_collisions = 0
        custom_data_key_collisions = 0

        # Keep first row in DESC created_at order as the current canonical mapping.
        for row in decision_rows:
            summary = (row["summary"] or "").strip()
            if not summary:
                continue
            if summary in decision_by_summary:
                decision_collisions += 1
                continue
            decision_by_summary[summary] = str(row["id"])

        for row in progress_rows:
            description = (row["description"] or "").strip()
            if not description:
                continue
            if description in progress_by_description:
                progress_collisions += 1
                continue
            progress_by_description[description] = str(row["id"])

        for row in custom_data_rows:
            key = (row["key"] or "").strip()
            if not key:
                continue
            if key in custom_data_by_key:
                custom_data_key_collisions += 1
                continue
            custom_data_by_key[key] = str(row["id"])

        return {
            "decision_by_summary": decision_by_summary,
            "progress_by_description": progress_by_description,
            "custom_data_by_key": custom_data_by_key,
            "stats": {
                "decisions_scanned": len(decision_rows),
                "progress_entries_scanned": len(progress_rows),
                "custom_data_scanned": len(custom_data_rows),
                "decision_summary_collisions": decision_collisions,
                "progress_description_collisions": progress_collisions,
                "custom_data_key_collisions": custom_data_key_collisions,
            },
        }

    async def insert_relationship(
        self,
        workspace_id: str,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relationship_type: str,
        created_at: datetime,
    ) -> bool:
        """Insert relationship if not already present. Returns True if inserted."""
        columns = await self.load_table_columns("entity_relationships")
        values_by_column: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relationship_type": relationship_type,
        }
        if "strength" in columns:
            values_by_column["strength"] = 1.0
        if "created_at" in columns:
            values_by_column["created_at"] = created_at

        ordered_columns = [k for k in values_by_column.keys() if k in columns]
        column_sql = ", ".join(f'"{c}"' for c in ordered_columns)
        values = [values_by_column[c] for c in ordered_columns]
        casts = {
            "workspace_id": "text",
            "source_type": "text",
            "source_id": "uuid",
            "target_type": "text",
            "target_id": "uuid",
            "relationship_type": "text",
            "strength": "numeric",
            "created_at": "timestamptz",
        }
        select_exprs = ", ".join(
            f"${i}::{casts.get(col, 'text')}" for i, col in enumerate(ordered_columns, start=1)
        )

        sql = f"""
            INSERT INTO {self.qname('entity_relationships')} ({column_sql})
            SELECT {select_exprs}
            WHERE NOT EXISTS (
                SELECT 1 FROM {self.qname('entity_relationships')}
                WHERE workspace_id::text = $1::text
                  AND source_type::text = $2::text
                  AND source_id = $3::uuid
                  AND target_type::text = $4::text
                  AND target_id = $5::uuid
                  AND relationship_type::text = $6::text
            )
        """
        result = await self.conn.execute(sql, *values)
        # asyncpg execute returns strings like "INSERT 0 1" or "INSERT 0 0"
        return result.endswith("1")

    async def run(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        schema = await self.detect_schema()
        if not await self.table_exists("entity_relationships"):
            raise RuntimeError("entity_relationships table not found.")

        decisions = bundle.get("decisions", [])
        progress_entries = bundle.get("progress_entries", [])
        context_links = bundle.get("context_links", [])
        if not isinstance(context_links, list):
            raise ValueError("Expected 'context_links' to be a list.")

        workspace_id = (
            (decisions[0].get("workspace_id") if decisions else None)
            or (progress_entries[0].get("workspace_id") if progress_entries else None)
            or "/Users/hue/code/dopemux-mvp"
        )

        decision_old_to_summary: Dict[str, str] = {}
        for d in decisions:
            if "id" in d and d.get("summary"):
                decision_old_to_summary[str(d["id"])] = d["summary"].strip()

        progress_old_to_description: Dict[str, str] = {}
        for p in progress_entries:
            if "id" in p and p.get("description"):
                progress_old_to_description[str(p["id"])] = p["description"].strip()

        custom_data_old_to_key: Dict[str, str] = {}
        for c in bundle.get("custom_data", []):
            key = (c.get("key") or "").strip()
            if not key:
                continue
            # Support both legacy numeric IDs and direct key references in links.
            if "id" in c:
                custom_data_old_to_key[str(c["id"])] = key
            custom_data_old_to_key[key] = key

        lookups = await self.fetch_lookup_maps(workspace_id)
        decision_by_summary: Dict[str, str] = lookups["decision_by_summary"]  # type: ignore[assignment]
        progress_by_description: Dict[str, str] = lookups["progress_by_description"]  # type: ignore[assignment]
        custom_data_by_key: Dict[str, str] = lookups["custom_data_by_key"]  # type: ignore[assignment]

        inserted = 0
        deduplicated = 0
        skipped = 0
        skipped_by_reason: Dict[str, int] = defaultdict(int)

        for link in context_links:
            source_type = normalize_type(link.get("source_item_type", ""))
            target_type = normalize_type(link.get("target_item_type", ""))
            source_old_id = link.get("source_item_id")
            target_old_id = link.get("target_item_id")
            relationship_type = link.get("relationship_type") or "relates_to"
            created_at = parse_timestamp(link.get("created_at"))

            def resolve_uuid(item_type: str, old_id: Any) -> Tuple[Optional[str], Optional[str]]:
                if old_id is None:
                    return None, "missing_old_id"
                old_key = str(old_id)
                if item_type == "decision":
                    summary = decision_old_to_summary.get(old_key)
                    if not summary:
                        return None, "missing_bundle_decision"
                    uuid_val = decision_by_summary.get(summary)
                    if not uuid_val:
                        return None, "missing_db_decision"
                    return uuid_val, None
                if item_type == "progress_entry":
                    desc = progress_old_to_description.get(old_key)
                    if not desc:
                        return None, "missing_bundle_progress_entry"
                    uuid_val = progress_by_description.get(desc)
                    if not uuid_val:
                        return None, "missing_db_progress_entry"
                    return uuid_val, None
                if item_type == "custom_data":
                    custom_key = custom_data_old_to_key.get(old_key)
                    if not custom_key:
                        return None, "missing_bundle_custom_data"
                    uuid_val = custom_data_by_key.get(custom_key)
                    if not uuid_val:
                        return None, "missing_db_custom_data"
                    return uuid_val, None
                return None, f"unsupported_type:{item_type}"

            source_uuid, source_reason = resolve_uuid(source_type, source_old_id)
            if source_uuid is None:
                skipped += 1
                skipped_by_reason[f"source:{source_reason}"] += 1
                continue

            target_uuid, target_reason = resolve_uuid(target_type, target_old_id)
            if target_uuid is None:
                skipped += 1
                skipped_by_reason[f"target:{target_reason}"] += 1
                continue

            was_inserted = await self.insert_relationship(
                workspace_id=workspace_id,
                source_type=source_type,
                source_id=source_uuid,
                target_type=target_type,
                target_id=target_uuid,
                relationship_type=relationship_type,
                created_at=created_at,
            )
            if was_inserted:
                inserted += 1
            else:
                deduplicated += 1

        return {
            "schema": schema,
            "workspace_id": workspace_id,
            "context_links_total": len(context_links),
            "resolved_candidates": inserted + deduplicated,
            "inserted": inserted,
            "deduplicated": deduplicated,
            "skipped": skipped,
            "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
            "lookup_stats": lookups["stats"],
        }


async def _main(args: argparse.Namespace) -> int:
    bundle_path: Path = args.json_path
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle not found: {bundle_path}")

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    backfill = RelationshipBackfill(args.db_url)
    await backfill.connect()
    try:
        result = await backfill.run(bundle)
    finally:
        await backfill.close()

    payload = {
        "run_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "bundle_path": str(bundle_path),
        "result": result,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill ConPort entity_relationships from import bundle."
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        required=True,
        help="Path to ConPort import bundle JSON.",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default="postgresql://dopemux_age:dopemux_age_dev_password@localhost:5456/dopemux_knowledge_graph",
        help="PostgreSQL connection URL.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path for run summary.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cli_args = parse_args()
    try:
        raise SystemExit(asyncio.run(_main(cli_args)))
    except Exception as exc:  # pragma: no cover - command-line guard
        logger.error(f"Backfill failed: {exc}")
        raise SystemExit(1)
