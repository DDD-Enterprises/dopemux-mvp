# Dopemux v1 Dual-Lane Operator Spec v2

## 1. Purpose

Dopemux v1 is a dual-lane operator workflow for human-supervised multi-agent development.

It is not a unified agent runtime, not a unified memory layer, and not a replacement for task packets, dopetask, or proof bundles.

It is:
- a task-managed workflow
- a packet-driven execution workflow
- a proof-gated review workflow
- a tmux-based operator cockpit for planning, execution, monitoring, and review

## 2. Canonical Baselines

### Task manager runtime baseline
- Runtime authority: `services/task-orchestrator/app/main.py`
- Launch baseline: `uvicorn app.main:app`
- Canonical address: `http://localhost:8000`
- Protocol baseline: `HTTP/JSON REST`
- Not baseline for v1: `/info` SSE claims, `3014` defaults, legacy `task_orchestrator/app.py`, `query_server.py`

### Packet baseline
- Filesystem packet inventory is truth
- v1 packet baseline anchors on:
  - `task-packets/TP-PM-ARCH-04A.md`
  - `task-packets/TP-PM-ARCH-04B.md`
- `task-packets/INDEX.md` is not registry truth

### Proof baseline
- v1 proof baseline is the dopetask bundle loader subset
- Required for acceptance-layer parsing:
  - `artifacts`
  - one of `tp_id | pr_id`
- Canonical subset fields:
  - `status`
  - `summary`
  - `acceptance_checks`
  - `validation`
  - `manifest`
- Richer governance docs are advisory unless enforced by code

### tmux baseline
- Extend `orchestrator` layout only
- Preserve current layout names: `low | medium | high | orchestrator | dope`
- Preserve current orchestrator pane names as substrate:
  - `monitor:worktree`
  - `monitor:logs`
  - `orchestrator:control`
  - `sandbox:shell`
  - `agent:primary`
  - optional `agent:secondary`
- Do not use `dope` as the v1 baseline

## 3. Authority Map

### task-orchestrator
Owns:
- task-manager queue
- blockers
- workflow state
- workflow transitions
- task-manager metadata
- decomposition metadata
- assignment metadata

Does not own:
- packet execution
- proof acceptance
- ConPort truth
- dope-memory truth
- retrieval authority
- merge authority

### task packets + dopetask
Own:
- execution contract
- command scope
- worktree/branch targeting
- stop/replan boundaries
- execution runtime

### proof bundles + validator
Own:
- evidence contract
- proof presence
- proof schema validity
- acceptance-gate inputs

### ConPort
Owns:
- structured context
- structured decisions
- structured progress

### dope-memory
Owns:
- chronicle receipts
- history
- evidence trail mirror

### dope-context
Owns:
- code/docs retrieval
- indexing

### Leantime
Owns:
- passive PM metadata

### dopecon-bridge
Owns:
- transport/proxy behavior only

## 4. Lane Model

### Lane A: Control / Planning
Purpose:
- research
- architecture
- PM work
- decomposition
- packet drafting
- review orchestration
- decision promotion

Primary systems:
- task-orchestrator
- ConPort
- dope-context
- bounded PAL
- optional Serena

### Lane B: Execution
Purpose:
- packet acknowledgment
- implementation
- local verification
- proof submission

Primary systems:
- task packets
- dopetask
- linked worktrees
- bounded retrieval

### Lane C: Monitor
Purpose:
- service health
- task-manager state
- packet/proof status
- worktree state
- logs

### Lane D: Review
Purpose:
- proof inspection
- diff review
- reruns
- acceptance/rejection
- merge-readiness judgment

## 5. tmux Window Model

### Window `0:control`
Suggested mapping onto orchestrator layout primitives:
- `orchestrator:control` -> primary planning/supervisor pane
- `sandbox:shell` -> packet drafting / notes / retrieval support pane
- one monitor pane -> task-manager state view
- one monitor pane -> ConPort / context / blockers view

### Window `1:execution`
Suggested panes:
- supervisor execution pane
- implementer A
- implementer B
- implementer C

### Window `2:monitor`
Suggested panes:
- service health
- task queue / blockers
- worktree state
- packet/proof watcher

### Window `3:review`
Suggested panes:
- proof validation
- diff review
- rerun shell
- signoff / acceptance notes

### Worktree rule
- supervisor stays in main worktree
- one worker = one linked worktree
- never place two workers in one worktree
- every packet pins a base commit

## 6. Separate Lifecycles (Do Not Collapse)

### Task state
Owned by task-orchestrator.
Suggested v1 display states:
- `TODO`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `REVIEW_PENDING`
- `DONE`
- `CANCELED`

### Packet state
Owned by execution contract layer.
Suggested v1 states:
- `DRAFT`
- `ISSUED`
- `ACKED`
- `EXECUTING`
- `PROOF_SUBMITTED`
- `ACCEPTED`
- `REJECTED`
- `ABANDONED`

