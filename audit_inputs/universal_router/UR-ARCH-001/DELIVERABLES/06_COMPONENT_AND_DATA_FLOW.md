# Component and Data Flow

## Record ownership rule

- **PROPOSED:** Every durable record names one owner. Cross-system records contain refs, hashes, and normalized observations, not copied authority.
- **PROPOSED:** A decision can include multiple `SubsystemDecisionRef` values, but none is rewritten into the Universal Router schema.

## Ten-record separation

| Step | Label | Record | Writer | Router action |
|---:|---|---|---|---|
| 1 | **OBSERVED** | DCP classification result | DCP | Import immutable ref. |
| 2 | **PROPOSED** | Universal orchestration decision | Universal Router | Write append-only decision. |
| 3 | **OBSERVED** | Freeflow admission decision | Freeflow | Request or import ref; do not copy quota state. |
| 4 | **OBSERVED** | LiteLLM proxy/provider observation | LiteLLM trace integration | Normalize observation with source confidence. |
| 5 | **OBSERVED** | RTE specialized route decision | RTE | Import ref for extraction tasks. |
| 6 | **PROPOSED** | Runner execution request | Future execution integration | Generate only after operator acceptance and handoff preparation. |
| 7 | **OBSERVED** | Dopetask accepted handoff | dopetask/handoff system | Import acceptance ref. |
| 8 | **OBSERVED** | Validation result | Validator/test runner | Import result ref. |
| 9 | **OBSERVED** | Independent audit result | Audit/proof system | Import ref and independence evidence. |
| 10 | **OBSERVED** | PR Steward readiness | PR Steward | Import merge-readiness ref. |

## `dopemux route explain`

1. **PROPOSED:** Parse task input into an ephemeral TaskEnvelope.
2. **PROPOSED:** Resolve an existing DCP ref or run the in-process DCP classifier without writing router state.
3. **PROPOSED:** Resolve active policy, registry, and snapshots.
4. **PROPOSED:** Generate candidates and explanations.
5. **PROPOSED:** Render selection logic, blockers, stale evidence, and alternatives.
6. **PROPOSED:** Do not write the journal unless `--record` is explicitly supplied.

## `dopemux route recommend`

1. **PROPOSED:** Build and validate TaskEnvelope.
2. **PROPOSED:** Append `INTAKE` event.
3. **PROPOSED:** Import DCP classification and append `CLASSIFIED` event.
4. **PROPOSED:** Resolve capability/provider-health snapshots and append `CAPABILITIES_RESOLVED` event.
5. **PROPOSED:** Evaluate policy and subsystem boundaries, appending `POLICY_CHECKED` or terminal `BLOCKED`/`ESCALATED`.
6. **PROPOSED:** Generate `RouteCandidate[]` and select a primary recommendation.
7. **PROPOSED:** Append `UniversalRouteDecision` and `ROUTE_RECOMMENDED` event.
8. **PROPOSED:** Return primary recommendation, up to two alternatives, blockers, validation route, audit route, freshness, and next action.
9. **PROPOSED:** No runner, provider, network, workflow, handoff, or proof mutation occurs.

## `dopemux route inspect`

### Decision inspection

- **PROPOSED:** Read the append-only decision and state events.
- **PROPOSED:** Resolve referenced subsystem records when adapters can read them.
- **PROPOSED:** Show unavailable refs as `UNKNOWN`, not silently omit them.
- **PROPOSED:** Show identity, usage, containment, network, and policy conflicts separately.

### Capability inspection

- **PROPOSED:** List registry entries and latest snapshots by runner/provider/model tuple.
- **PROPOSED:** Distinguish `DOCUMENTED`, `PROVEN_HELP`, `PROVEN_SMOKE`, `CERTIFIED`, `STALE`, `UNAVAILABLE`, and `UNKNOWN`.
- **PROPOSED:** Do not convert installed executable presence into authenticated availability.

### Health inspection

- **PROPOSED:** Show provider health by source, network posture, timestamp, expiry, and confidence.
- **PROPOSED:** Show Freeflow policy blocks separately from provider unhealth.
- **PROPOSED:** Show sandbox denial separately from host health.

## `dopemux route validate`

