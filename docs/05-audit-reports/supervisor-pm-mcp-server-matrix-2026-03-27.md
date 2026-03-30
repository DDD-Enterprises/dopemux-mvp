---
id: supervisor-pm-mcp-server-matrix-2026-03-27
title: Supervisor PM and Memory MCP Server Matrix
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Supervisor-facing matrix of PM and memory related MCP servers and adjacent runtime surfaces, grounded in repo-truth-pack evidence plus current repository runtime inspection where truth packs are missing.
graph_metadata:
  node_type: DocPage
  impact: high
---
# Supervisor PM and Memory MCP Server Matrix

## Scope and evidence class

- This matrix is for supervisor intake, not operator onboarding.
- `repo-truth-pack/` is the primary evidence base for `ConPort`, `dope-memory`, `dope-context`, and `Serena v2`.
- `Task Orchestrator`, `Leantime`, and `dopecon-bridge` do not have corresponding truth-pack directories in this checkout, so their rows use direct repository runtime inspection and tests instead.
- Where ADR intent and runtime behavior differ, the matrix records both and treats runtime as stronger evidence.

## Server matrix

| System | Plane / role | Active transport surface | Canonical responsibility | Durable store / substrate | Authority class | Supervisor reading | Evidence |
|---|---|---|---|---|---|---|---|
| `ConPort` | durable context / decisions / progress | HTTP REST `:3004`, JSON-RPC `POST /mcp`, MCP SSE `:3005/mcp`, MCP stdio proxy | decision objects, progress objects, structured project context | PostgreSQL durable store; Redis cache only | target canonical authority, but enforcement is partial | Use as the durable PM context and decision writer; do not assume runtime fully prevents bypass writes elsewhere | `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md`, `repo-truth-pack/conport/TRANSPORT_AND_RUNBOOK.md`, `repo-truth-pack/conport/INTEGRATION_NOTES.md` |
| `dope-memory` | chronicle / replay / recap / reflection | HTTP `:3020` active; Redis Streams internal ingest; legacy stdio adapter exists but targets the wrong service | chronological work log, replay, recap, reflection, trajectory, correction chains | SQLite canonical ledger; optional PostgreSQL mirror; Redis transport only | canonical chronicle authority | Use as the durable work chronology authority only; not PM entity truth and not decision truth | `repo-truth-pack/dope-memory/ARCHITECTURE_AND_INTENDED_USES.md`, `repo-truth-pack/dope-memory/DATA_MODEL.md`, `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md`, `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md` |
| `dope-context` | retrieval / search plane | MCP stdio default; HTTP / SSE / streamable-http on `:3010` | semantic retrieval, ranking, indexing over code/docs corpora | Qdrant vectors plus local snapshot files; no SQLite / Redis storage | canonical retrieval authority only | Use for evidence retrieval, never for durable PM or memory truth | `repo-truth-pack/dope-context/ARCHITECTURE_AND_INTENDED_USES.md`, `repo-truth-pack/dope-context/EXECUTIVE_SUMMARY.md`, `repo-truth-pack/dope-context/TRANSPORT_AND_RUNBOOK.md` |
| `Serena v2` | technical / code intelligence | local stdio MCP is the primary callable surface; separate HTTP dashboard `:8003`; Docker wrapper exposes a different SSE/info surface | technical and code intelligence, navigation, analysis, untracked-work support | own PostgreSQL intelligence DB; Redis navigation cache; ConPort integration for reads/writes | supporting technical-context authority, not PM truth | Use for implementation-aware context only; treat local stdio and Docker deployment as materially different surfaces | `repo-truth-pack/serena-v2/ARCHITECTURE_AND_INTENDED_USES.md`, `repo-truth-pack/serena-v2/EXECUTIVE_SUMMARY.md`, `repo-truth-pack/serena-v2/TRANSPORT_AND_RUNBOOK.md`, `repo-truth-pack/serena-v2/INTEGRATION_NOTES.md` |
| `Task Orchestrator` | workflow law / blockers / next action | FastAPI HTTP on `:3014` by default; project workflow routes under `/api/projects/{project_id}/workflow`; PM writes under `/api/pm` | workflow legality, blockers, next-action computation, workflow-significant transitions | runtime workflow state currently persists through `WorkflowStore` into `dopecon-bridge` `custom_data` | intended canonical workflow authority with a persistence-boundary leak | Use as workflow authority, but note that project-scoped transition binding is still unavailable and current persistence is not cleanly isolated from bridge/custom-data substrate | `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`, `services/task-orchestrator/app/api/project_workflow.py`, `services/task-orchestrator/app/api/pm_tools.py`, `services/task-orchestrator/app/services/workflow_service.py`, `services/task-orchestrator/app/services/workflow_store.py`, `services/task-orchestrator/tests/test_workflow.py` |
| `Leantime` | PM operational system of record | JSON-RPC `/api/jsonrpc` is the primary machine seam; plugin is secondary; no primary trustworthy MCP surface evidenced here | projects, tickets/tasks, sprints, milestones, PM-facing assignments and records | Leantime runtime storage is external to this repo; this repo evidences JSON-RPC adapters and bridge mediation | canonical PM record authority | Use as PM entity authority only; do not allow it to become workflow authority; normalize HTML-rich content before promoting into memory/context systems | `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md`, `src/integrations/leantime_jsonrpc_client.py`, `src/integrations/leantime_bridge.py`, `services/dopecon-bridge/tests/test_leantime_route_contract.py` |
| `dopecon-bridge` | adapter / router / translation plane | HTTP routes including `/route/pm`, `/events`, DDG and KG proxy routes | route and policy-wrap cross-system requests; proxy safe Leantime operations; publish/consume events | bridge-local state exists, but ADRs say it must stay non-canonical | adapter only by design, but still a runtime shadow-state risk | Do not treat the bridge as authority for PM records, workflow, decisions, or chronicle truth; current Task Orchestrator storage usage through bridge custom-data is debt, not a license | `docs/90-adr/adr-pm-plane-authority-boundaries.md`, `services/dopecon-bridge/tests/test_leantime_route_contract.py`, `services/task-orchestrator/app/services/workflow_store.py` |

