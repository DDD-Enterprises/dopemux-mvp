---
id: TRUTH_DATA_EVENTS
title: Truth Data Events
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Data Events (reference) for dopemux documentation and developer workflows.
---
# TRUTH_DATA_EVENTS

Method:
- `Observed` items come from code, schema, tests, or config inspected in this pass.
- `Inference` is explicitly labeled.
- `UNKNOWN` marks unresolved writer/reader behavior.

## A. Data / Storage Models

### `dope-memory` chronicle ledger

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/canonical_ledger.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/schema.sql`
- Observed canonical location resolution:
  - `DOPEMUX_CAPTURE_LEDGER_PATH` if set.
  - Absolute `workspace_id` path containing `.git` or `.dopemux`.
  - Upward search from cwd for `.git` or `.dopemux`.
  - Otherwise fail closed.
- Observed canonical file:
  - `repo_root/.dopemux/chronicle.sqlite`
- Observed SQLite behavior:
  - `PRAGMA foreign_keys = ON`
  - journal mode defaults to `WAL` via `DOPEMUX_SQLITE_JOURNAL_MODE`, with validation/fallback logic in store code.
- Observed schema objects:
  - `raw_activity_events`
  - `work_log_entries`
  - `issue_links`
  - `reflection_cards`
  - `trajectory_state`
  - `schema_migrations`
- Observed `work_log_entries` contract features:
  - category and entry_type enums enforced by SQL `CHECK`
  - `importance_score` bounded `1..10`
  - provenance fields required: `source_event_id`, `source_event_type`, `source_adapter`, `source_event_ts_utc`, `promotion_rule`, `promotion_ts_utc`
  - supersession support via `supersedes_entry_id`
  - unique scoped supersession index

### `conport` structured truth surfaces

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
- Observed storage split:
  - Milvus for vector similarity retrieval.
  - PostgreSQL for node and graph state.
- Observed tool-level data model:
  - `mem.upsert` stores node `type`, `id`, `text`, optional `metadata`, `repo`, `author`.
  - `graph.link` stores graph relationships with `from_id`, `to_id`, `relation`, optional `metadata`.
- Inference:
  - ConPort functions as structured truth plus semantic index, with vector hits resolved back to richer node records from PostgreSQL.

### `task-orchestrator` workflow persistence

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`
- Observed persistence model:
  - Workflow ideas are stored under custom data category `workflow_ideas`.
  - Workflow epics are stored under custom data category `workflow_epics`.
  - Workflow audit is stored under custom data category `workflow_audit`.
- Observed writer path:
  - Task-orchestrator writes through `AsyncDopeconBridgeClient`, not a local task-orchestrator database, in the inspected path.
- Observed PM authority split:
  - `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py` states:
    - metadata updates canonical in Leantime
    - workflow transitions canonical in task-orchestrator
    - progress and decision logging canonical in ConPort
    - dope-memory acts as mirror receipt sink for PM progress logging

### `ADHD engine` state surfaces

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py`
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/core/activity_tracker.py`
- Observed API state shapes:
  - endpoints exist for energy, attention, breaks, tasks, patterns, predictions, automation level, context save, unfinished work, progress, external activity, and git events.
- Observed dependency:
  - activity tracker references `ConPortMCPClient.get_progress`.
- UNKNOWN:
  - Exact persistent storage backends for these ADHD API surfaces were not fully traced in this pass.

### `dope-context` index/search storage

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
  - `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_hybrid_determinism.py`
- Observed behavior:
  - Indexing, docs indexing, hybrid search, sync, metrics, and autonomous indexing controls exist.
- Observed contracts:
  - Contract tests validate schemas under `/Users/hue/code/dopemux-mvp/services/dope-context/contracts`.
- UNKNOWN:
  - Exact on-disk or DB-backed index writers/readers were not fully traced in this pass.

## B. Event and Message Flow

### `dope-memory` request flow

- Observed request flow:
  - HTTP caller -> `/tools/memory_search` or sibling route in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
  - tool handler -> chronicle store lookup
  - search path -> trajectory boost application
  - response -> ranked entries plus pagination metadata
- Observed adjacent write routes:
  - `/tools/memory_store`
  - `/tools/memory_mark_issue`
  - `/tools/memory_link_resolution`
  - `/tools/memory_correct`
  - `/tools/memory_generate_reflection`
  - `/tools/memory_reflections`
  - `/tools/memory_trajectory`

### `task-orchestrator` workflow and coordination flow

