---
id: PM_PLANE_GAPS
title: Pm Plane Gaps
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Pm Plane Gaps (explanation) for dopemux documentation and developer workflows.
---
# PM Plane Gaps (Phase 0)

Status: DRAFT (evidence-first)

## Severity rubric
- P0: prevents PM plane from functioning or makes state untrustworthy
- P1: causes persistent friction or drift, but system still runs
- P2: quality/UX issue, not correctness critical
- P3: nice-to-have or cleanup

## Stop condition
If any P0 is present, stop after documenting it. Do not proceed to Phase 1.

## Gaps table
| Severity | Gap | Impact | Where observed | Evidence | Proposed next step (Phase 0 only) |
|---|---|---|---|---|---|
| P0 | rg missing in operator env | audit workflow breaks | operator shell | command output | install rg or lock grep fallback |
| TBD | TBD | TBD | TBD | path:line or output | TBD |

## Explicit absences (important)
Use this section to record searches that returned 0 hits.

| Expectation | Search command | Result | Why it matters |
|---|---|---|---|
| decision linkage fields exist | rg/grep query | 0 hits | traceability gap |
| PM CLI commands exist | rg/grep query | 0 hits | discoverability gap |
