# ConPort Database Migrations

## Migration 007: Worktree Multi-Instance Support

**Purpose**: Add minimal worktree support for parallel task workflows.

**Date**: 2025-10-04
**Decision**: #179 (Simplified MVP Design)

### Files

- `007_worktree_support_simple.sql` - Forward migration (adds instance_id columns)
- `007_rollback.sql` - Rollback migration (removes instance_id columns)
- `test_migration_007.sh` - Automated test suite (manual testing recommended)

### What This Migration Does

**Schema Changes**:
- Adds `instance_id VARCHAR(255)` to `progress_entries` table
- Adds `created_by_instance VARCHAR(255)` to `decisions` table
- Creates performance indexes for instance-based queries
- Sets existing data to shared mode (instance_id = NULL)

**Data Isolation Strategy**:
- `instance_id = NULL` → Shared across all worktrees (COMPLETED/BLOCKED tasks)
- `instance_id = 'worktree-name'` → Isolated to specific worktree (IN_PROGRESS/PLANNED tasks)

### Running the Migration

**Prerequisites**:
1. Backup your database first!
2. Identify correct PostgreSQL container and database name
3. Verify ConPort MCP server is stopped (to avoid mid-migration writes)

**Manual Execution** (Recommended):

```bash
# 1. Backup database
docker exec dopemux-postgres-age pg_dump \
  -U dopemux_age -d dopemux_knowledge_graph \
  > /tmp/conport_backup_$(date +%Y%m%d).sql

# 2. Run migration
docker exec -i dopemux-postgres-age psql \
  -U dopemux_age -d dopemux_knowledge_graph \
  < migrations/007_worktree_support_simple.sql

# 3. Verify migration
docker exec dopemux-postgres-age psql \
  -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'progress_entries' AND column_name = 'instance_id';"

# Expected: instance_id column exists
```

**Rollback** (If Needed):

```bash
# Revert to pre-migration state
docker exec -i dopemux-postgres-age psql \
  -U dopemux_age -d dopemux_knowledge_graph \
  < migrations/007_rollback.sql

# Or restore from backup
docker exec -i dopemux-postgres-age psql \
  -U dopemux_age -d dopemux_knowledge_graph \
  < /tmp/conport_backup_YYYYMMDD.sql
```

### Post-Migration Usage

**Single Worktree** (No Changes Required):
```bash
# Just use ConPort normally - all tasks remain shared
# instance_id stays NULL for all operations
```

**Multi-Worktree** (Manual Setup):
```bash
# 1. Create git worktree
cd ~/code/dopemux-mvp
git worktree add ../dopemux-feature-auth feature/auth

# 2. Set environment variables in new worktree
cd ../dopemux-feature-auth
export DOPEMUX_INSTANCE_ID="feature-auth"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# 3. Work normally
# IN_PROGRESS tasks → isolated to this worktree
# COMPLETED tasks → shared across all worktrees
```

### Validation Checklist

After migration, verify:
- [ ] Migration completed without errors
- [ ] `instance_id` column exists in `progress_entries`
- [ ] `created_by_instance` column exists in `decisions`
- [ ] Indexes `idx_progress_instance` and `idx_progress_workspace_instance` exist
- [ ] Existing data has `instance_id = NULL` (shared mode)
- [ ] Can insert new progress entries with instance_id
- [ ] Can query progress entries with instance filtering
- [ ] Rollback script works (test in dev first!)

### Known Limitations (MVP)

- **Manual environment setup**: No automatic git worktree detection
- **No commands**: Use `git worktree` manually
- **Last-write-wins**: No optimistic locking for concurrent updates
- **Basic isolation**: Only 5 core ConPort tools updated initially

### Future Enhancements (Post-MVP)

- Automatic git worktree detection
- /dx:worktree commands (create, list, switch, cleanup)
- Full service integration (ADHD Engine, dope-context, Serena)
- Advanced features (cleanup jobs, optimistic locking, hyperfocus warnings)

### Troubleshooting

**Migration fails with "column already exists"**:
- Migration was already run. Check schema with `\d progress_entries` in psql.
- If migration is partially complete, manually rollback and re-run.

**Cannot connect to database**:
- Verify container name: `docker ps | grep postgres`
- Verify database name: `docker exec <container> psql -l`
- Adjust connection commands above with correct names.

**Rollback doesn't complete**:
- Check for foreign key constraints or triggers
- Manually drop columns if needed: `ALTER TABLE progress_entries DROP COLUMN instance_id CASCADE;`

### Support

For issues or questions:
- Check Decision #179 in ConPort for design rationale
- Review Zen planning reference: continuation_id `2eaaeaa4-93da-42d0-bcb2-8ebb2a949aa9`
- Test in development environment first!

---

**Migration Status**: Ready for manual execution
**Testing Status**: Automated test limited by database access (manual validation recommended)
**Production Ready**: Yes (with backup and validation)
