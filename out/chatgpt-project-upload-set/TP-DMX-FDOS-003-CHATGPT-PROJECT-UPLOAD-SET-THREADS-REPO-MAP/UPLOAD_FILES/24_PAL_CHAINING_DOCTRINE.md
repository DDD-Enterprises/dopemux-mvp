---
id: pal-chaining-doctrine
title: Pal Chaining Doctrine
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Pal Chaining Doctrine (reference) for dopemux documentation and developer
  workflows.
---
# PAL_CHAINING_DOCTRINE.md

## Status
Canonical execution doctrine for PAL MCP tool chaining in software engineering workflows.

## Purpose
This document defines the authoritative doctrine for how PAL MCP tools should be chained across engineering work. It is intended to govern:
- understanding and reconnaissance
- approach selection
- implementation planning
- bug investigation
- implementation hardening
- diff review
- documentation generation and validation
- final verification before commit

It exists to prevent predictable failure modes:
- acting on shallow understanding
- planning from guesses
- implementing before the plan is pressure-tested
- trusting plausible reasoning over evidence
- treating tool output as proof
- using too many tools too early and poisoning context
- relying on final gates to clean up upstream sloppiness

This doctrine assumes PAL tools are not decorative assistants. They are workflow primitives. Their value comes from sequence, role discipline, and validation boundaries.

## Scope
This doctrine applies to implementation-oriented workflows where PAL tools are available, including:
- feature work
- refactors
- bug fixes
- architecture-sensitive changes
- API/SDK-sensitive changes
- documentation-sensitive changes
- security-sensitive changes
- validation and pre-commit hardening

This doctrine does not replace:
- repository-specific rules
- architecture canon
- change-management policy
- test requirements
- review requirements
- release procedures

Higher-priority local or project-specific rules override this doctrine where they conflict.

---

## 1. Core Thesis

PAL tool chaining should validate engineering work at multiple distinct levels:
1. understanding validation - did we correctly understand the code, architecture, dependencies, and flows?
2. approach validation - is the chosen strategy actually sound relative to alternatives?
3. plan validation - is the work sequenced safely, with verification and rollback built in?
4. root-cause validation - if behavior is broken, is the diagnosis actually evidenced?
5. implementation validation - did the change do what it intended without obvious breakage?
6. diff validation - is the resulting change-set correct, maintainable, safe, and coherent?
7. documentation validation - do the docs reflect the final implementation and its caveats?
8. final verification - is the full change ready to commit based on actual evidence?

The doctrine rejects the lazy habit of collapsing these into one vague question like "does this seem right?"

---

## 2. Non-Negotiable Chain Laws

### Law 1. No planner before validated understanding.
Do not use `planner` to produce an execution plan until understanding has reached at least MEDIUM confidence through `analyze`, `tracer`, or equivalent evidenced inspection.

### Law 2. No implementation before plan challenge.
Every non-trivial plan must be pressure-tested by `challenge`. High-risk or ambiguous plans should also be deepened with `thinkdeep` first.

### Law 3. No consensus unless real ambiguity exists.
Do not invoke `consensus` unless there are at least two credible approaches, the choice matters, and the decision is materially expensive to reverse.

### Law 4. No debug without failure, contradiction, or concrete uncertainty.
`debug` is for investigating behavior that is broken, surprising, or insufficiently explained. It is not a general-purpose thinking ritual.

### Law 5. No precommit without prior diff hardening.
`precommit` is the final gate, not the first serious review. Minimum acceptable hardening for meaningful changes is `codereview -> precommit`.

### Law 6. No docgen on unstable implementation.
Do not run `docgen` while implementation is still moving significantly.

### Law 7. No apilookup guessing.
If current API, SDK, framework, package, or OS-version behavior affects correctness, `apilookup` is mandatory before the plan is locked.

### Law 8. Every major stage artifact must be challenged or discarded.
Any artifact you are about to act on must be either pressure-tested or replaced. Unchallenged outputs are provisional.

### Law 9. Stage-boundary outputs must be compact.
At stage boundaries, output must be compressed to decision-grade form. Do not drag whole transcripts, giant diffs, or sprawling summaries into every subsequent stage.

### Law 10. Final completion claims require evidence.
No task may be called complete without an evidence ledger that records what was inspected, what was changed, what was tested, what was reviewed, and what final gate passed.

### Law 11. Tool output is not proof.
No PAL analysis tool by itself proves correctness. Tool output may reveal evidence, organize findings, or surface risks, but proof requires inspection, tests, review, or final gate validation.

### Law 12. Chaining must stop when additional tools no longer change the decision.
If the next tool call would add noise rather than decision value, stop.

---

## 3. Confidence Taxonomy

