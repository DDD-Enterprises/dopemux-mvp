---
id: COMPLETION_CHECKLIST
title: Completion_Checklist
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Completion_Checklist (explanation) for dopemux documentation and developer
  workflows.
---
# Multi-Workspace Implementation - Completion Checklist

**Created**: 2025-11-13
**Purpose**: Document what's needed to FULLY complete each service

---

## Current Status: Infrastructure + Wrappers

We have:
- ✅ Shared utilities (complete)
- ✅ Documentation (complete)
- ✅ Wrappers/support modules for 5 services
- ⚠️ **NOT fully integrated into core service logic**

---

## Service 1: dope-context ✅ COMPLETE

### Current State
- ✅ Fully integrated into MCP server
- ✅ All functions support workspace_paths
- ✅ Tests passing (10/10)
- ✅ Autonomous indexing daemon working
- ✅ Production ready

### Remaining Work
**NONE** - This is our reference implementation

**Status**: 100% Complete ✅

---

## Service 2: serena - CODE GRAPH 🟡 70% Complete

### Current State
- ✅ Wrapper created (`v2/multi_workspace_wrapper.py`)
- ✅ Tests for wrapper (9/9 passing)
- ❌ NOT integrated into main MCP server
- ❌ MCP tools don't expose multi-workspace params

### What's Missing

#### 1. Integrate into MCP Server (2-3 hours)
**File**: `services/serena/v2/mcp_server.py`

**Need to modify** (~20 MCP tool functions):
```python
# Current:
async def find_symbol_tool(self, query: str, ...) -> str:
    # Uses self.workspace only

# Needed:
async def find_symbol_tool(
    self,
    query: str,
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    ...
) -> str:
    # Use wrapper for multi-workspace
    if workspace_paths or workspace_path:
        from multi_workspace_wrapper import SerenaMultiWorkspace
        wrapper = SerenaMultiWorkspace()
        return await wrapper.find_symbol_multi(
            query, workspace_path=workspace_path,
            workspace_paths=workspace_paths, ...
        )
    # Else use self.workspace (backward compat)
```

**Functions to modify**:
1. `find_symbol_tool` (line ~1499)
1. `get_context_tool` (line ~1814)
1. `find_references_tool` (line ~1913)
1. `analyze_complexity_tool` (line ~2126)
1. `get_reading_order_tool` (line ~2411)
1. `find_relationships_tool` (line ~2493)
1. `get_navigation_patterns_tool` (line ~2586)
1. `find_similar_code_tool` (line ~4493)
1. `find_test_file_tool` (line ~4654)
1. `get_unified_complexity_tool` (line ~4753)

**Estimated**: 2-3 hours

#### 2. Per-Workspace LSP Clients (1-2 hours)
**Issue**: Current `SimpleLSPClient` uses single workspace

**Solution**: Modify wrapper to create LSP client per workspace
```python
class SerenaMultiWorkspace:
    def __init__(self):
        self._lsp_clients: Dict[str, SimpleLSPClient] = {}

    async def get_lsp_for_workspace(self, workspace: Path):
        key = str(workspace)
        if key not in self._lsp_clients:
            self._lsp_clients[key] = SimpleLSPClient(workspace)
        return self._lsp_clients[key]
```

**Estimated**: 1-2 hours

#### 3. Integration Tests (1 hour)
- Test MCP tools with multi-workspace params
- Test LSP clients per workspace
- Test result aggregation

**Total Remaining**: 4-6 hours

**Completion**: 🟡 70% → 100%

---

## Service 3: conport_kg - KNOWLEDGE GRAPH 🟡 60% Complete

### Current State
- ✅ Workspace support utilities created
- ✅ Tests for utilities (9/9 passing)
- ❌ NOT integrated into actual AGE queries
- ❌ Graph creation not hooked up
- ❌ No actual database operations

### What's Missing

#### 1. Integrate with AGE Client (2-3 hours)
**File**: `services/conport_kg/age_client.py`

**Current**:
```python
class AGEClient:
    async def execute_query(self, query: str, params: dict):
        # Uses single graph
```

**Needed**:
```python
from workspace_support import create_workspace_scoped_query

class AGEClient:
    async def execute_query(
        self,
        query: str,
        params: dict,
        workspace_path: Optional[str] = None,
    ):
        if workspace_path:
            query, ws_params = create_workspace_scoped_query(
                query, Path(workspace_path)
            )
            params = {**params, **ws_params}
        # Execute
```

#### 2. Modify Query Modules (2 hours)
**Files**: `services/conport_kg/queries/*.py`

Add workspace_path param to all query functions:
- `queries/deep_context.py`
- `queries/overview.py`
- `queries/exploration.py`

#### 3. Graph Initialization (1 hour)
**File**: `services/conport_kg/operations/migrations.py`

Add workspace graph creation:
```python
from workspace_support import create_workspace_graph_schema

async def ensure_workspace_graphs(workspaces: List[Path]):
    for ws in workspaces:
        schema = create_workspace_graph_schema(ws)
        await execute(schema)
```

#### 4. Update Orchestrator Interface (1 hour)
**File**: `services/conport_kg/orchestrator.py`

Expose workspace params in HTTP API

#### 5. Integration Tests (1 hour)
- Test workspace-scoped storage
- Test cross-workspace queries
- Test graph isolation

**Total Remaining**: 6-8 hours

**Completion**: 🟡 60% → 100%

---

