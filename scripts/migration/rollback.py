#!/usr/bin/env python3
"""
ConPort Schema Rollback
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Emergency rollback procedure if switchover fails.
Restores old schema tables.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"✓ Connected to ConPort PostgreSQL")

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def execute_rollback(self):
        """Execute rollback to old schema"""

        logger.warning("\n⚠️  WARNING: This will rollback to old schema")
        logger.info("Any data in new schema will be LOST")
        logger.info()

        response = input("Type 'ROLLBACK' to confirm: ")

        if response != "ROLLBACK":
            logger.info("Aborted - no changes made")
            return False

        await self.connect()

        try:
            logger.info("\nExecuting rollback...")

            async with self.conn.transaction():
                # Drop new tables if they exist
                logger.info("  1. Dropping new schema tables...")
                await self.conn.execute("DROP TABLE IF EXISTS decisions CASCADE")
                await self.conn.execute("DROP TABLE IF EXISTS entity_relationships CASCADE")
                await self.conn.execute("DROP TABLE IF EXISTS decisions_v2 CASCADE")
                await self.conn.execute("DROP TABLE IF EXISTS entity_relationships_v2 CASCADE")

                # Restore old tables
                logger.info("  2. Restoring old schema tables...")
                await self.conn.execute("ALTER TABLE decisions_old RENAME TO decisions")
                await self.conn.execute("ALTER TABLE entity_relationships_old RENAME TO entity_relationships")

                logger.info("  3. Transaction committed")

            logger.info("\n✓ Rollback complete - old schema restored")

            # Verify
            count = await self.conn.fetchval("SELECT COUNT(*) FROM decisions")
            logger.info(f"\nVerification: {count} decisions in old schema")

            return True

        finally:
            await self.disconnect()


async def main():
    """Main rollback procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"

    logger.info("=" * 60)
    logger.info("ConPort Schema Rollback (EMERGENCY)")
    logger.info("=" * 60)
    logger.info()

    rollback = SchemaRollback(DB_URL)

    try:
        success = await rollback.execute_rollback()

        if success:
            logger.info("\n" + "=" * 60)
            logger.info("✓ ROLLBACK COMPLETE")
            logger.info("=" * 60)
            logger.info("\nMANUAL STEPS REQUIRED:")
            logger.info("  1. Restart ConPort MCP server:")
            logger.info("     docker restart conport-mcp-server")
            logger.info()
            logger.info("  2. Verify old schema working:")
            logger.info("     (Use ConPort via Claude to query decisions)")
            logger.info()
            logger.info("  3. Investigate rollback cause")
            logger.info("  4. Fix issues before re-attempting migration")

            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"\n✗ ERROR: Rollback failed")
        logger.info(f"  {str(e)}")
        logger.info("\nContact administrator for manual recovery")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
