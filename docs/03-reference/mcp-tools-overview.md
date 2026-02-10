---
id: MCP_TOOLS_OVERVIEW
title: Mcp_Tools_Overview
type: reference
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# MCP Tools Overview (Dopemux)

This guide lists Dopemux MCP servers and their key tools with sample Claude usage.

## Global Servers

- ddg-mcp (stdio, on DopeconBridge)
  - related_decisions(decision_id, k)
  - related_text(query, workspace_id, k)
  - instance_diff(workspace_id, a, b, kind)
  - recent_decisions(workspace_id, limit)
  - search_decisions(q, workspace_id, limit)
  - conport_fork_instance(workspace_id, source_instance, target_instance, conport_url)
  - conport_promote(progress_id, conport_url)
  - conport_promote_all(workspace_id, conport_url)

- mas-sequential-thinking, zen (stdio)
- serena, exa, leantime-bridge (SSE)
- task-orchestrator (stdio on-demand)
- gptr-researcher-stdio (stdio)
- pal (stdio, includes apilookup for API/SDK documentation)

## Project Servers (per worktree)

- conport (stdio)
  - get_progress(workspace_id, status, limit)
  - get_decisions(workspace_id, limit)

- conport-admin (stdio)
  - fork_instance(workspace_id, source_instance, target_instance)
  - promote(progress_id)
  - promote_all(workspace_id)

## Sample Claude Prompts

### Find Related Decisions
```
Find decisions related to "optimize ConPort Redis caching" in this repo.
→ ddg-mcp.related_text(query="optimize ConPort Redis caching", workspace_id="${WORKSPACE}", k=8)
Then summarize the top 3 with links to worktrees.
```

### Compare Worktrees
```
Compare progress entries between feature/auth and main. Show items only in the feature branch.
→ ddg-mcp.instance_diff(workspace_id="${WORKSPACE}", a="feature/auth", b="main", kind="progress")
```

### Fork/Promote Instance Items
```
Fork active progress from shared into this instance to resume quickly.
→ conport-admin.fork_instance(workspace_id="${WORKSPACE}")

Promote this progress item to shared so it shows in all worktrees.
→ conport-admin.promote(progress_id="<uuid>")

Promote everything from this instance to shared.
→ conport-admin.promote_all(workspace_id="${WORKSPACE}")
```

### Project Memory Queries
```
List in-progress tasks for this project and propose 2 actionable next steps (< 25min each).
→ conport.get_progress(workspace_id="${WORKSPACE}", status="IN_PROGRESS", limit=10)
```

## Configuration

- VoyageAI
  - VOYAGEAI_API_KEY required
  - EMBEDDINGS_MODEL=voyage-3-large (default)
  - RERANKER_MODEL=reranker-2.5 (default)
- Qdrant (embeddings index)
  - QDRANT_URL (e.g., http://qdrant:6333)
  - QDRANT_COLLECTION=ddg_decisions (optional)
- AGE Graph (optional)
  - AGE_HOST, AGE_PORT, AGE_USER, AGE_PASSWORD, AGE_DATABASE

## Notes

- ConPort auto-wires per-worktree and auto-seeds/auto-forks to preserve momentum.
- DDG mirrors and graph upserts work best-effort; system continues to function without AGE/Qdrant.
