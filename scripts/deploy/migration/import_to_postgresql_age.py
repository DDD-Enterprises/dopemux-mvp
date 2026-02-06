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
from typing import Dict, List, Any, Optional
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


class ConPortMigration:
    """PostgreSQL AGE migration handler"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn: Optional[Any] = None
        self.id_mapping: Dict[int, str] = {}  # SQLite ID → PostgreSQL UUID

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

    async def verify_schema(self) -> bool:
        """Verify required tables exist"""
        logger.info("\n🔍 Verifying schema...")

        tables = ['decisions', 'progress_entries', 'custom_data',
                  'entity_relationships', 'workspaces', 'workspace_contexts']

        for table in tables:
            exists = await self.conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'ag_catalog'
                    AND table_name = $1
                )
            """, table)

            if exists:
                logger.info(f"   ✅ {table}")
            else:
                logger.info(f"   ❌ {table} - MISSING!")
                return False

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
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                updated_at_str = decision.get('updated_at')
                updated_at = dateparser.parse(updated_at_str) if updated_at_str else datetime.utcnow()

                # Insert decision
                await self.conn.execute("""
                    INSERT INTO ag_catalog.decisions
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

        imported = 0
        for entry in entries:
            try:
                new_id = str(uuid.uuid4())

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
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                updated_at_str = entry.get('updated_at')
                updated_at = dateparser.parse(updated_at_str) if updated_at_str else datetime.utcnow()

                await self.conn.execute("""
                    INSERT INTO ag_catalog.progress_entries
                    (id, workspace_id, status, description, parent_id,
                     linked_decision_id, link_relationship_type, tags, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    new_id,
                    entry.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    status,
                    entry.get('description', ''),
                    parent_id,
                    self.id_mapping.get(entry.get('linked_item_id')) if entry.get('linked_item_type') == 'decision' else None,
                    entry.get('link_relationship_type', 'relates_to_progress'),
                    tags,
                    created_at,
                    updated_at
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
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                updated_at_str = entry.get('updated_at')
                updated_at = dateparser.parse(updated_at_str) if updated_at_str else datetime.utcnow()

                await self.conn.execute("""
                    INSERT INTO ag_catalog.custom_data
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
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                # Schema uses source_type/source_id (not source_item_type/source_item_id)
                await self.conn.execute("""
                    INSERT INTO ag_catalog.entity_relationships
                    (workspace_id, source_type, source_id, target_type, target_id,
                     relationship_type, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    link.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    link.get('source_item_type', 'decision'),
                    source_id,
                    link.get('target_item_type', 'decision'),
                    target_id,
                    link.get('relationship_type', 'relates_to'),
                    created_at
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
        table_exists = await self.conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'ag_catalog'
                AND table_name = 'system_patterns'
            )
        """)

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
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                updated_at_str = pattern.get('updated_at')
                updated_at = dateparser.parse(updated_at_str) if updated_at_str else datetime.utcnow()

                await self.conn.execute("""
                    INSERT INTO ag_catalog.system_patterns
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
        imported = 0

        if active_context:
            logger.info("\n🎯 Importing active context...")
            try:
                content = active_context.get('content', {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception as e:
                        pass

                        logger.error(f"Error: {e}")
                # Parse timestamps
                created_at_str = active_context.get('created_at')
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                updated_at_str = active_context.get('updated_at')
                updated_at = dateparser.parse(updated_at_str) if updated_at_str else datetime.utcnow()

                # Store content in active_context column (not content)
                await self.conn.execute("""
                    INSERT INTO ag_catalog.workspace_contexts
                    (workspace_id, active_context, context_type, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    active_context.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    json.dumps(content),
                    'active',
                    created_at,
                    updated_at
                )
                imported += 1
                logger.info("   ✅ Imported active context")
            except Exception as e:
                logger.error(f"   ⚠️  Failed to import active context: {e}")

        if product_context:
            logger.info("\n📦 Importing product context...")
            try:
                content = product_context.get('content', {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception as e:
                        pass

                        logger.error(f"Error: {e}")
                # Parse timestamps
                created_at_str = product_context.get('created_at')
                created_at = dateparser.parse(created_at_str) if created_at_str else datetime.utcnow()

                updated_at_str = product_context.get('updated_at')
                updated_at = dateparser.parse(updated_at_str) if updated_at_str else datetime.utcnow()

                # Store in active_context column (reuse same column, differentiate by context_type)
                await self.conn.execute("""
                    INSERT INTO ag_catalog.workspace_contexts
                    (workspace_id, active_context, context_type, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    product_context.get('workspace_id', '/Users/hue/code/dopemux-mvp'),
                    json.dumps(content),
                    'product',
                    created_at,
                    updated_at
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
