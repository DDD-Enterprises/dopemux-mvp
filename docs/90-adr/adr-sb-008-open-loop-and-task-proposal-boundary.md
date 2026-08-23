---
id: ADR-SB-008
title: Open Loop and Task Proposal Boundary
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-14'
last_review: '2026-08-14'
next_review: '2026-11-14'
prelude: Open Loop and Task Proposal Boundary (adr) for dopemux Second Brain architecture authority.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001
    - TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001
---
# ADR-SB-008: Open Loop and Task Proposal Boundary

## Status

* Accepted by the human operator on 2026-08-14.

Acceptance makes this an accepted architecture record. **It confers no
implementation, runtime, production, or enablement authority**, and none may be
inferred from it. The implementation-time gates below remain exactly where they
were.

## Authority binding

```text
candidate document      docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
candidate sha256        e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c
ratification binding    a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34
clause inventory sha256 b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439
machine contract        schemas/second_brain/contracts/ADR-SB-008.contract.json
operator disposition    ACCEPT
disposition ledger      proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/ADR_OPERATOR_DECISION_LEDGER.yaml
disposition worksheet   proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/04_ADR_DISPOSITION_WORKSHEET.md
```

The decision text below is a byte-slice of the candidate document at the pinned
sha256. It is not a restatement.
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

## Implementation-time gates, unchanged by acceptance

```text
denial fixtures            NOT_IMPLEMENTED
runtime conformance        NOT_RUN
retrieval benchmarks       NOT_RUN
purge completeness         NOT_RUN
multi-project isolation    NOT_RUN
split-brain proof          NOT_RUN
encryption implementation  ABSENT

implementation execution   NOT_AUTHORIZED
runtime enablement         NOT_AUTHORIZED
```
