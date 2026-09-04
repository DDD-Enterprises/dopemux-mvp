---
id: universal-router-audit-broker-boundary-v1
title: "Universal Router Audit Broker Boundary V1"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Bind audit capability, identity, subject, execution, and mechanically distinct result classes without mutation authority.
---

# Universal Router Audit Broker Boundary V1

Audit Broker binds requests to current capability evidence, exact identity
layers, exact subject, an execution receipt, and a result. It routes and records;
it does not create authority missing from those records.

## Required sequence

1. Observe capability and all five identity layers.
2. Certify current capability, exact identity alignment, and independence.
3. Bind request to packet, head, digest, required capabilities, requested
   provider/model, and mandatory evidence.
4. Record execution identity and complete untruncated evidence.
5. Emit exactly one mechanically classified result.

## Failure discipline

- `MALFORMED`, `HEAD_MISMATCH`, `SUBJECT_MISMATCH`, and
  `REQUIRED_IDENTITY_UNKNOWN` are terminal intake/binding failures, not
  substantive judgments.
- `TRANSPORT_FAILURE` and `CAPACITY_FAILURE` occur before judgment and require
  current retry policy.
- `PASS`, `PASS_WITH_RISKS`, `FAIL`, and `NEEDS_SUPERVISOR` are substantive
  judgments only.

No route shops auditors after substantive judgment. No result mutates repository
or task state. Audit, readiness, merge, and activation remain separate gates.
