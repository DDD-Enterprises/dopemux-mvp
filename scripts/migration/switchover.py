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

import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"✓ Connected to ConPort PostgreSQL")

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def execute_switchover(self):
        """Execute atomic table rename"""

        logger.error("\n⚠️  CRITICAL: This will switchover to new schema")
        logger.info("Ensure ConPort MCP server is STOPPED before proceeding")
        logger.info()

        response = input("Type 'SWITCHOVER' to confirm: ")

        if response != "SWITCHOVER":
            logger.info("Aborted - no changes made")
            return False

        await self.connect()

        try:
            logger.info("\nExecuting atomic switchover...")

            async with self.conn.transaction():
                # Archive old tables
                logger.info("  1. Archiving old tables...")
                await self.conn.execute("ALTER TABLE decisions RENAME TO decisions_old")
                await self.conn.execute("ALTER TABLE entity_relationships RENAME TO entity_relationships_old")

                # Promote v2 tables
                logger.info("  2. Promoting v2 tables...")
                await self.conn.execute("ALTER TABLE decisions_v2 RENAME TO decisions")
                await self.conn.execute("ALTER TABLE entity_relationships_v2 RENAME TO entity_relationships")

                logger.info("  3. Transaction committed")

            logger.info("\n✓ Switchover complete - new schema active")

            # Verify
            count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions")
            logger.info(f"\nVerification: {count} decisions in new schema")

            return True

        finally:
            await self.disconnect()


async def main():
    """Main switchover procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"

    logger.info("=" * 60)
    logger.info("ConPort Schema Switchover")
    logger.info("=" * 60)
    logger.info()

    # Step 1: Validate first
    logger.info("Step 1: Running validation checks...")
    validator = MigrationValidator(DB_URL)

    try:
        all_passed, checks = await validator.validate_all()

        for check in checks:
            status = "✓" if check['passed'] else "✗"
            logger.info(f"  {status} {check['name']}: {check['details']}")

        if not all_passed:
            logger.error("\n✗ ERROR: Validation failed - cannot switchover")
            logger.error("Fix validation errors first")
            return 1

        logger.info("\n✓ Validation passed")

    except Exception as e:
        logger.error(f"\n✗ ERROR: Validation failed: {e}")
        return 1

    # Step 2: Execute switchover
    logger.info("\nStep 2: Execute switchover...")
    switcher = SchemaSwitchover(DB_URL)

    try:
        success = await switcher.execute_switchover()

        if success:
            logger.info("\n" + "=" * 60)
            logger.info("✓ SWITCHOVER COMPLETE")
            logger.info("=" * 60)
            logger.info("\nMANUAL STEPS REQUIRED:")
            logger.info("  1. Restart ConPort MCP server:")
            logger.info("     docker restart conport-mcp-server")
            logger.info()
            logger.info("  2. Test MCP server:")
            logger.info("     claude mcp status conport")
            logger.info()
            logger.info("  3. Verify data access:")
            logger.info("     (Use ConPort via Claude to query decisions)")
            logger.info()
            logger.info("Old tables preserved as:")
            logger.info("  - decisions_old")
            logger.info("  - entity_relationships_old")
            logger.info()
            logger.info("After AGE migration validated, clean up with:")
            logger.info("  DROP TABLE decisions_old CASCADE;")
            logger.info("  DROP TABLE entity_relationships_old CASCADE;")
            logger.info("  ALTER TABLE decisions DROP COLUMN old_uuid;")

            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"\n✗ ERROR: Switchover failed")
        logger.info(f"  {str(e)}")
        logger.info("\nRun rollback.py if needed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
