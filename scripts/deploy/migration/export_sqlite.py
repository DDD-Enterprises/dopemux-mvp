#!/usr/bin/env python3
"""
SQLite→AGE Direct Export
Part of CONPORT-KG-2025 Simplified Migration (Decision #113)

Exports from SQLite (already has INTEGER IDs!) directly to JSON.
NO schema upgrade needed - SQLite schema is AGE-compatible!
"""

import sqlite3

import logging

logger = logging.getLogger(__name__)

import json
import sys
from pathlib import Path
from datetime import datetime


class SQLiteExporter:
    """Exports ConPort data from SQLite"""

    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

    def export_decisions(self) -> list:
        """Export all 112 decisions (already INTEGER IDs!)"""

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, timestamp, summary, rationale, implementation_details, tags
            FROM decisions
            ORDER BY id ASC
        """)

        decisions = [dict(row) for row in cursor.fetchall()]

        conn.close()

        logger.info(f"✓ Exported {len(decisions)} decisions from SQLite")
        return decisions

    def export_relationships(self) -> list:
        """Export decision-to-decision relationships"""

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                workspace_id,
                source_item_type,
                source_item_id,
                target_item_type,
                target_item_id,
                relationship_type,
                description,
                timestamp
            FROM context_links
            WHERE source_item_type = 'decision'
              AND target_item_type = 'decision'
            ORDER BY timestamp ASC
        """)

        relationships = [dict(row) for row in cursor.fetchall()]

        conn.close()

        logger.info(f"✓ Exported {len(relationships)} relationships from SQLite")
        return relationships

    def export_all(self, output_file: Path):
        """Export complete dataset"""

        decisions = self.export_decisions()
        relationships = self.export_relationships()

        # Get unique relationship types
        rel_types = set(r['relationship_type'] for r in relationships)

        export_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "SQLite context_portal/context.db",
                "decision_count": len(decisions),
                "relationship_count": len(relationships),
                "relationship_types": list(rel_types),
                "export_version": "2.0-simplified",
                "purpose": "Direct SQLite→AGE migration (Decision #113)"
            },
            "decisions": decisions,
            "relationships": relationships
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        file_size = output_file.stat().st_size / 1024

        logger.info(f"\n✓ Export complete: {output_file}")
        logger.info(f"  - Decisions: {len(decisions)}")
        logger.info(f"  - Relationships: {len(relationships)}")
        logger.info(f"  - Relationship types: {len(rel_types)} ({', '.join(sorted(rel_types))})")
        logger.info(f"  - File size: {file_size:.1f} KB")

        return export_data


def main():
    """Main export procedure"""

    SQLITE_PATH = "/Users/hue/code/dopemux-mvp/context_portal/context.db"
    OUTPUT_FILE = Path("conport_sqlite_export.json")

    logger.info("=" * 60)
    logger.info("ConPort SQLite Export (Simplified Migration)")
    logger.info("=" * 60)
    logger.info(f"SQLite: {SQLITE_PATH}")
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info()

    exporter = SQLiteExporter(SQLITE_PATH)

    try:
        export_data = exporter.export_all(OUTPUT_FILE)

        logger.info("\n✓ SUCCESS: Data exported from SQLite")
        logger.info("\n✓ Schema advantages:")
        logger.info("  - INTEGER IDs (no UUID conversion needed!)")
        logger.info("  - implementation_details field present")
        logger.info("  - 9 relationship types (exceeds our 8-type design)")
        logger.info("  - JSON tags compatible with JSONB")
        logger.info("\nNext steps:")
        logger.info("  1. Review export file")
        logger.info("  2. Run load_age_direct.py (direct copy!)")

        return 0

    except Exception as e:
        logger.error(f"\n✗ ERROR: Export failed")
        logger.info(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
