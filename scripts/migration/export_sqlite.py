#!/usr/bin/env python3
"""
SQLite→AGE Direct Export
Part of CONPORT-KG-2025 Simplified Migration (Decision #113)

Exports from SQLite (already has INTEGER IDs!) directly to JSON.
NO schema upgrade needed - SQLite schema is AGE-compatible!
"""

import sqlite3
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

        print(f"✓ Exported {len(decisions)} decisions from SQLite")
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

        print(f"✓ Exported {len(relationships)} relationships from SQLite")
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

        print(f"\n✓ Export complete: {output_file}")
        print(f"  - Decisions: {len(decisions)}")
        print(f"  - Relationships: {len(relationships)}")
        print(f"  - Relationship types: {len(rel_types)} ({', '.join(sorted(rel_types))})")
        print(f"  - File size: {file_size:.1f} KB")

        return export_data


def main():
    """Main export procedure"""

    SQLITE_PATH = "/Users/hue/code/dopemux-mvp/context_portal/context.db"
    OUTPUT_FILE = Path("conport_sqlite_export.json")

    print("=" * 60)
    print("ConPort SQLite Export (Simplified Migration)")
    print("=" * 60)
    print(f"SQLite: {SQLITE_PATH}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    exporter = SQLiteExporter(SQLITE_PATH)

    try:
        export_data = exporter.export_all(OUTPUT_FILE)

        print("\n✓ SUCCESS: Data exported from SQLite")
        print("\n✓ Schema advantages:")
        print("  - INTEGER IDs (no UUID conversion needed!)")
        print("  - implementation_details field present")
        print("  - 9 relationship types (exceeds our 8-type design)")
        print("  - JSON tags compatible with JSONB")
        print("\nNext steps:")
        print("  1. Review export file")
        print("  2. Run load_age_direct.py (direct copy!)")

        return 0

    except Exception as e:
        print(f"\n✗ ERROR: Export failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
