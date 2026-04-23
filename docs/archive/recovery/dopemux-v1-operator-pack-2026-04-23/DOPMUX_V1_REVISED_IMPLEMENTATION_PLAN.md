# Dopemux v1 Revised Implementation Plan

## Goal
Build a local-first, deterministic v1 dual-lane tmux operator model by freezing canonical baselines first, repairing contract drift second, and then layering thin orchestration and operator UX on top of existing authorities.

## Non-Negotiable v1 Baselines
- task-orchestrator runtime: `app.main:app` at `http://localhost:8000` REST
- packet truth: filesystem packet files, anchored on `TP-PM-ARCH-04A/04B`
- proof truth: dopetask bundle loader subset only
- tmux baseline: `orchestrator` layout only
- execution authority: dopetask wrapper
- bridge remains proxy only

## Out of Scope
- replacing dopetask
- merging ConPort / dope-memory / dope-context
- making bridge authoritative
- building a new agent architecture
- treating PAL/Serena/task-orchestrator as one runtime
- faking durable `.dopetask/series/*` if it is absent

---

## Phase 0 - Spec Freeze

### Objective
Freeze the canonical baselines before code work.

### Work
- publish v1 authority map
- publish canonical runtime/protocol choices
- publish packet baseline choice
- publish proof baseline choice
- publish tmux baseline choice
- publish separate lifecycle model:
  - task
  - packet
  - proof
  - review

### Exit criteria
- one written v1 spec exists
- all later implementation work can cite the same baselines

### Stop/replan triggers
- discovery of a conflicting runtime authority stronger than `app.main:app`
- discovery of an enforceable proof schema stronger than the dopetask loader subset

---

## Phase 1 - Contract Repairs

### Objective
Repair drift that blocks correctness before adding lane automation.

### Work
- normalize task-orchestrator runtime authority around `8000` REST
- remove or clearly deprecate stale `3014` defaults in active paths
- fix `/api/pm` miswire/unmounted drift, or explicitly keep it out of v1 and route through the correct task-manager surface
- normalize packet identity handling against filesystem truth
- resolve launcher/file packet ID mismatch (notably PRMS packet IDs)
- establish a proof writer/validator path aligned to the dopetask loader subset
- mark stale tmux/operator doc/script references as non-authoritative in docs or remove operational references if touched

### Exit criteria
- active code paths no longer depend on stale 3014/SSE assumptions
- packet IDs can be resolved against real files
- proof validation target is enforceable and implemented against the chosen subset

### Stop/replan triggers
- packet IDs cannot be normalized without breaking existing downstream consumers
- proof loader subset proves too narrow for the acceptance path and needs one explicit additive field set

---

## Phase 2 - Thin Adapters

### Objective
Introduce reference-bearing glue without collapsing contracts.

### Work
- add packet registry adapter
  - discovers packet files from filesystem
  - validates registry/index drift
  - exposes packet metadata to task-manager surfaces
- add dopetask command adapter
  - shells out through `scripts/dopetask`
  - does not import or reimplement dopetask internals
- add series state reader
  - reads `.dopetask/series/<series_id>/state.json` when present
  - maps series display state only
  - does not become series authority
- add proof validation adapter
  - validates proof against the chosen subset
  - returns states such as `missing`, `present_unvalidated`, `validated`, `failed`, `degraded`

### Exit criteria
- task-manager can reference packets without owning them
- execution lane can generate exact dopetask commands
- review lane can validate proof presence/schema without inventing acceptance

### Stop/replan triggers
- no usable series state exists and the code begins to assume durable `.dopetask/series/*`
- proof validation requires schema expansion beyond the agreed subset

---

## Phase 3 - Lane Semantics over tmux

### Objective
Add lane semantics on top of the existing `orchestrator` tmux layout.

### Work
- extend `tmux/cli.py` from `orchestrator`, not `dope`
- map pane/window roles to:
  - `control:planning`
  - `execution:supervisor`
  - `execution:implementer`
  - `monitor:state`
  - `review:proof`
- export lane-specific env vars:
  - workflow id
  - task id
  - packet id
  - series id
  - proof root
- add readable lane commands instead of hidden mutation:
  - control lane command
  - execution lane command
  - monitor lane command
  - review lane command

### Exit criteria
- operator can start one tmux layout and understand lane roles immediately
- commands are readable and copyable
- no lane implies hidden state mutation without explicit command names/flags

### Stop/replan triggers
- `orchestrator` layout cannot support the lane mapping cleanly
- lane work starts reviving stale dashboard/script archaeology instead of thin semantics

---

## Phase 4 - Integration and Review Wiring

### Objective
Wire task-manager, execution contract, and proof contract together through explicit references.

### Work
- link task-manager records to `packet_id`
- link execution path to `series_id` when present
- link proof validation results to review state
- link review decision back to task-manager state
- keep all links reference-based, not contract-collapsing
- ensure `PROOF_GENERATED` is not accepted proof

### Exit criteria
- selected task retains packet identity
- execution lane can run or print exact dopetask command
- monitor lane shows task state and series state as separate fields
- review lane can validate proof and hold acceptance separate from execution completion

### Stop/replan triggers
- implementation starts embedding packet or proof truth inside task-manager storage
- monitor lane begins collapsing task state and series state into one field

---

## Phase 5 - Doctor, Tests, Docs

### Objective
Add narrow verification and operator-facing docs.

### Work
- add operator doctor command
  - reports pass/fail/degraded for:
    - task-orchestrator URL/health
    - dopetask version
    - packet registry health
    - proof adapter health
    - lane command availability
    - ConPort/dope-memory/dope-context reachability
    - bridge proxy health
- add tests for:
  - task-manager transitions
  - queue/blocker derivation
  - packet registry discovery
  - series state mapping
  - proof validation states
  - lane command generation
- add one narrow smoke path:
  - select packet
  - generate execution command
  - inspect series state if present
  - validate proof
  - reflect review state
- update docs with exact commands and known degraded modes

### Exit criteria
- doctor reports exact pass/fail/degraded status
- narrow existing tests still pass
- new adapter/lane tests pass
- docs match the implemented baseline, not stale scripts or aspirational schemas

### Stop/replan triggers
- doctor starts depending on services not required for local-first v1 correctness
- docs drift immediately from runtime behavior

---

## Acceptance Criteria
- task-orchestrator is standardized on `http://localhost:8000` REST
- packet selection retains packet identity from filesystem truth
- execution lane can run or print exact dopetask command
- monitor lane shows task-manager state and series state separately
- review lane validates proof subset and does not equate `PROOF_GENERATED` with proof acceptance
- PM writes remain routed by authority:
  - task-orchestrator for workflow transitions
  - Leantime for metadata
  - ConPort for structured progress/decisions
  - dope-memory for chronicle
  - dope-context for retrieval
- bridge remains proxy/routing only in code and docs
- existing narrow tests continue to pass
- new lane/adapter tests pass

## Assumptions
- v1 is local-first and operator-driven
- existing tmux `orchestrator` layout is the substrate
- dopetask remains execution authority
- proof acceptance requires explicit validation
- Serena and PAL may support planning/research but are not required authorities for v1 correctness
