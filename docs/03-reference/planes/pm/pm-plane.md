---
id: PM_PLANE
title: Pm Plane
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Pm Plane (reference) for dopemux documentation and developer workflows.
---
# PM_PLANE

This document is derived only from repository truth. Primary authority for this file is, in order: `docs/03-reference/truth/truth-gaps.md`, `docs/03-reference/truth/truth-data-events.md`, `docs/03-reference/truth/truth-systems.md`, `docs/03-reference/truth/truth-canonicals.md`, `src/dopemux/pm/writes.py`, `services/dopecon-bridge/README.md`, `services/dopecon-bridge/dopecon_bridge/routes.py`, `services/task-orchestrator/app/services/workflow_store.py`, and `services/task-orchestrator/app/adapters/bridge_adapter.py`.

It preserves split, ambiguous, and contradictory states where repo truth does not establish a single authority. It does not normalize unresolved drift. No runtime APIs, interfaces, or types are introduced or changed here.

## 1. PM Plane Definition

The PM plane is not a single system.

It is a distributed authority model for PM-domain concerns. Repo truth shows PM ownership split by domain slice, not collapsed into one service hub. `src/dopemux/pm/writes.py` assigns different canonical writers to metadata, workflow-significant transitions, and progress or decision logging. `docs/03-reference/truth/truth-gaps.md` and the derived secondary check in `docs/03-reference/systems/system-boundaries.md` both preserve PM authority as split rather than unified.

The safe current interpretation is:

- The PM plane is a documentation and contract boundary over multiple systems.
- Authority is per PM concern, not per service name.
- Any claim that one service owns all PM truth would exceed inspected repo evidence.

## 2. PM Authority Split

Observed PM authority split from repo truth:

- Metadata -> `Leantime`
- Workflow -> `task-orchestrator`
- Decisions -> `ConPort`
- Progress -> `ConPort`
- Memory receipts -> `dope-memory`

This split is stated directly in `src/dopemux/pm/writes.py` and repeated in `docs/03-reference/truth/truth-data-events.md`:

- `pm_update_work_item` performs canonical metadata writes through the Leantime client.
- `pm_transition_work_item` performs canonical workflow transitions through the task-orchestrator client and mirrors the outcome to Leantime.
- `pm_log_progress` performs canonical progress or decision-context logging through the ConPort client and mirrors to dope-memory.

Secondary consistency check: `docs/03-reference/planes/pm/pm-plane-write-matrix.md` does not list `dopecon-bridge` as a `canonical_writer` for any PM mutation row. Bridge mediation is present, but canonical writing remains assigned to the backend authority for each slice.

Mirror receipts are secondary evidence, not source truth. They record downstream reflection state after a canonical write; they do not replace the canonical system.

## 3. PM Flow Diagram (text)

`User / Agent -> task-orchestrator -> dopecon-bridge -> upstream systems (ConPort / Leantime) -> dope-memory (receipt)`

This is an observed bridge-mediated integration path, not proof that every PM write in the repo currently passes through the bridge. `docs/03-reference/truth/truth-data-events.md` shows task-orchestrator workflow persistence flowing outbound through DopeconBridge custom-data paths, and it separately shows `dopecon-bridge` routing selected PM calls to upstream services. At the same time, repo truth also includes normalized PM write helpers in `src/dopemux/pm/writes.py`, bridge-backed workflow persistence in `services/task-orchestrator/app/services/workflow_store.py`, and bridge-backed ConPort or PM adapters in `services/task-orchestrator/app/adapters/bridge_adapter.py`. The repo therefore contains multiple observed write-capable seams, and this document does not flatten them into one universal runtime path.

## 4. Bridge Role

`dopecon-bridge` is not PM authority.

Its active runtime role is adapter, router, translator, proxy, event transport, and policy-check layer. `services/dopecon-bridge/README.md` and `services/dopecon-bridge/dopecon_bridge/routes.py` explicitly constrain it to adapter-safe PM operations, ConPort-backed compatibility routes, and fail-closed blocking for bridge-local task creation or status mutation. Workflow-significant PM mutations are blocked unless adjudicated by task-orchestrator.

This creates a boundary risk. `docs/03-reference/truth/truth-gaps.md` calls out that downstream operators may still treat bridge endpoints as authoritative because they expose `/kg/*`, `/ddg/*`, and PM routing surfaces while repo truth simultaneously says the bridge must not be canonical task, workflow, decision, or progress authority.