### LOW
- speculative
- weakly evidenced
- incomplete or contradictory
- not safe to plan or implement from

### MEDIUM
- plausible and partially evidenced
- enough to proceed with bounded caution
- still requires challenge and often deeper validation

### HIGH
- strongly evidenced
- consistent with observed code, flow, or runtime behavior
- safe to proceed with execution or fix design

### VERIFIED
- supported by final evidence such as executed tests, confirmed behavior, review findings resolution, and pre-commit validation
- sufficient for completion claims

### Minimum required confidence by stage
- understanding before planning: MEDIUM
- plan before implementation: MEDIUM, preferably HIGH for risky changes
- root cause before bug fix: HIGH
- final completion claim: VERIFIED

If confidence does not meet the stage threshold, you must either gather evidence, narrow scope, or stop.

---

## 4. Tool Roles and Trust Boundaries

### 4.1 `analyze`
Role: systematic code understanding across files, modules, patterns, dependencies, and architecture.

Use for unfamiliar subsystem exploration, architecture scans, responsibility mapping, and invariant discovery.

Validates best: understanding.

Do not trust it for final correctness of a fix, proving runtime behavior, or replacing final review or final verification.

Best chain position: first or early.

Doctrine status: conditional but effectively mandatory when the area is unfamiliar or architecture-sensitive.

### 4.2 `tracer`
Role: structured tracing of call flow, dependencies, fan-in, and fan-out.

Use for call-flow ambiguity, dependency directionality, safe edit-point discovery, and high-coupling work.

Validates best: trace and flow assumptions.

Do not trust it for full architectural understanding by itself, runtime truth without corroboration, or strategy selection by itself.

Best chain position: after initial orientation, before planning if flow ambiguity blocks safe action.

Doctrine rule: tracer does not replace analyze. It sharpens the flow question. Analysis or equivalent reasoning still has to validate what the trace implies.

### 4.3 `planner`
Role: stepwise plan generation, sequencing, branching, dependency management.

Use for implementation plans, migration sequencing, safe refactor decomposition, and validation-aware execution paths.

Validates best: plan structure.

Do not trust it for choosing among ambiguous approaches without further challenge or proving feasibility without understanding inputs.

Best chain position: after understanding reaches MEDIUM confidence.

Doctrine status: core.

### 4.4 `thinkdeep`
Role: deep stage-transition reasoning, edge-case analysis, alternative approach exploration, second-order effect detection.

Use for deepening understanding after reconnaissance, stress-testing plans, probing review findings for deeper implications, and challenging hidden coupling or edge cases.

Validates best: approach and risk discovery.

Do not trust it for current API facts, completion proof, or runtime verification without evidence.

Best chain position: between major stages, not between every micro-step.

Doctrine status: core, budgeted.

### 4.5 `challenge`
Role: adversarial critique and anti-complacency check.

Use for testing assumptions after understanding, testing executable soundness after planning, questioning review verdicts, and questioning final readiness before commit.

Validates best: assumption strength.

Do not trust it for deep exploration by itself or replacing plan structure or analysis.

Best chain position: immediately after a stage artifact you are tempted to trust.

Doctrine status: core.

### 4.6 `consensus`
Role: multi-perspective approach comparison.

Use for real design forks, architecture decisions with tradeoffs, reversibility-expensive choices, and decisions involving security, performance, or operability tradeoffs.

Validates best: approach selection under ambiguity.

Do not trust it for trivial decisions or producing truth where facts are missing.

Best chain position: after planner when multiple serious options remain.

Doctrine status: escalation tool.

### 4.7 `debug`
Role: systematic investigation of concrete failures or surprising behavior.

Use for runtime bugs, flaky tests, unexplained failures, and contradictions between expectation and evidence.

Validates best: root-cause hypotheses.

Do not trust it for general architecture reconnaissance or feature planning without failure evidence.

Best chain position: lead tool for bugs, or conditional escalation from implementation when behavior breaks.

Doctrine status: conditional, mandatory for runtime uncertainty.

### 4.8 `codereview`
Role: professional diff hardening.

Use for final diff review, security/performance/maintainability review, issue severity triage, and cross-file quality validation.

Validates best: diff quality.

Do not trust it for proving requirements are met end-to-end or replacing executed verification.

Best chain position: after implementation stabilizes, before precommit.

Doctrine status: core.

### 4.9 `precommit`
Role: final readiness gate.

Use for final change-set validation, dependency impact checks, regression risk checks, and final approval or fix-required output.

Validates best: final verification.

Do not trust it for replacing earlier review hardening or discovering the entire strategy from scratch.

Best chain position: last validation tool before commit.

Doctrine status: mandatory final gate.

