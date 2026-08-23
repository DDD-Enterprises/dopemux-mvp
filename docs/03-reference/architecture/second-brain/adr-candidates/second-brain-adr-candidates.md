---
id: second-brain-adr-candidates
title: Second Brain ADR Candidates
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-07'
last_review: '2026-08-07'
next_review: '2026-11-05'
prelude: Corrected candidate ADR traceability derived from the ratified R2 architecture; all ADRs remain candidates pending a separate acceptance gate.
status: CANDIDATE
ratification_binding_sha256: a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34
source_candidate_sha256: 94b735c72ff3533f0cd73bed18fd3fb64b164530f7ef360f37584c73504a4e8e
source_adr_candidates_sha256: 9cff1e6c90c009ccc931676df14c838e6affafa7732fb11b5aecc0b8cf0858da
fo01: TRACEABILITY_REPAIR
---
# 24 ADR Candidates

These are architecture candidates only. Every ADR below remains `PROPOSED`; this synthesis does not alter the repository ADR index or confer implementation authority.

## Standing drift recheck precondition (MA-08)

Every ADR below carries the boilerplate acceptance condition "Any authority-corpus drift is re-adjudicated before implementation planning." MA-08 (`TP-DMX-SECOND-BRAIN-ARCHITECTURE-AMENDMENTS-001`) makes that concrete and standing, not a one-time check: before any of these ADRs is accepted, before a slice task packet is authorized, and before implementation planning begins, re-run the full-diff drift check from discovery base `72af781e42e0702d9047946e0f5a250e7dff0fa5` to the then-current remote main and produce a fresh `DRIFT_RECHECK.md`. An authority or privacy change in that diff blocks acceptance; a contained runtime change is recorded and the affected slice re-gated, not silently absorbed. This amendment run's own recheck (current main `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda`, disposition `MATERIAL_DRIFT_CONTAINED`) does not satisfy this precondition for a future acceptance or authorization decision — each one re-runs it fresh. ADR-SB-008 in particular is not accepted merely because MA-06 was applied to it here.

## ADR-SB-001: Extension Boundary and Non-Authority

**Status:** `PROPOSED`

### Context

The repository has no accepted Second Brain product and forbids a fourth canonical memory plane.

### Proposed decision

Create a Dopemux PCP/DCP-compatible extension. It owns control logic, derived read models, projections, local spool coordination, purge coordination, and receipts only. Canonical writes go to existing authorities.

### Consequences

* One package plus optional worker
* No canonical SB database
* Disable extension without changing canonical stores

### Rejected alternatives

* Dedicated Second Brain database
* ConPort as universal store

### Evidence and traceability

* `SB-DEC-001`
* `SB-DEC-002`
* `SB-DEC-027`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-002: Capture, Candidate, Review, and Promotion

**Status:** `PROPOSED`

### Context

Automatic capture must not silently promote candidates or mutate downstream authorities.

### Proposed decision

Append captured events and candidates to Dope-Memory, build a non-canonical review read model, require digest-bound affirmative review, route approved actions to exact canonical targets, and append promotion receipts to Dope-Memory.

### Consequences

* Replayable candidate history
* Default DEFER/NO MUTATION
* No cross-authority transaction fiction

### Rejected alternatives

* Direct extraction-to-ConPort
* Markdown review as authority

### Evidence and traceability

* `SB-DEC-003`
* `SB-DEC-004`
* `SB-DEC-005`
* `SB-DEC-006`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-003: Recall Fusion and Provenance

**Status:** `PROPOSED`

### Context

Recall spans structured authority, chronology, source-native state, and advisory retrieval without allowing search rank to become truth.

### Proposed decision

Use deterministic authority-first fusion with pre-model policy filtering, freshness and contradiction detection, bounded advisory retrieval, and evidence/access/uncertainty metadata on every response.

### Consequences

* Answer-first output
* Historical and current states remain distinct
* Partial outages are explicit

### Rejected alternatives

* Vector-first answer generation
* Model-selected access control

### Evidence and traceability

* `SB-DEC-016`
* `SB-DEC-017`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-004: Domain, Classification, and Provider Policy

**Status:** `PROPOSED`

### Context

Domain and classification are separate dimensions, and unknown eligibility cannot be safely inferred by a model.

### Proposed decision

Use project/hue/dom/shared and public/internal/confidential/restricted. Evaluate identity, grants, provider, embedding, custody, backup, and operation policy before retrieval disclosure or model context assembly. Unknown denies.

### Consequences

* Dom synthetic-only
* Shared disabled without grant
* No confidential/restricted semantic indexing in v1

### Rejected alternatives

* Post-retrieval filtering
* Model self-policing

### Evidence and traceability

* `SB-DEC-010`
* `SB-DEC-011`
* `SB-DEC-012`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-005: Markdown Projection Contract

**Status:** `PROPOSED`

### Context

Operators benefit from readable durable views, but Markdown and Obsidian must not become accidental authorities.

### Proposed decision

Compile deterministic Markdown from canonical snapshot revisions with stable paths, managed/manual regions, visible freshness, content hashes, purge propagation, and no silent write-back. Obsidian is an optional opener.

### Consequences

* Regenerable vault
* Manual regions preserved
* Canonical sources always win

### Rejected alternatives

