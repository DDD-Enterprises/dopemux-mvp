---
id: WEEK-7-INTEGRATION-BRIDGE-COMPLETION-PLAN
title: Week 7 Integration Bridge Completion Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Week 7 Integration Bridge Completion Plan (explanation) for dopemux documentation
  and developer workflows.
---
# Week 7: DopeconBridge Completion Plan
**Effort**: 12 hours total (4-6h bridge + 6-8h migration)
**Priority**: HIGH (eliminates architecture violations)
**Prerequisites**: Security fixes deployed and validated

---

## Overview

Complete the DopeconBridge by implementing the missing MCP→ConPort integration layer, then migrate services from direct SQLite access to proper HTTP API calls.

**Current State**: Bridge is 80% complete (authority, endpoints exist, but custom_data are stubs)
**Target State**: Full cross-plane coordination with all services using bridge

---

## Phase 1: Complete DopeconBridge (4-6 hours)

### Task 1.1: Add MCP Client to Bridge (2h)

**File**: `services/mcp-dopecon-bridge/mcp_client.py` (NEW)

```python
"""
MCP Client for DopeconBridge.
Connects to ConPort MCP server to enable custom_data persistence.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional

# This would use MCP SDK or direct HTTP to ConPort MCP server
class ConPortMCPClient:
    """Client for calling ConPort MCP tools from DopeconBridge"""

    def __init__(self, conport_url: str = "http://localhost:3004"):
        self.conport_url = conport_url
        self.workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

    async def log_custom_data(
        self,
        category: str,
        key: str,
        value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save custom data to ConPort.

        Implementation options:
        1. HTTP POST to ConPort MCP server (if exposed)
        2. Direct PostgreSQL AGE write (if bridge has DB access)
        3. MCP stdio client (if running in same process)
        """
        # Option 2: Direct PostgreSQL (bridge already has age_client.py access!)
        try:
            # Import existing ConPort query classes
            import sys
            sys.path.insert(0, '../conport_kg')
            from queries.overview import OverviewQueries

            # Use existing database connection
            # (Bridge already connects to PostgreSQL AGE)

            # SQL: INSERT INTO custom_data table
            # Return success with metadata

            return {
                "success": True,
                "category": category,
                "key": key,
                "stored_at": "conport_kg_database"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_custom_data(
        self,
        category: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve custom data from ConPort"""
        try:
            # SQL: SELECT FROM custom_data WHERE category = ?
            # Return list of results

            return []  # Placeholder until implemented

        except Exception as e:
            return []
```

**Effort**: 2 hours
- Write MCP client class (1h)
- Test connection to ConPort database (30min)
- Error handling and retries (30min)

---

### Task 1.2: Wire custom_data Endpoints (2h)

**File**: `services/mcp-dopecon-bridge/kg_endpoints.py`

**Change Line 357-363** (save_custom_data):
```python
# BEFORE (STUB):
@router.post("/custom_data")
async def save_custom_data(request: CustomDataRequest, ...):
    # For now, return success (bridge will implement actual MCP call)
    return {"success": True, ...}  # STUB!

# AFTER (WORKING):
from mcp_client import ConPortMCPClient

mcp_client = ConPortMCPClient()  # Initialize globally

@router.post("/custom_data")
async def save_custom_data(request: CustomDataRequest, ...):
    """Save custom data to ConPort via MCP"""
    if x_source_plane != "cognitive_plane":
        raise HTTPException(403, "Requires cognitive_plane authority")

    try:
        result = await mcp_client.log_custom_data(
            category=request.category,
            key=request.key,
            value=request.value
        )

        if not result["success"]:
            raise HTTPException(500, f"MCP call failed: {result.get('error')}")

        return result

    except Exception as e:
        raise HTTPException(500, f"Save failed: {str(e)}")
```

**Change Line 387-392** (get_custom_data):
```python
# BEFORE (STUB):
@router.get("/custom_data")
async def get_custom_data(...):
    return {"data": [], "count": 0}  # STUB!

# AFTER (WORKING):
@router.get("/custom_data")
async def get_custom_data(...):
    """Retrieve custom data from ConPort via MCP"""
    if x_source_plane not in ["pm_plane", "cognitive_plane"]:
        raise HTTPException(403, "Invalid source plane")

    try:
        data = await mcp_client.get_custom_data(
            category=category,
            key=key,
            limit=limit
        )

        return {
            "data": data,
            "count": len(data),
            "category": category
        }

    except Exception as e:
        raise HTTPException(500, f"Query failed: {str(e)}")
```

**Effort**: 2 hours
- Wire both endpoints (1h)
- Test with curl (30min)
- Error handling (30min)

---

### Task 1.3: Integration Testing (1-2h)