### 4.10 `docgen`
Role: documentation generation and documentation-grounding validation.

Use for public interface changes, complexity-heavy modules, gotcha-rich code, and onboarding-sensitive changes.

Validates best: documentation completeness and implementation alignment.

Do not trust it for correctness if the implementation is still unstable or final truth of docs without checking final code surfaces.

Best chain position: late-middle, once code stabilizes, before final review gates.

Doctrine status: conditional, mandatory where docs are required or behavior is likely to confuse future maintainers.

### 4.11 `apilookup`
Role: authoritative current API/SDK fact validation.

Use for breaking changes, migrations, version-dependent behavior, deprecations, and OS-specific APIs.

Validates best: API/SDK correctness assumptions.

Do not trust it for codebase-local architectural truth or final implementation safety by itself.

Best chain position: early, before the plan locks, and again if implementation hits external API ambiguity.

Doctrine status: mandatory when API/SDK sensitivity exists.

### 4.12 `testgen`
Role: generate validation-oriented tests, especially for regressions and edge cases.

Use for bug fixes, risky refactors, logic-heavy flows, and coverage gaps found during review.

Validates best: test strategy and regression coverage.

Do not trust it for correctness without actually executing tests.

Best chain position: middle-late, after the approach is chosen, before final precommit.

Doctrine status: escalation tool, strongly recommended for real regression risk.

### 4.13 `secaudit`
Role: security-focused validation and threat-surface assessment.

Use for auth/authz changes, secrets handling, sensitive data flows, and internet-facing surface changes.

Validates best: security risk.

Do not trust it for replacing full security engineering or production controls.

Best chain position: late-middle, once the diff exists and the real attack surface is visible.

Doctrine status: escalation tool, mandatory for security-sensitive work.

### 4.14 `refactor`
Role: refactor-specific decomposition and modernization guidance.

Use for large refactors, decomposition planning, and legacy modernization.

Validates best: refactor structure and seam discovery.

Do not trust it for proving the refactor is safe without tests/review/final validation.

Best chain position: early-middle.

Doctrine status: optional/conditional.

---

## 5. Standard Chain Grammar

The default chain grammar is:

1. Understand: `analyze`, optionally `tracer -> analyze`
2. Deepen: `thinkdeep`
3. Adversarial check: `challenge`
4. Plan: `planner`
5. Plan check: `challenge`, optionally `thinkdeep`, optionally `consensus`
6. Execute: implement outside PAL, optionally `testgen`, `refactor`, `secaudit`, `apilookup` re-entry as needed
7. Review: `codereview`
8. Final gate: `precommit`
9. Final sanity: `challenge`

This grammar should be adapted per task type, but not casually violated.

---

## 6. Chain Recipes by Task Type

### 6.1 Unfamiliar subsystem
Recommended chain: `analyze -> thinkdeep -> challenge -> (tracer -> analyze if needed) -> thinkdeep -> challenge -> planner`

Use when subsystem boundaries or ownership are unclear.

Do not use when the architectural map is already validated.

Required stage outputs:
- component map
- key files
- invariants
- primary entry points
- call-flow uncertainty list
- plan draft

Exit condition: you can name the safe edit points and relevant blast radius.

### 6.2 Architecture-sensitive change
Recommended chain: `analyze -> thinkdeep -> challenge -> planner -> thinkdeep -> challenge -> codereview -> precommit`

Use when the change spans modules or crosses abstraction boundaries.

Exit condition: impact boundary and regression risks are explicit.

### 6.3 Call-flow-sensitive work
Recommended chain: `tracer -> analyze -> thinkdeep -> challenge -> planner`

Use when safe edits depend on knowing call hierarchy or fan-out.

Exit condition: the call graph is understood well enough to choose a safe change point.

### 6.4 Ambiguous design fork
Recommended chain: `planner (alternatives) -> consensus -> thinkdeep -> challenge -> planner (final) -> codereview -> precommit`

Use when at least two credible designs remain and reversibility is expensive.

Exit condition: one approach is selected with explicit rationale and rejected alternatives.

### 6.5 Runtime bug
Recommended chain: `debug -> thinkdeep -> challenge -> testgen -> codereview -> precommit`

Use when behavior is broken, flaky, or contradicted by evidence.

Exit condition: root cause is HIGH confidence and fix is backed by regression validation.

### 6.6 API/SDK-sensitive change
Recommended chain: `apilookup -> challenge -> analyze -> planner -> codereview -> precommit`

Use when correctness depends on current external APIs or SDK behavior.

Exit condition: the plan includes version assumptions and verification steps.

### 6.7 Documentation-sensitive change
Recommended chain: `analyze -> planner -> implement -> docgen -> challenge -> codereview -> precommit`

