#!/usr/bin/env python3
"""
Import ConPort data from JSON export to PostgreSQL AGE.

Handles:
- ID mapping (SQLite integers → PostgreSQL UUIDs)
- Schema differences
- Relationship preservation
- Data validation
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

try:
    import asyncpg
except ModuleNotFoundError:  # pragma: no cover - optional in dry-run mode
    asyncpg = None
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import sys
from datetime import datetime
import uuid
try:
    from dateutil import parser as dateparser
except ModuleNotFoundError:  # pragma: no cover - fallback parser below
    dateparser = None


# Schema mapping for decisions
DECISION_MAPPING = {
    # SQLite → PostgreSQL column mapping
    'id': lambda x: str(uuid.uuid4()),  # Generate new UUID
    'workspace_id': lambda x: x,
    'summary': lambda x: x,
    'rationale': lambda x: x or '',
    'implementation_details': lambda x: x,  # Map to alternatives as JSON
    'tags': lambda x: x if isinstance(x, list) else [],
    'created_at': lambda x: x,
    'updated_at': lambda x: x
}


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


class ConPortMigration:
    """PostgreSQL AGE migration handler"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn: Optional[Any] = None
        self.id_mapping: Dict[int, str] = {}  # SQLite ID → PostgreSQL UUID
        self.schema: Optional[str] = None
        self.table_columns: Dict[str, Set[str]] = {}

    async def connect(self):
        """Connect to PostgreSQL"""
        if asyncpg is None:
            raise RuntimeError(
                "asyncpg is not installed. Install migration dependencies before non-dry-run import."
            )
        logger.info("🔌 Connecting to PostgreSQL AGE...")
        self.conn = await asyncpg.connect(self.db_url)
        logger.info("   ✅ Connected")

    async def close(self):
        """Close connection"""
        if self.conn:
            await self.conn.close()

    async def detect_schema(self) -> str:
        """Detect ConPort target schema."""
        if self.schema is not None:
            return self.schema
        for candidate in ("ag_catalog", "public"):
            exists = await self.conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = $1
                    AND table_name = 'decisions'
                )
                """,
                candidate,
            )
            if exists:
                self.schema = candidate
                return candidate
        raise RuntimeError("Unable to detect ConPort schema (expected ag_catalog or public)")

    async def table_exists(self, table_name: str) -> bool:
        """Check table existence in active schema."""
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
        """Load and cache table columns from active schema."""
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
        columns = {row["column_name"] for row in rows}
        self.table_columns[table_name] = columns
        return columns

    async def has_column(self, table_name: str, column_name: str) -> bool:
        """Check whether a column exists in a table."""
        return column_name in await self.load_table_columns(table_name)

    def qname(self, table_name: str) -> str:
        """Qualified table name for active schema."""
        if self.schema is None:
            raise RuntimeError("Schema not initialized. Call detect_schema() first.")
        return f'"{self.schema}"."{table_name}"'

    async def verify_schema(self) -> bool:
        """Verify required tables exist"""
        logger.info("\n🔍 Verifying schema...")
        schema = await self.detect_schema()
        logger.info(f"   ℹ️  Using schema: {schema}")

        required_tables = [
            "decisions",
            "progress_entries",
            "custom_data",
            "entity_relationships",
            "workspace_contexts",
        ]
        optional_tables = ["workspaces", "system_patterns"]

        for table in required_tables:
            if await self.table_exists(table):
                logger.info(f"   ✅ {table}")
            else:
                logger.info(f"   ❌ {table} - MISSING!")
                return False

        for table in optional_tables:
            if await self.table_exists(table):
                logger.info(f"   ✅ {table}")
            else:
                logger.info(f"   ⚠️  {table} - optional, not present")

        return True

    async def import_decisions(self, decisions: List[Dict[str, Any]]) -> int:
        """Import decisions with ID mapping"""
        logger.info(f"\n📋 Importing {len(decisions)} decisions...")

        imported = 0
        for decision in decisions:
            try:
                old_id = decision['id']
                new_id = str(uuid.uuid4())
                self.id_mapping[old_id] = new_id

                # Map tags
                tags = decision.get('tags', [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except Exception as e:
                        tags = []

                        logger.error(f"Error: {e}")
                # Parse timestamps
                created_at_str = decision.get('timestamp') or decision.get('created_at')
                created_at = parse_timestamp(created_at_str)

                updated_at_str = decision.get('updated_at')
                updated_at = parse_timestamp(updated_at_str)

                # Insert decision
                await self.conn.execute(f"""
                    INSERT INTO {self.qname('decisions')}
                    (id, workspace_id, summary, rationale, alternatives, tags,
                     confidence_level, decision_type, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    new_id,
                    decision.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    decision.get('summary', ''),
                    decision.get('rationale', ''),
                    json.dumps({'implementation_details': decision.get('implementation_details', '')}),
                    tags,
                    decision.get('confidence_level', 'medium'),
                    decision.get('decision_type', 'implementation'),
                    created_at,
                    updated_at
                )

                imported += 1
                if imported % 50 == 0:
                    logger.info(f"   Progress: {imported}/{len(decisions)}")

            except Exception as e:
                logger.error(f"   ⚠️  Failed to import decision {old_id}: {e}")

        logger.info(f"   ✅ Imported {imported}/{len(decisions)} decisions")
        return imported

    async def import_progress_entries(self, entries: List[Dict[str, Any]]) -> int:
        """Import progress entries"""
        logger.info(f"\n📊 Importing {len(entries)} progress entries...")

        table_name = "progress_entries"
        columns = await self.load_table_columns(table_name)
        imported = 0
        for entry in entries:
            try:
                new_id = str(uuid.uuid4())
                old_id = entry.get("id")
                if old_id is not None:
                    self.id_mapping[old_id] = new_id

                # Map tags
                tags = entry.get('tags', [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except Exception as e:
                        tags = []

                        logger.error(f"Error: {e}")
                # Handle parent_id mapping
                parent_id = None
                if entry.get('parent_id'):
                    parent_id = self.id_mapping.get(entry['parent_id'])

                # Map status values (DONE → COMPLETED for PostgreSQL constraint)
                status = entry.get('status', 'TODO')
                if status == 'DONE':
                    status = 'COMPLETED'
                elif status == 'TODO':
                    status = 'PLANNED'  # Match PostgreSQL constraint

                # Parse timestamps
                created_at_str = entry.get('timestamp') or entry.get('created_at')
                created_at = parse_timestamp(created_at_str)

                updated_at_str = entry.get('updated_at')
                updated_at = parse_timestamp(updated_at_str)

                values_by_column: Dict[str, Any] = {
                    "id": new_id,
                    "workspace_id": entry.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    "status": status,
                    "description": entry.get('description', ''),
                }
                if "parent_id" in columns:
                    values_by_column["parent_id"] = parent_id
                if "linked_decision_id" in columns:
                    values_by_column["linked_decision_id"] = (
                        self.id_mapping.get(entry.get('linked_item_id'))
                        if entry.get('linked_item_type') == 'decision'
                        else None
                    )
                if "link_relationship_type" in columns:
                    values_by_column["link_relationship_type"] = entry.get(
                        "link_relationship_type", "relates_to_progress"
                    )
                if "tags" in columns:
                    values_by_column["tags"] = tags
                if "priority" in columns:
                    values_by_column["priority"] = entry.get("priority", "medium")
                if "percentage" in columns:
                    values_by_column["percentage"] = entry.get("percentage", 0)
                if "estimated_hours" in columns:
                    values_by_column["estimated_hours"] = entry.get("estimated_hours")
                if "actual_hours" in columns:
                    values_by_column["actual_hours"] = entry.get("actual_hours")
                if "completed_at" in columns:
                    values_by_column["completed_at"] = (
                        updated_at if status == "COMPLETED" else None
                    )
                if "created_at" in columns:
                    values_by_column["created_at"] = created_at
                if "updated_at" in columns:
                    values_by_column["updated_at"] = updated_at

                present_columns = [name for name in values_by_column if name in columns]
                placeholders = ", ".join(f"${index}" for index in range(1, len(present_columns) + 1))
                column_sql = ", ".join(f'"{name}"' for name in present_columns)
                values = [values_by_column[name] for name in present_columns]
                await self.conn.execute(
                    f"INSERT INTO {self.qname(table_name)} ({column_sql}) VALUES ({placeholders})",
                    *values,
                )

                imported += 1

            except Exception as e:
                logger.error(f"   ⚠️  Failed to import progress entry: {e}")

        logger.info(f"   ✅ Imported {imported}/{len(entries)} progress entries")
        return imported

    async def import_custom_data(self, data_entries: List[Dict[str, Any]]) -> int:
        """Import custom data"""
        logger.info(f"\n💾 Importing {len(data_entries)} custom data entries...")

        imported = 0
        for entry in data_entries:
            try:
                value = entry.get('value', {})
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except Exception as e:
                        pass

                        logger.error(f"Error: {e}")
                # Parse timestamps
                created_at_str = entry.get('created_at')
                created_at = parse_timestamp(created_at_str)

                updated_at_str = entry.get('updated_at')
                updated_at = parse_timestamp(updated_at_str)

                await self.conn.execute(f"""
                    INSERT INTO {self.qname('custom_data')}
                    (workspace_id, category, key, value, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (workspace_id, category, key) DO UPDATE
                    SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
                """,
                    entry.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    entry.get('category', 'unknown'),
                    entry.get('key', 'unknown'),
                    json.dumps(value),
                    created_at,
                    updated_at
                )

                imported += 1

            except Exception as e:
                logger.error(f"   ⚠️  Failed to import custom data: {e}")

        logger.info(f"   ✅ Imported {imported}/{len(data_entries)} custom data entries")
        return imported

    async def import_relationships(self, links: List[Dict[str, Any]]) -> int:
        """Import entity relationships"""
        logger.info(f"\n🔗 Importing {len(links)} relationships...")

        table_name = "entity_relationships"
        columns = await self.load_table_columns(table_name)
        imported = 0
        for link in links:
            try:
                # Map source and target IDs
                source_id = self.id_mapping.get(link.get('source_item_id'))
                target_id = self.id_mapping.get(link.get('target_item_id'))

                if not source_id or not target_id:
                    # Skip silently (expected - relationships reference old IDs)
                    continue

                # Parse timestamp
                created_at_str = link.get('created_at')
                created_at = parse_timestamp(created_at_str)

                values_by_column: Dict[str, Any] = {
                    "workspace_id": link.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    "source_type": link.get('source_item_type', 'decision'),
                    "source_id": source_id,
                    "target_type": link.get('target_item_type', 'decision'),
                    "target_id": target_id,
                    "relationship_type": link.get('relationship_type', 'relates_to'),
                }
                if "strength" in columns:
                    values_by_column["strength"] = link.get("strength", 1.0)
                if "created_at" in columns:
                    values_by_column["created_at"] = created_at

                present_columns = [name for name in values_by_column if name in columns]
                placeholders = ", ".join(f"${index}" for index in range(1, len(present_columns) + 1))
                column_sql = ", ".join(f'"{name}"' for name in present_columns)
                values = [values_by_column[name] for name in present_columns]
                await self.conn.execute(
                    f"INSERT INTO {self.qname(table_name)} ({column_sql}) VALUES ({placeholders})",
                    *values,
                )

                imported += 1

            except Exception as e:
                logger.error(f"   ⚠️  Failed to import relationship: {e}")

        logger.info(f"   ✅ Imported {imported}/{len(links)} relationships")
        return imported

    async def import_system_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """Import system patterns"""
        logger.info(f"\n🧩 Importing {len(patterns)} system patterns...")

        # Check if table exists first
        table_exists = await self.table_exists("system_patterns")

        if not table_exists:
            logger.info("   ⚠️  system_patterns table doesn't exist - skipping")
            return 0

        imported = 0
        for pattern in patterns:
            try:
                new_id = str(uuid.uuid4())

                tags = pattern.get('tags', [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except Exception as e:
                        tags = []

                        logger.error(f"Error: {e}")
                # Parse timestamps
                created_at_str = pattern.get('created_at')
                created_at = parse_timestamp(created_at_str)

                updated_at_str = pattern.get('updated_at')
                updated_at = parse_timestamp(updated_at_str)

                await self.conn.execute(f"""
                    INSERT INTO {self.qname('system_patterns')}
                    (id, workspace_id, name, description, tags, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    new_id,
                    pattern.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    pattern.get('name', 'Unknown Pattern'),
                    pattern.get('description', ''),
                    tags,
                    created_at,
                    updated_at
                )

                imported += 1

            except Exception as e:
                logger.error(f"   ⚠️  Failed to import system pattern: {e}")

        logger.info(f"   ✅ Imported {imported}/{len(patterns)} system patterns")
        return imported

    async def import_contexts(self, active_context: Optional[Dict], product_context: Optional[Dict]) -> int:
        """Import active and product contexts"""
        table_name = "workspace_contexts"
        columns = await self.load_table_columns(table_name)
        imported = 0

        def decode_content(context_obj: Optional[Dict[str, Any]]) -> Dict[str, Any]:
            if not context_obj:
                return {}
            content = context_obj.get("content", {})
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except Exception:
                    return {}
            if isinstance(content, dict):
                return content
            return {}

        # Older public schema stores one row per workspace with no context_type column.
        # Preserve both active/product payloads by storing them in a combined JSON object.
        if "context_type" not in columns and (active_context or product_context):
            logger.info("\n🧠 Importing combined workspace context (single-row schema)...")
            try:
                workspace_id = (
                    (active_context or {}).get("workspace_id")
                    or (product_context or {}).get("workspace_id")
                    or "/Users/hue/code/dopemux-mvp"
                )
                active_created = parse_timestamp((active_context or {}).get("created_at"))
                product_created = parse_timestamp((product_context or {}).get("created_at"))
                active_updated = parse_timestamp((active_context or {}).get("updated_at"))
                product_updated = parse_timestamp((product_context or {}).get("updated_at"))

                values_by_column: Dict[str, Any] = {
                    "workspace_id": workspace_id,
                    "active_context": json.dumps(
                        {
                            "active_context": decode_content(active_context),
                            "product_context": decode_content(product_context),
                        }
                    ),
                }
                if "session_milestone" in columns:
                    values_by_column["session_milestone"] = "combined_context_imported"
                if "last_activity" in columns:
                    values_by_column["last_activity"] = "historical_context_import"
                if "created_at" in columns:
                    values_by_column["created_at"] = min(active_created, product_created)
                if "updated_at" in columns:
                    values_by_column["updated_at"] = max(active_updated, product_updated)

                present_columns = [name for name in values_by_column if name in columns]
                placeholders = ", ".join(
                    f"${index}" for index in range(1, len(present_columns) + 1)
                )
                column_sql = ", ".join(f'"{name}"' for name in present_columns)
                values = [values_by_column[name] for name in present_columns]

                update_columns = [
                    name for name in ("active_context", "updated_at", "session_milestone", "last_activity")
                    if name in present_columns
                ]
                if update_columns:
                    update_sql = ", ".join(
                        f'"{name}" = EXCLUDED."{name}"' for name in update_columns
                    )
                    sql = (
                        f"INSERT INTO {self.qname(table_name)} ({column_sql}) VALUES ({placeholders}) "
                        f'ON CONFLICT ("workspace_id") DO UPDATE SET {update_sql}'
                    )
                else:
                    sql = (
                        f"INSERT INTO {self.qname(table_name)} ({column_sql}) VALUES ({placeholders}) "
                        f'ON CONFLICT ("workspace_id") DO NOTHING'
                    )

                await self.conn.execute(sql, *values)
                logger.info("   ✅ Imported combined workspace context")
                return 1
            except Exception as e:
                logger.error(f"   ⚠️  Failed to import combined workspace context: {e}")
                return 0

        if active_context:
            logger.info("\n🎯 Importing active context...")
            try:
                content = decode_content(active_context)
                # Parse timestamps
                created_at_str = active_context.get('created_at')
                created_at = parse_timestamp(created_at_str)

                updated_at_str = active_context.get('updated_at')
                updated_at = parse_timestamp(updated_at_str)

                values_by_column: Dict[str, Any] = {
                    "workspace_id": active_context.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    "active_context": json.dumps(content),
                }
                if "context_type" in columns:
                    values_by_column["context_type"] = "active"
                if "session_milestone" in columns:
                    values_by_column["session_milestone"] = "active_context_imported"
                if "created_at" in columns:
                    values_by_column["created_at"] = created_at
                if "updated_at" in columns:
                    values_by_column["updated_at"] = updated_at

                present_columns = [name for name in values_by_column if name in columns]
                placeholders = ", ".join(f"${index}" for index in range(1, len(present_columns) + 1))
                column_sql = ", ".join(f'"{name}"' for name in present_columns)
                values = [values_by_column[name] for name in present_columns]
                await self.conn.execute(
                    f"INSERT INTO {self.qname(table_name)} ({column_sql}) VALUES ({placeholders})",
                    *values,
                )
                imported += 1
                logger.info("   ✅ Imported active context")
            except Exception as e:
                logger.error(f"   ⚠️  Failed to import active context: {e}")

        if product_context:
            logger.info("\n📦 Importing product context...")
            try:
                content = decode_content(product_context)
                # Parse timestamps
                created_at_str = product_context.get('created_at')
                created_at = parse_timestamp(created_at_str)

                updated_at_str = product_context.get('updated_at')
                updated_at = parse_timestamp(updated_at_str)

                values_by_column: Dict[str, Any] = {
                    "workspace_id": product_context.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    "active_context": json.dumps(content),
                }
                if "context_type" in columns:
                    values_by_column["context_type"] = "product"
                if "session_milestone" in columns:
                    values_by_column["session_milestone"] = "product_context_imported"
                if "created_at" in columns:
                    values_by_column["created_at"] = created_at
                if "updated_at" in columns:
                    values_by_column["updated_at"] = updated_at

                present_columns = [name for name in values_by_column if name in columns]
                placeholders = ", ".join(f"${index}" for index in range(1, len(present_columns) + 1))
                column_sql = ", ".join(f'"{name}"' for name in present_columns)
                values = [values_by_column[name] for name in present_columns]
                await self.conn.execute(
                    f"INSERT INTO {self.qname(table_name)} ({column_sql}) VALUES ({placeholders})",
                    *values,
                )
                imported += 1
                logger.info("   ✅ Imported product context")
            except Exception as e:
                logger.error(f"   ⚠️  Failed to import product context: {e}")

        return imported


def validate_export_structure(data: Dict[str, Any]) -> Dict[str, int]:
    """
    Validate importer input payload structure without DB access.

    Returns:
        Count summary for each top-level collection.

    Raises:
        ValueError: when required structure is missing.
    """
    required = [
        "decisions",
        "progress_entries",
        "custom_data",
        "context_links",
        "system_patterns",
    ]

    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Missing required top-level keys: {missing}")

    counts: Dict[str, int] = {}
    for key in required:
        value = data.get(key)
        if not isinstance(value, list):
            raise ValueError(f"Expected list for '{key}', got {type(value).__name__}")
        counts[key] = len(value)

    # Optional context objects (allow dict or None)
    for optional_key in ("active_context", "product_context"):
        value = data.get(optional_key)
        if value is not None and not isinstance(value, dict):
            raise ValueError(
                f"Expected dict or null for '{optional_key}', got {type(value).__name__}"
            )
        counts[optional_key] = 1 if isinstance(value, dict) else 0

    return counts


async def run_import(json_path: Path, db_url: str, dry_run: bool = False) -> Dict[str, int]:
    """
    Execute full import from JSON to PostgreSQL.

    Returns:
        Import statistics
    """
    logger.info(f"📂 Reading export from: {json_path}")
    logger.info("=" * 60)

    if not json_path.exists():
        logger.info(f"❌ Export file not found: {json_path}")
        sys.exit(1)

    with open(json_path, 'r') as f:
        data = json.load(f)

    counts = validate_export_structure(data)
    logger.info(f"📊 Export contains:")
    logger.info(f"   - {counts['decisions']} decisions")
    logger.info(f"   - {counts['progress_entries']} progress entries")
    logger.info(f"   - {counts['custom_data']} custom data entries")
    logger.info(f"   - {counts['context_links']} relationships")
    logger.info(f"   - {counts['system_patterns']} system patterns")

    if dry_run:
        logger.info("🔍 Dry-run validation complete (no database writes attempted).")
        return {
            "decisions": counts["decisions"],
            "progress_entries": counts["progress_entries"],
            "custom_data": counts["custom_data"],
            "relationships": counts["context_links"],
            "system_patterns": counts["system_patterns"],
            "contexts": counts["active_context"] + counts["product_context"],
        }

    # Initialize migrator
    migrator = ConPortMigration(db_url)
    await migrator.connect()

    # Verify schema
    if not await migrator.verify_schema():
        logger.error("\n❌ Schema verification failed!")
        logger.info("   Run schema migrations first")
        await migrator.close()
        sys.exit(1)

    # Import data
    stats = {}

    try:
        # Import in dependency order
        stats['decisions'] = await migrator.import_decisions(data.get('decisions', []))
        stats['progress_entries'] = await migrator.import_progress_entries(data.get('progress_entries', []))
        stats['custom_data'] = await migrator.import_custom_data(data.get('custom_data', []))
        stats['relationships'] = await migrator.import_relationships(data.get('context_links', []))
        stats['system_patterns'] = await migrator.import_system_patterns(data.get('system_patterns', []))
        stats['contexts'] = await migrator.import_contexts(
            data.get('active_context'),
            data.get('product_context')
        )

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ IMPORT COMPLETE")
        logger.info("=" * 60)
        total = sum(stats.values())
        for key, value in stats.items():
            logger.info(f"{key:20s}: {value}")
        logger.info(f"{'TOTAL':20s}: {total}")

        return stats

    except Exception as e:
        logger.error(f"\n❌ Import failed: {e}")
        raise
    finally:
        await migrator.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import ConPort JSON to PostgreSQL AGE")
    parser.add_argument(
        "--json-path",
        type=Path,
        default=Path("/Users/hue/code/dopemux-mvp/scripts/migration/conport_export.json"),
        help="Path to JSON export file"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default="postgresql://dopemux_age:dopemux_age_dev_password@localhost:5456/dopemux_knowledge_graph",
        help="PostgreSQL connection URL (ConPort on 5456, DDG on 5455)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, don't import"
    )

    args = parser.parse_args()

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - Validation only")

    try:
        stats = asyncio.run(run_import(args.json_path, args.db_url, dry_run=args.dry_run))
        logger.info(f"\n🎉 Migration successful!")
        logger.info(f"📊 Total items imported: {sum(stats.values())}")
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        sys.exit(1)
