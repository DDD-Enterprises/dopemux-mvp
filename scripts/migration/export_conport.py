#!/usr/bin/env python3
"""
ConPort Data Export Script
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Exports all decisions and relationships to JSON backup for schema upgrade.
Preserves created_at order to ensure SERIAL ID sequence matches temporal order.
"""

import asyncio
import asyncpg
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ConPortExporter:
    """Exports ConPort data for schema upgrade migration"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None

    async def connect(self):
        """Establish database connection"""
        self.conn = await asyncpg.connect(self.db_url)
        print(f"✓ Connected to ConPort PostgreSQL")

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def export_decisions(self, workspace_id: str) -> List[Dict]:
        """
        Export all decisions ordered by created_at

        CRITICAL: Order by created_at ASC ensures SERIAL IDs match temporal sequence
        """
        query = """
            SELECT
                id::text as id,
                workspace_id,
                summary,
                rationale,
                alternatives,
                tags,
                confidence_level,
                decision_type,
                created_at,
                updated_at
            FROM decisions
            WHERE workspace_id = $1
            ORDER BY created_at ASC
        """

        rows = await self.conn.fetch(query, workspace_id)

        decisions = []
        for row in rows:
            decision = dict(row)
            # Convert timestamp to ISO format
            decision['created_at'] = decision['created_at'].isoformat()
            decision['updated_at'] = decision['updated_at'].isoformat()
            decisions.append(decision)

        print(f"✓ Exported {len(decisions)} decisions (ordered by created_at)")
        return decisions

    async def export_relationships(self) -> List[Dict]:
        """Export all decision-to-decision relationships"""
        query = """
            SELECT
                id::text as id,
                workspace_id,
                source_type,
                source_id::text as source_id,
                target_type,
                target_id::text as target_id,
                relationship_type,
                strength,
                created_at
            FROM entity_relationships
            WHERE source_type = 'decision'
              AND target_type = 'decision'
            ORDER BY created_at ASC
        """

        rows = await self.conn.fetch(query)

        relationships = []
        for row in rows:
            rel = dict(row)
            rel['created_at'] = rel['created_at'].isoformat()
            relationships.append(rel)

        print(f"✓ Exported {len(relationships)} relationships")
        return relationships

    async def export_all(self, workspace_id: str, output_file: Path):
        """Export complete dataset to JSON"""
        await self.connect()

        try:
            decisions = await self.export_decisions(workspace_id)
            relationships = await self.export_relationships()

            export_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "workspace_id": workspace_id,
                    "decision_count": len(decisions),
                    "relationship_count": len(relationships),
                    "export_version": "1.0",
                    "purpose": "CONPORT-KG-2025 schema upgrade (Decision #112)"
                },
                "decisions": decisions,
                "relationships": relationships
            }

            # Write to JSON file
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            print(f"\n✓ Export complete: {output_file}")
            print(f"  - Decisions: {len(decisions)}")
            print(f"  - Relationships: {len(relationships)}")
            print(f"  - File size: {output_file.stat().st_size / 1024:.1f} KB")

            return export_data

        finally:
            await self.disconnect()


async def main():
    """Main export procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_secure_2024_unified@localhost:5432/conport"
    WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"
    OUTPUT_FILE = Path("conport_backup_dopemux-mvp.json")

    print("=" * 60)
    print("ConPort Data Export for Schema Upgrade")
    print("=" * 60)
    print(f"Workspace: {WORKSPACE_ID}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    exporter = ConPortExporter(DB_URL)

    try:
        export_data = await exporter.export_all(WORKSPACE_ID, OUTPUT_FILE)

        print("\n✓ SUCCESS: Data exported successfully")
        print("\nNext steps:")
        print("  1. Review backup file")
        print("  2. Create decisions_v2 and entity_relationships_v2 tables")
        print("  3. Run transformation and re-ingestion")

        return 0

    except Exception as e:
        print(f"\n✗ ERROR: Export failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
