---
id: multi-workspace-guide
title: Multi Workspace Guide
type: system-doc
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Serena Multi-Workspace Guide

**ADHD-optimized code intelligence across multiple workspaces**

---

## Overview

Serena v2 now supports multi-workspace operations, allowing you to search code, analyze complexity, and navigate across multiple project workspaces simultaneously.

**Key Benefits**:
- 🔍 Semantic code search across all your projects
- 📊 Unified complexity analysis and reading order
- 🧪 Multi-workspace test file discovery
- 🎯 Cross-project navigation patterns
- 🚀 Automatic workspace instance management

---

## Quick Start

### Single Workspace (Default)

```python
# Via MCP tool call
result = await mcp__serena-v2__find_similar_code(
    query="authentication middleware",
    top_k=10
)
# Searches current workspace only
```

### Multi-Workspace Search

```python
# Search across multiple workspaces
result = await mcp__serena-v2__find_similar_code(
    query="authentication middleware",
    top_k=10,
    workspace_paths=[
        "/Users/hue/code/dopemux-mvp",
        "/Users/hue/code/api-gateway",
        "/Users/hue/code/auth-service"
    ]
)

# Results ranked by semantic similarity across all workspaces
# Each result tagged with workspace identifier
```

---

## Supported Multi-Workspace Tools

### 1. Semantic Code Search

Find code semantically similar to natural language queries:

```python
result = await mcp__serena-v2__find_similar_code(
    query="error handling patterns for HTTP requests",
    top_k=15,
    user_id="developer1",
    workspace_paths=[
        "/workspace1",
        "/workspace2",
        "/workspace3"
    ]
)

# Returns unified results ranked by relevance
{
    "query": "error handling patterns for HTTP requests",
    "workspaces": ["workspace1", "workspace2", "workspace3"],
    "total_found": 45,
    "top_k": 15,
    "results": [
        {
            "file_path": "src/api/client.py",
            "function_name": "handle_http_error",
            "score": 0.94,
            "workspace": "workspace2",
            "complexity": 0.45
        },
        # ... more results sorted by score
    ]
}
```

### 2. Unified Complexity Analysis

Analyze complexity metrics across workspaces:

```python
result = await mcp__serena-v2__get_unified_complexity(
    file_path="src/auth/middleware.py",
    symbol="authenticate_request",
    user_id="developer1",
    workspace_paths=[
        "/project-v1",
        "/project-v2",
        "/project-v3"
    ]
)

# Returns aggregated complexity
{
    "file_path": "src/auth/middleware.py",
    "symbol": "authenticate_request",
    "workspaces": ["project_v1", "project_v2", "project_v3"],
    "complexity": {
        "average": 0.62,
        "max": 0.85,
        "min": 0.45
    },
    "per_workspace": [
        {
            "workspace": "project_v1",
            "complexity_score": 0.45,
            "interpretation": "MEDIUM - Needs focus"
        },
        # ... more per-workspace results
    ]
}
```

### 3. Cross-Workspace Reading Order

Get optimal reading order with complexity progression:

```python
result = await mcp__serena-v2__get_reading_order(
    files=[
        "src/api/routes.py",
        "src/auth/jwt.py",
        "src/db/models.py",
        "src/utils/validators.py"
    ],
    workspace_paths=["/workspace1", "/workspace2"]
)

# Returns files sorted by complexity across workspaces
{
    "workspaces": ["workspace1", "workspace2"],
    "total_files": 8,  # 4 files × 2 workspaces
    "reading_order": [
        {
            "file": "src/utils/validators.py",
            "complexity_score": 0.25,
            "reading_minutes": 5.0,
            "level": "LOW - Safe to read anytime",
            "workspace": "workspace1"
        },
        {
            "file": "src/api/routes.py",
            "complexity_score": 0.48,
            "reading_minutes": 12.5,
            "level": "MEDIUM - Needs focus",
            "workspace": "workspace2"
        },
        # ... sorted simple → complex
    ],
    "session_plan": {
        "total_reading_minutes": 85.5,
        "pomodoro_sessions_needed": 4,
        "breaks_recommended": 3
    }
}
```

### 4. Complexity Analysis (ADHD-Aware)

Analyze code complexity across workspaces:

