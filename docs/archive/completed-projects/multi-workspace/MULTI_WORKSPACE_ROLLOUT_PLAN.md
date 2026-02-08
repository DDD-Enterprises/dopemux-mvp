---
id: MULTI_WORKSPACE_ROLLOUT_PLAN
title: Multi_Workspace_Rollout_Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Multi_Workspace_Rollout_Plan (explanation) for dopemux documentation and
  developer workflows.
---
# Multi-Workspace Support - Dopemux Ecosystem Rollout Plan

## 🎯 Goal
Extend multi-workspace support to all dopemux services, MCP servers, and infrastructure components to enable seamless work across multiple Git worktrees, projects, and contexts.

## 📊 Service Inventory & Priority

### ✅ COMPLETED
1. **dope-context** (MCP Server)
   - ✅ Multi-workspace search (code, docs, all)
   - ✅ Multi-workspace sync
   - ✅ Autonomous indexing daemon
   - ✅ Tests passing (10/10)

### 🔥 HIGH PRIORITY - Core MCP Servers

1. **serena** (Code Graph Analysis)
   - Location: `services/serena/`
   - Functions: Call graph, dependency analysis, impact assessment
   - Multi-workspace need: Track relationships across worktrees
   - Priority: HIGH (used by dope-context for graph enrichment)

2. **conport_kg** (Knowledge Graph)
   - Location: `services/conport_kg/`
   - Functions: Context storage, decision logging, session memory
   - Multi-workspace need: Isolate contexts per workspace
   - Priority: HIGH (persistent memory across sessions)

3. **workspace-watcher** (File Monitoring)
   - Location: `services/workspace-watcher/`
   - Functions: File change detection, git event monitoring
   - Multi-workspace need: Monitor multiple directories
   - Priority: HIGH (triggers indexing)

### 🟡 MEDIUM PRIORITY - Intelligence & Coordination

1. **task-orchestrator** (Task Management)
   - Location: `services/task-orchestrator/`
   - Functions: Task routing, workflow coordination
   - Multi-workspace need: Per-workspace task queues
   - Priority: MEDIUM

2. **orchestrator** (Service Coordination)
   - Location: `services/orchestrator/`
   - Functions: Service health, message routing
   - Multi-workspace need: Workspace-aware routing
   - Priority: MEDIUM

3. **session_intelligence** (Session Context)
   - Location: `services/session_intelligence/`
   - Functions: Session state, context switching
   - Multi-workspace need: Track sessions per workspace
   - Priority: MEDIUM

4. **intelligence** (AI Coordination)
   - Location: `services/intelligence/`
   - Functions: Model selection, prompt routing
   - Multi-workspace need: Workspace-specific prompts
   - Priority: MEDIUM

### 🟢 LOW PRIORITY - ADHD Features

1. **adhd_engine** (ADHD Accommodations)
   - Location: `services/adhd_engine/`
   - Functions: Energy tracking, attention state
   - Multi-workspace need: Per-workspace energy tracking
   - Priority: LOW (nice-to-have)

2. **activity-capture** (Activity Logging)
    - Location: `services/activity-capture/`
    - Functions: Event logging, metrics
    - Multi-workspace need: Tag events by workspace
    - Priority: LOW

3. **context-switch-tracker** (Context Switching)
    - Location: `services/context-switch-tracker/`
    - Functions: Track workspace switches
    - Multi-workspace need: Core feature!
    - Priority: MEDIUM-HIGH

### 🔧 INFRASTRUCTURE

1. **Docker Compose Files**
    - Environment variables for multi-workspace
    - Volume mounts for multiple workspaces
    - Service configuration

2. **MCP DopeconBridge**
    - Location: `services/mcp-dopecon-bridge/`
    - Workspace-aware request routing
    - Priority: HIGH

## 🏗️ Implementation Strategy

### Phase 1: Core MCP Servers (Week 1)
1. ✅ dope-context (DONE)
2. serena - Code graph
3. conport_kg - Knowledge graph
4. workspace-watcher - File monitoring

### Phase 2: Coordination Layer (Week 2)
1. mcp-dopecon-bridge - Request routing
2. orchestrator - Service coordination
3. task-orchestrator - Task management

### Phase 3: Intelligence & ADHD (Week 3)
1. session_intelligence - Session context
2. context-switch-tracker - Workspace switching
3. intelligence - AI coordination

### Phase 4: Infrastructure & Polish (Week 4)
1. Docker compose updates
2. Environment variable standards
3. Documentation & examples
4. Integration tests

## 🎨 Design Patterns

