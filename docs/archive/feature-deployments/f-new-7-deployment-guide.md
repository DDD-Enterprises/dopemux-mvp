---
id: F-NEW-7_DEPLOYMENT_GUIDE
title: F New 7_Deployment_Guide
type: reference
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# F-NEW-7 Phase 1: Deployment Guide

**Migration 003**: Multi-Tenancy Foundation
**Status**: SQL ready, tested, awaiting execution
**Safety**: Zero-downtime, fully rollback-able
**Duration**: 15 minutes

---

## Pre-Deployment Checklist

- [ ] ConPort database accessible (port 5456)
- [ ] Backup created and verified
- [ ] Migration 003 SQL reviewed
- [ ] Rollback procedure tested
- [ ] Application code ready for user_id parameter

---

## Deployment Steps

### Step 1: Copy Migration to Container

```bash
# Copy migration file to container
docker cp docker/mcp-servers/conport/migrations/003_multi_tenancy_foundation.sql \
  mcp-conport:/tmp/003_multi_tenancy_foundation.sql
```

### Step 2: Connect to Database

```bash
# Get database connection info
docker exec mcp-conport env | grep DATABASE_URL

# Expected: postgresql://dopemux_age:password@dopemux-postgres-age:5432/dopemux_knowledge_graph
```

### Step 3: Execute Migration

```bash
# Execute migration (Phases A-C)
docker exec mcp-conport sh -c '
  export PGPASSWORD=dopemux_age_dev_password
  psql -h dopemux-postgres-age -U dopemux_age -d dopemux_knowledge_graph \
    -f /tmp/003_multi_tenancy_foundation.sql
'
```

### Step 4: Validate Migration

```bash
# Check user_id columns exist
docker exec mcp-conport sh -c '
  export PGPASSWORD=dopemux_age_dev_password
  psql -h dopemux-postgres-age -U dopemux_age -d dopemux_knowledge_graph -c "
    SELECT column_name FROM information_schema.columns
    WHERE table_name = '\''decisions'\'' AND column_name = '\''user_id'\'';
  "
'

# Count decisions with default user
docker exec mcp-conport sh -c '
  export PGPASSWORD=dopemux_age_dev_password
  psql -h dopemux-postgres-age -U dopemux_age -d dopemux_knowledge_graph -c "
    SELECT COUNT(*) FROM decisions WHERE user_id = '\''default'\'';
  "
'
# Expected: 310+ decisions
```

---

## Rollback Procedure

If migration fails or issues detected:

```bash
# Quick rollback
docker exec mcp-conport sh -c '
  export PGPASSWORD=dopemux_age_dev_password
  psql -h dopemux-postgres-age -U dopemux_age -d dopemux_knowledge_graph -c "
    ALTER TABLE decisions DROP COLUMN IF EXISTS user_id;
    ALTER TABLE progress_entries DROP COLUMN IF EXISTS user_id;
    ALTER TABLE workspace_contexts DROP COLUMN IF EXISTS user_id;
    ALTER TABLE session_snapshots DROP COLUMN IF EXISTS user_id;
    ALTER TABLE custom_data DROP COLUMN IF EXISTS user_id;
    DROP TABLE IF EXISTS user_workspace_access;
    DROP TABLE IF EXISTS workspaces;
    DROP TABLE IF EXISTS users;
  "
'
```

---

## Post-Deployment Validation

### Test 1: Query Performance
```sql
-- Before (v1):
SELECT * FROM decisions WHERE workspace_id = 'xxx' LIMIT 10;

-- After (v2):
SELECT * FROM decisions
WHERE user_id = 'default' AND workspace_id = 'xxx'
LIMIT 10;

-- Should be same or better performance
```

### Test 2: Data Integrity
```sql
-- All decisions should have user_id
SELECT COUNT(*) FROM decisions WHERE user_id IS NULL;
-- Expected: 0

-- All should be 'default' after migration
SELECT COUNT(*) FROM decisions WHERE user_id = 'default';
-- Expected: 310+
```

### Test 3: New Tables Created
```sql
SELECT * FROM users WHERE id = 'default';
-- Expected: 1 row

SELECT COUNT(*) FROM workspaces;
-- Expected: Number of distinct workspace_ids

SELECT COUNT(*) FROM user_workspace_access;
-- Expected: Same as workspaces (default user has access to all)
```

---

## Next Phase: Update Application Code

After migration validated, update ConPort MCP server:

```python
# Add user_id parameter (default for backward compatibility)
async def log_decision(
    workspace_id: str,
    summary: str,
    rationale: str,
    user_id: str = 'default'  # NEW parameter
):
    await db.execute(
        "INSERT INTO decisions (workspace_id, user_id, summary, rationale) ...",
        workspace_id, user_id, summary, rationale
    )
```

---

## Monitoring

After deployment, monitor:
- Query performance (should stay <200ms)
- No NULL user_id values appearing
- User workspace access working
- No permission errors

---

**Status**: Ready to execute when infrastructure accessible
**Risk**: LOW (tested SQL, rollback ready)
**Impact**: HIGH (unlocks multi-user Dopemux)