```bash
# Test custom_data POST
curl -X POST http://localhost:3016/custom_data \
  -H "X-Source-Plane: cognitive_plane" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "/Users/test",
    "category": "test_data",
    "key": "test_key",
    "value": {"message": "test"}
  }'

# Expected: {"success": true, ...}

# Test custom_data GET
curl "http://localhost:3016/custom_data?workspace_id=/Users/test&category=test_data" \
  -H "X-Source-Plane: cognitive_plane"

# Expected: {"data": [{...}], "count": 1}

# Test authority enforcement
curl -X POST http://localhost:3016/custom_data \
  -H "X-Source-Plane: pm_plane" \
  ...

# Expected: 403 Forbidden (PM plane can't write)
```

**Effort**: 1-2 hours
- Manual endpoint testing (30min)
- Authority validation (30min)
- Error scenario testing (30-60min)

---

## Phase 2: Migrate Services (6-8 hours)

### Task 2.1: Create DopeconBridge HTTP Client (2h)

**File**: `src/integrations/bridge_client.py` (NEW, shared library)

```python
"""
DopeconBridge HTTP Client.
Used by services to call bridge instead of direct SQLite.
"""

import os
import aiohttp
from typing import Dict, Any, Optional

class DopeconBridgeClient:
    """HTTP client for DopeconBridge API"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "DOPECON_BRIDGE_URL",
            "http://localhost:3016"
        )
        self.source_plane = "cognitive_plane"  # Services are cognitive plane

    async def save_custom_data(
        self,
        category: str,
        key: str,
        value: Dict[str, Any],
        workspace_id: str
    ) -> Dict[str, Any]:
        """Save custom data via bridge"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/custom_data",
                json={
                    "workspace_id": workspace_id,
                    "category": category,
                    "key": key,
                    "value": value
                },
                headers={"X-Source-Plane": self.source_plane}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Bridge call failed: {resp.status}")
                return await resp.json()

    async def get_custom_data(
        self,
        category: str,
        workspace_id: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get custom data via bridge"""
        params = {
            "workspace_id": workspace_id,
            "category": category,
            "limit": limit
        }
        if key:
            params["key"] = key

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/custom_data",
                params=params,
                headers={"X-Source-Plane": self.source_plane}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Bridge call failed: {resp.status}")
                result = await resp.json()
                return result.get("data", [])
```

**Effort**: 2 hours (client implementation + testing)

---

### Task 2.2: Migrate ADHD Engine (2-3h)

**File**: `services/adhd_engine/conport_client.py`

**Change Strategy**: Replace direct SQLite with HTTP API calls

```python
# BEFORE (Direct SQLite):
class ConPortSQLiteClient:
    def __init__(self, db_path: str, workspace_id: str, read_only: bool = True):
        self.db_path = db_path  # Direct file access!
        # ...

    def write_custom_data(self, category, key, value):
        conn = self._get_connection(write_mode=True)  # Direct write!
        conn.execute("INSERT OR REPLACE INTO custom_data ...")

# AFTER (HTTP API):
from src.integrations.bridge_client import DopeconBridgeClient

class ConPortBridgeClient:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.bridge = DopeconBridgeClient()

    async def write_custom_data(self, category, key, value):
        result = await self.bridge.save_custom_data(
            category=category,
            key=key,
            value=value,
            workspace_id=self.workspace_id
        )
        return result["success"]
```

**Files to Update**:
1. `conport_client.py` - Replace with bridge client
2. `engine.py` - Update instantiation (if needed)
3. `main.py` - Verify no breaking changes

**Effort**: 2-3 hours
- Rewrite client (1-1.5h)
- Update callers (30min-1h)
- Testing (30min-1h)

---

### Task 2.3: Migrate ConPort Orchestrator (2-3h)

**File**: `services/conport_kg/orchestrator.py`

**Change Line 127** (currently TODO):
```python
# BEFORE:
if impl_decisions:
    print(f"   → Would publish decision.requires_implementation event")
    # TODO: Publish to DopeconBridge event bus

# AFTER:
if impl_decisions:
    await self.bridge_client.publish_event(
        event_type="decision.requires_implementation",
        payload={
            "decision_id": decision_id,
            "implementation_tasks": impl_decisions
        }
    )
```

**Effort**: 2-3 hours
- Add bridge client to orchestrator (1h)
- Wire all TODO integration points (1-1.5h)
- Testing (30min-1h)

---

### Task 2.4: Integration Testing (2h)

**End-to-End Flow Testing**:
```bash
# Test 1: ADHD Engine → Bridge → ConPort
# 1. ADHD Engine writes custom_data
# 2. Bridge receives HTTP call
# 3. Bridge calls ConPort (via MCP or direct DB)
# 4. Data persists in ConPort database

# Test 2: ConPort Orchestrator → Bridge → Event Bus
# 1. Orchestrator detects implementation decision
# 2. Publishes event to bridge
# 3. Bridge routes event
# 4. Verify event delivered

# Test 3: Authority Enforcement
# 1. Try PM plane write to custom_data
# 2. Should get 403 Forbidden
# 3. Try cognitive plane write
# 4. Should succeed

# Test 4: Error Scenarios
# 1. Bridge down, service fallback?
# 2. Database down, error handling?
# 3. Invalid requests, proper 4xx codes?
```

