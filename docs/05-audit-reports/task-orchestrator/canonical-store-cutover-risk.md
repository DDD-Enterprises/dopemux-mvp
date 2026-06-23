---
id: canonical-store-cutover-risk
title: Canonical Store Cutover Risk Assessment
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: Canonical Store Cutover Risk Assessment (reference) for dopemux documentation and developer
  workflows.
---
# Canonical Store Cutover — Red-Team Risk Assessment

Companion to [canonical-store-cutover-plan.md](../../03-reference/systems/task-orchestrator/canonical-store-cutover-plan.md).

## Verdict

**PASS_WITH_RISKS.**

The cutover *plan* is safe to merge because it authorizes **no writes**, performs no live mutation, and
fails closed at an explicit operator-approval gate. The residual risks below are about **future
execution** (Phase 3), which this plan deliberately leaves NOT AUTHORIZED. None of them are introduced by
adopting the plan document itself.

## Risk register

| ID | Risk | Likelihood (at plan stage) | Impact if executed unsafely | Mitigation in the plan |
|----|------|----------------------------|-----------------------------|------------------------|
| R1 | Data loss from overwriting a live `current-tasks.db` | None now (no writes) | High | Phase 1 backup + integrity check are mandatory preconditions; Phase 3 is NOT AUTHORIZED |
| R2 | Authority flattening — treating the derived store as the single PM truth | Low | High (breaks split-authority model) | Authority-boundary table is normative; store is DERIVED/read-only; canonical writer stays the live TO MCP |
| R3 | `dopecon-bridge` promoted to a data authority | Low | High | Explicit invariant: bridge is transport-only and MUST NOT become an authority |
| R4 | Replay / idempotency regressions after a write cutover | None now | Medium-High | Precondition 4 requires replay/dedupe verification before any write |
| R5 | Stale / recovery DB rows promoted into active state | Low | Medium | Stale/legacy/recovery DBs stay provenance-only; archive-never-delete |
| R6 | Operator-approval gate bypass / automation | Low | High | Plan fails closed; default denied; no step past Phase 2 without recorded sign-off |
| R7 | Stale point-in-time view presented as live | Medium | Medium | Read view (006) carries a `valid_as_of` banner; cutover requires a freshly regenerated snapshot |
| R8 | Task Orchestrator MCP health / SQLite contention during backup | Medium | Low-Medium | Backup and rollback use SQLite online `.backup` / `.restore` to produce a single consistent file; never bare `cp -a` of live DB files (WAL/SHM sidecars can tear snapshots under contention) |

## Notes

- The most dangerous step (R1) is gated behind a precondition chain (backup → approval) and is explicitly
  marked NOT AUTHORIZED in the plan. Merging the plan does not enable it.
- R7 is the subtlest operational risk: a derived view must never imply liveness. The 006 read surface
  mitigates this with an explicit `valid_as_of` banner; the cutover plan reinforces it by requiring a fresh
  snapshot before any cutover.

## Residual uncertainty

- The future write cutover (Phase 3) is intentionally under-specified; it requires a dedicated ADR before it
  can be designed. This risk doc covers the *plan*, not an executed migration.
