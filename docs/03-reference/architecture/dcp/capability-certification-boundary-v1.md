---
id: dcp-capability-certification-boundary-v1
title: "DCP Capability Certification Boundary V1"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Separate capability requirements, five-layer identity observation, certification, execution, and judgment.
---

# DCP Capability Certification Boundary V1

Capability requirement, observation, certification, execution, and judgment are
separate records.

## Identity layers

Always record independently:

- requested;
- configured;
- response-claimed;
- proxy-reported;
- provider-attested.

Absent evidence produces `UNKNOWN`; identity is never inferred across layers.
Exact requested provider/model remains binding when substitution is false.
GPT-5.6 cannot satisfy a retained GPT-5.5 named gate.

## Certification

Certification requires a current capability snapshot, matched identity,
verified independence, and audit-only scope. Certification may authorize
substantive judgment for its exact subject. It never grants repository or Task
Orchestrator mutation.

## Result classes

Substantive judgment, terminal intake/binding failure, and pre-judgment
transport/capacity failure are mechanically distinct. Only substantive judgment
may report PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR. Retry policy applies
only before substantive judgment.
