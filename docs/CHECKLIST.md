---
id: CHECKLIST
title: Checklist
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Checklist (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Process Checklist

### Enforceable guardrails for investigations, ADRs, and Task Packets

════════════════════════════════════════════════════════════

Use this checklist before declaring any phase or packet complete.

────────────────────────────────────────────────────────────

## A) Evidence Discipline

[ ] All load-bearing claims are backed by evidence (repo path + identifier).
[ ] Unknowns are explicitly labeled UNKNOWN.
[ ] No fabricated files, functions, ports, env vars, services, commands, or outcomes.
[ ] Command outputs are captured verbatim with exit codes.

────────────────────────────────────────────────────────────

## B) Phase Discipline (PRIMER)

[ ] Phase 0 completed (scope IN/OUT, success criteria, stop conditions, evidence plan).
[ ] Phase 1 completed (inventory of components, entry points, stores, surfaces).
[ ] Phase 2 completed (failure/drift audit with Observed/Inferred/Unknown labels).
[ ] Phase 3 completed (design delta with frozen invariants).
[ ] Phase 4 completed (ADRs written and alternatives considered).
[ ] Phase 5 completed (Task Packets written, scoped, and testable).
[ ] Phase 6 completed (handoff artifact produced when roles/models change).

────────────────────────────────────────────────────────────

## C) Task Packet Quality

[ ] Objective is one sentence and testable.
[ ] Scope includes explicit IN and OUT.
[ ] Invariants are listed and enforceable.
[ ] Plan is numbered and mechanical.
[ ] Files to touch are listed; unexpected files trigger stop condition.
[ ] Exact commands to run are provided.
[ ] Output capture rules require diff + logs + exit codes.
[ ] Acceptance criteria are measurable.
[ ] Rollback steps are explicit.
[ ] Stop conditions are explicit.

────────────────────────────────────────────────────────────

## D) Determinism & Safety

[ ] Changes prefer minimal diffs.
[ ] No refactors unless requested by Task Packet.
[ ] Fail-closed behavior used where correctness/safety is at stake.
[ ] No implicit injection or hidden side effects introduced.
[ ] ASCII-clean maintained in code/config.

────────────────────────────────────────────────────────────

## E) CI and Local Verification

[ ] Proposed checks match GitHub Actions expectations.
[ ] All suggested checks can be run locally.
[ ] Tests were run or explicitly marked skipped with justification.
[ ] Success signals are stated and observed.

────────────────────────────────────────────────────────────

## F) Documentation Hygiene

[ ] ADR references DESIGN_DELTA and related packets where relevant.
[ ] PRIMER and PROJECT_INSTRUCTIONS are referenced, not duplicated, in prompts.
[ ] Workflows are treated as outputs, not drivers, unless canonized in ADR/packet.

────────────────────────────────────────────────────────────

## G) Multi-Model Handoffs

[ ] Handoff artifact exists when switching roles/models.
[ ] Handoff freezes invariants and lists what may change vs must not change.
[ ] Handoff lists known unresolved issues and risks.
[ ] Next packet ordering is explicit.

────────────────────────────────────────────────────────────

If any box is not checked, the phase is not complete.
