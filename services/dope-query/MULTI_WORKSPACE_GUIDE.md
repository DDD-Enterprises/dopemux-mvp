# ConPort_KG Multi-Workspace Guide

**Query decisions across multiple workspace knowledge graphs**

---

## Overview

ConPort_KG now supports multi-workspace queries, allowing you to search for decisions, explore relationships, and analyze context across multiple project workspaces simultaneously.

**Key Benefits**:
- 🔍 Find similar decisions across all your projects
- 🌐 Cross-workspace genealogy and impact analysis  
- 📊 Unified decision context from multiple codebases
- 🎯 Automatic workspace graph creation (no manual setup)

---

## Quick Start

### Single Workspace Query (Default)

```python
from services.conport_kg.queries.overview import OverviewQueries

queries = OverviewQueries()

# Query current workspace only
recent = queries.get_recent_decisions(limit=10)
```

### Multi-Workspace Query

```python
# Query across multiple workspaces
recent = queries.get_recent_decisions(
    limit=10,
    workspace_path="/Users/hue/code/dopemux-mvp"
)

# Or query multiple workspaces at once
recent = queries.get_recent_decisions(
    limit=10,
    workspace_paths=[
        "/Users/hue/code/dopemux-mvp",
        "/Users/hue/code/serena-standalone",
        "/Users/hue/code/conport-cli"
    ]
)
```

---

## Supported Query Methods

### Overview Queries (Tier 1)

All overview queries support `workspace_path` (single) or `workspace_paths` (multiple):

```python
from services.conport_kg.queries.overview import OverviewQueries

queries = OverviewQueries()

# Get recent decisions across workspaces
recent = queries.get_recent_decisions(
    limit=10,
    workspace_path="/path/to/workspace"
)

# Get decision summary (workspace-scoped)
summary = queries.get_decision_summary(
    decision_id=123,
    workspace_path="/path/to/workspace"
)

# Find root decisions (no parents) across workspaces
roots = queries.get_root_decisions(
    limit=5,
    workspace_paths=["/workspace1", "/workspace2"]
)

# Search by tag across multiple workspaces
tagged = queries.search_by_tag(
    tag="authentication",
    limit=10,
    workspace_paths=["/workspace1", "/workspace2"]
)
```

### Exploration Queries (Tier 2)

```python
from services.conport_kg.queries.exploration import ExplorationQueries

queries = ExplorationQueries()

# Get decision neighborhood (related decisions)
neighborhood = queries.get_decision_neighborhood(
    decision_id=123,
    max_hops=2,
    limit_per_hop=5,
    workspace_path="/path/to/workspace"
)

# Get genealogy chain (ancestors/descendants)
genealogy = queries.get_genealogy_chain(
    decision_id=123,
    direction="both",  # or "ancestors", "descendants"
    max_depth=3,
    workspace_path="/path/to/workspace"
)

# Find decisions by relationship type
implements = queries.find_by_relationship_type(
    decision_id=123,
    relationship_type="IMPLEMENTS",
    direction="outgoing",
    workspace_path="/path/to/workspace"
)

# Get impact graph
impact = queries.get_impact_graph(
    decision_id=123,
    max_depth=2,
    workspace_paths=["/workspace1", "/workspace2"]
)
```

---

## Workspace Graph Auto-Creation

ConPort_KG automatically creates workspace-specific graphs on first query. No manual setup required!

```python
from services.conport_kg.age_client import AGEClient

client = AGEClient()

# First query to a workspace automatically creates its graph
result = client.execute_cypher(
    "MATCH (d:Decision) RETURN d LIMIT 10",
    workspace_path="/new/workspace"
)
# Graph "conport_kg_new_workspace" created automatically
```

**Graph Naming Convention**:
- Workspace path: `/Users/hue/code/dopemux-mvp`
- Graph name: `conport_kg_dopemux_mvp`

---

## Event Orchestrator Integration

The KG Orchestrator automatically respects workspace context from events:

