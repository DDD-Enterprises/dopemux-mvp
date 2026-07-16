# DR-04: Audit Routing, Evaluation, and Independence

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Track:** `DR-04-AUDIT-ROUTING-EVALUATION-AND-INDEPENDENCE`  
**Research date:** 2026-07-13  
**Status:** `COMPLETE_WITH_UNKNOWNS`

## Executive disposition

**PROPOSED:** Use a two-stage PR classifier:

1. a deterministic risk floor based on paths, artifact types, semantic triggers, and protected categories;
2. an empirical complexity modifier based on churn, file count, ownership, dependency centrality, language/tool maturity, and historical defect concentration.

The selected route is the maximum of those two results.

**OBSERVED:** The local capability probe was static-only. Mechanical validation is the only currently observed usable execution lane. All model-capable live probes were `NOT_RUN`, and actual model identity remains `UNKNOWN`.

**PROPOSED:** Route selection should be mostly deterministic at the bottom, evidence-weighted in the middle, and fail-closed at the top. Premium models should be reserved for changes that can break trust, data, releases, security boundaries, or unresolved auditor disagreement.

---

## Questions answered

### Classification

**INFERRED, HIGH confidence:** Relative churn, change dispersion, multi-file modification, weak reviewer participation, ownership mismatch, and dependency centrality are more defensible complexity signals than raw line count alone.

**PROPOSED:** Use five route classes:

1. **Evidence-only**
   - plain text documentation;
   - comments;
   - issue templates;
   - non-executable metadata;
   - additive non-executable assets.

2. **Test-evidence**
   - additive tests that increase coverage;
   - mutated or deleted assertions;
   - fixture and snapshot changes;
   - test selection or exclusion changes.

3. **Routine bounded change**
   - application or library changes inside one ownership domain;
   - one trust boundary;
   - no protected security or release category.

4. **Boundary or supply-chain change**
   - dependency manifests and lockfiles;
   - CI/CD definitions;
   - build and container definitions;
   - infrastructure as code;
   - public API or schema contracts;
   - cross-service interfaces;
   - data-access layers.

5. **Security-critical or irreversible change**
   - authentication;
   - authorization;
   - sessions;
   - secrets;
   - cryptography;
   - security monitoring;
   - release signing or provenance;
   - destructive schema or data operations;
   - deletion and rollback-sensitive persistence changes.

**PROPOSED:** Size and file count are modifiers, not sovereign rulers. A tiny auth diff can be more dangerous than a 500-line documentation cleanup.

### Mechanical-only eligibility

**PROPOSED:** Mechanical-only closure is eligible only when all of the following hold:

- every changed file is in a non-executable allowlist;
- no dependency, workflow, build, container, infrastructure, schema, authentication, secrets, persistence, or release path is touched;
- no executable-bit change exists;
- no unknown binary or generated shipping artifact is changed without authoritative source;
- CODEOWNERS and required checks pass;
- deterministic secret, dependency, schema, and policy checks pass;
- the diff and proof envelope are complete and parseable.

**PROPOSED:** Additive tests may qualify for a narrow low-risk lane, but not automatic mechanical-only closure unless the project explicitly certifies that subclass. Test deletions, assertion weakening, fixture semantic changes, and test-selection changes must leave the mechanical-only lane.

### Fail-closed conditions

**PROPOSED:** Bypass model selection and fail closed for:

- unknown or unsupported file type in a protected path;
- auth, authorization, session, crypto, or secrets changes;
- vulnerable dependency additions or upgrades;
- CI/CD, release-signing, provenance, or build-pipeline changes;
- destructive operations such as `DROP`, `DELETE`, `TRUNCATE`, incompatible type narrowing, or rollbackless migrations;
- generated or binary output without authoritative source;
- malformed or incomplete diffs;
- missing CODEOWNERS coverage on protected paths;
- missing required status evidence;
- unpinned or unknown model identity where independence or certification is claimed.

---

## Proposed routing ladder

### Route 0: Mechanical validation

Use only for certified evidence-only changes.

**OBSERVED:** The local probe records deterministic Git, JSON, schema, proof-bundle, and diff-hygiene validators. Each validator has a narrow authority limit and cannot establish semantic correctness.