## Authority map by object class

| Object class | Canonical owner | Mirrors / projections | Explicit non-owner rule |
|---|---|---|---|
| PM entities, sprint state, PM-facing task metadata | `Leantime` | `Task Orchestrator`, `ConPort`, `dope-memory` may hold links or reflections | workflow legality does not move here |
| Workflow legality, blockers, next action, transitions | `Task Orchestrator` | `Leantime` may reflect status after adjudication | no direct Leantime or bridge-local workflow authority |
| Decisions, progress, durable project context | `ConPort` | `dope-memory` may reference; `Serena` may consume or contribute | dope-memory is not decision truth |
| Chronicle / work history / replay / reflection | `dope-memory` | `dope-context` may index retrieval-safe material | ConPort and Leantime are not chronicle authorities |
| Retrieval indexes / ranking | `dope-context` | none | search results are not source truth |
| Technical context / code intelligence | `Serena v2` | durable attachments should still land in `ConPort` if promoted | Serena is not PM truth |

## Current landmines

1. `Task Orchestrator` workflow persistence currently uses `dopecon-bridge` `custom_data` categories `workflow_ideas`, `workflow_epics`, and `workflow_audit`, which weakens the clean separation between workflow authority and bridge adapter role.
2. The project-scoped Task Orchestrator transition route still returns an explicit unavailable receipt instead of performing a canonical transition.
3. `dope-memory`'s stdio adapter targets legacy WMA port `8096`, not the canonical dope-memory HTTP service on `3020`.
4. `Serena v2` has a 33-tool local stdio surface, but the Docker-deployed "Serena" wrapper does not expose the same surface.
5. `ConPort` is the target decision/progress/context authority, but its own truth-pack explicitly says the "if it is not in ConPort, it did not formally happen" invariant is not enforced in code.

## Immediate supervisor use

- Route PM entity writes to `Leantime`.
- Route workflow-significant requests to `Task Orchestrator`.
- Route decision/progress/context writes to `ConPort`.
- Route chronology and recap queries to `dope-memory`.
- Route retrieval/search to `dope-context`.
- Route technical/code context to `Serena v2`.
- Treat `dopecon-bridge` as mediation infrastructure, not a place where authority should accumulate.
