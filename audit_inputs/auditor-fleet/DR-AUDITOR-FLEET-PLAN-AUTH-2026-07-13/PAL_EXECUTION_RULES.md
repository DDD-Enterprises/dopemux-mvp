---
id: pal-execution-rules
title: Pal Execution Rules
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Pal Execution Rules (reference) for dopemux documentation and developer workflows.
---
# PAL_EXECUTION_RULES.md

## Status
Compressed operational rules derived from `docs/03-reference/execution/pal-chaining-doctrine.md` (historical source label: `PAL_CHAINING_DOCTRINE.md`).

## Purpose
Daily-use rules for running PAL-driven engineering packets without re-litigating the doctrine every time.

---

## 1. Hard Rules

1. No planner before validated understanding.
2. No implementation before plan challenge.
3. No consensus unless at least two credible approaches exist.
4. No debug without failure, contradiction, or concrete uncertainty.
5. No precommit without codereview first.
6. No docgen on unstable code.
7. No API guessing. Use apilookup when external behavior matters.
8. Every major artifact must be challenged or discarded.
9. Keep stage-boundary outputs compressed.
10. Final completion requires an evidence ledger.

---

## 2. Confidence Thresholds

- LOW: speculative, not actionable
- MEDIUM: partially evidenced, safe for bounded planning
- HIGH: strongly evidenced, safe for implementation or bug-fix targeting
- VERIFIED: passed final evidence gates, safe for completion claims

Minimum thresholds:
- understanding before planner: MEDIUM
- plan before implementation: MEDIUM or HIGH depending on risk
- root cause before bug fix: HIGH
- final completion: VERIFIED

---

## 3. Standard Chain Grammar

### Default
`analyze -> thinkdeep -> challenge -> planner -> challenge -> codereview -> precommit -> challenge`

### Add tracer when
- call-flow ambiguity blocks safe planning or editing

### Add consensus when
- multiple credible approaches remain
- the choice is expensive to reverse

### Add debug when
- runtime behavior is broken, surprising, or contradictory

### Add testgen when
- regression risk is real
- codereview finds coverage gaps
- bug fixes need durable lock-in

### Add secaudit when
- auth, secrets, sensitive data, or attack surface changes

### Add docgen when
- docs are required
- public interfaces changed
- complexity or gotchas need documentation

### Add apilookup when
- API/SDK/OS behavior affects correctness

---

## 4. Task Recipes

### Unknown subsystem
`analyze -> thinkdeep -> challenge -> (tracer -> analyze if needed) -> planner`

### Architecture-sensitive change
`analyze -> thinkdeep -> challenge -> planner -> codereview -> precommit`

### Runtime bug
`debug -> thinkdeep -> challenge -> testgen -> codereview -> precommit`

### Ambiguous design fork
`planner (alts) -> consensus -> thinkdeep -> challenge -> planner (final)`

### API-sensitive work
`apilookup -> challenge -> analyze -> planner -> codereview -> precommit`

### Documentation-sensitive work
`analyze -> planner -> implement -> docgen -> challenge -> codereview -> precommit`

### Security-sensitive work
`analyze -> planner -> implement -> secaudit -> codereview -> precommit`

---

## 5. Slice Execution Rule

Work in commit-sized slices.

After each meaningful slice:
- run the smallest relevant verification
- inspect the diff
- decide whether to continue, re-plan, or enter debug

Do not accumulate multiple unvalidated slices unless explicitly authorized.

---

## 6. Artifact Contract

Every stage artifact must include:
- summary
- evidence ledger
- assumptions
- confidence
- next action

Keep it compact.

---

## 7. Stop Rules

Stop chaining when:
- the next tool would not change the decision
- uncertainty can only be resolved by implementation or runtime evidence
- outputs are repetitive rather than decision-advancing
- blast radius is growing instead of narrowing

Stop the packet when:
- understanding cannot reach MEDIUM
- the plan cannot be made executable in scope
- required API facts cannot be sourced
- root cause cannot reach HIGH
- final verification cannot reach VERIFIED

---

## 8. Minimum Completion Standard

Before commit:
- codereview complete
- precommit passed
- evidence ledger complete
- final confidence = VERIFIED