### Route 1: One lightweight model

Use for bounded routine changes with:

- one ownership domain;
- low-to-moderate churn;
- no protected category;
- no fail-closed trigger;
- complete mechanical evidence;
- certified route performance for the relevant cohort.

**UNKNOWN:** Which locally installed plan-authenticated tool may legally and safely fill this lane remains dependent on DR-01 and DR-03 evidence. Static CLI presence is not proof of sanctioned unattended use.

### Route 2: One stronger model

Use when:

- architecture or service boundaries are crossed;
- tooling coverage is weak;
- churn, hotspot, or dependency-centrality signals are elevated;
- semantics involve state transitions, concurrency, schema interaction, business logic, or broad blast radius.

### Route 3: Two independent auditors

Require for:

- security-critical changes;
- irreversible persistence changes;
- release or provenance changes;
- high-risk automatic decisions;
- severe findings;
- low-confidence output;
- conflict with deterministic evidence;
- disagreement between reviewers.

### Route 4: Premium escalation

Reserve GPT-5.6 Pro-class or Claude Opus-class review for:

- large cross-boundary refactors;
- ambiguous auth, crypto, or destructive-data semantics;
- release and provenance rewrites;
- unresolved severe disagreement;
- high-value adjudication where cheaper routes have failed to produce a stable decision.

**PROPOSED:** Premium escalation must not be triggered merely by plan exhaustion or runner failure. Environment failure is not evidence that a more expensive model is needed.

---

## Failure handling

### Environment versus model quality

**PROPOSED:** Maintain separate outcome classes:

- `EXECUTION_FAILURE`
- `MODEL_OUTPUT_FAILURE`
- `MODEL_QUALITY_FAILURE`
- `POLICY_BLOCK`
- `AUDITOR_CONFLICT`
- `HUMAN_ESCALATION`

Runner unavailability, rate limiting, plan exhaustion, malformed transport, parser exceptions, and tool outages are execution failures. They must not count as model-quality misses or passes.

### Plan exhaustion and runner unavailability

**PROPOSED:**

1. record the failure exactly;
2. retry only within a bounded, policy-defined budget;
3. reroute only to a pre-certified equivalent route;
4. otherwise escalate to human review;
5. never silently upgrade cost, privacy exposure, or trust claims.

### Malformed output

**PROPOSED:** Treat schema-invalid output as a failed audit execution. A parser salvage operation may produce diagnostic evidence, but it must not convert the run into a certified pass.

### Conflicting findings

**PROPOSED:** Severe disagreement is itself a risk signal. Resolve with:

- a stronger independent auditor; or
- a human adjudicator using exact code locations, evidence, transcripts, and deterministic results.

Do not average contradictory findings into beige fog.

---

## Independence policy options

### Independence dimensions

**INFERRED:** The most material dimensions are:

1. pinned actual model identity;
2. provider and model-family separation;
3. separate session and context;
4. separate runner or harness;
5. separate execution host where common-mode failures matter;
6. separate credential profile for least privilege and attribution;
7. separate prompt author, which is useful but weaker than the controls above.

### Strong independence

**PROPOSED:** Claim strong independence only when:

- actual model identities are pinned and recorded;
- providers or model families differ;
- sessions are separate;
- hidden conversation state is not shared;
- mutable tool state and runner state are separated;
- each auditor emits an independently attributable proof record.

### Same-provider review

**PROPOSED:** Same-provider review may count as partial independence for medium-risk work when:

- versions are pinned;
- sessions are separate;
- prompts are independently authored or materially distinct;
- runners are separated;
- no hidden shared state is reused.

It should not be treated as strong independence for critical automatic decisions.

### Unknown actual model identity

**PROPOSED:** When actual model identity is unknown, cap the claim at `SESSION_INDEPENDENT` or `RUNNER_INDEPENDENT`. Do not claim model-family or provider independence.

**OBSERVED:** The local probe records all model identities as `UNKNOWN` because no live calls were run.

### Human plus mechanical validation

**PROPOSED:** For genuinely evidence-only changes, human review plus deterministic validation can satisfy the practical independence requirement. This is a proportional-risk policy choice, not proof of statistical independence.

---

## Benchmark and shadow-evaluation design

### Corpus

