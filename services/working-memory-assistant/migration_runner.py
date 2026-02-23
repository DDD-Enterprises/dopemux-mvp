#!/usr/bin/env python3
"""
Working Memory Assistant Database Migration Runner

Applies WMA schema migration to ConPort PostgreSQL database.
Integrates WMA tables with existing ConPort knowledge graph structure.

Usage:
    python migration_runner.py [--dry-run] [--force]

Options:
    --dry-run: Show what would be executed without running it
    --force: Force migration even if tables exist
"""

import argparse
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WMAMigrationRunner:
    """Handles WMA database schema migration for ConPort integration."""

    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.connection = None

        # Database configuration for WMA service (uses its own PostgreSQL instance)
        # WMA has its own database: dopemux_knowledge_graph on port 5432
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'dopemux_knowledge_graph'),
            'user': os.getenv('POSTGRES_USER', 'dopemux_age'),
            'password': os.getenv('POSTGRES_PASSWORD', 'dopemux_age_dev_password')
        }

        # Migration file path
        self.migration_file = Path(__file__).parent / 'wma_migration.sql'

    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False  # Use transactions
            logger.info("Connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")

    def check_existing_tables(self):
        """Check if WMA tables already exist."""
        tables = [
            'wma_context_snapshots',
            'wma_recovery_sessions',
            'wma_recovery_patterns',
            'wma_conport_links'
        ]

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN %s;
                """, (tuple(tables),))
                results = cursor.fetchall()
                return [row[0] for row in results]
        except psycopg2.Error as e:
            logger.error(f"Error checking existing tables: {e}")
            return []

    def validate_database_connection(self):
        """Validate that we can connect to the WMA database."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version[:50]}...")
                return True
        except psycopg2.Error as e:
            logger.error(f"Database connection validation failed: {e}")
            return False

    def apply_migration(self):
        """Apply the WMA migration SQL."""
        if not self.migration_file.exists():
            logger.error(f"Migration file not found: {self.migration_file}")
            return False

        try:
            with open(self.migration_file, 'r') as f:
                migration_sql = f.read()

            if self.dry_run:
                logger.info("DRY RUN - Would execute migration:")
                logger.info("=" * 50)
                # Show first 500 chars to avoid overwhelming output
                preview = migration_sql[:500] + "..." if len(migration_sql) > 500 else migration_sql
                logger.info(preview)
                logger.info("=" * 50)
                return True

            # Execute migration
            with self.connection.cursor() as cursor:
                cursor.execute(migration_sql)

            self.connection.commit()
            logger.info("WMA migration applied successfully")
            return True

        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Migration failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during migration: {e}")
            return False

    def verify_migration(self):
        """Verify that migration was applied correctly."""
        expected_tables = [
            'wma_context_snapshots',
            'wma_recovery_sessions',
            'wma_recovery_patterns',
            'wma_conport_links'
        ]

        try:
            with self.connection.cursor() as cursor:
                # Optimized existence check for all tables
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN %s;
                """, (tuple(expected_tables),))
                existing_tables = {row[0] for row in cursor.fetchall()}

                for table in expected_tables:
                    if table not in existing_tables:
                        logger.error(f"Table '{table}' was not created")
                        return False

                    # Check if table has data structure
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    logger.info(f"Table '{table}' created successfully (rows: {count})")

                # Optimized check for views
                views = ['wma_recovery_performance', 'wma_snapshot_analytics']
                cursor.execute("""
                    SELECT table_name FROM information_schema.views
                    WHERE table_schema = 'public'
                    AND table_name IN %s;
                """, (tuple(views),))
                existing_views = {row[0] for row in cursor.fetchall()}

                for view in views:
                    if view not in existing_views:
                        logger.warning(f"View '{view}' was not created")
                    else:
                        logger.info(f"View '{view}' created successfully")

            logger.info("Migration verification completed successfully")
            return True

        except psycopg2.Error as e:
            logger.error(f"Verification failed: {e}")
            return False

    def run_migration(self):
        """Run the complete migration process."""
        logger.info("Starting WMA Database Migration")
        logger.info("=" * 50)

        if not self.connect():
            return False

        try:
            # Validate database connection
            if not self.validate_database_connection():
                logger.error("Database connection validation failed")
                return False

            # Check for existing WMA tables
            existing_tables = self.check_existing_tables()
            if existing_tables and not self.force:
                logger.warning(f"WMA tables already exist: {', '.join(existing_tables)}")
                logger.warning("Use --force to overwrite existing tables")
                return False
            elif existing_tables and self.force:
                logger.warning(f"Force mode: overwriting existing tables: {', '.join(existing_tables)}")

            # Apply migration
            if not self.apply_migration():
                logger.error("Migration application failed")
                return False

            # Verify migration
            if not self.dry_run and not self.verify_migration():
                logger.error("Migration verification failed")
                return False

            logger.info("=" * 50)
            if self.dry_run:
                logger.info("DRY RUN completed successfully")
            else:
                logger.info("WMA Database Migration completed successfully!")
                logger.info("Next steps:")
                logger.info("1. Start WMA FastAPI service")
                logger.info("2. Configure Redis cache layer")
                logger.info("3. Test snapshot creation and recovery")

            return True

        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description="WMA Database Migration Runner")
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be executed without running it')
    parser.add_argument('--force', action='store_true',
                       help='Force migration even if tables exist')

    args = parser.parse_args()

    runner = WMAMigrationRunner(dry_run=args.dry_run, force=args.force)
    success = runner.run_migration()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()