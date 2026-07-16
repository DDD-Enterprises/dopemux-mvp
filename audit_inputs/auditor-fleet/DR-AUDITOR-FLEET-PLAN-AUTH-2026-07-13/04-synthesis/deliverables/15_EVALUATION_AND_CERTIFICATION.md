# Evaluation and Certification

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `15_EVALUATION_AND_CERTIFICATION.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Current status

`OBSERVED` No model route has been benchmarked or certified on Dopemux repositories. Automatic model routing is therefore blocked.

## Evaluation phases

1. **Harness conformance:** schema, identity, timeout, failure mapping, containment, and trace behavior.
2. **Offline replay:** fixed public or redacted corpus, no merge impact.
3. **Shadow mode:** candidate route runs beside current human/mechanical process.
4. **Adjudication:** humans compare findings against gold evidence.
5. **Certification review:** independent approval of the exact route tuple.
6. **Limited operator-triggered use:** no automatic policy promotion.
7. **Automatic low-risk execution:** only after sustained certified performance and independent architecture/security audit.

## Corpus design

`PROPOSED` Use a mixed, stratified corpus containing:

- internal historical PRs with adjudicated outcomes;
- clean controls;
- docs-only and metadata changes;
- additive and destructive test changes;
- dependencies and lockfiles;
- CI/CD, build, container, and release changes;
- public API and schema changes;
- auth, session, secret, crypto, and provenance changes;
- additive and destructive persistence changes;
- cross-boundary refactors;
- adversarial unsupported-claim and prompt-injection cases;
- relevant public review and security benchmarks.

No single vendor benchmark determines certification.

## Gold adjudication

Each expected finding records:

- exact file and location;
- severity;
- reproducible failure, authoritative rule, or technical rationale;
- adjudicator identity;
- reviewer disagreement;
- tie-break outcome;
- whether the finding is in scope for the route class.

Hard cases receive double review plus tie-break.

## Shadow evidence

Preserve for every candidate run:

- exact request and head SHA;
- prompt and instruction hashes;
- tool, version, requested and observed model evidence;
- provider and credential class;
- reasoning or effort settings;
- worker image, config, network, and policy hashes;
- deterministic evidence bundle;
- raw and normalized output hashes;
- human outcome and corrections;
- execution, parser, quota, and environment failures;
- cost and latency where measurable.

## Metrics

| Metric | Purpose |
|---|---|
| Severe-defect recall | Primary blocking quality metric for high-risk cohorts |
| False-positive rate | Operator burden and trust erosion |
| Unsupported severe-claim rate | Hallucinated blocking risk |
| Schema-validity rate | Operational reliability |
| Evidence-grounding rate | Traceability to code or authoritative rules |
| Contradiction detection | Ability to surface conflicting evidence |
| Unnecessary escalation rate | Cost and workflow burden |
| Operator correction rate | Practical quality |
| Environment-failure rate | Harness reliability, separate from model quality |
| Adjudicator disagreement | Gold-label uncertainty |
| Latency and measurable cost | Operational viability |

## Certification tuple

`PROPOSED` Certification binds to:

```text
repository_class
+ diff_class
+ language_and_tooling_class
+ tool_and_adapter_version
+ model_snapshot_or_version
+ provider_and_endpoint
+ auth_class
+ reasoning_settings
+ prompt_hash
+ containment_profile_hash
+ network_policy_hash
+ deterministic_bundle_version
+ runner_image_hash
+ normalizer_version
+ output_schema_version
```

A vendor brand or model family cannot be certified in the abstract.

## Initial gates

`PROPOSED`, low-to-medium confidence policy starting points requiring local calibration:

- severe-defect recall at least `0.90` for the certified cohort;
- at least `0.95` for security-critical or irreversible cohorts;
- structured-output validity at least `99.5%`;
- unsupported severe claims below `2%`;
- no unresolved systematic human-disagreement pattern;
- environment failure within an operator-approved control limit;
- unnecessary escalation within an operator-approved budget.

These are not research-established universal constants.

## Independence certification

| Level | Requirements |
|---|---|
| `SESSION_INDEPENDENT` | Separate session and context only |
| `RUNNER_INDEPENDENT` | Separate session plus separated mutable runner state |
| `PARTIAL_PROVIDER_INDEPENDENCE` | Same provider allowed, but versions, sessions, prompts, credentials, and runners separated |
| `STRONG_INDEPENDENCE` | Actual identities recorded, provider or family separation, separate sessions and mutable state, attributable proof |

Unknown actual model identity prohibits provider- or model-family independence claims.

## Expiry and revocation

`PROPOSED` Certification expires after 90 days or immediately after material change to any tuple component.

Immediate revocation follows:

- severe production miss;
- failure to detect a protected fail-closed condition;
- systematic unsupported severe claims;
- schema-validity control-limit breach;
- model/provider identity drift;
- prompt, config, worker, normalizer, or policy drift;
- benchmark drift;
- containment violation or security incident;
- privacy or terms change;
- missing cost or route provenance.

## Promotion rule

`PROPOSED` Certification permits use within a narrow scope. It does not automatically promote policy or grant merge authority. A separate governance decision is required for every increase in automation.
