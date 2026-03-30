---
id: supervisor-pm-evidence-packet-2026-03-27
title: Supervisor PM and Memory Authority Evidence Packet
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Supervisor-facing evidence packet for PM and memory authorities, promotion semantics, storage roles, and integration boundaries, organized in the requested priority order.
graph_metadata:
  node_type: DocPage
  impact: high
---
# Supervisor PM and Memory Authority Evidence Packet

## Evidence basis

- Primary evidence base in this checkout:
  - `repo-truth-pack/conport/`
  - `repo-truth-pack/dope-memory/`
  - `repo-truth-pack/dope-context/`
  - `repo-truth-pack/serena-v2/`
- Missing truth-pack coverage in this checkout:
  - `Task Orchestrator`
  - `Leantime`
  - `dopecon-bridge`
- For the missing PM-side packs, this packet uses direct repository runtime inspection and tests.

## Priority 1. Canonical memory and PM roles

### Durable memory

- `ConPort` is the intended durable authority for decisions, progress, and structured project context.
- Runtime evidence: `ConPort` runs a canonical data server on `:3004`; all reads and writes flow through PostgreSQL with Redis as cache only.
- Important constraint: ConPort's truth-pack says this authority is only partially enforced in code; the repo does not yet prevent bypass writes elsewhere.

Evidence:
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:25-29`
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:57-100`
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:133-152`

### Working memory / chronicle memory

- `dope-memory` is the canonical chronicle authority.
- It owns temporal work log capture, replay, recap, reflection, trajectory, and correction chains.
- Canonical storage is SQLite, with optional PostgreSQL mirror and Redis streams only as transport.

Evidence:
- `repo-truth-pack/dope-memory/ARCHITECTURE_AND_INTENDED_USES.md:7-25`
- `repo-truth-pack/dope-memory/ARCHITECTURE_AND_INTENDED_USES.md:118-133`
- `repo-truth-pack/dope-memory/DATA_MODEL.md:151-168`

### Session memory

- `dope-memory` session state is chronicle-oriented, not general PM authority.
- Session boundaries and reflections are derived from event streams and idle/pulse windows.
- `Serena v2` has session lifecycle code, but its own truth-pack says those session tools are dead code at the MCP level and are not the canonical PM memory surface.

Evidence:
- `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md:116-155`
- `repo-truth-pack/serena-v2/WORKFLOW_AND_GATES.md:47-51`
- `repo-truth-pack/serena-v2/ARCHITECTURE_AND_INTENDED_USES.md:173-175`

### Project memory / durable project context

- The target owner is `ConPort`, not `Leantime` and not `dope-memory`.
- PM-plane docs define `pm_get_project_context` and `pm_get_decision_context` around `ConPort`.
- Runtime drift remains: `src/dopemux/pm/reads.py` currently returns an empty/fail-closed project-context envelope and incorrectly labels its `canonical_backend` as `orchestrator` even while provenance says `leantime`.

Evidence:
- `docs/planes/pm/pm-plane-normalized-tool-surface.md:30-40`
- `docs/planes/pm/pm-plane-read-matrix.md:16-27`
- `src/dopemux/pm/reads.py:81-96`
- `src/dopemux/pm/reads.py:199-206`

### Project / PM operational record truth

- `Leantime` is the canonical PM operational system of record for projects, tasks, sprints, milestones, and PM-facing state.
- The primary machine integration seam is JSON-RPC, not MCP.
- PM-plane write docs and ADRs consistently reject Leantime as workflow authority.

Evidence:
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:65-81`
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md:58-88`
- `src/integrations/leantime_jsonrpc_client.py:32-47`
- `src/integrations/leantime_jsonrpc_client.py:73-87`

### Workflow truth

- `Task Orchestrator` is the canonical workflow authority for blockers, next action, legality, gating, and transitions.
- PM-plane read/write matrices route queue/blocker/state/transition operations to Task Orchestrator.
- Runtime drift remains: the project-scoped transition route exists but still returns an explicit unavailable receipt instead of performing the canonical transition.

Evidence:
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:82-96`
- `docs/planes/pm/pm-plane-write-matrix.md:18-23`
- `services/task-orchestrator/app/api/project_workflow.py:96-110`
- `services/task-orchestrator/app/api/project_workflow.py:178-199`

### Graph memory

- `conport-kg` is not evidenced as canonical in this checkout.
- The PM-plane ADR explicitly says it is architecturally important but blocked pending remediation and runtime validation.
- No `repo-truth-pack/conport-kg` directory exists here, so there is no hard runtime packet to upgrade its status.

Evidence:
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:182-191`

## Priority 2. Promotion / demotion / supersession

### dope-memory promotion

- Promotion is gated by a strict pipeline: redact, normalize event type, allowlist check, provenance validation, deterministic ID generation, then SQLite insert.
- Only a closed allowlist is promotable: `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `workflow.phase_changed`, `manual.memory_store`.
- Non-promotable events are discarded.

Evidence:
- `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md:3-42`
- `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md:44-57`

### Provenance requirements

