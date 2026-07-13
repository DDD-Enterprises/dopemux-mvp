# Route State Machine

## State ownership

- **PROPOSED:** The Universal Router journals state transitions for the orchestration attempt only.
- **PROPOSED:** Later execution, validation, audit, and PR states are projections driven by refs from their owning systems.
- **PROPOSED:** Release one automates transitions only through `ROUTE_RECOMMENDED`; it may record explicit `OPERATOR_ACCEPTED`.

## States

| State | Label | Meaning |
|---|---|---|
| `INTAKE` | **PROPOSED** | TaskEnvelope accepted and journaled. |
| `CLASSIFIED` | **PROPOSED** | DCP ref and route-specific risk/privacy record resolved. |
| `CAPABILITIES_RESOLVED` | **PROPOSED** | Registry and snapshot inputs are bound. |
| `POLICY_CHECKED` | **PROPOSED** | Active policy and hard invariants evaluated. |
| `ROUTE_RECOMMENDED` | **PROPOSED** | Primary recommendation and alternatives emitted. |
| `OPERATOR_ACCEPTED` | **PROPOSED** | Operator accepted the recommendation scope; not equivalent to protected-action approval. |
| `HANDOFF_PREPARED` | **PROPOSED** | Future phase assembled existing handoff contract with refs. |
| `EXECUTION_ACCEPTED` | **PROPOSED** | Dopetask accepted the handoff. |
| `EXECUTING` | **PROPOSED** | Certified runner adapter started execution. |
| `VALIDATING` | **PROPOSED** | Validation system is evaluating results. |
| `AUDITING` | **PROPOSED** | Audit system is evaluating evidence independently or with declared non-independence. |
| `COMPLETED` | **PROPOSED** | Required validation, audit, proof, and readiness conditions for the task phase are met. |
| `ESCALATED` | **PROPOSED** | Attempt requires supervisor or explicit higher-scope decision. |
| `BLOCKED` | **PROPOSED** | Hard condition prevents continuation. |

## Legal transitions

| From | To | Label | Guard |
|---|---|---|---|
| none | `INTAKE` | **PROPOSED** | Valid TaskEnvelope. |
| `INTAKE` | `CLASSIFIED` | **PROPOSED** | DCP ref valid; route-specific classification complete. |
| `INTAKE` | `BLOCKED` | **PROPOSED** | Invalid repo binding, missing required classification, or prohibited input. |
| `INTAKE` | `ESCALATED` | **PROPOSED** | Ambiguous authority or operator scope. |
| `CLASSIFIED` | `CAPABILITIES_RESOLVED` | **PROPOSED** | Required registry/snapshot inputs are present or explicitly stale/unknown. |
| `CLASSIFIED` | `BLOCKED` | **PROPOSED** | Red lane, privacy conflict, or forbidden network/write posture. |
| `CLASSIFIED` | `ESCALATED` | **PROPOSED** | Risk/authority conflict cannot be resolved deterministically. |
| `CAPABILITIES_RESOLVED` | `POLICY_CHECKED` | **PROPOSED** | Active policy valid and snapshot posture accepted for task risk. |
| `CAPABILITIES_RESOLVED` | `BLOCKED` | **PROPOSED** | Required fresh capability/health/identity evidence absent for protected route. |
| `CAPABILITIES_RESOLVED` | `ESCALATED` | **PROPOSED** | No certified candidate, but operator/supervisor may choose a bounded investigation route. |
| `POLICY_CHECKED` | `ROUTE_RECOMMENDED` | **PROPOSED** | At least one eligible candidate. |
| `POLICY_CHECKED` | `BLOCKED` | **PROPOSED** | Hard policy conflict or no legal route. |
| `POLICY_CHECKED` | `ESCALATED` | **PROPOSED** | Competing high-risk choices or policy conflict. |
| `ROUTE_RECOMMENDED` | `OPERATOR_ACCEPTED` | **PROPOSED** | Explicit operator acceptance before expiry. |
| `ROUTE_RECOMMENDED` | `CAPABILITIES_RESOLVED` | **PROPOSED** | Explicit refresh creates a new attempt that supersedes the prior recommendation. |
| `ROUTE_RECOMMENDED` | `BLOCKED` | **PROPOSED** | Recommendation expires or new evidence introduces a hard block. |
| `ROUTE_RECOMMENDED` | `ESCALATED` | **PROPOSED** | Operator rejects all candidates or asks for protected override. |
| `OPERATOR_ACCEPTED` | `HANDOFF_PREPARED` | **PROPOSED** | Future phase only; handoff prerequisites and any HumanApprovalRef exist. |
| `OPERATOR_ACCEPTED` | `BLOCKED` | **PROPOSED** | Acceptance expires or policy/snapshot drift invalidates it. |
| `HANDOFF_PREPARED` | `EXECUTION_ACCEPTED` | **PROPOSED** | DopetaskHandoffRef says accepted. |
| `HANDOFF_PREPARED` | `BLOCKED` | **PROPOSED** | Dopetask/handoff rejects or blockers exist. |
| `EXECUTION_ACCEPTED` | `EXECUTING` | **PROPOSED** | Certified adapter starts within approved scope. |
| `EXECUTING` | `VALIDATING` | **PROPOSED** | RunnerResult produced. |
| `EXECUTING` | `BLOCKED` | **PROPOSED** | Policy, containment, or non-retryable execution failure. |
| `EXECUTING` | `ESCALATED` | **PROPOSED** | Retry/escalation budget exhausted or authority boundary touched. |
| `VALIDATING` | `AUDITING` | **PROPOSED** | Audit required and validation is sufficiently complete. |
| `VALIDATING` | `COMPLETED` | **PROPOSED** | Audit `NOT_REQUIRED`, validation passed, and proof requirements met. |
| `VALIDATING` | `BLOCKED` | **PROPOSED** | Validation failed without permitted repair. |
| `VALIDATING` | `ESCALATED` | **PROPOSED** | Repeated validation failure or conflicting results. |
| `AUDITING` | `COMPLETED` | **PROPOSED** | Audit `PASS` or permitted non-blocking `PASS_WITH_RISKS`; proof current. |
| `AUDITING` | `BLOCKED` | **PROPOSED** | Audit `FAIL` or required audit skipped/not run. |
| `AUDITING` | `ESCALATED` | **PROPOSED** | `NEEDS_SUPERVISOR`, conflict, unknown independence, or risk acceptance needed. |