```python
result = await mcp__serena-v2__analyze_complexity(
    file_path="src/core/engine.py",
    symbol_name="process_workflow",
    workspace_paths=["/workspace1", "/workspace2"]
)

# Returns aggregate metrics
{
    "file_path": "src/core/engine.py",
    "symbol": "process_workflow",
    "workspaces": ["workspace1", "workspace2"],
    "aggregate_complexity": {
        "average_score": 0.72,
        "max_score": 0.85,
        "min_score": 0.58,
        "interpretation": "HIGH - Complex code, peak focus required"
    },
    "per_workspace": [
        {
            "workspace": "workspace1",
            "complexity": {
                "score": 0.58,
                "level": "MEDIUM - Needs focus"
            },
            "metrics": {
                "cyclomatic_complexity": 12,
                "nesting_depth": 3,
                "lines_of_code": 145
            }
        },
        # ... more workspace results
    ]
}
```

### 5. Multi-Workspace Test Discovery

Find test files across workspaces:

```python
result = await mcp__serena-v2__find_test_file(
    file_path="src/auth/middleware.py",
    workspace_paths=[
        "/monorepo/services/auth",
        "/standalone/auth-lib"
    ]
)

# Returns test matches from all workspaces
{
    "file_path": "src/auth/middleware.py",
    "workspaces": ["auth_service", "auth_lib"],
    "matches_found": 2,
    "test_files": [
        {
            "found": true,
            "implementation_file": "src/auth/middleware.py",
            "test_file": "tests/test_auth_middleware.py",
            "relationship": "impl→test",
            "workspace": "auth_service"
        },
        {
            "found": true,
            "implementation_file": "src/auth/middleware.py",
            "test_file": "test/middleware_test.py",
            "relationship": "impl→test",
            "workspace": "auth_lib"
        }
    ]
}
```

### 6. Navigation Patterns (Placeholder)

Analyze navigation patterns across workspaces:

```python
result = await mcp__serena-v2__get_navigation_patterns(
    days_back=7,
    workspace_paths=["/workspace1", "/workspace2"]
)

# Currently returns placeholder (Phase 3 feature)
# Will learn navigation patterns across workspaces
```

---

## Architecture

### Workspace Instance Management

Serena creates per-workspace instances automatically:

```python
from serena.v2.multi_workspace_wrapper import SerenaMultiWorkspace

wrapper = SerenaMultiWorkspace()

# First call creates instance for workspace1
result1 = await wrapper.find_similar_code_multi(
    query="authentication",
    workspace_paths=["/workspace1"]
)

# Instance cached and reused
result2 = await wrapper.find_similar_code_multi(
    query="authorization",
    workspace_paths=["/workspace1"]  # Reuses instance
)
```

### Result Aggregation Strategies

Different tools use different aggregation strategies:

| Tool | Strategy |
|------|----------|
| `find_similar_code` | Unified ranking by similarity score |
| `get_unified_complexity` | Average/max/min aggregation |
| `analyze_complexity` | Per-workspace breakdown + aggregate |
| `get_reading_order` | Cross-workspace complexity sorting |
| `find_test_file` | Collect all matches |
| `get_navigation_patterns` | Standard aggregation helper |

---

## Best Practices

### When to Use Multi-Workspace

✅ **Good use cases:**
- Finding similar code patterns across projects
- Comparing complexity across different versions
- Cross-project test coverage analysis
- Learning from multiple implementations

❌ **Avoid for:**
- Single-project daily workflows
- Performance-critical operations
- Very large numbers of workspaces (>5)

### Performance Optimization

```python
# ❌ Too many workspaces
result = await find_similar_code(
    query="...",
    workspace_paths=["/ws1", "/ws2", ..., "/ws20"]  # Slow!
)

# ✅ Focused workspace set
result = await find_similar_code(
    query="...",
    workspace_paths=["/current", "/related", "/reference"]  # Fast
)

# ✅ Single workspace when appropriate
result = await find_similar_code(
    query="...",
    workspace_path="/current"  # Fastest
)
```

### ADHD-Aware Limits

Multi-workspace results respect ADHD limits:

```python
# With focused attention: sees more results
result = await find_similar_code(
    query="...",
    top_k=10,  # Actually adjusted 5-15 by ADHD engine
    user_id="user_focused_state"
)

# With scattered attention: sees fewer results
result = await find_similar_code(
    query="...",
    top_k=10,  # Actually adjusted 3-8 by ADHD engine
    user_id="user_scattered_state"
)
```

---

## Environment Configuration

Set default workspaces:

```bash
# Single workspace
export SERENA_WORKSPACE="/Users/hue/code/dopemux-mvp"

# Multiple workspaces (comma-separated)
export SERENA_WORKSPACES="/workspace1,/workspace2,/workspace3"
```

Tools will use these defaults if no workspace parameters provided.

---

## Examples

### Example 1: Find Auth Patterns Across Microservices

