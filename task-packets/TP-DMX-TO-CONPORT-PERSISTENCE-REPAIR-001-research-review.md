---
id: TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-research-review
title: Tp Dmx To Conport Persistence Repair 001 Research Review
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Dmx To Conport Persistence Repair 001 Research Review (explanation) for
  dopemux documentation and developer workflows.
---
# Research Review — TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001

## Verdict

APPROVED for a compose-only repair plus static and synthetic contract tests.

## Evidence sufficiency

- Current WorkflowStore implementation, shared bridge client, bridge auth, and
  protected proxy routes were traced end-to-end.
- Canonical compose and the active ConPort launch script identify REST `3004`,
  MCP `3005`, and absent token injection.
- Current ConPort schema and REST writer prove synthetic upsert/idempotency on
  `(workspace_id, category, key)`.

## Approved scope

- `compose.yml`: configure Task Orchestrator to inherit the externally supplied
  bridge token; bind its REST URL and DopeconBridge's REST URL to `conport:3004`.
- One new static contract test and one narrowly extended synthetic persistence
  test. No direct writer, token generation, auth bypass, retry policy, schema,
  or live runtime change.

## Residual risks

- Token issuance and expiry lifecycle remains external configuration. This
  packet must state that it is not solved here.
- Static/synthetic tests prove wiring and upsert semantics, not live container
  reachability, JWT validity, or credential custody.
- Task Orchestrator work-item mutation remains unavailable; its workflow notes
  are `NOT_RUN` and do not authorize a status transition.
