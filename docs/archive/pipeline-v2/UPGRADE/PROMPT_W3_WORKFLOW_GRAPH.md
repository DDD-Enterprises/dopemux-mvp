---
id: PROMPT_W3_WORKFLOW_GRAPH
title: Prompt W3 Workflow Graph
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Prompt W3 Workflow Graph (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt W3 (v2): Global Workflow Graph Builder

**Outputs:** `WORKFLOW_GRAPH_GLOBAL.json`

---

## TASK

Produce ONE JSON file: `WORKFLOW_GRAPH_GLOBAL.json`.

## INPUTS

- `WORKFLOW_SURFACE_OPS.json` from W1
- `WORKFLOW_SURFACE_LLM.json` from W2
- `DOC_WORKFLOWS.json` (merged, from D1 if available)
- `SERVICE_MAP.json` (from code extraction A)
- `LLM_SERVER_CALL_SURFACE.json` (from I2)
- `DB_SURFACE.json` (from code extraction D)

## GOAL

Build a mechanical workflow graph showing service/tool/store connections based on **exact string matches only**.

## WORKFLOW_GRAPH_GLOBAL.json

### Nodes

Extract unique node names from:
- **Services** (from SERVICE_MAP.json, WORKFLOW_SURFACE_OPS.json)
- **Scripts/Targets** (from WORKFLOW_SURFACE_OPS.json)
- **MCP Tools/Servers** (from LLM_SERVER_CALL_SURFACE.json)
- **Stores/DBs** (from DB_SURFACE.json - table names)

For each node:
```json
{
  "node_id": "node:<type>:<name>",
  "node_type": "service|script|mcp_tool|mcp_server|db_table|gate|store",
  "node_name": "<exact name>",
  "source_artifacts": ["SERVICE_MAP.json", "..."]
}
```

### Edges

Derive edges mechanically:
1. **Compose dependencies**: If service A has `depends_on: [B]`, add edge `A → B`
2. **Workflow steps**: If step text mentions two node names in sequence, connect them
3. **MCP calls**: If instruction references "call X" and mentions node Y, add edge `instruction → X`
4. **Script orchestration**: If script mentions multiple services, connect script → services

For each edge:
```json
{
  "edge_id": "edge:<from_node_id>:<to_node_id>",
  "from_node": "node:service:adhd_engine",
  "to_node": "node:db_table:chronicle",
  "edge_type": "depends_on|calls|writes_to|reads_from|routes_to",
  "evidence": [
    {
      "path": "compose.yml",
      "line_range": [45, 47],
      "excerpt": "depends_on: chronicle"
    }
  ]
}
```

## RULES

- **Exact string match only** - do not infer connections
- **Include evidence pointers** on each edge
- **No guessing** - only connect if names match literally
- **JSON only**, ASCII only
- **Deterministic sorting** by (node_id, edge_id)

## OUTPUT FORMAT

```json
{
  "artifact_type": "WORKFLOW_GRAPH_GLOBAL",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "nodes": [...],
  "edges": [...],
  "graph_metrics": {
    "total_nodes": 45,
    "total_edges": 67,
    "isolated_nodes": 3,
    "node_types": {"service": 12, "mcp_server": 8, "..."}
  }
}
```