- All promoted chronicle entries require `source_event_id`, `source_event_type`, `source_adapter`, `source_event_ts_utc`, `promotion_rule`, and `promotion_ts_utc`.
- Sentinel values `pre_migration`, `unknown`, and empty string are banned at runtime.

Evidence:
- `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md:58-74`
- `repo-truth-pack/dope-memory/DATA_MODEL.md:53-61`

### Append-only and correction model

- `dope-memory` corrections are handled through supersession chains, not in-place edits.
- Chain rules are explicit: head-only correction, max depth 10, no forks, no cycles.
- This is the strongest append-only / evidence-preserving memory model present in the inspected stack.

Evidence:
- `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md:75-115`
- `repo-truth-pack/dope-memory/DATA_MODEL.md:27-69`

### ConPort "promotion" warning

- `ConPort` uses the term "promotion" differently.
- In code, promotion means changing `instance_id` visibility for progress entries, not supervisor-reviewed truth promotion.
- There is no provenance-backed supervisor promotion chain in ConPort runtime.

Evidence:
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:147-163`

### PM-plane transition and reflection

- `pm_transition_work_item` treats Task Orchestrator as canonical and Leantime as mirror only.
- `pm_log_progress` treats ConPort as canonical and `dope-memory` as chronicle mirror only.
- Both are best-effort on the mirror path and degrade instead of silently changing authority.

Evidence:
- `src/dopemux/pm/writes.py:165-216`
- `src/dopemux/pm/writes.py:218-260`
- `services/task-orchestrator/tests/test_leantime_reflection.py:146-205`

## Priority 3. Authority and boundary docs

### Canonical writer and source of truth

- PM entity lifecycle: `Leantime`
- Workflow law and transitions: `Task Orchestrator`
- Decisions / progress / durable project context: `ConPort`
- Chronicle / replay / reflection: `dope-memory`
- Retrieval indexes: `dope-context`
- Technical context: `Serena v2`

This is the architectural target and is supported by ADRs plus the PM read/write matrices.

Evidence:
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:61-191`
- `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md:55-155`
- `docs/planes/pm/pm-plane-read-matrix.md:14-32`
- `docs/planes/pm/pm-plane-write-matrix.md:14-31`

### Sync direction and conflict resolution

- `dope-memory` mirror direction is one-way from SQLite canonical ledger to PostgreSQL mirror.
- `Task Orchestrator` writes canonical workflow decisions first, then mirrors or reflects out to Leantime.
- `ConPort` publishes best-effort events to `dopecon-bridge`; bridge unavailability does not block the canonical write.

Evidence:
- `repo-truth-pack/dope-memory/ARCHITECTURE_AND_INTENDED_USES.md:118-133`
- `src/dopemux/pm/writes.py:183-216`
- `repo-truth-pack/conport/INTEGRATION_NOTES.md:92-137`

### "Do not store X here" rules

- `dope-context` never writes durable decision truth; it reads ConPort decisions and ADHD state but stays on the search plane.
- `Leantime` is not workflow authority.
- `dope-memory` is not decision truth, workflow truth, or PM entity truth.
- `dopecon-bridge` must not become canonical for tasks, next action, decisions, progress, or workflow state.

Evidence:
- `repo-truth-pack/dope-context/ARCHITECTURE_AND_INTENDED_USES.md:198-215`
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md:104-148`
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:133-152`
- `repo-truth-pack/dope-memory/ARCHITECTURE_AND_INTENDED_USES.md:118-125`

### Boundary leak now evidenced

- `Task Orchestrator` runtime persistence uses `WorkflowStore`, which writes workflow ideas, epics, and audit records through `dopecon-bridge` `custom_data`.
- This does not make `dopecon-bridge` canonical, but it does mean workflow runtime state currently depends on a bridge-mediated storage path that the ADRs call out as debt.

Evidence:
- `services/task-orchestrator/app/services/workflow_store.py:42-90`
- `services/task-orchestrator/app/services/workflow_store.py:113-141`

## Priority 4. Data model / storage docs

### SQLite / Postgres / Redis / vector roles

| System | Canonical store | Mirror / cache | Role |
|---|---|---|---|
| `ConPort` | PostgreSQL | Redis cache | durable decisions, progress, project context |
| `dope-memory` | SQLite | PostgreSQL mirror, Redis streams transport | chronicle, reflection, replay, trajectory |
| `dope-context` | Qdrant + local snapshot files | Redis only for ADHD feature flags | semantic retrieval and indexing |
| `Serena v2` | own PostgreSQL intelligence DB | Redis navigation cache | technical context and analysis |
| `Task Orchestrator` | no cleanly isolated store evidenced; current workflow store uses bridge `custom_data` | optional sync engine / Redis coordination | workflow law plus bridge-backed entity/audit persistence |