- **PROPOSED:** `validate policy` verifies schema, hash, precedence, hard invariants, certification refs, and active-pointer consistency.
- **PROPOSED:** `validate decision` replays the decision against recorded inputs and confirms deterministic output or records drift.
- **PROPOSED:** `validate snapshots` checks freshness, adapter version, source evidence, redaction, and impossible combinations.
- **PROPOSED:** Validation is local and deterministic in release one.

## Candidate-generation data flow

```text
TaskEnvelope
  + DCPClassificationRef
  + RiskPrivacyClassification
  + active RoutePolicy
  + ModelCapabilityRecord[]
  + RunnerCapabilitySnapshot[]
  + ProviderHealthSnapshot[]
  + optional FreeflowAdmissionDecision refs
  + optional RTE route-capability refs
          |
          v
Eligibility filters
  - hard boundaries
  - privacy/network/containment
  - snapshot freshness
  - identity requirements
  - cost/credit observability
  - certification
  - subsystem availability
          |
          v
Candidate scoring
  1. required capability coverage
  2. validation/audit fitness
  3. containment confidence
  4. identity confidence
  5. expected quality tier
  6. exact/estimated cost posture
  7. plan-credit posture
  8. latency posture
  9. context/token overhead
 10. operator preference
          |
          v
UniversalRouteDecision
```

## Scoring rule

- **PROPOSED:** Hard constraints are boolean gates and cannot be traded for score.
- **PROPOSED:** Among eligible candidates, the router chooses the lowest expected resource route that meets the required quality, validation, containment, audit, and identity class.
- **PROPOSED:** Unknown cost or credits lower confidence and may require operator acceptance; they never become zero.
- **PROPOSED:** A stale snapshot may lower confidence or block the route by risk class. It never receives a freshness bonus.
- **PROPOSED:** A route with unproven containment cannot outrank an equivalent route with enforced containment for write, audit, security, or release-sensitive tasks.

## Future operator acceptance flow

1. **PROPOSED:** Operator reviews recommendation.
2. **PROPOSED:** Operator records `OPERATOR_ACCEPTED` with scope and expiry.
3. **PROPOSED:** This is acceptance of a recommendation, not human approval for every protected action.
4. **PROPOSED:** A separate `HumanApprovalRef` is still required when policy demands approval.
5. **PROPOSED:** Release one stops here.

## Future handoff and execution flow

1. **PROPOSED:** A later phase constructs `ExecutionRequest` from the accepted recommendation.
2. **PROPOSED:** A handoff builder extends the existing handoff bundle only by adding route-decision and policy refs.
3. **PROPOSED:** Dopetask evaluates and accepts or rejects the handoff under its own authority.
4. **PROPOSED:** `EXECUTION_ACCEPTED` is written only after a valid `DopetaskHandoffRef` says accepted.
5. **PROPOSED:** Runner invocation occurs through one certified adapter at a time.
6. **PROPOSED:** Validation, audit, proof, and PR Steward records are created by their existing systems and referenced afterward.

## RTE specialized flow

- **PROPOSED:** For repo-truth extraction, candidate generation yields `route_kind=RTE_SPECIALIZED` instead of a universal model/provider ladder.
- **PROPOSED:** RTE then performs its own model, reasoning, strict-schema, provider-lock, preflight, repair, and spend decisions.
- **PROPOSED:** Universal Router records only the RTE decision ref and normalized observations.

## Failure flow

```text
Failure observed
  |
  +--> environment/auth/network? --> same-tier retry at most once or BLOCKED
  |                                  never premium escalation
  |
  +--> capability mismatch? -------> select eligible same-tier alternative or ESCALATED
  |
  +--> quality/validation failure? -> bounded reasoning escalation, then model tier escalation
  |
  +--> policy/identity conflict? ---> BLOCKED or NEEDS_SUPERVISOR
  |
  +--> audit failure? --------------> BLOCKED or ESCALATED; never self-clear
```

## Context minimization

- **PROPOSED:** Candidate generation operates on normalized metadata, not full repository content.
- **PROPOSED:** Runner recommendations include bounded context manifests rather than copying entire task histories.
- **PROPOSED:** Audit assignment receives a hash-pinned evidence manifest, not the implementer conversation transcript by default.
- **PROPOSED:** This reduces token overhead, context pollution, and accidental secret propagation.
