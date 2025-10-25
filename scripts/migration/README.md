# ConPort SQLite → PostgreSQL AGE Migration

Complete migration of ConPort from SQLite to PostgreSQL AGE with DDG backfill.

## Quick Start

```bash
cd scripts/migration
./migrate_conport_to_age.sh
```

**Time**: ~15 minutes | **Risk**: LOW (backup created first)

## What This Does

1. Backs up SQLite (4MB, 293 decisions)
2. Exports SQLite → JSON
3. Rebuilds postgres-age with working AGE
4. Imports to PostgreSQL AGE
5. Backfills DDG (publishes 293 events)
6. Verifies migration success

## Files Created

- **export_sqlite_to_json.py** - SQLite → JSON export
- **import_to_postgresql_age.py** - JSON → PostgreSQL import
- **backfill_ddg.py** - Publish events to DDG
- **migrate_conport_to_age.sh** - Master orchestrator

## Success Criteria

- ✅ ConPort PostgreSQL: 293 decisions
- ✅ DDG PostgreSQL: 293 decisions
- ✅ AGE graph queries work
- ✅ mcp__conport__* tools work
- ✅ ddg-mcp.related_text returns results

## Rollback

```bash
# Restore from backup
cp backups/context_YYYYMMDD_HHMMSS.db context_portal/context.db
```

## Support

See full documentation in this file for troubleshooting and manual steps.