Use when docs are acceptance criteria or behavior/gotchas must be captured.

Exit condition: docs match final code surfaces and caveats.

### 6.8 Security-sensitive change
Recommended chain: `analyze -> thinkdeep -> planner -> challenge -> implement -> secaudit -> codereview (security) -> precommit`

Use when auth, secrets, sensitive data, or exposed attack surface changes.

Exit condition: no unresolved material security findings remain.

---

## 7. Implementation-Phase Doctrine

### 7.1 Slice execution rule
Implementation must proceed in commit-sized slices.

After each meaningful slice:
- run the smallest relevant verification
- inspect the diff
- decide whether to continue, revise the plan, or enter debug

Do not stack multiple unvalidated slices unless the packet explicitly authorizes it.

### 7.2 Slice review loop
For risky or growing diffs: `(implement slice) -> codereview (quick/full as appropriate) -> challenge -> continue`

Use `testgen` if the slice creates or reveals coverage gaps.

### 7.3 Debug re-entry rule
If implementation produces surprising failures, contradictions, or unclear behavior:
- stop speculative patching
- enter `debug`
- do not continue implementation until the root cause reaches at least HIGH confidence

### 7.4 Re-plan rule
If codereview, debug, or precommit reveals architecture-level issues or sequence flaws:
- return to `planner`
- revise the plan
- continue only once the revised plan is challenged again

---

## 8. Output Artifact Contract

Every stage artifact must be:
- compact
- evidence-linked
- decision-oriented
- challengeable

### Required artifact fields at stage boundaries
1. summary - what is currently believed
2. evidence ledger - files, flows, logs, findings, or API docs inspected
3. assumptions - what remains provisional
4. confidence - LOW / MEDIUM / HIGH / VERIFIED
5. next action - and why it is justified

### Output-shape rule
Use richer output inside investigation workflows. Use compressed output at stage boundaries.

Do not carry forward:
- giant code dumps
- full review transcripts
- repeated summaries
- giant diffs in-band

If output is not improving the next decision, compress it or discard it.

---

## 9. Escalation Rules

Escalate to `consensus` when there are at least two credible approaches, the decision is expensive to reverse, and tradeoffs matter materially.

Escalate to `debug` when there is a concrete failure, expected behavior is contradicted by evidence, or confidence is too low to justify a fix.

Escalate to `docgen` when docs are required, public interfaces changed, or complexity or gotcha risk is high.

Escalate to `apilookup` when external API or SDK behavior matters, version/deprecation/migration facts affect correctness, or OS-bound behavior is relevant.

Escalate to `testgen` when regression risk is real, a bug fix needs lock-in coverage, or codereview identifies coverage gaps.

Escalate to `secaudit` when auth/authz changes, secrets or sensitive data are touched, or network-facing behavior changes.

Escalate to `refactor` when refactor scope is broad enough that seam discovery matters or decomposition strategy is unclear.

---

## 10. Termination Rules

Stop chaining when any of the following is true:
- the next tool would not change the decision
- uncertainty is below the packet's risk threshold
- remaining uncertainty can only be resolved by implementation or runtime evidence
- outputs have become repetitive rather than decision-advancing
- the chain is widening the blast radius instead of narrowing the problem
- the packet should be split rather than further reasoned about

Stop the packet entirely when:
- understanding cannot reach MEDIUM confidence
- the plan cannot be made executable within scope
- required API facts cannot be sourced
- runtime evidence is insufficient to reach HIGH confidence on a root cause
- final verification cannot reach VERIFIED

---

## 11. Anti-Patterns

- using many tools before validating the subsystem map
- using planner before understanding
- using consensus for straightforward decisions
- using debug without concrete failure or contradiction
- using challenge only after implementation is largely complete
- carrying giant outputs across every stage
- letting precommit become the first serious quality step
- generating docs before code is stable
- making completion claims without an evidence ledger
- looping through thinkdeep/challenge/consensus after the decision is already clear

---

## 12. Final Verification Standard

Minimum acceptable final hardening for meaningful work: `codereview -> precommit`

Recommended final hardening for most non-trivial work: `codereview -> challenge -> precommit -> challenge`

A task may only be declared complete when:
- required scope is satisfied
- no unresolved material review findings remain
- final precommit passes or required fixes were completed and rerun
- evidence ledger is complete
- final confidence is VERIFIED

---

## 13. Evidence Ledger Requirements

Every completed packet must include:
- task objective
- scope actually changed
- relevant files inspected
- tools used and why
- key findings by stage
- assumptions resolved or remaining
- tests run or validation performed
- codereview findings and disposition
- precommit verdict
- residual risks
- final completion status
