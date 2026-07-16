# Risk, Complexity, and Routing Policy

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `08_RISK_COMPLEXITY_ROUTING_POLICY.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Policy status

`PROPOSED` This policy is a synthesis specification, not an active router. In the first release it produces a recommendation that a human approves. Automatic execution remains limited to the certified mechanical lane.

## Stage 1: deterministic risk floor

| Class | Name | Typical changes | Minimum posture |
|---|---|---|---|
| `E0` | Evidence-only | Plain text docs, comments, non-executable metadata, additive inert assets | Mechanical candidate |
| `T1` | Test-evidence | Additive tests, fixtures, snapshots, assertions, test selection | Human review; model route only after certification |
| `R2` | Routine bounded | One ownership domain, no protected category, bounded application/library logic | Certified single reviewer route in future |
| `B3` | Boundary or supply chain | Dependencies, lockfiles, CI, build, containers, IaC, public schemas/APIs, cross-service interfaces | Strong reviewer plus human; dual route where policy requires |
| `S4` | Security-critical or irreversible | Auth, authorization, sessions, secrets, crypto, release signing, destructive persistence, rollback-sensitive changes | Fail closed to strong independent review plus human |

`PROPOSED` Protected categories set the floor. Size cannot lower it.

## Stage 2: complexity modifiers

| Signal | Effect |
|---|---|
| Relative churn and dispersion | Raise complexity when change spans many semantic areas |
| File count | Modifier only, never sole classifier |
| Ownership mismatch or missing CODEOWNERS | Raise or fail closed on protected paths |
| Dependency centrality | Raise for widely consumed modules |
| Historical defect concentration | Raise for hotspots |
| Cross-language or weak tooling | Raise |
| Generated/binary content without source | Fail closed |
| Large docs-only diff | May remain low runtime risk if every file is allowlisted |

## Stage 3: privacy class

| Class | Route restriction |
|---|---|
| `PUBLIC` | Certified local or approved API routes may be considered |
| `PRIVATE` | Prefer local or approved direct API; OpenRouter default deny |
| `SENSITIVE` | Secret triage and explicit security approval; OpenRouter deny |
| `CLIENT` | Contract, privacy, and client approval; consumer plan routes deny |
| `RELEASE` | Model evidence only, never release authority; strongest human gate |

Privacy can only remove routes. It cannot reduce the risk floor.

## Stage 4: adapter eligibility gate

A route is eligible only when every field is `PASS`:

```text
vendor_permission
credential_lifecycle
approved_deployment_class
installed_version_conformance
containment_profile
network_policy
identity_proof
privacy_approval
cost_admission
route_certification
availability
```

Any `UNKNOWN`, `CLAIMED`, or `CONFLICTING` material gate produces `INELIGIBLE` for unattended execution.

## Stage 5: independence requirement

| Risk class | Future minimum independence |
|---|---|
| `E0` | Mechanical plus human can be sufficient |
| `T1` | Separate human or certified model review; destructive test changes escalate |
| `R2` | One certified model with independent human governance |
| `B3` | Strong certified model; dual review for broad or ambiguous changes |
| `S4` | Two strongly independent auditors or one plus specialist human adjudication |

`PROPOSED` Strong independence requires recorded actual identities, provider or model-family separation, separate sessions, separated mutable state, and independently attributable proof. Unknown model identity caps the claim at session or runner independence.

## Stage 6: cost-aware selection

`PROPOSED` Among routes that already satisfy risk, privacy, identity, containment, independence, and certification, choose the lowest expected total cost.

Cost may break ties. Cost may never make an ineligible route eligible.

## Routing ladder

| Route | Purpose | Current status |
|---|---|---|
| `M0` Mechanical | Deterministic bounded validation | `CURRENTLY_IMPLEMENTABLE` |
| `L1` Lightweight certified model | Low-risk semantic review | `BLOCKED_NO_CERTIFIED_TOOL` |
| `S2` Strong single model | Cross-boundary or high-complexity review | `BLOCKED_NO_CERTIFIED_TOOL` |
| `I3` Independent dual audit | Critical or disagreement route | `BLOCKED_IDENTITY_AND_CERTIFICATION` |
| `A4` Premium adjudication | Severe ambiguity or unresolved conflict | `BLOCKED_NO_CERTIFIED_TOOL` |
| `MANUAL` Human-operated receipt | Compatibility and supervised review | `DESIGNABLE` |

## Mechanical-only eligibility

All conditions must hold:

- every file is on an explicit non-executable allowlist;
- no dependency, workflow, build, container, infrastructure, schema, auth, secret, persistence, or release path is touched;
- no executable-bit change;
- no generated/binary shipping output without authoritative source;
- required ownership and status evidence is present;
- deterministic validators pass;
- request and proof are complete;
- the human approves closure under the mechanical policy.

## Fail-closed triggers

`PROPOSED`

- unknown protected file or artifact type;
- malformed or incomplete diff;
- auth, secrets, cryptography, session, CI/CD, release, provenance, or destructive persistence change;
- vulnerable or unreviewed dependency change;
- missing ownership coverage;
- missing exact-head evidence;
- unknown actual model identity where independence is claimed;
- expired route certificate;
- unapproved privacy or cost state;
- schema-invalid result;
- containment or network-policy violation.

## Failure is not escalation

`PROPOSED` Plan exhaustion, quota, login expiry, worker crash, parser failure, or provider outage yields an environment or output failure. It does not select a stronger or more expensive route. A different route requires a fresh eligibility decision and human approval.

## Future automatic-routing gate

Automatic routing may begin only after:

1. route-specific shadow evaluation;
2. approved certification thresholds;
3. current model/provider identity proof;
4. frozen prompt and config hashes;
5. certified worker and normalizer versions;
6. operator-approved rollback and revocation rules;
7. independent audit of the routing implementation.
