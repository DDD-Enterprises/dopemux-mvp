---
id: MCP_STARTUP_FIXES
title: Mcp_Startup_Fixes
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# MCP Startup Fixes - 2026-02-03

## Issues Fixed

### P0 - Validation Breaking (CRITICAL)
**Problem**: docker-compose.yml had duplicate networks causing validation failures:
- `plane-coordinator`: `dopemux-network` listed twice (lines 270-271)
- `leantime-bridge`: `dopemux-network` listed twice (lines 232, 234)
- `activity-capture`: `dopemux-network` listed THREE times (lines 566-568)

**Impact**: `docker compose config` failed validation, preventing container creation. Scripts continued anyway due to `|| true`, masking the real failure.

**Fix**: Removed duplicate network entries. All services now have unique network list.

**Verification**:
```bash
cd docker/mcp-servers
docker compose config >/dev/null && echo "OK: compose valid"
```

### P0 - Script Masking Failures
**Problem**: `docker-compose up ... || true` swallowed critical errors.

**Fix**: Removed `|| true` from critical service startup. Script now fails fast on compose errors.

### P1 - Leantime Dev Loop Integration
**Problem**:
- Leantime stack never started (lives in `docker/leantime/`)
- Health check always failed, blocking MCP startup
- No way to disable Leantime check for non-PM workflows

**Fix**:
1. Added `ENABLE_LEANTIME` environment variable (default: 0)
2. When `ENABLE_LEANTIME=1`:
   - Start Leantime stack first: `(cd ../leantime && docker compose up -d --build)`
   - Run health check
   - Continue even if health check fails (warning only)
3. When `ENABLE_LEANTIME=0`:
   - Skip Leantime startup
   - Skip health check

**Usage**:
```bash
# With Leantime (PM integration)
ENABLE_LEANTIME=1 ./start-all-mcp-servers.sh

# Without Leantime (dev mode)
./start-all-mcp-servers.sh
```

### P2 - Unified Project Name
**Problem**: Multiple compose files created separate Docker Desktop groups, duplicate redis/postgres instances.

**Fix**: Set `COMPOSE_PROJECT_NAME=dopemux` at script start. All compose calls now use same project.

**Expected Behavior**:
- One "dopemux" project in Docker Desktop
- Shared networks: `dopemux-network`, `leantime-net`
- No duplicate infrastructure services

## Networks Architecture

### External Networks (shared across stacks)
```yaml
networks:
  dopemux-network:
    external: true
    name: dopemux-network
  leantime-net:
    external: true
    name: leantime-net
```

**Created by**: Installer script (`install.sh`)

**Purpose**:
- `dopemux-network`: Main MCP server communication
- `leantime-net`: Leantime ↔ leantime-bridge communication

### Service Network Assignments

**Single network** (dopemux-network only):
- context7, pal, mas-sequential-thinking
- task-master-ai, mcp-client, task-orchestrator
- serena, dopemux-gpt-researcher, exa, dope-context
- gptr-mcp, desktop-commander
- redis-primary, qdrant
- **plane-coordinator** (was duplicate)
- **activity-capture** (was triplicate)

**Dual network** (dopemux-network + leantime-net):
- **leantime-bridge** (was duplicate) - bridges PM plane to cognitive plane

**Host network** (special case):
- litellm - uses `network_mode: host` to access localhost:5432 postgres

## Verification Steps

### 1. Validate Compose Config
```bash
cd docker/mcp-servers
docker compose config >/dev/null
echo $?  # Should be 0
```

### 2. Test Startup (No Leantime)
```bash
cd docker/mcp-servers
./start-all-mcp-servers.sh
```

**Expected**:
- ✅ Compose validation passes
- ℹ️ Skipping Leantime (ENABLE_LEANTIME=0)
- ✅ Critical servers start (context7, litellm, conport)
- ✅ No duplicate network errors

### 3. Test Startup (With Leantime)
```bash
cd docker/mcp-servers
ENABLE_LEANTIME=1 ./start-all-mcp-servers.sh
```

**Expected**:
- ✅ Leantime stack starts first
- ✅ Leantime health check runs
- ✅ MCP servers start
- ✅ leantime-bridge connects to both networks

### 4. Check Docker Desktop Groups
```bash
docker compose ls
```

**Expected**: One "dopemux" project, not multiple groups

### 5. Check Network Membership
```bash
docker network inspect dopemux-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

**Expected**: All MCP services listed, no duplicates

## Next Steps (Not Implemented)

### Multi-Instance Leantime (Future)
**Not recommended now** - Leantime is singleton PM system. If multi-worktree PM needed, drive from Dopemux instance allocator, not per-instance Leantime.

## Implemented Features

### ✅ /info Endpoint for leantime-bridge
**Status**: IMPLEMENTED (2026-02-03)

**Endpoint**: `GET http://localhost:3015/info`

**Features**:
- Service discovery metadata (name, version, description)
- Real-time Leantime health status
- MCP connection configuration (SSE endpoints)
- Architecture metadata (plane, role, priority)
- Tool count and capabilities

**Documentation**: See `leantime-bridge/INFO_ENDPOINT.md`

**Testing**:
```bash
# Manual test
curl http://localhost:3015/info | jq

# Automated test
cd docker/mcp-servers/leantime-bridge
python test_info_endpoint.py
```

**Response Example**:
```json
{
  "name": "leantime-bridge",
  "version": "1.0.0",
  "leantime": {
    "url": "http://leantime:80",
    "status": "healthy",
    "rate_limit_seconds": 1.0
  },
  "mcp": {
    "protocol": "sse",
    "endpoints": {
      "sse": "http://localhost:3015/sse",
      "health": "http://localhost:3015/health",
      "info": "http://localhost:3015/info"
    }
  },
  "metadata": {
    "plane": "pm_plane",
    "tools_count": 8
  }
}
```

## Files Modified

- ✅ `docker/mcp-servers/docker-compose.yml` - Fixed duplicate networks
- ✅ `docker/mcp-servers/start-all-mcp-servers.sh` - Added validation, Leantime gate, project name
- ✅ `docker/mcp-servers/leantime-bridge/leantime_bridge/http_server.py` - Enhanced /info endpoint

## Files Created

- ✅ `docker/mcp-servers/MCP_STARTUP_FIXES.md` - This document
- ✅ `docker/mcp-servers/QUICK_FIX_SUMMARY.md` - Quick reference
- ✅ `docker/mcp-servers/test-fixes.sh` - Automated verification
- ✅ `docker/mcp-servers/show-network-topology.sh` - Network topology viewer
- ✅ `docker/mcp-servers/leantime-bridge/INFO_ENDPOINT.md` - /info endpoint documentation
- ✅ `docker/mcp-servers/leantime-bridge/test_info_endpoint.py` - /info endpoint test

## Breaking Changes

**None** - All changes are backward compatible. Default behavior unchanged (Leantime disabled).

## Environment Variables

### New
- `ENABLE_LEANTIME` (default: 0) - Start Leantime stack and run health checks

### Existing (unchanged)
- `LEANTIME_HEALTH_URL` (default: http://localhost:8080/index.php)
- `LEANTIME_HEALTH_EXPECT` (default: "Dopemux plugin register.php loaded successfully")
- `COMPOSE_PROJECT_NAME` (default: dopemux)

---

**Author**: AI Assistant
**Date**: 2026-02-03
**Issue**: Docker Compose validation failures, Leantime startup race, script masking errors
