# Multi-Workspace Implementation Guide

## 📚 Purpose

This guide provides step-by-step instructions for adding multi-workspace support to any dopemux service. Follow these patterns for consistency across the ecosystem.

---

## 🎯 Quick Start

### For Simple Services (Stateless Functions)

**Time**: 30-60 minutes per service

1. Import shared utilities
2. Add `workspace_paths` parameter
3. Loop over workspaces
4. Aggregate results
5. Add tests

### For Complex Services (Stateful, LSP, Database)

**Time**: 2-4 hours per service

1. Design workspace isolation strategy
2. Refactor state management
3. Create per-workspace instances
4. Implement workspace switching
5. Add comprehensive tests

---

## 📋 Implementation Checklist

### Phase 1: Planning (5-10 minutes)

- [ ] Identify all functions that operate on workspace
- [ ] Determine if service is stateful or stateless
- [ ] Plan workspace isolation strategy
- [ ] Identify test coverage needs

### Phase 2: Code Changes (30-120 minutes)

- [ ] Import shared utilities
- [ ] Add `workspace_paths` parameter to functions
- [ ] Implement workspace resolution
- [ ] Add processing loop for multiple workspaces
- [ ] Implement result aggregation
- [ ] Update docstrings with return type info

### Phase 3: Testing (30-60 minutes)

- [ ] Add multi-workspace tests (minimum 3)
- [ ] Test backward compatibility (single workspace)
- [ ] Test environment variable support
- [ ] Test error handling (invalid paths, etc.)

### Phase 4: Documentation (15-30 minutes)

- [ ] Update README with multi-workspace examples
- [ ] Document environment variables
- [ ] Update CLI help text
- [ ] Add migration notes if needed

---

## 🔧 Implementation Patterns

### Pattern 1: Stateless Function (Simple)

**Example**: Search functions, read-only operations

```python
# BEFORE
async def search_function(query: str, workspace_path: str = None) -> List[Dict]:
    workspace = Path(workspace_path or os.getcwd())
    return await _search_impl(workspace, query)

# AFTER
from services.shared.workspace_utils import (
    resolve_workspaces,
    aggregate_multi_workspace_results,
)

async def search_function(
    query: str,
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Any:
    """
    Search for code matching query.
    
    Args:
        query: Search query
        workspace_path: Single workspace (backward compatible)
        workspace_paths: Multiple workspaces (new)
    
    Returns:
        Single workspace: List[Dict] - original format
        Multiple workspaces: {
            "workspace_count": 2,
            "total_results": 10,
            "results": [
                {"workspace": "/ws1", "results": [...], "result_count": 5},
                {"workspace": "/ws2", "results": [...], "result_count": 5}
            ]
        }
    """
    # Resolve workspaces
    workspaces = resolve_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
        env_var_name="SERVICE_WORKSPACES",
    )
    
    # Process each workspace
    results = []
    for workspace in workspaces:
        result = await _search_impl(workspace, query)
        results.append(result)
    
    # Aggregate
    return aggregate_multi_workspace_results(results, workspaces)
```

### Pattern 2: Stateful Service (Complex)

**Example**: LSP clients, database connections, file watchers

```python
# BEFORE
class ServiceServer:
    def __init__(self):
        self.workspace = detect_workspace()
        self.lsp_client = LSPClient(self.workspace)
    
    async def search(self, query: str) -> List[Dict]:
        return await self.lsp_client.search(query)

# AFTER
from services.shared.workspace_utils import resolve_workspaces

class ServiceServer:
    def __init__(self):
        # Keep single workspace for backward compat
        self.workspace = detect_workspace()
        self.lsp_client = None  # Lazy load
        
        # New: workspace-specific instances
        self._workspace_instances = {}  # workspace_path -> instance
    
    async def _get_workspace_instance(self, workspace: Path):
        """Get or create per-workspace instance."""
        key = str(workspace)
        if key not in self._workspace_instances:
            self._workspace_instances[key] = LSPClient(workspace)
        return self._workspace_instances[key]
    
    async def search(
        self,
        query: str,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> Any:
        """Search with multi-workspace support."""
        workspaces = resolve_workspaces(
            workspace_path,
            workspace_paths,
            fallback_to_current=True,
        )
        
        results = []
        for workspace in workspaces:
            instance = await self._get_workspace_instance(workspace)
            result = await instance.search(query)
            results.append(result)
        
        return aggregate_multi_workspace_results(results, workspaces)
```

### Pattern 3: CLI Tool

```python
#!/usr/bin/env python3
import argparse
from services.shared.workspace_utils import (
    resolve_workspaces,
    parse_workspace_cli_args,
)

def main():
    parser = argparse.ArgumentParser(description="Service CLI")
    parser.add_argument(
        "-w", "--workspace",
        action="append",
        dest="workspaces",
        help="Workspace path (repeatable)",
    )
    args = parser.parse_args()
    
    # Resolve from CLI args and environment
    workspace_inputs = args.workspaces or []
    workspaces = resolve_workspaces(
        workspace_paths=workspace_inputs,
        env_var_name="SERVICE_WORKSPACES",
        fallback_to_current=True,
    )
    
    # Process each workspace
    for workspace in workspaces:
        process_workspace(workspace)
```

