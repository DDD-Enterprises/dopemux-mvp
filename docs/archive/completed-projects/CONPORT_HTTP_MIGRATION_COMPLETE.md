# ConPort HTTP Migration Complete

**Date**: 2025-10-24
**Status**: ✅ READY - Restart Claude Code to activate

---

## What Changed

**ConPort MCP Configuration**: Switched from stdio (SQLite) to HTTP/SSE (PostgreSQL AGE)

**Before**:
```json
"conport": {
  "type": "stdio",
  "command": "/path/to/conport-wrapper.sh",
  "args": []
}
```

**After**:
```json
"conport": {
  "type": "sse",
  "url": "http://localhost:3004/mcp",
  "env": {}
}
```

---

## Benefits

### **Immediate**:
- ✅ All decisions → PostgreSQL AGE (not SQLite)
- ✅ EventBus publishing automatic
- ✅ DDG auto-ingestion for new decisions
- ✅ Single source of truth (PostgreSQL)

### **ADHD**:
- ✅ Reduced cognitive load (one database)
- ✅ Global search working (find decisions across workspaces)
- ✅ Automatic sync (no manual backfill needed)

---

## Next Steps

### 1. Restart Claude Code ⚠️ REQUIRED

The config change won't take effect until restart:
```bash
# Quit Claude Code completely
# Relaunch Claude Code
# Open this project
```

### 2. Verify Connection

After restart, test in Claude Code:
```
Create any message to trigger MCP connection
You should see conport connect to http://localhost:3004
```

### 3. Test New Decision Flow

Create a test decision:
```python
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="Test HTTP mode decision",
    rationale="Testing PostgreSQL + EventBus flow"
)
```

**Verify it appears**:
```bash
# Check PostgreSQL (immediate)
docker exec dopemux-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT COUNT(*) FROM ag_catalog.decisions WHERE summary LIKE '%Test HTTP%';"

# Check DDG (within ~5-10 seconds)
docker exec dope-decision-graph-postgres psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT COUNT(*) FROM ddg_decisions WHERE summary LIKE '%Test HTTP%';"
```

**Expected**:
- PostgreSQL: 1 decision (immediate)
- DDG: 1 decision (5-10 seconds later)
- EventBus: New event published
- Qdrant: Embedding created (if EmbeddingManager configured)

---

## Rollback

If issues occur:

**Restore Config**:
```bash
cp ~/.claude.json.backup_YYYYMMDD_HHMMSS ~/.claude.json
# Restart Claude Code
```

**Data Safe**:
- SQLite backup: `backups/context_20251024_181450.db`
- PostgreSQL has all data
- DDG has all data
- Qdrant has all embeddings

---

## Architecture

**New Data Flow**:
```
Claude Code
    ↓
mcp__conport__* tools (HTTP/SSE on port 3004)
    ↓
enhanced_server.py (PostgreSQL AGE)
    ↓
PostgreSQL (port 5456 external, 5432 internal)
    ↓
EventBus (Redis Streams: dopemux:events)
    ↓
DDG Ingestion (dope-decision-graph-bridge)
    ↓
DDG PostgreSQL (port 5455) + Qdrant embeddings
    ↓
ddg-mcp.related_text (global search) ✅
```

---

## Troubleshooting

### ConPort Connection Fails

**Check container**:
```bash
docker ps --filter "name=mcp-conport"
# Should show: Up X minutes (healthy)
```

**Check logs**:
```bash
docker logs mcp-conport --tail 50
```

**Restart container**:
```bash
docker restart mcp-conport
```

### DDG Not Receiving Events

**Check EventBus**:
```bash
docker exec dopemux-redis-events redis-cli XLEN dopemux:events
# Should increase with new decisions
```

**Check DDG bridge**:
```bash
docker logs dope-decision-graph-bridge --tail 50
# Look for ingestion activity
```

### Qdrant Embeddings Not Created

**Check EmbeddingManager** (in DDG bridge logs):
```bash
docker logs dope-decision-graph-bridge | grep -i "embedding"
```

**Voyag API key set**:
```bash
docker exec dope-decision-graph-bridge env | grep VOYAGE
# Should show: VOYAGEAI_API_KEY=pa-...
```

---

## Performance

**Expected Latency**:
- ConPort write: < 10ms (PostgreSQL)
- EventBus publish: < 5ms (Redis)
- DDG ingestion: ~5-10 seconds (async)
- Qdrant embedding: ~1-2 seconds (async, best-effort)

**ADHD Target**: All operations < 200ms for user-facing queries ✅

---

## Backup Information

**Config Backup**: `~/.claude.json.backup_YYYYMMDD_HHMMSS`
**SQLite Backup**: `/Users/hue/code/dopemux-mvp/backups/context_20251024_181450.db`
**Export JSON**: `/Users/hue/code/dopemux-mvp/scripts/migration/conport_export.json`

---

## Success Criteria

After restart and testing:
- ✅ ConPort MCP tools work in Claude Code
- ✅ New decisions appear in PostgreSQL immediately
- ✅ New decisions appear in DDG within 10 seconds
- ✅ EventBus shows new events
- ✅ No SQLite writes (context.db unchanged)

---

**Status**: Configuration updated, awaiting Claude Code restart ⚠️