```python
from services.conport_kg.orchestrator import KGOrchestrator, KGEvent

orchestrator = KGOrchestrator()

# Event with workspace context
event = KGEvent(
    event_type="decision.logged",
    payload={
        "decision_id": 123,
        "summary": "Multi-workspace API design",
        "workspace_path": "/Users/hue/code/dopemux-mvp"
    },
    timestamp="2026-02-01T14:00:00Z"
)

# Orchestrator queries respect workspace scope
await orchestrator.on_decision_logged(event)
# Finds similar decisions only in specified workspace
```

---

## Best Practices

### When to Use Single Workspace

- ✅ Working within one project
- ✅ Need faster query performance
- ✅ Decisions are project-specific

### When to Use Multi-Workspace

- ✅ Finding reusable patterns across projects
- ✅ Cross-project dependency analysis
- ✅ Unified decision search across portfolio
- ✅ Learning from similar problems in other codebases

### Performance Tips

1. **Limit workspace count**: Query 2-3 workspaces max for best performance
2. **Use specific queries**: `search_by_tag` is faster than full-text across workspaces
3. **Cache results**: Store frequently accessed cross-workspace data
4. **Scope limits**: Use smaller `limit` values for multi-workspace queries

---

## Environment Variables

Set default workspaces via environment:

```bash
# Single workspace
export CONPORT_WORKSPACE="/Users/hue/code/dopemux-mvp"

# Multiple workspaces (comma-separated)
export CONPORT_WORKSPACES="/workspace1,/workspace2,/workspace3"
```

Query methods will use these defaults if no workspace parameters provided.

---

## Troubleshooting

### Graph Not Found

If you get "graph does not exist" errors:

```python
# Manually ensure graph exists
from services.conport_kg.age_client import AGEClient

client = AGEClient()
client.ensure_workspace_graph(
    client.get_workspace_graph_name("/path/to/workspace")
)
```

### Slow Multi-Workspace Queries

- Reduce number of workspaces
- Add indexes to AGE graphs
- Use more specific query filters
- Consider caching results

### Workspace Path Resolution

```python
# Use absolute paths
workspace_path = "/Users/hue/code/dopemux-mvp"  # ✅ Good

# Relative paths may not work consistently
workspace_path = "../dopemux-mvp"  # ⚠️  Avoid
```

---

## Examples

### Find Similar Decisions Across All Projects

```python
from services.conport_kg.queries.deep_context import DeepContextQueries

queries = DeepContextQueries()

# Search full text across all workspaces
results = queries.search_full_text(
    query="authentication implementation",
    limit=20,
    workspace_paths=[
        "/Users/hue/code/dopemux-mvp",
        "/Users/hue/code/serena-standalone",
        "/Users/hue/code/api-gateway"
    ]
)

for decision in results:
    print(f"{decision.id}: {decision.summary}")
    print(f"  Workspace: {decision.workspace}")
```

### Cross-Project Genealogy

```python
# Find how a decision evolved across projects
genealogy = queries.get_genealogy_chain(
    decision_id=123,
    direction="both",
    max_depth=5,
    workspace_paths=["/project1", "/project2"]
)

print(f"Ancestors: {len(genealogy.ancestors)}")
print(f"Descendants: {len(genealogy.descendants)}")
```

### Workspace-Specific Root Decisions

```python
# Find architectural decisions per workspace
for workspace in ["/workspace1", "/workspace2"]:
    roots = queries.get_root_decisions(
        limit=10,
        workspace_path=workspace
    )
    print(f"\n{workspace}:")
    for decision in roots:
        print(f"  #{decision.id}: {decision.summary}")
```

---

## Migration from Single Workspace

Existing code continues to work! Multi-workspace is opt-in:

```python
# Old code (still works)
recent = queries.get_recent_decisions(limit=10)

# New code (multi-workspace)
recent = queries.get_recent_decisions(
    limit=10,
    workspace_path="/specific/workspace"
)
```

All query methods maintain backward compatibility.

---

## See Also

- [ConPort_KG Architecture](../../docs/94-architecture/)
- [Query API Reference](./queries/README.md)
- [Workspace Support Implementation](./workspace_support.py)
- [Multi-Workspace Testing](./tests/test_multi_workspace.py)