The repo also contains a contradiction that must be preserved. `services/shared/dopecon_bridge_client/README.md` describes the bridge as a "single authority point" for coordination and several shared access paths. That wording conflicts with the sanctioned runtime truth in `services/dopecon-bridge/README.md` and the active route policy in `services/dopecon-bridge/dopecon_bridge/routes.py`, both of which explicitly deny canonical PM authority to the bridge. For PM-plane purposes, the sanctioned active runtime wins; the shared-client wording is terminology drift, not canonical PM authority.

## 5. Data Consistency Model

Canonical data lives in the named authority for each PM slice. Mirrored or reflected data is non-canonical.

Observed consistency model from `src/dopemux/pm/writes.py`:

- Canonical writes return `canonical_system` and `canonical_id`.
- Secondary reflections are reported through `mirror_receipts`.
- Reconciliation status is reported through `reconciliation_state`.

Observed consistency states:

- `SYNCED` means the canonical write succeeded and the configured mirror also succeeded.
- `PARTIAL` means the canonical write succeeded but mirror reconciliation is still incomplete because a mirror failed or was unavailable.

This is receipt-based validation, not single-store validation. The canonical system remains authoritative even when a mirror is stale, absent, or degraded. `docs/03-reference/planes/pm/write-boundaries.md` reinforces the same rule: canonical success and mirror success are separate outcomes, and mirror failure does not promote the mirror into source truth.

The safe current model is eventual consistency where mirrors exist:

- Canonical first
- Mirror second
- Receipt records whether reflection completed
- Downstream consumers must treat reflected state as secondary unless the named canonical authority agrees

## 6. Known Weaknesses

Observed risks from current repo truth:

- Split authority risk
  - `docs/03-reference/truth/truth-gaps.md` states that PM authority is split across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts, and warns that any service expanding beyond its declared slice creates silent contract drift.
- Bridge confusion
  - `TRUTH_GAPS.md`, `services/dopecon-bridge/README.md`, and the active bridge routes all show the same risk: bridge endpoints can look authoritative while the sanctioned runtime explicitly says they are not.
- Multiple write-capable paths
  - The repo contains `src/dopemux/pm/writes.py`, bridge proxy routes under `services/dopecon-bridge/dopecon_bridge/routes.py`, task-orchestrator bridge-backed persistence in `services/task-orchestrator/app/services/workflow_store.py`, task-orchestrator bridge-backed progress or PM routing in `services/task-orchestrator/app/adapters/bridge_adapter.py`, and shared bridge-client guidance in `services/shared/dopecon_bridge_client/README.md`. That multiplicity increases routing ambiguity even where the canonical writer for each PM slice is separately declared.

This document does not claim a single unified PM writer exists today. Repo truth supports the opposite: PM authority is distributed and still operationally easy to misread.

## 7. Required Improvements

These are repo-supported future resolutions, not claims of current completion.

### Single PM contract layer

`docs/03-reference/planes/pm/pm-plane-normalized-tool-surface.md` defines one normalized PM-plane tool surface so agents use a stable contract instead of raw subsystem-native methods. Current runtime evidence remains partial, but the contract direction is explicit: normalize the agent-facing PM layer instead of exposing backend-native write seams directly.

### Explicit write routing rules

`docs/03-reference/planes/pm/pm-plane-write-matrix.md` and `docs/03-reference/planes/pm/write-boundaries.md` already define the intended routing rules:

- one canonical writer per mutation class
- explicit required prechecks
- explicit forbidden direct paths
- fail-closed rejection for workflow-significant payloads on metadata routes

The remaining improvement is convergence: those routing rules need to remain the controlling PM contract across all observed write-capable seams.

### Stronger canonical guarantees

`docs/03-reference/systems/system-boundaries.md` forbids treating a bridge as source truth, allowing multiple writers for the same domain, allowing silent mirroring without receipts, or leaving ownership undeclared. `src/dopemux/pm/writes.py` already exposes a stronger receipt and reconciliation vocabulary through `canonical_system`, `canonical_id`, `mirror_receipts`, and `reconciliation_state`. The repo-supported direction is to extend those canonical guarantees consistently wherever PM-adjacent writes occur.
