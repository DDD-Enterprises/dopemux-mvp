#!/usr/bin/env python3
"""
Export ConPort SQLite data to JSON for PostgreSQL migration.

Exports all tables:
- decisions
- progress_entries
- custom_data
- context_links (entity_relationships)
- system_patterns
- active_context
- product_context
"""

import sqlite3

import logging

logger = logging.getLogger(__name__)

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys


def export_sqlite_to_json(sqlite_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Export all ConPort data from SQLite to JSON.

    Args:
        sqlite_path: Path to SQLite database
        output_path: Path for JSON output file

    Returns:
        Export statistics
    """
    logger.info(f"📂 Exporting from: {sqlite_path}")
    logger.info(f"📝 Output to: {output_path}")
    logger.info("=" * 60)

    if not sqlite_path.exists():
        logger.info(f"❌ SQLite database not found: {sqlite_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    cursor = conn.cursor()

    export_data = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "source_db": str(sqlite_path),
        "decisions": [],
        "progress_entries": [],
        "custom_data": [],
        "context_links": [],
        "system_patterns": [],
        "active_context": None,
        "product_context": None
    }

    # Export decisions
    logger.info("\n📋 Exporting decisions...")
    cursor.execute("SELECT * FROM decisions ORDER BY id")
    for row in cursor.fetchall():
        decision = dict(row)
        # Convert tags from JSON string if needed
        if decision.get('tags') and isinstance(decision['tags'], str):
            try:
                decision['tags'] = json.loads(decision['tags'])
            except Exception as e:
                decision['tags'] = []
                logger.error(f"Error: {e}")
        export_data["decisions"].append(decision)
    logger.info(f"   ✅ Exported {len(export_data['decisions'])} decisions")

    # Export progress entries
    logger.info("\n📊 Exporting progress entries...")
    cursor.execute("SELECT * FROM progress_entries ORDER BY id")
    for row in cursor.fetchall():
        entry = dict(row)
        if entry.get('tags') and isinstance(entry['tags'], str):
            try:
                entry['tags'] = json.loads(entry['tags'])
            except Exception as e:
                entry['tags'] = []
                logger.error(f"Error: {e}")
        export_data["progress_entries"].append(entry)
    logger.info(f"   ✅ Exported {len(export_data['progress_entries'])} progress entries")

    # Export custom data
    logger.info("\n💾 Exporting custom data...")
    cursor.execute("SELECT * FROM custom_data ORDER BY category, key")
    for row in cursor.fetchall():
        data = dict(row)
        # Parse JSON value
        if data.get('value') and isinstance(data['value'], str):
            try:
                data['value'] = json.loads(data['value'])
            except Exception as e:
                pass  # Keep as string if not valid JSON
                logger.error(f"Error: {e}")
        export_data["custom_data"].append(data)
    logger.info(f"   ✅ Exported {len(export_data['custom_data'])} custom data entries")

    # Export relationships (context_links)
    logger.info("\n🔗 Exporting relationships...")
    cursor.execute("SELECT * FROM context_links ORDER BY id")
    for row in cursor.fetchall():
        link = dict(row)
        export_data["context_links"].append(link)
    logger.info(f"   ✅ Exported {len(export_data['context_links'])} relationships")

    # Export system patterns
    logger.info("\n🧩 Exporting system patterns...")
    cursor.execute("SELECT * FROM system_patterns ORDER BY id")
    for row in cursor.fetchall():
        pattern = dict(row)
        if pattern.get('tags') and isinstance(pattern['tags'], str):
            try:
                pattern['tags'] = json.loads(pattern['tags'])
            except Exception as e:
                pattern['tags'] = []
                logger.error(f"Error: {e}")
        export_data["system_patterns"].append(pattern)
    logger.info(f"   ✅ Exported {len(export_data['system_patterns'])} system patterns")

    # Export active context
    logger.info("\n🎯 Exporting active context...")
    cursor.execute("SELECT * FROM active_context ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        context = dict(row)
        if context.get('content') and isinstance(context['content'], str):
            try:
                context['content'] = json.loads(context['content'])
            except Exception as e:
                pass
                logger.error(f"Error: {e}")
        export_data["active_context"] = context
        logger.info(f"   ✅ Exported active context (version {context.get('id', 'unknown')})")

    # Export product context
    logger.info("\n📦 Exporting product context...")
    cursor.execute("SELECT * FROM product_context ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        context = dict(row)
        if context.get('content') and isinstance(context['content'], str):
            try:
                context['content'] = json.loads(context['content'])
            except Exception as e:
                pass
                logger.error(f"Error: {e}")
        export_data["product_context"] = context
        logger.info(f"   ✅ Exported product context (version {context.get('id', 'unknown')})")

    conn.close()

    # Write JSON file
    logger.info(f"\n💾 Writing JSON to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    file_size = output_path.stat().st_size / 1024  # KB
    logger.info(f"   ✅ Wrote {file_size:.1f} KB")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ EXPORT COMPLETE")
    logger.info("=" * 60)
    stats = {
        "decisions": len(export_data["decisions"]),
        "progress_entries": len(export_data["progress_entries"]),
        "custom_data": len(export_data["custom_data"]),
        "relationships": len(export_data["context_links"]),
        "system_patterns": len(export_data["system_patterns"]),
        "active_context": 1 if export_data["active_context"] else 0,
        "product_context": 1 if export_data["product_context"] else 0,
        "output_size_kb": file_size
    }

    for key, value in stats.items():
        logger.info(f"{key:20s}: {value}")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export ConPort SQLite to JSON")
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path("/Users/hue/code/dopemux-mvp/context_portal/context.db"),
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/Users/hue/code/dopemux-mvp/scripts/migration/conport_export.json"),
        help="Output JSON file"
    )

    args = parser.parse_args()

    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Run export
    stats = export_sqlite_to_json(args.sqlite_path, args.output)

    logger.info(f"\n🎉 Export successful! Output: {args.output}")
    logger.info(f"📊 Total items: {sum(v for k, v in stats.items() if k != 'output_size_kb')}")