**PROPOSED:** Build a mixed, route-specific corpus containing:

- internal historical PRs with adjudicated outcomes;
- clean PRs to measure false positives;
- security-related review examples;
- dependency and lockfile changes;
- CI/CD and release changes;
- auth, secrets, and crypto changes;
- additive and destructive schema changes;
- destructive data operations;
- cross-boundary refactors;
- adversarial examples designed to trigger unsupported claims;
- public corpora such as PR review datasets, security review datasets, OpenSSF CVE material, and SWE-bench-like issue/patch tasks.

No single vendor benchmark should control routing certification.

### Gold adjudication

**PROPOSED:** Every expected finding should include:

- exact location;
- severity;
- reproducible failure, policy violation, or authoritative rationale;
- adjudicator identity;
- disagreement record;
- tie-break outcome.

Hard cases should receive double review plus tie-break.

### Shadow mode

**PROPOSED:** Run candidate routes beside the incumbent without affecting merge decisions. Preserve:

- exact prompt;
- model and provider identity;
- reasoning or effort settings;
- deterministic checks;
- structured output;
- cited evidence;
- transcript or trace where available;
- runner and harness version;
- human outcome;
- correction required.

Review disagreement buckets explicitly:

- incumbent pass, candidate fail;
- incumbent fail, candidate pass;
- both pass, human finds issue;
- both fail, no real issue;
- schema or execution failure;
- unnecessary escalation.

---

## Metrics

**PROPOSED:** Track at least:

- severe-defect recall;
- false-positive rate;
- unsupported-claim rate;
- schema-validity rate;
- evidence-grounding rate;
- contradiction-detection rate;
- unnecessary-escalation rate;
- latency;
- plan usage where measurable;
- API cost where applicable;
- operator correction rate;
- environment-failure rate;
- adjudicator disagreement rate.

Severe-defect recall is the primary blocking metric for high-risk routes. Unsupported severe claims and schema failure are separate operational hazards and must not be hidden inside one aggregate score.

---

## Certification and revocation

### Certification scope

**PROPOSED:** Bind certification to this tuple:

- repository class;
- diff class;
- language and tooling class;
- model snapshot or version;
- provider;
- reasoning settings;
- prompt-template hash;
- deterministic-check bundle;
- runner and harness version;
- output schema version.

Certification must not attach vaguely to “Claude,” “OpenAI,” or “an AI reviewer.”

### Initial numeric gates

**PROPOSED, policy choice rather than research fact:**

- severe-defect recall at least `0.90` for the certified cohort;
- at least `0.95` for security-critical or irreversible cohorts;
- structured-output validity at least `99.5%`;
- unsupported severe claims below `2%`;
- no unresolved systematic human-disagreement pattern;
- unnecessary escalation below an operator-defined budget.

These thresholds require local calibration against failure cost.

### Expiry

**PROPOSED:** Expire certification after 90 days, or sooner after any material change to:

- model version or alias resolution;
- provider;
- prompt template;
- route predicate;
- runner image;
- tool set;
- schema;
- deterministic validation bundle.

### Immediate revocation

**PROPOSED:** Revoke after:

- a demonstrated severe production miss;
- failure to detect a protected fail-closed condition;
- sustained increase in unsupported severe claims;
- schema-validity dropping below its control limit;
- evidence of model or provider drift;
- benchmark drift;
- security incident;
- loss of model identity or route provenance.

---

## Contradictions and carried unknowns

### `CONFLICTING`: Size as risk signal

Small changes are generally easier to review, but size alone is not a sufficient safety classifier. Security-critical one-line changes exist; large generated or documentation diffs can be low runtime risk. Resolution: treat size as a modifier, never the only floor.

### `CONFLICTING`: Multi-model review as independence

A second model can reduce risk, but same-provider, same-family, shared-session, or shared-harness review can preserve common-mode error. Resolution: certify independence dimensions explicitly rather than counting model calls.

### `UNKNOWN`: Exact optimal thresholds

The literature does not dictate Dopemux-specific numeric gates. Local benchmark costs, repository mix, and tolerance for false positives are required.

### `UNKNOWN`: Which plan-backed model fills each lane

Local installation is observed, but unattended plan authentication, containment, and model identity are not proven by this track.

