---
id: ADR-SB-004
title: Domain, Classification, and Provider Policy
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-14'
last_review: '2026-08-14'
next_review: '2026-11-14'
prelude: Domain, Classification, and Provider Policy (adr) for dopemux Second Brain architecture authority.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001
    - TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001
---
# ADR-SB-004: Domain, Classification, and Provider Policy

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
machine contract        schemas/second_brain/contracts/ADR-SB-004.contract.json
operator disposition    ACCEPT
disposition ledger      proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/ADR_OPERATOR_DECISION_LEDGER.yaml
disposition worksheet   proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/04_ADR_DISPOSITION_WORKSHEET.md
```

The decision text below is a byte-slice of the candidate document at the pinned
sha256. It is not a restatement.
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
