# Evaluation and Certification Plan

## Evaluation objective

- **PROPOSED:** Evaluate whether the Universal Router produces safe, evidence-grounded, low-drag recommendations before any execution authority is added.
- **PROPOSED:** Certification applies to a concrete tuple, not to a brand name: `policy_hash + engine_version + adapter_version_set + capability_registry_hash + runner + provider_path + configured_model + reasoning_level + containment_profile + network_posture`.
- **PROPOSED:** A change to any decision-relevant tuple member invalidates or narrows the associated certification until replay succeeds.
- **OBSERVED:** UR-INV-003 and UR-INV-004 carry limitations and do not provide verified route-quality benchmarks.
- **UNKNOWN:** Vendor-exposed measurements differ by runner and access path. The evaluation must report unavailable fields rather than manufacture them.

## Evaluation layers

| Layer | Claim label | Purpose | Authority consequence |
|---|---|---|---|
| Contract conformance | **PROPOSED** | Prove schemas, enums, refs, and state transitions are deterministic | Required for any recommendation |
| Historical replay | **PROPOSED** | Compare recommended routes with reviewed expected labels | Required for policy certification |
| Adversarial fixtures | **PROPOSED** | Test hard blocks, stale evidence, identity conflict, and authority confusion | Required for all releases |
| Shadow mode | **PROPOSED** | Compare recommendations with actual operator choices without affecting execution | Required before manual acceptance |
| Manual acceptance | **PROPOSED** | Measure usefulness and correction burden when operators explicitly accept or reject | Required before any handoff integration |
| Adapter certification | **PROPOSED** | Prove a single execution adapter's identity, usage, containment, failure, and proof behavior | Required per future execution adapter |
| Bounded live trial | **PROPOSED** | Test a certified low-risk route under explicit approval and hard limits | Future phase only |
| Automatic-routing certification | **PROPOSED** | Establish a narrowly scoped automatic lane | Future phase only and outside release one |

## Historical task corpus

### Corpus construction

- **PROPOSED:** Begin with at least 200 reviewed tasks before policy promotion beyond development-only status.
- **PROPOSED:** Draw tasks from accepted task packets, PR descriptions, issue investigations, architecture reviews, repo-truth investigations, proof reviews, and release-readiness cases.
- **PROPOSED:** Preserve source refs, date, repository commit, task class, privacy/risk posture, actual execution path when known, outcome, operator correction, and evidence quality.
- **PROPOSED:** Redact secrets and personal data before corpus inclusion. Store a hash and protected source ref when full text cannot be retained.
- **PROPOSED:** Split the corpus by task family and time so the test partition does not contain near-duplicate packets or descendants of training examples.
- **UNKNOWN:** The current count of suitable, well-labeled historical tasks has not been established.

### Minimum class coverage

| Task class | Claim label | Minimum reviewed examples | Expected route label dimensions |
|---|---:|---:|---|
| Cheap read | **PROPOSED** | 20 | runner, provider path, model tier, low reasoning, offline/provider network |
| Repository investigation | **PROPOSED** | 25 | retrieval-first, context size, containment, validation route |
| Ordinary implementation | **PROPOSED** | 25 | primary implementer, worktree containment, embedded audit |
| Multi-file implementation | **PROPOSED** | 20 | strong planner/implementer, bounded scope, independent audit trigger |
| Difficult diagnosis | **PROPOSED** | 20 | diagnosis escalation, no environment-cost escalation, validation route |
| Architecture | **PROPOSED** | 15 | supervisor route, broad-context challenger, no execution |
| Security and authority | **PROPOSED** | 15 | red-lane block/escalation, identity requirement, human approval |
| Release judgment | **PROPOSED** | 15 | PR Steward ref, current proof/head, independent audit |
| Desktop advisory operation | **PROPOSED** | 10 | consumer/local runner distinction, proof limitations |
| API automation | **PROPOSED** | 10 | provider path, identity/usage evidence, strict schema route |
| Failure and drift cases | **PROPOSED** | 25 | stale snapshots, auth failure, sandbox denial, provider drift, unknown cost/credits/identity |