- Observed request flow:
  - HTTP caller -> `/api/workflow/*` or `/api/coordination/*` in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
  - service layer -> `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_service.py`
  - persistence -> `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`
  - outbound -> DopeconBridge custom-data client
- Observed event flow:
  - coordination events are broadcast to connected WebSocket clients through `/ws/coordination`
- Inference:
  - task-orchestrator uses bridge-mediated persistence to keep workflow state in the broader shared truth plane instead of owning its own local DB in the inspected path.

### `dopecon-bridge` event and proxy flow

- Observed request flow:
  - HTTP caller -> `routes.py` route group
  - route -> auth/event/task/PM/KG adapter logic
  - outbound -> upstream MCP HTTP tools or direct ConPort HTTP endpoints
- Observed event flow:
  - `/events` routes publish to Redis-backed event bus through `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/event_bus.py`
- Observed PM proxy flow:
  - PM requests enter `/route/pm`
  - workflow-significant mutations are policy-checked
  - selected tool calls route to upstream services through `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py`

### `conport` semantic request flow

- Observed request flow:
  - MCP caller or HTTP caller -> `mem.search`
  - vector similarity query against Milvus
  - record enrichment/fetch against PostgreSQL
  - response serialized as text content or JSON
- Observed graph flow:
  - `graph.link` creates relationships
  - `graph.neighbors` traverses relationships from PostgreSQL-backed graph state

### `repo-truth-extractor` execution flow

- Observed CLI flow:
  - `dopemux extractor` / `dopemux upgrades` -> `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`
  - command resolves runner path -> `run_extraction_v5.py`
  - subprocess executes runner in resolved repo root
  - artifacts are written under `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/v3/runs`
- Observed contradiction:
  - `dopemux truth` in `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` bypasses this path and invokes legacy `PipelineRunner`.

## C. Retrieval / Ranking / Determinism Behavior

### `dope-memory` ranking

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/tests/test_trajectory_boost_in_ranking.py`
- Observed behavior:
  - search fetch limit is `min(top_k * 2, 20)`
  - `top_k` is clamped to `1..10`
  - raw chronicle matches receive trajectory boost through `TrajectoryManager`
  - final ordering is:
    - descending `boosted_score`
    - descending timestamp parsed from `ts_utc`
    - ascending `id`
- Observed determinism:
  - presence of explicit sort key and ranking test indicates deterministic tie-break intent.

### `dope-context` hybrid search determinism

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_hybrid_determinism.py`
- Observed behavior:
  - reciprocal rank fusion ties are broken by document id.
  - repeated runs are expected to preserve stable order.
- Observed contract discipline:
  - contract tests exist under `/Users/hue/code/dopemux-mvp/services/dope-context/tests/contract/test_dope_context_contracts.py`.

### `conport` semantic retrieval

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
- Observed behavior:
  - semantic retrieval uses vector similarity through Milvus.
  - result details are resolved from PostgreSQL.
- UNKNOWN:
  - Exact ranking tie-break order beyond Milvus result order was not fully traced in this pass.

### PM determinism surfaces

- Observed authority:
  - `/Users/hue/code/dopemux-mvp/src/dopemux/pm/models.py`
- Observed behavior:
  - canonical PM task IDs are deterministically derived in model code.
  - task status is normalized via typed models.

## D. Unknowns and Contradictions

- Contradiction:
  - `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py` targets `http://localhost:8096`, while `/Users/hue/code/dopemux-mvp/services/registry.yaml` and `compose.yml` place `dope-memory` on `3020`.
- Contradiction:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` says canonical runtime is `app/main.py (Port 3014)`, while `/Users/hue/code/dopemux-mvp/services/registry.yaml` and `compose.yml` use `8000`, and the Dockerfile targets the hard-failing module.
- Contradiction:
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config*.{json,yaml}` reference missing `services/dope-context/run_mcp.sh`, while the Dockerfile and tests indicate `python -m src.mcp.server`.
- Contradiction:
  - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` `truth` command uses legacy `PipelineRunner`, while `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/README.md` and extractor commands point to v5.
- UNKNOWN:
  - Canonical Serena implementation authority between `/Users/hue/code/dopemux-mvp/services/serena` and `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`.
- UNKNOWN:
  - Canonical agent-system authority between `/Users/hue/code/dopemux-mvp/services/agents`, `/Users/hue/code/dopemux-mvp/src/dopemux/agent_orchestrator.py`, and `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/agents`.
- UNKNOWN:
  - Exact persistence model for the non-dope-memory `working-memory-assistant` app surface and several ADHD API subsystems.
