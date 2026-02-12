---
id: adr-214
title: MCP Stack Leantime Decoupling via Compose Overlay
type: adr
owner: system
created: 2026-02-12
status: accepted
tags:
- mcp
- docker
- leantime
- deployment
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: MCP Stack Leantime Decoupling via Compose Overlay (adr) for dopemux documentation
  and developer workflows.
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-214: MCP Stack Leantime Decoupling via Compose Overlay

## Status
**Accepted** - 2026-02-12

## Context

The MCP Docker stack (`docker/mcp-servers/docker-compose.yml`) was blocked from starting due to a missing external network dependency. The compose file declared `leantime-net` as a top-level external network, and Docker validates ALL external networks before starting ANY services.

### Problem
- **External network coupling**: `leantime-net` was declared external in main compose
- **Validation-first behavior**: Docker validates all externals before service creation
- **Stack blocked**: Missing `leantime-net` prevented entire 12-service MCP stack from starting
- **Fragile deployment**: Clean machines, CI environments, new team members all hit this blocker
- **100% blast radius**: One missing network blocked 100% of services

### Evidence
```bash
$ docker compose -f docker/mcp-servers/docker-compose.yml up -d
network leantime-net declared as external, but could not be found
# Exit code: 1
# Result: Zero services started
```

### Root Cause
Docker's compose validation happens before any service creation. When a top-level external network is missing, the entire compose operation fails with no partial success possible.

## Decision

**Adopt a two-file compose architecture**: Standalone (default) + Linked overlay (opt-in)

### Architecture

#### 1. Standalone Mode (Default)
**File**: `docker-compose.yml`
- Removed `leantime-net` network declaration
- Removed `leantime-bridge` service
- **Services**: 12 core MCP servers (ConPort, Serena, LiteLLM, etc.)
- **Networks**: `dopemux-network` only
- **Can start on**: Clean machines, CI, any environment without Leantime

#### 2. Linked Mode (Opt-In)
**File**: `docker-compose.leantime.yml` (overlay)
- Adds `leantime-bridge` service
- Declares `leantime-net` as external
- **Usage**: `docker compose -f docker-compose.yml -f docker-compose.leantime.yml up -d`
- **Prerequisite**: Leantime stack running OR `leantime-net` exists

### Usage Patterns

**Standalone (default)**:
```bash
docker compose -f docker/mcp-servers/docker-compose.yml up -d
# ✅ 12 services start without Leantime dependency
```

**Linked (opt-in)**:
```bash
# Requires: docker network ls | grep leantime-net
docker compose -f docker/mcp-servers/docker-compose.yml \
               -f docker/mcp-servers/docker-compose.leantime.yml up -d
# ✅ 13 services including leantime-bridge (if leantime-net exists)
# ❌ Explicit error if leantime-net missing (error isolated to overlay)
```

### Dopemux CLI Integration
The `dopemux mcp start-all` command:
- Runs from `docker/mcp-servers/` directory
- Uses `docker compose` (defaults to `docker-compose.yml`)
- **Automatically uses standalone mode** ✅
- Leantime integration via `ENABLE_LEANTIME=1` environment variable

### Script Updates
Modified `start-all-mcp-servers.sh`:
- **Line 140**: Create `leantime-net` only if `ENABLE_LEANTIME=1` (not unconditionally)
- **Line 89**: Create `leantime-bridge/.env` only if `ENABLE_LEANTIME=1`
- **Line 356-360**: Start `leantime-bridge` only if `ENABLE_LEANTIME=1`

## Consequences

### Positive
- ✅ **MCP stack starts independently**: No Leantime dependency for core functionality
- ✅ **Explicit opt-in**: Leantime integration is intentional, not accidental
- ✅ **Error isolation**: Missing `leantime-net` only affects linked mode
- ✅ **Zero blast radius**: One missing network no longer blocks all services
- ✅ **CI/CD friendly**: Clean environments work out-of-box
- ✅ **Team onboarding**: New developers can start MCP stack immediately
- ✅ **Deterministic**: No "works on my machine" scenarios due to external network state