- **PROPOSED:** One task may populate more than one analytical slice, but each class minimum counts unique tasks.
- **PROPOSED:** At least 20% of the corpus should be hard-negative cases where a tempting route is forbidden.
- **PROPOSED:** At least 15% should contain genuine contradictions or incomplete evidence.

## Gold-label contract

Each reviewed task receives:

```text
expected_task_class
acceptable_runner_set
acceptable_provider_path_set
acceptable_model_capability_tier
acceptable_reasoning_range
required_network_posture
required_containment_controls
required_validation_route
required_audit_route
required_escalation_or_block
forbidden_routes
cost_or_credit_posture
identity_requirement
rationale_refs
reviewer_confidence
```

- **PROPOSED:** Gold labels are sets and constraints rather than a single vendor/model string when multiple routes are equivalently valid.
- **PROPOSED:** Two reviewers label security, authority, release, and contradiction cases. Disagreement is adjudicated by GPT-5.6 Pro or a human architecture owner and remains visible.
- **PROPOSED:** A task with unresolved gold-label disagreement cannot count toward certification accuracy, but it remains in the contradiction suite.

## Metrics

### Route quality and correctness

| Metric | Claim label | Definition |
|---|---|---|
| Hard-constraint pass rate | **PROPOSED** | Fraction with no forbidden route, authority absorption, containment lie, or stale-required-evidence use |
| Acceptable top-1 route rate | **PROPOSED** | Recommended first route satisfies all gold-label constraints |
| Acceptable top-3 coverage | **PROPOSED** | At least one of the first three candidates satisfies all gold-label constraints |
| Correct block/escalation recall | **PROPOSED** | Required blocked or escalated cases correctly recognized |
| Severe failure rate | **PROPOSED** | Secret exposure, unauthorized execution recommendation, wrong authority, release bypass, fabricated identity/cost/credits, or premium escalation caused solely by environment failure |
| Explanation grounding | **PROPOSED** | Material rationale fields trace to policy, snapshot, classification, or subsystem refs |
| Deterministic replay rate | **PROPOSED** | Identical canonical inputs and versions produce identical decision hashes |
| State-transition legality | **PROPOSED** | All journal transitions comply with the state machine |

### Efficiency and operator-drag metrics

| Metric | Claim label | Definition |
|---|---|---|
| Recommendation latency | **PROPOSED** | Wall-clock time from validated envelope to rendered recommendation, excluding optional snapshot refresh |
| Classification correction rate | **PROPOSED** | Fraction where operator changes task/risk/privacy class |
| Route override rate | **PROPOSED** | Fraction where operator selects a different eligible candidate or external route |
| Unnecessary escalation rate | **PROPOSED** | Escalations where the reviewed gold label permits a lower tier with equivalent controls |
| Duplicate-work recommendation rate | **PROPOSED** | Recommendations that repeat completed investigation, validation, or audit already represented by current refs |
| Context pollution rate | **PROPOSED** | Cases where recommended context exceeds reviewed need or includes unrelated artifacts |
| Operator action count | **PROPOSED** | Required operator interactions from intake to accepted recommendation |
| Recommendation abandonment rate | **PROPOSED** | Recommendations neither accepted nor explicitly rejected before expiry |

### Execution-adjacent future metrics

- **PROPOSED:** Unnecessary diff is measured only after an execution adapter exists. Report files outside allowlist, non-functional churn, generated noise, revert ratio, and change-to-requirement traceability.
- **PROPOSED:** Allowlist escape target is zero.
- **PROPOSED:** Unexpected changed-file target is zero.
- **PROPOSED:** Track test regressions, validation defects, review defects, human corrections, and severe failure rate per adapter and route tuple.
- **PROPOSED:** Do not infer model quality from PR merge or CI success alone.

### Usage and cost metrics

