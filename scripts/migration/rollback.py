#!/usr/bin/env python3
"""
ConPort Schema Rollback
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Emergency rollback procedure if switchover fails.
Restores old schema tables.
"""

import asyncio
import asyncpg
import sys


class SchemaRollback:
    """Handles emergency rollback to old schema"""

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

    async def execute_rollback(self):
        """Execute rollback to old schema"""

        print("\n⚠️  WARNING: This will rollback to old schema")
        print("Any data in new schema will be LOST")
        print()

        response = input("Type 'ROLLBACK' to confirm: ")

        if response != "ROLLBACK":
            print("Aborted - no changes made")
            return False

        await self.connect()

        try:
            print("\nExecuting rollback...")

            async with self.conn.transaction():
                # Drop new tables if they exist
                print("  1. Dropping new schema tables...")
                await self.conn.execute("DROP TABLE IF EXISTS decisions CASCADE")
                await self.conn.execute("DROP TABLE IF EXISTS entity_relationships CASCADE")
                await self.conn.execute("DROP TABLE IF EXISTS decisions_v2 CASCADE")
                await self.conn.execute("DROP TABLE IF EXISTS entity_relationships_v2 CASCADE")

                # Restore old tables
                print("  2. Restoring old schema tables...")
                await self.conn.execute("ALTER TABLE decisions_old RENAME TO decisions")
                await self.conn.execute("ALTER TABLE entity_relationships_old RENAME TO entity_relationships")

                print("  3. Transaction committed")

            print("\n✓ Rollback complete - old schema restored")

            # Verify
            count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions")
            print(f"\nVerification: {count} decisions in old schema")

            return True

        finally:
            await self.disconnect()


async def main():
    """Main rollback procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"

    print("=" * 60)
    print("ConPort Schema Rollback (EMERGENCY)")
    print("=" * 60)
    print()

    rollback = SchemaRollback(DB_URL)

    try:
        success = await rollback.execute_rollback()

        if success:
            print("\n" + "=" * 60)
            print("✓ ROLLBACK COMPLETE")
            print("=" * 60)
            print("\nMANUAL STEPS REQUIRED:")
            print("  1. Restart ConPort MCP server:")
            print("     docker restart conport-mcp-server")
            print()
            print("  2. Verify old schema working:")
            print("     (Use ConPort via Claude to query decisions)")
            print()
            print("  3. Investigate rollback cause")
            print("  4. Fix issues before re-attempting migration")

            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Rollback failed")
        print(f"  {str(e)}")
        print("\nContact administrator for manual recovery")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