### Pattern 4: Daemon/Long-Running Service

```python
#!/usr/bin/env python3
import asyncio
import signal
from services.shared.workspace_utils import resolve_workspaces

async def run_daemon(workspaces: List[Path]):
    """Run daemon for multiple workspaces."""
    workspace_states = []
    
    # Start per-workspace services
    for workspace in workspaces:
        state = await start_workspace_service(workspace)
        workspace_states.append(state)
    
    # Shutdown handling
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Main loop
    try:
        while not shutdown_event.is_set():
            await asyncio.sleep(60)
            for state in workspace_states:
                logger.info(f"Status: {state['workspace']}")
    finally:
        # Cleanup
        for state in workspace_states:
            await state["service"].stop()

if __name__ == "__main__":
    workspaces = resolve_workspaces(
        env_var_name="SERVICE_WORKSPACES",
        fallback_to_current=True,
    )
    asyncio.run(run_daemon(workspaces))
```

---

## 🧪 Testing Patterns

### Test 1: Single Workspace (Backward Compatibility)

```python
@pytest.mark.anyio
async def test_function_single_workspace(tmp_path):
    """Single workspace returns original format."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    
    result = await function(workspace_path=str(ws))
    
    # Should return original format (not wrapped)
    assert isinstance(result, list)  # or dict, depending on function
    assert "workspace_count" not in result  # Not aggregated
```

### Test 2: Multiple Workspaces (New Feature)

```python
@pytest.mark.anyio
async def test_function_multi_workspace(tmp_path, monkeypatch):
    """Multiple workspaces returns aggregated format."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()
    
    # Mock implementation to return predictable results
    mock_impl = AsyncMock(side_effect=[
        [{"item": "from_ws1"}],
        [{"item": "from_ws2"}],
    ])
    monkeypatch.setattr("module._impl_func", mock_impl)
    
    result = await function(workspace_paths=[str(ws1), str(ws2)])
    
    # Should return aggregated format
    assert result["workspace_count"] == 2
    assert result["total_results"] == 2
    assert len(result["results"]) == 2
    assert result["results"][0]["workspace"] == str(ws1)
    assert result["results"][1]["workspace"] == str(ws2)
```

### Test 3: Environment Variable Support

```python
@pytest.mark.anyio
async def test_function_from_env(tmp_path, monkeypatch):
    """Function respects environment variable."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()
    
    monkeypatch.setenv("SERVICE_WORKSPACES", f"{ws1},{ws2}")
    
    result = await function()  # No parameters
    
    assert result["workspace_count"] == 2
```

### Test 4: Priority (Explicit > Env > Current)

```python
@pytest.mark.anyio
async def test_workspace_resolution_priority(tmp_path, monkeypatch):
    """Explicit paths take priority over environment."""
    ws_explicit = tmp_path / "explicit"
    ws_env = tmp_path / "env"
    ws_explicit.mkdir()
    ws_env.mkdir()
    
    monkeypatch.setenv("SERVICE_WORKSPACES", str(ws_env))
    
    result = await function(workspace_path=str(ws_explicit))
    
    # Should use explicit, not env
    assert "workspace_count" not in result  # Single workspace
```

---

## 📖 Documentation Templates

### README Update

```markdown
## Multi-Workspace Support

{SERVICE_NAME} now supports working with multiple workspaces simultaneously.

### Usage

#### Single Workspace (Backward Compatible)
```python
result = await service.function(workspace_path="/path/to/workspace")
```

#### Multiple Workspaces
```python
result = await service.function(
    workspace_paths=["/path/ws1", "/path/ws2"]
)
```

#### Environment Variable
```bash
SERVICE_WORKSPACES="/path/ws1,/path/ws2" python service.py
```

### Return Format

**Single workspace**: Returns original format (backward compatible)
**Multiple workspaces**: Returns aggregated format:
```json
{
  "workspace_count": 2,
  "total_results": 10,
  "results": [
    {"workspace": "/ws1", "results": [...], "result_count": 5},
    {"workspace": "/ws2", "results": [...], "result_count": 5}
  ]
}
```
```

### Docstring Template

