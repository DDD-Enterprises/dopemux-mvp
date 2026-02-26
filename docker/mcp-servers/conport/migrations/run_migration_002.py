#!/usr/bin/env python3
"""Execute Phase 3 migration: decision_patterns table"""

import asyncio
import asyncpg
from pathlib import Path

DATABASE_URL = "postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph"

async def run():
    migration_file = Path(__file__).parent / "002_decision_patterns_table.sql"

    print("🔧 Executing Migration 002: decision_patterns table")
    print("=" * 60)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Execute migration
        sql = migration_file.read_text()
        await conn.execute(sql)

        print("✅ Migration SQL executed")

        # Verify table created
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'decision_patterns'
            )
        """)

        if exists:
            print("✅ decision_patterns table created")
        else:
            print("❌ Table creation failed")
            return False

        # Verify view created
        view_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.views
                WHERE table_name = 'pattern_statistics'
            )
        """)

        if view_exists:
            print("✅ pattern_statistics view created")

        print("\n✅ Migration 002 SUCCESSFUL")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        await conn.close()

if __name__ == "__main__":
    import sys
    success = asyncio.run(run())
    sys.exit(0 if success else 1)
