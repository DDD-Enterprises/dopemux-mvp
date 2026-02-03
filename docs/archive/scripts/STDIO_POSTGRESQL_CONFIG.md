---
id: STDIO_POSTGRESQL_CONFIG
title: Stdio_Postgresql_Config
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Configuring stdio conport-mcp for PostgreSQL

**Current Situation**:
- stdio conport-mcp uses SQLite (context_portal/context.db)
- SQLite backend has NO EventBus integration
- New decisions go to SQLite only, NOT to DDG

**Problem**:
Future decisions logged via `mcp__conport__log_decision` won't appear in DDG global search.

---

## Solution Options

### Option A: Switch to enhanced_server.py HTTP (Recommended)

Update `~/.claude.json` conport configuration:

**Before** (stdio to SQLite):
```json
"conport": {
  "type": "stdio",
  "command": "/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/conport-wrapper.sh",
  "args": [],
  "env": {}
}
```

**After** (HTTP to PostgreSQL + EventBus):
```json
"conport": {
  "type": "sse",
  "url": "http://localhost:3004"
}
```

**Benefits**:
- ✅ Uses PostgreSQL AGE (port 5456 via enhanced_server.py)
- ✅ Publishes to EventBus automatically
- ✅ DDG ingests all new decisions
- ✅ No code changes needed

**Requirements**:
- enhanced_server.py must be running on port 3004
- Start: `docker start mcp-conport` or via docker-compose

---

### Option B: Add PostgreSQL Backend to stdio conport-mcp

**Code Changes Needed**:
1. Update `services/conport/src/context_portal_mcp/db/database.py`
2. Add PostgreSQL support alongside SQLite
3. Use DATABASE_URL env var to choose backend
4. Add EventBus publishing to all write operations

**Complexity**: High (significant refactoring)
**Time**: 4-6 hours
**Benefit**: Keep stdio mode

---

### Option C: Hybrid Dual-Write

Modify conport-wrapper.sh to:
1. Call stdio conport-mcp (SQLite)
2. Also POST to enhanced_server.py HTTP API
3. Dual-write to both backends

**Pros**: Backward compatible
**Cons**: Eventual consistency issues, complexity

---

## Recommended Path: Option A

**Steps**:
1. Ensure `mcp-conport` container running
2. Update `~/.claude.json` to use SSE on port 3004
3. Restart Claude Code
4. Test: Create new decision
5. Verify: Decision appears in DDG within seconds

**Verification**:
```bash
# Create test decision in Claude Code
mcp__conport__log_decision(workspace_id="...", summary="Test", ...)

# Check PostgreSQL (immediate)
docker exec dopemux-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT COUNT(*) FROM ag_catalog.decisions WHERE summary LIKE '%Test%';"

# Check DDG (within ~5 seconds)
docker exec dope-decision-graph-postgres psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT COUNT(*) FROM ddg_decisions WHERE summary LIKE '%Test%';"
```

---

## Current Workaround

**For Now**:
- SQLite decisions: Manually backfill to DDG periodically
- PostgreSQL decisions: Auto-sync via EventBus ✅

**Long-term**:
- Switch to Option A (HTTP/SSE mode)
- All future decisions auto-sync to DDG

---

## Migration Impact

**What Works**:
- ✅ Historical data migrated (1495 decisions in DDG)
- ✅ Qdrant search operational (1495 embeddings)
- ✅ DDG ingestion pipeline working

**What Needs Config**:
- ⏳ stdio conport-mcp → PostgreSQL switch
- ⏳ EventBus auto-publishing for new decisions

**Timeline**: Can be done anytime (DDG works with existing data now)