### Proof state
Owned by evidence layer.
Suggested v1 states:
- `MISSING`
- `SUBMITTED`
- `SCHEMA_VALID`
- `SCHEMA_INVALID`
- `REVIEWED`
- `ACCEPTED`
- `REJECTED`
- `DEGRADED`

### Review state
Owned by supervisor/control lane.
Suggested v1 states:
- `NOT_STARTED`
- `IN_REVIEW`
- `CHANGES_REQUESTED`
- `APPROVED`
- `SUPERSEDED`

### Hard rules
- task state is not packet state
- packet state is not dopetask series state
- series state is not proof state
- `PROOF_GENERATED` is not accepted proof
- review approval is what promotes packet/proof/task closure

## 7. Linkage Model

v1 must assume separate contracts with explicit references, not an already-unified lifecycle.

### Required references
- task-manager record -> `packet_id` reference
- packet -> `task_id` reference
- execution run -> `series_id` reference when present
- proof bundle -> `tp_id` or `pr_id`
- review result -> task-manager state update

### Current truth
These references exist only partially today. v1 should introduce thin glue, not pretend a unified model already exists.

## 8. Packet Contract

Task packets remain the execution contract.

### v1 minimum packet contract
A v1 packet should contain:
- packet id
- objective
- scope
- invariants
- commands
- acceptance criteria
- rollback / stop conditions
- base commit
- worker/worktree assignment
- optional task reference

### Packet truth rules
- filesystem packets are truth
- packet registry must derive from filesystem, not `INDEX.md`
- packet IDs must be normalized before automation

## 9. Proof Contract

Proof bundles remain the evidence contract.

### v1 minimum enforceable subset
- `tp_id` or `pr_id`
- `artifacts`
- `status`
- `summary`
- `acceptance_checks`
- `validation`
- `manifest`

### v1 acceptance rules
- missing required subset -> proof invalid
- heterogeneous historical proof files are evidence, not schema authority
- proof validation must be explicit
- packet completion cannot imply proof acceptance

## 10. Write Routing Rules

### Task-manager writes
Use task-orchestrator for:
- queue state
- blockers
- task state
- legal transitions
- assignment / linkage metadata

### Structured writes
Use ConPort for:
- promoted decisions
- promoted progress
- accepted active context

### Chronicle writes
Use dope-memory for:
- receipts
- accepted historical trail
- mirror events after promotion

### Metadata writes
Use Leantime for:
- passive PM metadata only

### Retrieval
Use dope-context for:
- code/docs retrieval only

### Proxy
Use dopecon-bridge for:
- transport/proxy only

## 11. Supervisor / Implementer Policy

### Supervisor
May:
- issue packets
- assign workers
- accept/reject proof
- promote decisions/progress
- request workflow transitions
- judge merge readiness

### Implementer
May:
- execute assigned packet
- use bounded retrieval allowed by packet
- run allowed commands
- submit proof
- propose local implementation notes

May not:
- freely write shared decisions
- advance workflow state without explicit command path
- self-accept proof
- self-complete tasks

## 12. PAL and Serena Policy

### PAL
- supervisor-primary adjunct only
- worker use only if packet-bounded
- treat as global retrieval input channel
- not control bus
- not proof authority
- not workflow authority

### Serena
- optional workspace-aware code helper
- not authority-bearing
- not control plane

## 13. Failure Handling

### Stale packet
Trigger:
- base commit invalidated
- overlapping accepted edits in allowed scope

Action:
- reject current proof until rebased and revalidated

### Invalid proof
Trigger:
- missing enforceable subset
- invalid schema
- failed required checks

Action:
- do not mark accepted
- return to review/rework path

### Infrastructure mismatch
Trigger:
- stale route assumptions (`/sse`, `/api/pm`, 3014)

Action:
- use canonical `http://localhost:8000` REST only
- fail closed on non-baseline route usage

## 14. v1 Scope Boundaries

In scope:
- task-manager references to packets/proofs
- packet registry normalization
- proof validation against enforced subset
- dual-lane tmux semantics over orchestrator layout
- command surfaces for control/execution/monitor/review

Out of scope:
- replacing dopetask
- merging memory systems
- making bridge authoritative
- treating PAL/Serena/task-orchestrator as one runtime
- pretending durable `.dopetask/series/*` exists when it does not

## 15. Hard Conclusion

Dopemux v1 should be built as a reference-linked dual-lane system:
- task-orchestrator manages tasks
- task packets + dopetask manage execution
- proof bundles + validator manage evidence acceptance
- ConPort / dope-memory / dope-context / Leantime remain split
- tmux `orchestrator` layout is extended with lane semantics
- supervisor remains the authority root