### Neutral
- ⚪ **Two-file maintenance**: Must keep overlay in sync with main compose
- ⚪ **Explicit linking**: Leantime users must use overlay or set `ENABLE_LEANTIME=1`

### Negative
- ⚠️ **Documentation burden**: Must explain standalone vs linked modes
  - *Mitigation*: Comprehensive README with examples created

## Implementation

### Files Modified
1. **`docker/mcp-servers/docker-compose.yml`** (standalone)
   - Removed: `leantime-net` network definition
   - Removed: `leantime-bridge` service (37 lines)
   - Removed: `mcp_leantime_bridge_data` and `mcp_leantime_bridge_logs` volumes

2. **`docker/mcp-servers/docker-compose.leantime.yml`** (NEW - overlay)
   - Added: Complete `leantime-bridge` service definition
   - Added: `leantime-net` external network
   - Added: Bridge service volumes

3. **`docker/mcp-servers/start-all-mcp-servers.sh`**
   - Line 140: Conditional `leantime-net` creation
   - Line 89: Conditional `leantime-bridge/.env` placeholder
   - Line 356-360: Conditional bridge startup

4. **`docker/mcp-servers/README.md`** (NEW)
   - Complete documentation of standalone vs linked usage
   - Service reference table (14 services including optional bridge)
   - Troubleshooting guide
   - Preflight checks for linked mode

### Validation
- ✅ Standalone boot: 12 services running (exit code 0)
- ✅ Linked mode error: Explicit network error when Leantime missing
- ✅ Dopemux CLI: Uses standalone compose by default
- ✅ Config validation: `docker compose config` succeeds

## Alternatives Considered

### 1. Docker Compose Profiles
**Approach**: Use `profiles: [leantime]` on bridge service
```yaml
leantime-bridge:
  profiles: [leantime]
  networks:
    - leantime-net  # Still external in top-level networks
```
**Rejected**: Docker still validates top-level external networks regardless of profiles. Blast radius remains 100%.

### 2. Manual Network Creation
**Approach**: Create `leantime-net` in startup script unconditionally
**Implemented in**: `start-all-mcp-servers.sh` (line 140)
**Limitation**: Creates unused networks on systems not using Leantime. Overlay approach is cleaner.

### 3. Remove Leantime Integration
**Approach**: Delete bridge service entirely
**Rejected**: Leantime integration is valuable for PM plane users. Opt-in overlay preserves functionality while fixing coupling.

## Related Decisions
- **ADR-207**: Task Orchestrator capabilities (mentions Leantime integration)
- **ADR-208**: MCP config drift prevention
- **ADR-012**: MCP Integration Patterns (original MCP architecture)

## Verification Commands

### Standalone Mode
```bash
docker compose -f docker/mcp-servers/docker-compose.yml up -d
docker compose -f docker/mcp-servers/docker-compose.yml ps
# Expected: 12 services running
```

### Linked Mode (Leantime Running)
```bash
docker compose -f docker/leantime/docker-compose.yml up -d  # Start Leantime first
docker compose -f docker/mcp-servers/docker-compose.yml \
               -f docker/mcp-servers/docker-compose.leantime.yml up -d
docker compose -f docker/mcp-servers/docker-compose.yml \
               -f docker/mcp-servers/docker-compose.leantime.yml ps
# Expected: 13 services including leantime-bridge
```

### Linked Mode (Leantime Not Running)
```bash
docker compose -f docker/mcp-servers/docker-compose.yml \
               -f docker/mcp-servers/docker-compose.leantime.yml up -d
# Expected: Error "network leantime-net declared as external, but could not be found"
# Standalone services unaffected
```

## Notes
- This pattern can be extended for other optional integrations (e.g., monitoring, tracing)
- The overlay approach follows Docker Compose best practices for environment-specific configuration
- External network validation behavior is a Docker Compose limitation, not a bug

## References
- Docker Compose documentation: [Extending services](https://docs.docker.com/compose/extends/)
- Task Packet: DOCKER-FIX-LEANTIME-01 (2026-02-12)
- Implementation: 4 commits completed successfully