### API Pattern (Same as dope-context)
```python
async def search_function(
    query: str,
    workspace_path: Optional[str] = None,      # Single workspace (backward compat)
    workspace_paths: Optional[List[str]] = None,  # Multiple workspaces (new)
    **kwargs
) -> Any:
    """
    Single workspace returns: List[Dict] or Dict
    Multiple workspaces returns: {
        "workspace_count": 2,
        "total_results": 10,
        "results": [
            {"workspace": "/path1", "results": [...], "result_count": 5},
            {"workspace": "/path2", "results": [...], "result_count": 5}
        ]
    }
    """
    targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
    )

    multi = len(targets) > 1
    aggregated_results = []

    for workspace in targets:
        workspace_results = await _impl_func(str(workspace), **kwargs)
        aggregated_results.append({
            "workspace": str(workspace),
            "results": workspace_results,
            "result_count": len(workspace_results),
        })

    if not multi:
        return aggregated_results[0]["results"]

    return {
        "workspace_count": len(aggregated_results),
        "total_results": sum(r["result_count"] for r in aggregated_results),
        "results": aggregated_results,
    }
```

### Environment Variable Standard
```bash
# Standard across all services
DOPE_WORKSPACES="/path/ws1,/path/ws2;/path/ws3"  # Comma or semicolon separated

# Or service-specific
DOPE_CONTEXT_WORKSPACES="/path1,/path2"
SERENA_WORKSPACES="/path1,/path2"
CONPORT_WORKSPACES="/path1,/path2"
```

### Docker Compose Pattern
```yaml
services:
  service-name:
    environment:
      - DOPE_WORKSPACES=${DOPE_WORKSPACES:-/workspace}
    volumes:
      # Mount all workspaces
      - ${WORKSPACE_1:-/workspace}:/workspace1:ro
      - ${WORKSPACE_2}:/workspace2:ro
      - ${WORKSPACE_3}:/workspace3:ro
```

### CLI Pattern
```bash
# All services support --workspace flag (repeatable)
python service.py --workspace /path1 --workspace /path2

# Or via environment
DOPE_WORKSPACES="/path1,/path2" python service.py
```

## 🧪 Testing Strategy

### Per-Service Tests
```python
@pytest.mark.anyio
async def test_service_multi_workspace(tmp_path, monkeypatch):
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    mock_impl = AsyncMock(side_effect=[result1, result2])
    monkeypatch.setattr("service._impl_func", mock_impl)

    result = await service_function(workspace_paths=[str(ws1), str(ws2)])

    assert result["workspace_count"] == 2
    assert result["total_results"] > 0
```

### Integration Tests
```bash
# Test cross-service multi-workspace
DOPE_WORKSPACES="/ws1,/ws2" pytest integration/test_multi_workspace.py
```

## 📋 Checklist Per Service

For each service:
- [ ] Add `workspace_paths` parameter to public functions
- [ ] Implement `_resolve_explicit_workspaces()` helper
- [ ] Add aggregation logic for multi-workspace results
- [ ] Maintain backward compatibility (single workspace)
- [ ] Add fallback imports for heavy dependencies
- [ ] Write multi-workspace tests (minimum 3 functions)
- [ ] Update docstrings with return type documentation
- [ ] Update README with multi-workspace examples
- [ ] Add environment variable support
- [ ] Add CLI --workspace flag support

## 📖 Documentation Requirements

Each service needs:
1. **README update** - Multi-workspace usage examples
2. **API docs** - Parameter descriptions, return types
3. **Architecture docs** - Multi-workspace design decisions
4. **Environment variables** - All workspace-related vars
5. **Docker compose** - Multi-workspace configuration

## 🔍 Verification Commands

```bash
# Test collection (no heavy deps needed)
PYTHONPATH="$(pwd)/services/SERVICE_NAME" pytest services/SERVICE_NAME/tests -k multi

# Single test
pytest services/SERVICE_NAME/tests/test_server.py::test_function_multi_workspace

# Integration test
DOPE_WORKSPACES="/ws1,/ws2" pytest integration/test_cross_service.py
```

## 🎯 Success Criteria

### Per Service
- ✅ All multi-workspace tests passing
- ✅ Backward compatibility verified
- ✅ Documentation complete
- ✅ Environment variables supported
- ✅ Docker compose updated

### Ecosystem
- ✅ All core services support multi-workspace
- ✅ Cross-service integration works
- ✅ Docker stack supports multi-workspace
- ✅ End-to-end examples documented
- ✅ Migration guide for existing users

## 📅 Timeline

- **Week 1 (Now)**: Core MCP servers (serena, conport_kg, workspace-watcher)
- **Week 2**: Coordination layer (orchestrator, task-orchestrator, mcp-bridge)
- **Week 3**: Intelligence & ADHD features
- **Week 4**: Infrastructure & final polish

## 🚀 Next Steps

1. Start with **serena** (code graph) - High priority, clear scope
2. Then **conport_kg** (knowledge graph) - Critical for context
3. Then **workspace-watcher** - Enables autonomous indexing
4. Document patterns as we go
5. Create shared utilities for common functionality

---

**Status**: Planning Complete
**Ready to start**: serena multi-workspace implementation
