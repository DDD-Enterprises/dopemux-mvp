#!/usr/bin/env python3
"""
ConPort Schema Switchover
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Atomic switchover from old to new schema:
1. Validates data integrity
2. Stops MCP server
3. Renames tables atomically
4. Instructions for MCP restart
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

from validate import MigrationValidator


class SchemaS witchover:
    """Handles atomic schema switchover"""

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

    async def execute_switchover(self):
        """Execute atomic table rename"""

        print("\n⚠️  CRITICAL: This will switchover to new schema")
        print("Ensure ConPort MCP server is STOPPED before proceeding")
        print()

        response = input("Type 'SWITCHOVER' to confirm: ")

        if response != "SWITCHOVER":
            print("Aborted - no changes made")
            return False

        await self.connect()

        try:
            print("\nExecuting atomic switchover...")

            async with self.conn.transaction():
                # Archive old tables
                print("  1. Archiving old tables...")
                await self.conn.execute("ALTER TABLE decisions RENAME TO decisions_old")
                await self.conn.execute("ALTER TABLE entity_relationships RENAME TO entity_relationships_old")

                # Promote v2 tables
                print("  2. Promoting v2 tables...")
                await self.conn.execute("ALTER TABLE decisions_v2 RENAME TO decisions")
                await self.conn.execute("ALTER TABLE entity_relationships_v2 RENAME TO entity_relationships")

                print("  3. Transaction committed")

            print("\n✓ Switchover complete - new schema active")

            # Verify
            count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions")
            print(f"\nVerification: {count} decisions in new schema")

            return True

        finally:
            await self.disconnect()


async def main():
    """Main switchover procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"

    print("=" * 60)
    print("ConPort Schema Switchover")
    print("=" * 60)
    print()

    # Step 1: Validate first
    print("Step 1: Running validation checks...")
    validator = MigrationValidator(DB_URL)

    try:
        all_passed, checks = await validator.validate_all()

        for check in checks:
            status = "✓" if check['passed'] else "✗"
            print(f"  {status} {check['name']}: {check['details']}")

        if not all_passed:
            print("\n✗ ERROR: Validation failed - cannot switchover")
            print("Fix validation errors first")
            return 1

        print("\n✓ Validation passed")

    except Exception as e:
        print(f"\n✗ ERROR: Validation failed: {e}")
        return 1

    # Step 2: Execute switchover
    print("\nStep 2: Execute switchover...")
    switcher = SchemaSwitchover(DB_URL)

    try:
        success = await switcher.execute_switchover()

        if success:
            print("\n" + "=" * 60)
            print("✓ SWITCHOVER COMPLETE")
            print("=" * 60)
            print("\nMANUAL STEPS REQUIRED:")
            print("  1. Restart ConPort MCP server:")
            print("     docker restart conport-mcp-server")
            print()
            print("  2. Test MCP server:")
            print("     claude mcp status conport")
            print()
            print("  3. Verify data access:")
            print("     (Use ConPort via Claude to query decisions)")
            print()
            print("Old tables preserved as:")
            print("  - decisions_old")
            print("  - entity_relationships_old")
            print()
            print("After AGE migration validated, clean up with:")
            print("  DROP TABLE decisions_old CASCADE;")
            print("  DROP TABLE entity_relationships_old CASCADE;")
            print("  ALTER TABLE decisions DROP COLUMN old_uuid;")

            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Switchover failed")
        print(f"  {str(e)}")
        print("\nRun rollback.py if needed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