```python
async def function_name(
    param1: str,
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Any:
    """
    Brief description of what the function does.
    
    Supports multiple workspaces for parallel processing across Git worktrees.
    
    Args:
        param1: Description of parameter
        workspace_path: Single workspace path (backward compatible)
        workspace_paths: List of workspace paths for multi-workspace mode
    
    Returns:
        Single workspace mode:
            Original return type (List[Dict], Dict, etc.)
        
        Multi-workspace mode:
            Dict containing:
            - workspace_count: Number of workspaces processed
            - total_results: Aggregated result count
            - results: List of per-workspace results with metadata
    
    Examples:
        >>> # Single workspace
        >>> result = await function_name("query", workspace_path="/path")
        >>> # Returns: [{"item": 1}, {"item": 2}]
        
        >>> # Multiple workspaces
        >>> result = await function_name(
        ...     "query",
        ...     workspace_paths=["/ws1", "/ws2"]
        ... )
        >>> # Returns: {
        ...     "workspace_count": 2,
        ...     "total_results": 3,
        ...     "results": [...]
        ... }
    """
```

---

## ⚠️ Common Pitfalls

### 1. Forgetting Backward Compatibility

❌ **Wrong**:
```python
# Always returns aggregated format
return {
    "workspace_count": len(workspaces),
    "results": results,
}
```

✅ **Correct**:
```python
# Return original format for single workspace
if len(workspaces) == 1:
    return results[0]
return aggregate_multi_workspace_results(results, workspaces)
```

### 2. Not Handling State Properly

❌ **Wrong**:
```python
class Service:
    def __init__(self):
        self.workspace = Path("/single/workspace")
        self.db = Database(self.workspace)  # Only works for one!
```

✅ **Correct**:
```python
class Service:
    def __init__(self):
        self._workspace_instances = {}
    
    async def _get_instance(self, workspace):
        if str(workspace) not in self._workspace_instances:
            self._workspace_instances[str(workspace)] = Database(workspace)
        return self._workspace_instances[str(workspace)]
```

### 3. Hardcoding Environment Variable Names

❌ **Wrong**:
```python
workspaces = os.getenv("MY_CUSTOM_VAR", "").split(",")
```

✅ **Correct**:
```python
workspaces = resolve_workspaces(
    workspace_path,
    workspace_paths,
    env_var_name="SERVICE_WORKSPACES",  # Configurable
)
```

### 4. Not Testing Multi-Workspace Mode

❌ **Wrong**: Only testing single workspace

✅ **Correct**: Test matrix:
- Single workspace (backward compat)
- Multiple workspaces
- Environment variable
- Priority handling
- Edge cases (empty, invalid paths)

---

## 🎓 Examples by Service Type

### MCP Server (e.g., dope-context, serena)

**Key Points**:
- Tools accept `workspace_paths` in MCP arguments
- Each tool handles multi-workspace internally
- Cache keys include workspace identifier
- LSP clients per workspace

**Template**: See `services/dope-context/src/mcp/server.py`

### Daemon (e.g., workspace-watcher, autonomous-indexing)

**Key Points**:
- Start one monitor per workspace
- Graceful shutdown for all
- Status reporting per workspace
- Signal handling for clean exit

**Template**: See `scripts/autonomous-indexing-daemon.py`

### CLI Tool (e.g., batch scripts)

**Key Points**:
- Repeatable `--workspace` flag
- Environment variable support
- Progress reporting per workspace
- Error handling doesn't stop processing

**Template**: See `scripts/enable-autonomous-indexing.py`

### HTTP API (e.g., orchestrator, task-router)

**Key Points**:
- Accept `workspace_paths` in request body
- Return aggregated JSON response
- OpenAPI spec documents both formats
- Rate limiting per workspace

---

## 📊 Effort Estimates

| Service Type | Estimated Time | Difficulty |
|--------------|----------------|------------|
| Stateless function | 30-60 min | Easy |
| Stateful service | 2-4 hours | Medium |
| Complex service (LSP, DB) | 4-8 hours | Hard |
| Daemon | 1-2 hours | Medium |
| CLI tool | 30-90 min | Easy |

---

## ✅ Validation Checklist

Before marking a service complete:

- [ ] All public functions accept `workspace_paths`
- [ ] Shared utilities imported and used
- [ ] Backward compatibility tested
- [ ] Multi-workspace tests added (minimum 3)
- [ ] Environment variable support works
- [ ] Documentation updated
- [ ] Docstrings include return type info
- [ ] README has examples
- [ ] No hardcoded workspace assumptions

---

## 🚀 Quick Commands

```bash
# Test shared utilities
pytest services/shared/test_workspace_utils.py -v

# Test specific service multi-workspace
pytest services/SERVICE_NAME/tests -k multi_workspace -v

# Run with environment variable
DOPE_WORKSPACES="/ws1,/ws2" python service.py

# Run daemon
python service-daemon.py --workspace /ws1 --workspace /ws2
```

---

## 📚 References

- `services/shared/workspace_utils.py` - Shared utilities
- `services/dope-context/` - Reference implementation
- `MULTI_WORKSPACE_ROLLOUT_PLAN.md` - Overall strategy
- `MULTI_WORKSPACE_ECOSYSTEM_STATUS.md` - Current status

---

**Last Updated**: 2025-01-13
**Maintainer**: Dopemux Team
