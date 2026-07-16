# ADR: Audit Broker Authority

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `03_ADR_AUDIT_BROKER_AUTHORITY.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## ADR metadata

| Field | Value |
|---|---|
| ADR ID | `ADR-DMX-AUDIT-BROKER-001` |
| Status | `PROPOSED_FOR_INDEPENDENT_AUDIT` |
| Decision type | Architecture and authority boundary |
| Chosen first release | Operator-triggered local broker, mechanical execution only |
| Chosen later path | Trusted-main GitHub request workflow, pull-based pickup, isolated workers, separate publisher |

## Context

`OBSERVED` Dopemux is the operator control surface. Existing repository guidance rejects promoting bridges, helpers, mirrors, or agent families into canonical authority. The accepted local probe shows no broker implementation and no executable model route. `[AGENTS] [RULES] [LOCAL:PROBE_SUMMARY]`

`INFERRED` An audit transport layer is still needed to bind a PR to an exact head, execute a bounded route, collect proof, and return evidence without granting the model GitHub write access.

## Decision

`PROPOSED` Introduce an **Audit Broker** as a narrow adapter and execution coordinator.

The broker may:

- validate a canonical audit request;
- verify repository, PR, base SHA, head SHA, workflow identity, freshness, nonce, and digests;
- classify eligibility using Dopemux-owned policy inputs;
- enforce a durable single-job lease;
- launch an eligible worker;
- collect and normalize a result;
- seal the result and hand it to a human or publisher.

The broker must not:

- decide merge or release readiness;
- write canonical embedded-audit verdict semantics;
- override PR Steward;
- choose an uncertified route;
- execute candidate code itself;
- hold provider credentials for multiple tools;
- hold GitHub write credentials;
- silently retry through another provider or model;
- use Task-router, PAL, DopeconBridge, or agent helper families as delegated authority.

## Authority map

| Domain | Canonical authority | Broker role |
|---|---|---|
| Operator intent and route recommendation | Dopemux plus human operator | Receive approved request |
| Audit-proof semantics | Existing embedded-audit contract | Produce evidence compatible with it, never fork it |
| PR intake and merge-readiness evaluation | PR Steward | Supply exact-head evidence |
| Execution transport | Audit Broker | Coordinate one bounded run |
| Candidate execution | Disposable worker | Run allowlisted commands only |
| Provider credentials | Per-tool credential boundary | Never expose to broker-wide or candidate-execution context |
| GitHub publication | Human first, separate GitHub App later | Broker writes sealed spool only |
| Approval | Human operator | Broker cannot approve |

## Options considered

| Option | Label | Decision | Rationale |
|---|---|---|---|
| Operator-triggered local broker | `PROPOSED` | **Selected first release** | Smallest shape with exact-head proof and visible human control. |
| GitHub-hosted request plus local pull | `PROPOSED` | **Selected later path** | Automates ingress without exposing local host to arbitrary workflow execution. |
| Persistent dedicated self-hosted runner | `REJECTED` | Do not use as broker | Dedicated naming does not eliminate PR-controlled compromise or persistent state. |
| Ephemeral self-hosted runner | `PROPOSED_WITH_LIMITS` | Credential-free worker only | Useful lifecycle hygiene; unsafe with provider credentials and hostile execution. |
| Dedicated per-tool OS users | `PROPOSED` | Required defense in depth | Separates homes, configs, keychains, and attribution, but is not a same-host sandbox. |
| Disposable VM workers | `PROPOSED` | Preferred candidate-execution boundary | Stronger kernel and cleanup boundary than a shared host account. |
| Containers | `PROPOSED_WITH_LIMITS` | Lower-risk credential-free work only | Shared-kernel risk must be explicit. |
| Manual application receipt | `PROPOSED` | Required compatibility path | Preserves access to blocked/manual tools without pretending they are unattended adapters. |
| OpenRouter fallback | `PROPOSED_WITH_LIMITS` | API fallback only | Must be pinned, policy-approved, and certified. |
| Direct provider API | `PROPOSED_WITH_LIMITS` | Preferred exceptional private fallback | Better direct trace and policy surface, still disabled pending approval and certification. |

## Consequences

### Positive

`INFERRED`

- Credentials, hostile data, publication authority, and governance authority remain in separate zones.
- Mechanical validation can be delivered without waiting for vendor ambiguity to evaporate.
- Every model integration has a uniform promotion gate rather than bespoke optimism.
- Exact-head result binding becomes a first-class contract.

### Costs

`INFERRED`

- First release is intentionally manual and slower.
- Model-capable tools remain dormant until evidence exists.
- Multiple OS users or VMs increase operational burden.
- A separate publisher introduces another component, but prevents the far worse broker-as-god-object pattern.

## Invariants

`PROPOSED`

1. Route eligibility is a conjunction of independent gates, never a single boolean inferred from CLI presence.
2. The broker fails closed on stale head, replay, malformed output, identity mismatch, policy mismatch, containment failure, or cost uncertainty.
3. A failed environment does not select a different route.
4. Publication is exact-head bound and idempotent.
5. Manual receipts are labeled manual and cannot masquerade as automated proof.
6. The broker is replaceable transport. Its records are evidence, not canonical business truth.

## Status rationale

`UNKNOWN` The ADR is ready for independent architecture audit, but not for implementation authorization. Worker technology, tool conformance, credential lifecycle, and route certification remain open.
