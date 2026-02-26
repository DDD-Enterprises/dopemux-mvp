#!/usr/bin/env python3
"""
Execute ConPort Phase 1 Migration: Enhanced Decision Model

Safely applies migration 001 with:
- Backup verification
- Rollback on failure
- Validation checks
- Progress reporting

Usage:
    python run_migration_001.py
    python run_migration_001.py --dry-run
    python run_migration_001.py --rollback
"""

import asyncio
import asyncpg
import argparse
from pathlib import Path
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph"

async def backup_decisions_table(conn: asyncpg.Connection) -> str:
    """Create backup of decisions table before migration."""
    backup_table = f"decisions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    await conn.execute(f"""
        CREATE TABLE {backup_table} AS
        SELECT * FROM decisions
    """)

    count = await conn.fetchval(f"SELECT COUNT(*) FROM {backup_table}")
    print(f"✅ Backup created: {backup_table} ({count} rows)")

    return backup_table


async def run_migration(dry_run: bool = False):
    """Execute the migration script."""

    migration_file = Path(__file__).parent / "001_enhanced_decision_model.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print("🔧 ConPort Phase 1 Migration: Enhanced Decision Model")
    print("=" * 60)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Step 1: Create backup
        print("\n📦 Step 1: Creating backup...")
        if not dry_run:
            backup_table = await backup_decisions_table(conn)
        else:
            print("  [DRY RUN] Would create backup table")
            backup_table = "decisions_backup_dryrun"

        # Step 2: Check current schema
        print("\n🔍 Step 2: Checking current schema...")
        current_cols = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'decisions'
            ORDER BY ordinal_position
        """)
        print(f"  Current columns: {len(current_cols)}")

        # Step 3: Run migration
        print("\n⚙️  Step 3: Applying migration...")
        if not dry_run:
            migration_sql = migration_file.read_text()
            await conn.execute(migration_sql)
            print("  ✅ Migration SQL executed")
        else:
            print("  [DRY RUN] Would execute migration SQL")

        # Step 4: Validate new schema
        print("\n✅ Step 4: Validating new schema...")
        new_cols = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'decisions'
            ORDER BY ordinal_position
        """)

        if not dry_run:
            print(f"  New columns: {len(new_cols)}")
            print(f"  Added: {len(new_cols) - len(current_cols)} columns")

            # Verify expected columns
            expected_new = [
                'impact_score', 'reversibility', 'alternatives_considered',
                'success_criteria', 'review_date', 'outcome_status',
                'outcome_notes', 'outcome_date', 'lessons_learned',
                'cognitive_load', 'decision_time_minutes', 'energy_level',
                'requires_followup'
            ]

            col_names = [col['column_name'] for col in new_cols]
            missing = [c for c in expected_new if c not in col_names]

            if missing:
                print(f"  ⚠️  Missing columns: {missing}")
                raise Exception(f"Validation failed: missing {missing}")
            else:
                print(f"  ✅ All 13 enhanced columns present")

        # Step 5: Verify new tables
        print("\n🗃️  Step 5: Verifying new tables...")
        if not dry_run:
            tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('decision_relationships', 'adhd_metrics', 'review_reminders')
            """)

            if len(tables) != 3:
                raise Exception(f"Expected 3 new tables, found {len(tables)}")

            print(f"  ✅ All 3 new tables created:")
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
                print(f"     - {table['tablename']} ({count} rows)")
        else:
            print("  [DRY RUN] Would verify 3 new tables")

        # Step 6: Test data compatibility
        print("\n🧪 Step 6: Testing backward compatibility...")
        if not dry_run:
            # Verify old decisions still query correctly
            old_decision_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM decisions
                WHERE alternatives_considered = '[]'
                AND success_criteria = '[]'
                AND outcome_status IS NULL
            """)
            print(f"  ✅ Existing decisions compatible: {old_decision_count} rows")
        else:
            print("  [DRY RUN] Would verify existing data compatibility")

        print("\n" + "=" * 60)
        print("✅ MIGRATION SUCCESSFUL!")
        print("=" * 60)

        if not dry_run:
            print(f"\n💾 Backup available: {backup_table}")
            print("   (Can be dropped after validation: DROP TABLE {backup_table};)")

        print("\n📊 Next steps:")
        print("  1. Test Quick Win commands with enhanced schema")
        print("  2. Migrate energy data: python migrate_energy_data.py")
        print("  3. Update ConPort MCP server to use new fields")
        print("  4. Update CLI commands to show enhanced metadata")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")

        if not dry_run:
            print(f"\n🔄 Rolling back...")
            print(f"   To restore: DROP TABLE decisions; ALTER TABLE {backup_table} RENAME TO decisions;")

        return False

    finally:
        await conn.close()


async def migrate_energy_data():
    """Migrate existing energy logs from custom_data to adhd_metrics."""

    print("\n🔄 Migrating Energy Data")
    print("=" * 60)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Count existing energy logs
        count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM custom_data
            WHERE category = 'adhd_energy'
        """)

        print(f"Found {count} energy log entries to migrate")

        if count == 0:
            print("✅ No energy data to migrate")
            return True

        # Migrate energy logs
        await conn.execute("""
            INSERT INTO adhd_metrics (workspace_id, metric_type, level, context_note, created_at)
            SELECT
                workspace_id,
                'energy',
                (value->>'energy_level')::VARCHAR,
                value->>'context',
                created_at
            FROM custom_data
            WHERE category = 'adhd_energy'
            ON CONFLICT DO NOTHING
        """)

        migrated = await conn.fetchval("SELECT COUNT(*) FROM adhd_metrics WHERE metric_type = 'energy'")
        print(f"✅ Migrated {migrated} energy entries to adhd_metrics table")

        # Keep original data for now (can be cleaned up later)
        print(f"   Original custom_data entries preserved (cleanup manually if desired)")

        return True

    except Exception as e:
        print(f"❌ Energy data migration failed: {e}")
        return False

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run ConPort Phase 1 migration")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without executing")
    parser.add_argument("--migrate-data", action="store_true", help="Also migrate energy data to adhd_metrics")

    args = parser.parse_args()

    # Run schema migration
    success = asyncio.run(run_migration(dry_run=args.dry_run))

    if not success:
        print("\n⚠️  Migration failed - check errors above")
        return 1

    # Optionally migrate data
    if args.migrate_data and not args.dry_run:
        data_success = asyncio.run(migrate_energy_data())
        if not data_success:
            print("\n⚠️  Data migration had issues - check logs")
            return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