### `UNKNOWN`: Route performance on Dopemux repositories

No benchmark execution occurred. Route certification requires a future bounded evaluation program.

---

## Activities not run

- no repository implementation;
- no GitHub mutation;
- no provider login;
- no credential inspection;
- no model invocation;
- no benchmark execution;
- no plan-credit measurement;
- no final architecture synthesis.

---

## Recommendations

1. **PROPOSED:** Adopt the five-class taxonomy and deterministic risk-floor model for synthesis input.
2. **PROPOSED:** Keep mechanical validation as a first-class route with narrow authority.
3. **PROPOSED:** Treat auth, secrets, CI/CD, release, provenance, dependency, and destructive persistence categories as elevated route floors.
4. **PROPOSED:** Separate execution failure from model-quality failure in all metrics and proof contracts.
5. **PROPOSED:** Require pinned identity and explicit independence dimensions before claiming independent review.
6. **PROPOSED:** Establish shadow evaluation before automatic route execution.
7. **BLOCKED:** Do not automatically bind locally installed model tools to routing lanes until DR-01 and DR-03 evidence resolves authorization and containment.

---

## Synthesis implications

- Routing should compute a deterministic floor before considering model cost or availability.
- Mechanical validation cannot certify semantic correctness beyond each validator’s authority.
- Unknown authentication, containment, privacy, or model identity must remain non-executable.
- Environment failure must not automatically trigger premium escalation.
- Exact route, provider, model, runner, schema, and prompt provenance belong in proof.
- Human approval remains external to the broker or auditor.
- This report proposes policy options. It does not establish final Dopemux policy.

---

## Source ledger

Access date for all sources: **2026-07-13**.

1. NIST, **AI Risk Management Framework 1.0**, standard.
2. NIST, **Secure Software Development Framework 1.1**, standard.
3. NIST, **Guidelines on Minimum Standards for Developer Verification of Software**, standard.
4. OWASP, **Secure Code Review Cheat Sheet**, official security guidance.
5. OWASP, **CI/CD Security Cheat Sheet**, official security guidance.
6. OWASP, **Secrets Management Cheat Sheet**, official security guidance.
7. GitHub Docs, **Dependency review**, official documentation.
8. GitHub Docs, **About code owners**, official documentation.
9. GitHub Docs, **Managing a branch protection rule**, official documentation.
10. SLSA, **Build provenance and security levels**, standard.
11. Microsoft Research, **Use of Relative Code Churn Measures to Predict System Defect Density**, peer-reviewed research.
12. Hassan et al., **Predicting Faults Using the Complexity of Code Changes**, peer-reviewed research.
13. McIntosh et al., **Impact of Modern Code Review Practices on Software Quality**, peer-reviewed research.
14. Bird et al., **Don’t Touch My Code! Examining the Effects of Ownership on Software Quality**, peer-reviewed research.
15. Google Engineering Practices, **Small CLs** and code review guidance, official engineering guidance.
16. Kim et al., **Correlated Errors in Large Language Models**, research.
17. Shi et al., **Position Bias in LLM-as-a-Judge**, peer-reviewed research.
18. Spiliopoulou et al., **Self-Bias and Family-Bias in LLM-as-a-Judge**, research.
19. OpenAI, **Evaluation best practices**, official documentation.
20. Anthropic, **Demystifying evals for AI agents**, official engineering guidance.
21. OpenSSF, **CVE Benchmark**, official repository.
22. Qodo, **PR-Review-Bench**, public benchmark dataset.
23. SWE-bench and SWE-bench Verified, public benchmark corpus.
24. Google DeepMind, **FACTS Grounding**, research benchmark.
25. Atlas, Liquibase, PostgreSQL documentation on destructive schema change and rollback behavior.

---

## Local evidence relationship

The local probe remains authoritative for the inspected host:

- mechanical validation is the only observed usable lane;
- all model-capable live probes were `NOT_RUN`;
- requested and observed model identities are `UNKNOWN`;
- plan-backed billing and full containment remain unproven;
- OpenRouter remains a static-only future API fallback;
- the aggregate Dopemux CLI import attempted network access and is unsuitable for offline preflight.

This report extends those observations with external routing and evaluation research. It does not overwrite them.