## Service 4: orchestrator - ROUTING 🟢 90% Complete

### Current State
- ✅ Workspace support utilities created
- ✅ Tests passing (8/8)
- ❌ NOT integrated into main router
- ❌ Service doesn't use the utilities

### What's Missing

#### 1. Integrate into Router (30 min)
**File**: `services/orchestrator/src/router.py`

```python
from workspace_support import add_workspace_context

class Router:
    async def route(self, request: dict):
        # Add workspace context
        request = add_workspace_context(request)
        # Continue routing
```

#### 2. Update TUI/CLI (30 min)
**File**: `services/orchestrator/tui/main.py`

Add workspace argument parsing

#### 3. Integration Test (30 min)
Test workspace context flows through system

**Total Remaining**: 1.5 hours

**Completion**: 🟢 90% → 100%

---

## Service 5: activity-capture - METADATA 🟢 85% Complete

### Current State
- ✅ Workspace support utilities created
- ❌ NOT used in main tracking code
- ❌ Events don't include workspace

### What's Missing

#### 1. Integrate into Tracker (30 min)
**File**: `services/activity-capture/activity_tracker.py`

```python
from workspace_support import enrich_event_with_workspace

class ActivityTracker:
    def track_event(self, event_type: str, data: dict):
        event = create_event(event_type, data)
        event = enrich_event_with_workspace(event)  # ADD THIS
        self.emit(event)
```

#### 2. Update Event Subscriber (30 min)
**File**: `services/activity-capture/event_subscriber.py`

Ensure workspace metadata is preserved

#### 3. Tests (30 min)
- Verify events include workspace
- Test workspace auto-detection

**Total Remaining**: 1.5 hours

**Completion**: 🟢 85% → 100%

---

## Summary: First 5 Services

| Service | Current | Remaining Work | Time | Priority |
|---------|---------|----------------|------|----------|
| dope-context | ✅ 100% | NONE | 0h | - |
| serena | 🟡 70% | MCP integration, LSP | 4-6h | HIGH |
| conport_kg | 🟡 60% | AGE integration, queries | 6-8h | HIGH |
| orchestrator | 🟢 90% | Router integration | 1.5h | MEDIUM |
| activity-capture | 🟢 85% | Tracker integration | 1.5h | LOW |

**Total to Complete First 5**: 13-17 hours

---

## Next 5 Services - Priority Order

### 6. task-orchestrator 📋 0% Complete
**Priority**: HIGH
**Complexity**: Medium
**Estimated**: 3-4 hours

**What's needed**:
- Add workspace field to Task model
- Filter tasks by workspace
- Tag tasks with workspace on creation
- Workspace-aware task routing

**Files to modify**:
- `services/task-orchestrator/task_coordinator.py`
- `services/task-orchestrator/server.py`
- Database schema updates

### 7. session_intelligence 📋 0% Complete
**Priority**: HIGH
**Complexity**: Medium
**Estimated**: 2-3 hours

**What's needed**:
- Track sessions per workspace
- Detect workspace switches
- Restore session state by workspace

**Files to modify**:
- `services/session_intelligence/*.py` (main modules)

### 8. mcp-client 📋 0% Complete
**Priority**: MEDIUM
**Complexity**: Low
**Estimated**: 1-2 hours

**What's needed**:
- Forward workspace params in MCP calls
- Handle multi-workspace responses

### 9. adhd_engine 📋 0% Complete
**Priority**: MEDIUM
**Complexity**: Low
**Estimated**: 1-2 hours

**What's needed**:
- Tag metrics with workspace
- Per-workspace energy tracking (optional)

### 10. intelligence 📋 0% Complete
**Priority**: LOW
**Complexity**: Low
**Estimated**: 1-2 hours

**What's needed**:
- Include workspace in AI prompts
- Workspace context in model selection

**Total for Next 5**: 8-13 hours

---

## Implementation Strategy

### Phase 1: Complete First 5 (13-17 hours)
**Order**:
1. orchestrator (1.5h) - Quick win
1. activity-capture (1.5h) - Quick win
1. serena (4-6h) - High value
1. conport_kg (6-8h) - High value

### Phase 2: Next 5 Services (8-13 hours)
**Order**:
1. task-orchestrator (3-4h) - High priority
1. session_intelligence (2-3h) - High priority
1. mcp-client (1-2h) - Enables others
1. adhd_engine (1-2h) - Quick
1. intelligence (1-2h) - Quick

### Phase 3: Polish & Integration (4-6 hours)
- Cross-service integration tests
- Docker compose updates
- End-to-end examples
- Performance testing

**Total: 25-36 hours for complete ecosystem**

---

## Success Criteria - Full Completion

For each service:
- [ ] Multi-workspace params in ALL public functions
- [ ] Integrated into core service logic (not just wrappers)
- [ ] Tests for integration (not just utilities)
- [ ] Works in production deployment
- [ ] Documentation updated
- [ ] No breaking changes

---

## Next Steps

**Right now, let's**:
1. Complete orchestrator (1.5h) - Quick win
1. Complete activity-capture (1.5h) - Quick win
1. Then tackle serena MCP integration (4-6h)

**After that**:
- Complete conport_kg AGE integration
- Move to next 5 services

---

**Current Reality**: We have infrastructure + wrappers (60-90% complete)
**Next Goal**: Full integration (100% complete)
**Total Work Remaining**: 25-36 hours

Ready to continue? 🚀