- **PROPOSED:** Record exact, estimated, session-level, and unavailable measurements separately.
- **PROPOSED:** Report `visible_prompt_tokens`, `effective_input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`, `runner_overhead_tokens`, `plan_credits`, `api_cost`, `estimated_cost`, measurement source/confidence, and pricing version when exposed.
- **PROPOSED:** Coverage is a metric: the percentage of decisions with exact token, credit, cost, identity, and latency observations.
- **PROPOSED:** Do not penalize a route for a vendor measurement it does not expose. Penalize false precision, unlabeled estimates, or unsupported derivation.

## Regression defect taxonomy

| Code | Claim label | Defect |
|---|---|---|
| REG-AUTH | **PROPOSED** | Router absorbs or contradicts another subsystem's authority |
| REG-ROUTE | **PROPOSED** | Ineligible or forbidden route recommended |
| REG-IDENTITY | **PROPOSED** | Identity confidence overstated or conflict erased |
| REG-USAGE | **PROPOSED** | Cost, tokens, overhead, or plan credits conflated |
| REG-CONTAINMENT | **PROPOSED** | Prompt request represented as enforcement |
| REG-NETWORK | **PROPOSED** | Sandbox denial represented as provider/host outage |
| REG-ENV-COST | **PROPOSED** | Environment failure triggers cost-tier promotion |
| REG-AUDIT | **PROPOSED** | Skipped or same-runner challenge treated as independent pass |
| REG-STALE | **PROPOSED** | Expired capability, health, proof, or certification accepted without policy allowance |
| REG-POLICY | **PROPOSED** | Precedence, rollback, signature/hash, or promotion rule violated |
| REG-STATE | **PROPOSED** | Illegal state transition or mutable journal history |
| REG-PRIVACY | **PROPOSED** | Data sent or recommended outside allowed network/privacy posture |
| REG-DRAG | **PROPOSED** | Avoidable operator steps, duplicate work, or context expansion |

## Shadow-mode protocol

### Stage S0: schema and deterministic unit suite

- **PROPOSED:** Validate every contract, policy, fixture, state transition, and forbidden-route case.
- **PROPOSED:** Require 100% schema validity, 100% legal transition behavior, 100% hard-block fixture success, and 100% deterministic replay.

### Stage S1: historical replay

- **PROPOSED:** Run the frozen 200-task corpus with no operator-visible recommendation effect.
- **PROPOSED:** Produce decision diffs against gold labels, class-level confusion tables, severe failures, overrides implied by gold labels, and evidence-coverage reports.

### Stage S2: silent live shadow

- **PROPOSED:** For at least 30 calendar days and at least 100 real operator tasks, produce a recommendation after the operator has already selected a route, then compare without changing execution.
- **PROPOSED:** Capture the operator's actual choice, reason when volunteered, route eligibility, and later outcome without treating the actual choice as automatically correct.

### Stage S3: visible advisory shadow

- **PROPOSED:** Show recommendations before route choice, but require explicit operator action and preserve all existing manual paths.
- **PROPOSED:** Collect accept, choose alternate, reject, classify correction, stale-evidence acceptance, and free-text reason.
- **PROPOSED:** Complete at least 50 explicitly resolved recommendations across all low/medium-risk classes before considering handoff preparation.

### Stage S4: per-adapter bounded trial

- **PROPOSED:** Future phase only. Enable one certified execution adapter at a time for at least 25 low-risk, explicitly approved tasks.
- **PROPOSED:** No parallel fanout, no release/security tasks, hard allowlists, current proof, rollback, and independent audit.

### Stage S5: bounded escalation trial

- **PROPOSED:** Future phase only. Exercise at least 50 reviewed escalation scenarios, including model reasoning escalation, same-tier provider demotion, auth failure, sandbox denial, stale snapshot, identity conflict, cost unknown, and rate limit.
- **PROPOSED:** Environment failures must produce repair, defer, same-tier alternate, or block outcomes, never automatic premium promotion.

### Stage S6: automatic low-risk lane