```python
# Search for authentication across all microservices
result = await mcp__serena-v2__find_similar_code(
    query="JWT token validation and refresh logic",
    top_k=20,
    workspace_paths=[
        "/monorepo/services/api-gateway",
        "/monorepo/services/auth-service",
        "/monorepo/services/user-service"
    ]
)

# Analyze results
for item in result["results"]:
    print(f"[{item['workspace']}] {item['file_path']}")
    print(f"  Score: {item['score']:.2f}")
    print(f"  Complexity: {item.get('complexity', 'N/A')}")
```

### Example 2: Complexity Comparison Across Versions

```python
# Compare same file across project versions
result = await mcp__serena-v2__get_unified_complexity(
    file_path="src/core/scheduler.py",
    symbol="schedule_task",
    workspace_paths=[
        "/projects/scheduler-v1",
        "/projects/scheduler-v2",
        "/projects/scheduler-v3"
    ]
)

print(f"Average complexity: {result['complexity']['average']}")
print(f"Evolution: {result['complexity']['min']} → {result['complexity']['max']}")
```

### Example 3: Unified Reading Order for Learning

```python
# Create learning path across projects
result = await mcp__serena-v2__get_reading_order(
    files=[
        "src/basics/intro.py",
        "src/intermediate/patterns.py",
        "src/advanced/optimizations.py"
    ],
    workspace_paths=[
        "/tutorials/beginner",
        "/tutorials/intermediate",
        "/tutorials/advanced"
    ]
)

print("📚 Learning Path (simple → complex):")
for i, file in enumerate(result["reading_order"], 1):
    print(f"{i}. [{file['workspace']}] {file['file']}")
    print(f"   Complexity: {file['level']}")
    print(f"   Reading time: {file['reading_minutes']} min")
```

### Example 4: Test Coverage Across Repos

```python
# Find tests for shared module across repos
result = await mcp__serena-v2__find_test_file(
    file_path="shared/utils/validators.py",
    workspace_paths=[
        "/repos/backend-api",
        "/repos/frontend-bff",
        "/repos/shared-lib"
    ]
)

print(f"Found {result['matches_found']} test files:")
for match in result["test_files"]:
    print(f"  [{match['workspace']}] {match['test_file']}")
```

---

## Migration from Single Workspace

All existing code continues to work! Multi-workspace is opt-in:

```python
# Old code (still works - uses current workspace)
result = await find_similar_code(
    query="authentication",
    top_k=10
)

# New code (multi-workspace)
result = await find_similar_code(
    query="authentication",
    top_k=10,
    workspace_paths=["/ws1", "/ws2"]
)
```

---

## Troubleshooting

### Slow Multi-Workspace Queries

**Solution**: Reduce workspace count or use caching

```python
# Cache results for expensive queries
import functools

@functools.lru_cache(maxsize=100)
def cached_similarity_search(query, workspaces_tuple):
    return find_similar_code(
        query=query,
        workspace_paths=list(workspaces_tuple)
    )

# Use cached version
result = cached_similarity_search(
    "authentication",
    ("/ws1", "/ws2", "/ws3")  # Tuple for hashability
)
```

### Workspace Instance Memory

Instances are cached per-workspace. For very long sessions:

```python
from serena.v2.multi_workspace_wrapper import SerenaMultiWorkspace

wrapper = SerenaMultiWorkspace()

# Clear cache periodically
wrapper._workspace_instances.clear()
```

### Missing Results from Workspace

Ensure workspace path is absolute:

```python
# ❌ Relative path might not work
workspace_paths=["../other-project"]

# ✅ Absolute path
import os
workspace_paths=[os.path.abspath("../other-project")]
```

---

## See Also

- [Serena F002 Multi-Session Guide](./docs/F002_USER_GUIDE.md)
- [Multi-Workspace Wrapper Implementation](./multi_workspace_wrapper.py)
- [Complexity Coordinator](../../services/shared/complexity_coordinator/)
- [ADHD Engine Integration](./adhd_features.py)

---

## Technical Details

**Implementation**: All multi-workspace tools use the `SerenaMultiWorkspace` wrapper class which:
1. Creates per-workspace Serena instances
2. Aggregates results using appropriate strategies
3. Manages instance lifecycle and caching

**Supported Tools**: 6 tools currently support multi-workspace:
- `find_similar_code` (F-NEW-2)
- `find_test_file` (F-NEW-18)
- `get_unified_complexity` (F-NEW-3)
- `get_reading_order` (Tier 2)
- `analyze_complexity` (Tier 2)
- `get_navigation_patterns` (Tier 3)

**Future**: Additional tools will gain multi-workspace support in Phase 3.
