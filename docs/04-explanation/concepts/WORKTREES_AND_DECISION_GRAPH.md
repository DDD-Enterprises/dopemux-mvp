---
id: WORKTREES_AND_DECISION_GRAPH
title: Worktrees_And_Decision_Graph
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Worktrees, ConPort, and Dope Decision Graph

This document explains how per-project ConPort memory integrates with the global Dope Decision Graph (DDG) across multiple worktrees and projects.

## Identity and Isolation

- `DOPEMUX_WORKSPACE_ID` (workspace_id): Canonical project identifier (repo root path by default).
- `DOPEMUX_INSTANCE_ID` (instance_id): Per-worktree identifier (branch name by default).

Isolation rules:
- Shared statuses: COMPLETED/BLOCKED/CANCELLED — visible across instances.
- Isolated statuses: IN_PROGRESS/PLANNED — visible only within a worktree’s instance.

## ConPort Behavior

- Storage: PostgreSQL (relational) + Redis cache.
- Event publishing: decision/progress events to DopeconBridge.
- Auto seeding for new worktrees: first context read seeds from shared context if present.
- Auto fork (enabled): first progress read copies PLANNED/IN_PROGRESS items from shared into the new instance.
  - Toggle: `DOPEMUX_AUTO_FORK_PROGRESS=1` (default on)

### Instance Management Endpoints

- `POST /api/instance/fork`
  - Body: `{ "workspace_id": "...", "source_instance": null|"main"|"...", "target_instance": "optional" }`
  - Copies PLANNED/IN_PROGRESS progress from source (shared or instance) to the target instance.

- `POST /api/progress/promote`
  - Body: `{ "progress_id": "..." }`
  - Promotes an instance-local progress entry to shared (clears instance_id).

- `POST /api/progress/promote_all`
  - Body: `{ "workspace_id": "..." }`
  - Promotes all instance-local PLANNED/IN_PROGRESS entries to shared for the current instance.

## Dope Decision Graph (DDG)

- Storage: PostgreSQL + AGE (graph).
- Bridge: HTTP service that ingests ConPort events, provides endpoints, and mirrors data.
- Relational mirrors: `ddg_decisions`, `ddg_progress` for lightweight search/analytics.
- Graph upserts (best-effort): Project nodes, Decision nodes, Progress nodes, and edges:
  - `(:Decision)-[:BELONGS_TO]->(:Project)`
  - `(:Progress)-[:BELONGS_TO]->(:Project)`
  - `(:Progress)-[:RELATES_TO]->(:Decision)` when linked

### DDG Endpoints

- `GET /ddg/decisions/recent?workspace_id=&limit=` — recent decision summaries.
- `GET /ddg/decisions/search?q=&workspace_id=&limit=` — simple summary search.
- `GET /ddg/instance-diff?workspace_id=&a=&b=&kind=decisions|progress` — compare items across worktrees.
- `POST /ddg/decisions/link-similar?workspace_id=&min_overlap=&limit=` — naive similarity linker (creates SIMILAR_TO edges).
- `GET /ddg/decisions/related?decision_id=&k=` — embedding-based related decisions (fallback to naive if embeddings unavailable).
- `GET /ddg/decisions/related-text?q=&workspace_id=&k=` — text query for related decisions (embeds query, vector search + rerank).

### Embeddings

- Provider: `EMBEDDINGS_PROVIDER=voyageai|litellm|openai` (default: `voyageai`)
- Model: `EMBEDDINGS_MODEL` (default: `voyage-3-large`)
- VoyageAI: requires `VOYAGEAI_API_KEY`
- Reranker: `RERANKER_MODEL` (default: `reranker-2.5`)
- LiteLLM base: `LITELLM_BASE` (when using proxy provider)
- OpenAI: requires `OPENAI_API_KEY` (if chosen)
- Qdrant (recommended for scale): set `QDRANT_URL` (e.g., `http://host.docker.internal:6333`). Collection defaults to `ddg_decisions`.

Embeddings are mirrored to Postgres (`ddg_embeddings`), and indexed in Qdrant when available for fast KNN. Reranking uses VoyageAI’s `reranker-2.5` for high-quality results.

AGE config env (optional): `AGE_HOST`, `AGE_PORT`, `AGE_USER`, `AGE_PASSWORD`, `AGE_DATABASE`.

## Claude Configuration

- Global config wires all Docker MCP servers (stdio/SSE) automatically.
- Project config is auto-wired for ConPort per worktree; `.claude/claude_config.json` is maintained by:
  - `dopemux start` (auto)
  - `scripts/stack_up_all.sh` (auto)
  - `.git/hooks/post-checkout` (auto-installed)

Server names in Claude:
- Global: `mas-sequential-thinking`, `zen`, `context7`, `serena`, `exa`, `leantime-bridge`, `task-orchestrator`, `gptr-researcher-stdio`.
- Project: `conport` (stdio → docker exec into `mcp-conport[_<instance>]`).

Optional DDG MCP tools (global): `ddg-mcp` (stdio)
- Tools:
  - `related_decisions(decision_id, k)`
  - `related_text(query, workspace_id, k)`
  - `instance_diff(workspace_id, a, b, kind)`
  - `recent_decisions(workspace_id, limit)`
  - `search_decisions(q, workspace_id, limit)`
  - `conport_fork_instance(workspace_id, source_instance, target_instance, conport_url)`
  - `conport_promote(progress_id, conport_url)`
  - `conport_promote_all(workspace_id, conport_url)`

Tip: For project-local ConPort, `conport_url` is typically `http://localhost:3004` when your project’s ConPort container maps 3004 on the host.
