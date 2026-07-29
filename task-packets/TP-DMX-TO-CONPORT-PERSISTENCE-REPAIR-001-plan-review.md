---
id: TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-plan-review
title: Tp Dmx To Conport Persistence Repair 001 Plan Review
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Dmx To Conport Persistence Repair 001 Plan Review (explanation) for dopemux
  documentation and developer workflows.
---
# Plan Review — TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001

## Verdict

APPROVED.

## Scope check

Plan changes only canonical compose wiring and named tests. It preserves the
existing WorkflowStore -> authenticated bridge -> ConPort REST authority path,
does not use Task Orchestrator API key as bridge auth, and adds no writer,
credential value, retry, schema, or live runtime path.

## Verification check

Plan includes a RED compose-contract test, existing bridge/store serialization
tests, synthetic bearer-header assertion, synthetic ConPort custom-data
contract, compose syntax-only rendering, packet schema validation, and diff
validation. Live JWT issuance, container reachability, and writes remain out
of scope and must be reported `NOT_RUN`.

## Risks retained

External JWT issuance/expiry remains a deployment concern. The token expression
is required at compose interpolation so authentication fails closed before Task
Orchestrator starts; this packet does not invent token issuance or rotation.