## Terminal states

- **PROPOSED:** `COMPLETED`, `BLOCKED`, and `ESCALATED` are terminal for one attempt.
- **PROPOSED:** Continuation after a terminal state creates a new attempt with `parent_decision_id` and starts at `INTAKE` or `CLASSIFIED` depending on what changed.
- **PROPOSED:** Release one also treats `ROUTE_RECOMMENDED` and `OPERATOR_ACCEPTED` as operational stopping points, but not terminal historical states.

## First-release transition limit

```text
INTAKE -> CLASSIFIED -> CAPABILITIES_RESOLVED -> POLICY_CHECKED -> ROUTE_RECOMMENDED
                                                                      |
                                                                      v
                                                             OPERATOR_ACCEPTED
```

- **PROPOSED:** No release-one code may transition to `HANDOFF_PREPARED` or beyond.

## Retry limits

| Operation | Label | Limit | Rule |
|---|---|---:|---|
| Intake/schema validation | **PROPOSED** | 0 automatic retries | Return exact validation errors. |
| DCP classification | **PROPOSED** | 1 corrected attempt | Correction requires changed input or operator-provided missing evidence. |
| Snapshot file/read acquisition | **PROPOSED** | 1 retry | Only transient lock/read errors. |
| Policy evaluation | **PROPOSED** | 0 retries | Deterministic failure is not retried. |
| Provider transient request | **PROPOSED** | 1 same-route retry | Future phase; idempotent only and policy-permitted. |
| Validation after repair | **PROPOSED** | 1 revalidation | New RunnerResult/proof required. |
| Independent audit after fixes | **PROPOSED** | 1 re-audit | New bounded input manifest and report. |
| Model/reasoning escalation | **PROPOSED** | 2 total steps | At most one reasoning step then one model-tier/runner step. |
| Environment failure | **PROPOSED** | 1 same-tier retry | Never automatic premium escalation. |

## Escalation behavior

- **PROPOSED:** Reasoning escalation is permitted only for capability-sufficient routes that failed a quality/analysis gate, not for authentication, network, filesystem, sandbox, or provider-health failures.
- **PROPOSED:** Model-tier escalation is permitted only after a recorded quality/validation failure or an explicit capability mismatch.
- **PROPOSED:** Security, authority, and release tasks may begin at a high tier without consuming an escalation step when policy requires it.
- **PROPOSED:** When escalation would exceed cost, credit, network, containment, or identity constraints, transition to `ESCALATED`, not a silent override.

## Demotion behavior

- **PROPOSED:** Candidate selection may choose a cheaper certified route initially when all hard requirements are met.
- **PROPOSED:** In-task demotion is permitted only for cost/latency constraint changes before execution or after a completed phase boundary, never as a response to quality failure.
- **PROPOSED:** A route can be policy-demoted for repeated excessive cost, latency, or token overhead in shadow evaluation.
- **PROPOSED:** Demotion cannot weaken containment, audit independence, identity confidence, or validation requirements.

## Stale capability behavior

- **PROPOSED:** Low-risk read/draft tasks may receive a recommendation using stale capability evidence only when the candidate is marked `STALE`, no provider call is automatically made, and operator refresh is the next action.
- **PROPOSED:** Write, security, authority, audit-independent, benchmark, and release-sensitive routes block on required stale snapshots.
- **PROPOSED:** Stale positive provider health becomes `STALE`, not `UNAVAILABLE`.

## Identity conflicts

- **PROPOSED:** Any mismatch among requested, configured, proxy-reported, and provider-attested model values creates `CONFLICTING` identity evidence.
- **PROPOSED:** Pinned-model, benchmark, independent-audit, security, or release-sensitive flows transition to `BLOCKED` or `ESCALATED`.
- **PROPOSED:** Low-risk advisory flows may continue only with explicit conflict display and no certification claim.

## Policy conflicts

- **PROPOSED:** Invalid active policy blocks recommendation generation.
- **PROPOSED:** A local overlay that attempts to loosen a hard invariant is rejected.
- **PROPOSED:** Two simultaneously active policies with different hashes create `CONFLICTING` and block.
- **PROPOSED:** Operator hints never override policy.

## Audit failures

- **PROPOSED:** `FAIL` transitions to `BLOCKED`.
- **PROPOSED:** `NEEDS_SUPERVISOR` transitions to `ESCALATED`.
- **PROPOSED:** `REQUIRED_NOT_RUN` and `SKIPPED_WITH_REASON` block protected completion and release readiness.
- **PROPOSED:** `PASS_WITH_RISKS` is accepted only when policy classifies every remaining risk as non-blocking.

## Operator override

- **PROPOSED:** An operator override is a scoped external HumanApprovalRef, never an in-place state mutation.
- **PROPOSED:** It creates a new attempt and records which policy constraint, cost ceiling, or route preference was overridden.
- **PROPOSED:** Overrides cannot legalize secret leakage, fabricate model identity, convert skipped audit to pass, mutate another subsystem's authority, or bypass current-head proof for release.