* Markdown-first canonical vault
* Obsidian runtime dependency

### Evidence and traceability

* `SB-DEC-018`
* `SB-DEC-019`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-006: Local Spool and Custody Interface

**Status:** `PROPOSED`

### Context

Outage capture needs bounded durability, but an unencrypted spool can become a private-data trapdoor.

### Proposed decision

Define `LocalSpoolPort` and `CustodyPort`. Spool records are non-canonical, identity/domain/class scoped, deterministic, integrity-protected, short-lived, idempotently flushed, purge-aware, and never remote backed up. Public is allowed; internal requires OS-protected storage; confidential/restricted remain disabled until verified encryption and key ownership.

### Consequences

* Crash-safe eligible capture
* No unknown-class spooling
* Custody product remains replaceable

### Rejected alternatives

* Plaintext universal spool
* Cloud queue fallback

### Evidence and traceability

* `SB-DEC-014`
* `SB-DEC-015`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-007: Forget, Purge, and Residual Verification

**Status:** `PROPOSED`

### Context

Hide-from-view, retrieval denial, logical tombstone, physical deletion, and backup expiry are different operations.

### Proposed decision

Model Archive, Forget, and Purge separately. Build a dependency graph, impact preview, explicit approval, per-surface receipts, residual scan, and completion receipt. Searchable residual count must be zero before success. Impossible physical deletion uses explicit tombstone/retrieval denial and pending backup-expiry state.

### Consequences

* No soft-delete masquerading as purge
* Derived representations participate
* Irreversible steps require immediate confirmation

### Rejected alternatives

* UI-only deletion
* Best-effort fire-and-forget purge

### Evidence and traceability

* `SB-DEC-019`
* `SB-DEC-029`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-008: Open Loop and Task Proposal Boundary

**Status:** `PROPOSED`

### Context

An unresolved commitment is not necessarily a PM task, and the PM/workflow authority path is not yet operationally unambiguous.

### Proposed decision

Represent detected loops as suggested candidates. Confirmation appends open/close/cancel events to Dope-Memory; the active list is derived. Task proposals are separate candidates. Actual task creation requires Leantime plus Task Orchestrator proof and explicit approval; it is disabled initially.

**MA-06 PM-semantics firewall** (`TP-DMX-SECOND-BRAIN-ARCHITECTURE-AMENDMENTS-001`): confirmed open-loop events are chronological attention markers, not tasks. A confirmed open loop, and its derived current-state view, may never carry an assignee, PM priority, workflow status, sprint state, ownership assignment, due-driven escalation, automatic scheduling, or task completion state. `OpenLoopCandidate.due_at` is advisory display metadata only. Any task-shaped behavior must be represented as a separate `TaskProposal` and mutated only through the disabled `TaskPromotionRequest` path (Slice 6). Leantime and Task Orchestrator remain the sole authorities for PM and workflow semantics; this ADR does not grant Dope-Memory or the Second Brain any PM authority.

### Consequences

* No automatic task pressure
* Chronology remains in Dope-Memory
* ConPort never owns task state
* Open loops carry zero PM-semantic fields; `due_at` cannot trigger scheduling or escalation

### Rejected alternatives

* Every loop becomes task
* ConPort progress entry as task

### Evidence and traceability

* `SB-DEC-006`
* `SB-DEC-007`
* `SB-DEC-008`
* `SB-DEC-030`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-009: Single-Project Safety and Identity Dependencies

**Status:** `PROPOSED`

### Context

Path hashes, ports, and singleton event streams cannot safely establish canonical project identity.

### Proposed decision

Require registry-backed identity envelopes and current service capability receipts for authority operations. Permit one active automatic-capture project, explicit project switching, writer epochs, and wrong-project denial. Multi-project background capture remains disabled until isolation proof.

### Consequences

* Fail-closed split-brain prevention
* Mac mini remains optional
* No host-singleton routing authority

### Rejected alternatives

* Port-based identity
* Implicit current-directory project selection for writes

### Evidence and traceability

* `SB-DEC-009`
* `SB-DEC-013`
* `SB-DEC-022`
* `SB-DEC-024`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
## ADR-SB-010: UX Contract

**Status:** `PROPOSED`

### Context

ADHD-supportive operation requires low interruption and clear consequences without hiding authority or privacy decisions.

### Proposed decision

Use Capture, Recall, Review; one dominant next action; at most seven visible queue items; answer-first recall; evidence one action away; session-end batching; and immediate interruption only for privacy, identity, data-loss, irreversible-action, or authority-conflict conditions. Consequential defaults are DEFER or CANCEL.

### Consequences

* Quiet terminal and agent UX
* No dashboard dependency
* No productivity scoring or surprise writes

### Rejected alternatives

* Always-on notification stream
* Gamified backlog

### Evidence and traceability

* `SB-DEC-020`
* `SB-DEC-021`

### Acceptance conditions

* Independent reviewer confirms alignment with accepted repository authority.
* Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance. Required denial fixtures MUST be implemented, executed, and pass before the affected implementation capability is authorized for enablement. Absence of not-yet-implemented denial fixtures does not constitute implementation evidence and does not permit any runtime, production, or enablement claim.
* No runtime, implementation, or production claim is inferred from acceptance.
* Any authority-corpus drift is re-adjudicated before implementation planning.