**Effort**: 2 hours (comprehensive validation)

---

## Implementation Timeline

### Day 1 (4-5h): Complete Bridge
- Morning (2h): Implement MCP client
- Afternoon (2-3h): Wire custom_data endpoints + test

**Checkpoint**: Bridge custom_data endpoints working ✅

### Day 2 (3-4h): Migrate ADHD Engine
- Morning (2-3h): Replace SQLite client with HTTP client
- Afternoon (1h): Test and validate

**Checkpoint**: ADHD Engine using bridge ✅

### Day 3 (3-4h): Migrate ConPort + Final Testing
- Morning (2-3h): Wire ConPort Orchestrator
- Afternoon (1-2h): End-to-end integration testing

**Checkpoint**: Full architecture compliance ✅

**Total**: 10-13 hours across 3 days

---

## Success Criteria

### DopeconBridge Complete When:
- [ ] MCP client implemented and tested
- [ ] custom_data POST actually saves to ConPort
- [ ] custom_data GET retrieves real data
- [ ] Authority enforcement validated (PM read-only, Cognitive full)
- [ ] Error handling robust (retry logic, fallbacks)

### Services Migrated When:
- [ ] ADHD Engine uses bridge HTTP API (not direct SQLite)
- [ ] ConPort Orchestrator publishes events to bridge
- [ ] No direct database access remains
- [ ] All services respect authority boundaries

### Architecture Compliant When:
- [ ] All cross-plane communication via bridge
- [ ] Authority matrix enforced
- [ ] No service-to-service direct DB writes
- [ ] Event bus properly utilized

---

## Risk Mitigation

**Risk 1: Bridge MCP Integration Complex**
- Mitigation: Use existing age_client.py from ConPort (bridge already has PostgreSQL AGE access)
- Fallback: Direct SQL writes from bridge (still better than service direct access)
- Testing: Incremental (test each method)

**Risk 2: Service Migration Breaks Things**
- Mitigation: Feature flag—keep old code, add bridge code, toggle via env var
- Testing: Run both paths in staging, compare results
- Rollback: Remove bridge calls, revert to direct access

**Risk 3: Performance Degradation**
- Mitigation: Bridge adds one HTTP hop (~2-5ms)
- Monitoring: Measure latency before/after
- Optimization: Add caching at bridge layer if needed

---

## Alternative: Incremental Migration

**Week 7**: Complete bridge only (4-6h)
**Week 8**: Migrate ADHD Engine (2-3h)
**Week 9**: Migrate ConPort Orchestrator (2-3h)
**Week 10**: Integration testing (2h)

**Total**: Same 10-13h, spread over 4 weeks (less risky)

---

## Verification Plan

**After Week 7 Completion**:

```bash
# 1. Verify bridge endpoints work
curl -X POST http://localhost:3016/custom_data \
  -H "X-Source-Plane: cognitive_plane" \
  -d '{"workspace_id": "...", "category": "test", "key": "k", "value": {"v":1}}'

# 2. Verify data persisted
curl "http://localhost:3016/custom_data?workspace_id=...&category=test" \
  -H "X-Source-Plane: cognitive_plane"
# Should return the data we saved

# 3. Verify services using bridge
# Check ADHD Engine logs for "DopeconBridge" or HTTP calls
# Check no more direct SQLite writes

# 4. Verify authority enforcement
# PM plane can't write, cognitive plane can

# 5. Performance check
# Bridge calls < 50ms p95
```

---

## Documentation Updates Post-Week-7

**Files to Update**:
1. `.claude/CLAUDE.md` - Update authority routing (bridge now complete)
2. `services/mcp-dopecon-bridge/README.md` - Remove "stub" notes
3. `services/adhd_engine/README.md` - Document bridge integration
4. `docs/94-architecture/` - Update architecture diagrams

**Create**:
5. ADR-207: DopeconBridge Completion (document decisions made)
6. Integration guide: How to use bridge for new services

---

## Success Metrics

**Before Week 7**:
- Architecture compliance: 3/10
- Services bypassing bridge: 2
- Direct DB writes: 1 (ADHD Engine)

**After Week 7**:
- Architecture compliance: 9/10 ✅
- Services using bridge: All
- Direct DB writes: 0 ✅
- Authority violations: 0 ✅

---

**Week 7 Plan Ready** ✅
**Effort**: 10-13 hours
**Value**: Full architecture compliance, elimination of violations
**Risk**: LOW (incremental, reversible, well-planned)