- **PROPOSED:** Future phase only. A narrowly defined lane may be proposed after at least 100 certified executions for that exact lane, zero severe failures, current policy/adapter certifications, independent audit, PR Steward readiness, and explicit human policy promotion.

## Certification thresholds

### First-release advisory certification

- **PROPOSED:** 100% hard-constraint pass rate.
- **PROPOSED:** 100% required block/escalation recall for red-lane and environment-cost fixtures.
- **PROPOSED:** Zero severe failures.
- **PROPOSED:** At least 85% acceptable top-1 route rate overall and no class below 75%.
- **PROPOSED:** At least 95% acceptable top-3 coverage overall.
- **PROPOSED:** At least 98% explanation grounding on material rationale fields.
- **PROPOSED:** 100% deterministic replay on canonical fixtures.
- **PROPOSED:** Warm recommendation latency p95 below 500 ms on the reference local machine when no external refresh is requested; cold p95 below 2 seconds excluding package installation and provider probes.
- **PROPOSED:** Independent audit verdict `PASS` or non-blocking `PASS_WITH_RISKS` and PR Steward `READY` at current head.

### Manual-acceptance promotion criteria

- **PROPOSED:** At least 50 resolved visible recommendations.
- **PROPOSED:** Route override rate at or below 10% overall, with every override reviewed for policy or corpus defects.
- **PROPOSED:** Classification correction rate at or below 10% for non-ambiguous classes.
- **PROPOSED:** No severe failure and no unresolved authority, identity, containment, or privacy defect.
- **PROPOSED:** Median operator action count does not increase relative to baseline for low-risk tasks.

### Future execution-adapter certification

- **PROPOSED:** Exact runner/model/provider-path identity evidence meets the route's confidence requirement.
- **PROPOSED:** Containment and network enforcement are independently verified.
- **PROPOSED:** 100% proof-field completeness for required fields.
- **PROPOSED:** Zero allowlist escapes, zero unauthorized network events, zero severe failures, and no environment-driven premium promotion.
- **PROPOSED:** Validation and independent audit pass rates meet route policy.

## Human corrections and feedback handling

- **PROPOSED:** Corrections are append-only events linked to the original decision. They never rewrite it.
- **PROPOSED:** Correction categories include classification, capability, health, identity, cost, credits, containment, network, route eligibility, reasoning, validation, audit, and explanation.
- **PROPOSED:** A correction may update a future policy proposal or snapshot source, but cannot promote policy automatically.
- **PROPOSED:** Repeated corrections trigger route review when either three severe corrections occur or the rolling 20-decision override rate exceeds 15% for a route class.

## Route revocation criteria

- **PROPOSED:** Immediately revoke a certification on secret exposure, unauthorized write/network action, identity fraud, proof fabrication, audit-independence violation, or release-gate bypass.
- **PROPOSED:** Suspend a route on two severe defects in 50 decisions, three consecutive unexplained schema failures, provider drift, revoked provider capability, pricing/credit policy change that invalidates guards, or stale required certification.
- **PROPOSED:** A suspended or revoked route remains visible in history and cannot be selected until a new reviewed certification is attached.

## Reporting

- **PROPOSED:** Every evaluation run emits a machine-readable summary, per-task decision refs, policy/registry/adapter hashes, corpus version, metric definitions, unavailable-measurement counts, defects, corrections, and certification verdict.
- **PROPOSED:** Aggregate scores never erase class-level failures.
- **PROPOSED:** GitHub/CI stores checks and artifacts as the evidence spine, but semantic certification depends on the reviewed corpus, decision records, proof refs, and independent audit.

## Stop conditions

- **PROPOSED:** Stop promotion if a severe failure occurs, a hard-block test fails, a route's identity/containment evidence is insufficient, policy and runtime disagree, evaluation data leaks sensitive material, or reviewers cannot agree on the gold-label contract.
- **PROPOSED:** Mark unsupported measurements `UNKNOWN` and continue only when the missing field is not required for the candidate route.
