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

## Contract ownership and resolution

`CapabilityRequirementRef` owns required capability, requested provider/model,
substitution policy, minimum evidence policy, and required identity layers. It
does not own exact audit subject, actual runner/tool, observed execution,
certification judgment, or repository authority.

`AuditRequest` owns exact packet/head/tree/digest subject, one or more exact
capability-requirement references, requested runner/tool, requested
provider/model, required independence, substitution policy, and certification
reference. Its retained `required_capabilities` must equal capabilities from the
resolved requirements. Resolved requirements must agree with request
provider/model and forbid substitution.

`AuditorCapabilitySnapshot` is observed state for one exact subject. It records
observed or `UNKNOWN` route identity, all five provider/model identity layers,
capability availability, and verified, unverified, or `UNKNOWN` independence.
No missing observation is inferred.

`AuditorCertification` binds one request to one current snapshot for the same
exact subject and exact capability-requirement set. It retains audit-only scope,
matched identity, verified independence, satisfied capability, and no repository
or task mutation authority.

`AuditExecutionReceipt` records actual runner/tool and provider/model identity
layers. A satisfied result requires request route, observed snapshot route, and
execution route to agree exactly. Required identity layers must be observed and
equal the request and resolved requirement identity. For substantive judgment,
receipt mandatory evidence refs must be an order-insensitive superset of the
resolved `AuditRequest.mandatory_evidence_refs`: every requested opaque ref must
appear exactly once under `AuditExecutionReceipt.mandatory_evidence.refs`.
Supplemental refs may be present, but they cannot substitute for missing
requested refs. Ordering has no authority semantics.

Before substantive judgment, deterministic validation resolves the complete
request, capability requirement, certification, snapshot, execution receipt,
and result chain. Missing, ambiguous, stale, `UNKNOWN`, unavailable,
substituted, subject-mismatched, route-mismatched, identity-mismatched, or
unverified records cannot authorize judgment.

## Result classes

Substantive judgment, terminal intake/binding failure, and pre-judgment
transport/capacity failure are mechanically distinct. Only substantive judgment
may report PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR. Retry policy applies
only before substantive judgment.
