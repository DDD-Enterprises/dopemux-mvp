---
id: supervisor-memory-pm-authority-reconciliation-2026-03-27
title: Supervisor Memory and PM Authority Reconciliation
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Reconciles PM-plane authority ADRs, Memory Trinity ADR, repo-truth-pack outputs, and current runtime behavior into one supervisor-facing map with explicit contradictions and narrowed unknowns.
graph_metadata:
  node_type: DocPage
  impact: high
---
# Supervisor Memory and PM Authority Reconciliation

## Reconciled authority map

### Stable and evidence-backed

- `Leantime` is the PM operational system of record.
- `Task Orchestrator` is the workflow authority.
- `ConPort` is the durable decision / progress / structured context authority.
- `dope-memory` is the chronicle / replay / reflection authority.
- `dope-context` is the retrieval authority.
- `Serena v2` is the technical-context authority.
- `dopecon-bridge` is supposed to be adapter-only.

This map is supported jointly by:

- `docs/90-adr/adr-pm-plane-authority-boundaries.md`
- `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md`
- `docs/planes/pm/pm-plane-read-matrix.md`
- `docs/planes/pm/pm-plane-write-matrix.md`
- `repo-truth-pack/{conport,dope-memory,dope-context,serena-v2}/`

## Unknowns removed or narrowed

### Previously unknown: Leantime integration role

Now narrowed to:

- primary machine seam is JSON-RPC at `/api/jsonrpc`
- plugin is secondary
- MCP is not the primary contract in current evidence
- Leantime owns PM entities but not workflow law

Evidence:
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md:58-88`
- `src/integrations/leantime_jsonrpc_client.py:32-47`

### Previously unknown: memory <-> Task Orchestrator relationship

Now narrowed to:

- workflow-significant transitions are canonically owned by Task Orchestrator
- progress logging is canonically owned by ConPort and only mirrored into dope-memory
- chronicle-worthy workflow events belong in dope-memory only as referenced/mirrored chronology
- project-scoped transition route still lacks a working canonical runtime binding

Evidence:
- `src/dopemux/pm/writes.py:165-260`
- `services/task-orchestrator/app/api/project_workflow.py:96-110`

### Previously unknown: memory <-> Leantime relationship

Now narrowed to:

- Leantime records can provide promotable source material
- Leantime content must be normalized before promotion into ConPort or dope-memory
- workflow-significant mutations are blocked on bridge PM routes and must be adjudicated by Task Orchestrator

Evidence:
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md:167-247`
- `services/dopecon-bridge/tests/test_leantime_route_contract.py:207-242`

## Contradictions now explicit

### 1. PM docs say bridge is adapter-only, but Task Orchestrator persists workflow state through bridge custom data

Architectural intent:

- `dopecon-bridge` must not be canonical for tasks, workflow state, next-action, or PM entity authority.

Runtime behavior:

- `WorkflowStore` reads and writes `workflow_ideas`, `workflow_epics`, and `workflow_audit` through dopecon-bridge `custom_data`.

Why it matters:

- This creates a persistence-boundary leak.
- It does not automatically make the bridge canonical, but it means canonical workflow state currently depends on a substrate the ADR classifies as non-canonical.

Evidence:
- `docs/90-adr/adr-pm-plane-authority-boundaries.md:133-152`
- `services/task-orchestrator/app/services/workflow_store.py:42-141`

### 2. PM read contract says project context belongs to ConPort and sprint snapshot to Leantime, but runtime read envelopes are partial and mislabeled

Architectural intent:

- `pm_get_project_context` -> `ConPort`
- `pm_get_sprint_snapshot` -> `Leantime`

Runtime behavior:

- both current read functions return empty/fail-closed payloads
- both helper envelopes set `canonical_backend="orchestrator"`
- provenance and supporting-source fields point elsewhere

Why it matters:

- supervisor tooling reading only `canonical_backend` would infer the wrong authority
- the current runtime is not just incomplete; it is internally contradictory on these two paths

Evidence:
- `docs/planes/pm/pm-plane-normalized-tool-surface.md:30-40`
- `src/dopemux/pm/reads.py:81-96`
- `src/dopemux/pm/reads.py:163-178`
- `src/dopemux/pm/reads.py:199-255`

### 3. ConPort is the target durable authority, but its own truth-pack says the strongest invariants are not enforced

Architectural intent:

- if a decision or progress is not in ConPort, it did not formally happen

Runtime behavior:

- truth-pack says this is not enforced
- mutable progress and deletable custom data remain possible

Why it matters:

- supervisor policy can still treat ConPort as the canonical target
- but enforcement work must be tracked separately from the conceptual authority map

Evidence:
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md:133-163`

### 4. dope-memory canonical server is on `3020`, but stdio tooling still points to legacy WMA `8096`

Architectural intent:

- `dope-memory` is the canonical chronicle service

Runtime behavior:

- truth-pack transport notes say the active stdio adapter proxies to legacy WMA `8096`
- the canonical dope-memory HTTP service is `3020`

Why it matters:

- any MCP or stdio client using the old adapter can silently land on the wrong runtime

Evidence:
- `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md:77-95`
- `repo-truth-pack/dope-memory/TRANSPORT_AND_RUNBOOK.md:195-196`

## What the supervisor can now treat as settled

1. `ConPort` vs `dope-memory`: ConPort owns structured durable decision/progress/context truth; dope-memory owns temporal chronology and correction chains.
2. `dope-memory` vs WMA: dope-memory on `3020` is the canonical chronicle runtime; legacy WMA on `8096` is not the authoritative memory future.
3. `Leantime` vs `Task Orchestrator`: Leantime owns PM records; Task Orchestrator owns workflow law.
4. `dope-context` and `Serena v2`: both are supporting planes, not PM or memory truth stores.
5. `conport-kg`: still not canonical in this checkout.

## Remaining uncertainty

- There is still no `repo-truth-pack` packet for `Task Orchestrator`, `Leantime`, or `dopecon-bridge` in this checkout.
- The PM-side packet is therefore evidence-backed from live repo inspection, but not yet normalized into the same extracted-pack format as the memory services.
- `Task Orchestrator` transition execution remains partially unbound at the project workflow route.
- `pm_get_project_context` and `pm_get_sprint_snapshot` need runtime repair before their envelopes can be considered trustworthy.

## Enforcement implications

- Do not allow direct Leantime status mutation to count as workflow truth.
- Do not allow dopecon-bridge storage usage to become a quiet excuse for bridge authority expansion.
- Do not allow ConPort's incomplete invariant enforcement to blur the target ownership model.
- Do not allow legacy WMA transport to stand in for the canonical dope-memory runtime.