Evidence:
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:57-100`
- `repo-truth-pack/dope-memory/DATA_MODEL.md:151-168`
- `repo-truth-pack/dope-context/EXECUTIVE_SUMMARY.md:54-60`
- `repo-truth-pack/serena-v2/ARCHITECTURE_AND_INTENDED_USES.md:126-157`
- `services/task-orchestrator/app/services/workflow_store.py:42-141`

### Retention / TTL

- `dope-memory.raw_activity_events` has 7-day TTL.
- `dope-memory.work_log_entries` are durable and never auto-deleted.
- `ConPort` uses Redis cache TTLs but PostgreSQL is the durable store.

Evidence:
- `repo-truth-pack/dope-memory/DATA_MODEL.md:5-26`
- `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md:156-167`
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:89-100`

### Replay / rebuild semantics

- `dope-memory` is the clearest rebuildable evidence system: deterministic work-log IDs, semantic migrations, replay and recap tools, and one-way mirror semantics.
- `ConPort` is durable but not append-only for all object classes.

Evidence:
- `repo-truth-pack/dope-memory/DATA_MODEL.md:141-194`
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:147-163`

## Priority 5. Integration docs

### ConPort <-> dope-memory

- Intended relation: ConPort owns decisions/progress/context; dope-memory may ingest decision/progress-derived chronicle entries with provenance.
- PM write helper enforces this split: `pm_log_progress` writes canonically to ConPort, then mirrors to dope-memory.

Evidence:
- `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md:166-205`
- `src/dopemux/pm/writes.py:218-260`

### dope-memory <-> dopecon-bridge

- `dope-memory` truth-pack shows Redis event ingestion and optional downstream integrations, but no evidence that dopecon-bridge is the chronicle authority.
- Bridge remains transport or adapter infrastructure; it should not absorb chronicle truth.

Evidence:
- `repo-truth-pack/dope-memory/ARCHITECTURE_AND_INTENDED_USES.md:126-133`
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:133-152`

### memory <-> Task Orchestrator

- Workflow outcomes should remain in Task Orchestrator.
- Chronicle-worthy workflow events can be mirrored into dope-memory.
- Project-scoped workflow transition remains incompletely wired at runtime.

Evidence:
- `src/dopemux/pm/writes.py:165-216`
- `services/task-orchestrator/app/api/project_workflow.py:96-110`
- `services/task-orchestrator/app/api/project_workflow.py:178-199`

### memory <-> Leantime

- Leantime is the PM record authority, but raw Leantime content must be normalized before promotion into ConPort or dope-memory.
- Workflow-significant writes through bridge routes are blocked and explicitly require Task Orchestrator adjudication.

Evidence:
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md:167-247`
- `services/dopecon-bridge/tests/test_leantime_route_contract.py:207-242`

### memory <-> Serena

- Serena is a consumer and contributor to ConPort and has its own technical-context storage.
- It is not a memory or PM authority.

Evidence:
- `repo-truth-pack/serena-v2/INTEGRATION_NOTES.md:8-27`
- `repo-truth-pack/serena-v2/ARCHITECTURE_AND_INTENDED_USES.md:145-147`

### memory <-> conport-kg

- No truth-pack evidence in this checkout.
- Current ADR status remains "not canonical until remediated."

Evidence:
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:182-191`

## Requested extraction format: title / filename / important lines

### 1. `repo-truth-pack/dope-memory/WORKFLOW_AND_GATES.md`

- Promotion pipeline is redact -> normalize -> allowlist -> provenance validation -> deterministic ID -> SQLite insert.
- Non-promotable events are discarded.
- Required provenance fields are explicit and sentinel values are banned.
- Corrections use supersession chains with no forks and no cycles.
- `work_log_entries` are durable; `raw_activity_events` alone are TTL-bound.

### 2. `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md`

- Canonical data server is `enhanced_server.py` on `:3004`.
- PostgreSQL is the single durable store; Redis is cache only.
- Doc claims about formal decision/progress authority are not fully enforced in code.
- "Promotion" in ConPort means instance visibility change, not supervisor truth promotion.

### 3. `repo-truth-pack/dope-context/ARCHITECTURE_AND_INTENDED_USES.md`

- dope-context owns the search plane only.
- It writes to Qdrant and local snapshots.
- It never writes durable ConPort or ADHD truth.
- Read-only integration to memory/cognitive planes is explicit.

### 4. `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md`

- JSON-RPC is the primary Leantime machine seam.
- Leantime is canonical for PM entities, not workflow.
- HTML-rich content must be normalized before promotion into memory/context systems.
- Leantime MCP is explicitly not the primary contract today.

### 5. `services/task-orchestrator/app/services/workflow_store.py`

- WorkflowStore persists `workflow_ideas`, `workflow_epics`, and `workflow_audit` through dopecon-bridge `custom_data`.
- That means Task Orchestrator workflow persistence is currently bridge-mediated.
- This is an authority leak relative to the ADR goal that the bridge remain adapter-only.

## Bottom line for supervisor

- The high-confidence canonical map is now clear.
- The major remaining landmines are not "who should own what"; they are runtime leaks where those boundaries are not yet cleanly enforced.
- The most important leak on the PM side is Task Orchestrator persistence through dopecon-bridge `custom_data`.
- The most important leak on the memory side is ConPort's incomplete enforcement of its own durable-authority claims.
- The most important transport drift is dope-memory's stdio adapter still targeting legacy WMA `8096`.
