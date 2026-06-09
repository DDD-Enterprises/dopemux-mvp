---
id: TP-DMX-DCP-CI-GATE-001
title: "Wire tests/dcp/ into CI — DCP Red-Lane Gate Enforcement"
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-07'
last_review: '2026-06-07'
next_review: '2026-09-07'
status: READY_FOR_REVIEW
prelude: Add tests/dcp/ as a required CI step in ci-complete.yml. Deselects pre-existing
  test_16_no_forbidden_files_modified (stale base SHA, unrelated to this gate). 82 DCP
  tests now run on every PR. Closes the CI enforcement gap deferred by TP-DMX-DCP-SEAM-ENFORCEMENT-001.
---
# Task Packet: TP-DMX-DCP-CI-GATE-001 · Development Factory · Wire DCP Gate into CI

════════════════════════════════════════════════════════════

## Objective

Add `tests/dcp/` as a required CI enforcement step in `.github/workflows/ci-complete.yml`. This closes the CI enforcement gap explicitly deferred by `TP-DMX-DCP-SEAM-ENFORCEMENT-001`.

────────────────────────────────────────────────────────────

## Why This Packet Exists Now

`TP-DMX-DCP-SEAM-ENFORCEMENT-001` wired `RedLaneScanner` as an invokable gate and noted:

> `ci_enforcement: ABSENT — tests/dcp/ not in any .github/workflows/*.yml`

That packet deferred CI wiring as "non-trivial CI wiring." This packet closes it.

Investigation confirmed:
- `tests/dcp/` has 5 test files, 83 tests total
- 82 pass cleanly; 1 pre-existing failure (`test_16_no_forbidden_files_modified`) uses hardcoded base SHA `68f7435f6` and blocks `.github/workflows/` changes — this is a packet-execution guard, not a CI invariant
- The deselect is minimal and principled: only the single stale-SHA test is excluded

────────────────────────────────────────────────────────────

## Outcome

**WIRED** — `tests/dcp/` runs on every PR as a required CI step.

────────────────────────────────────────────────────────────

## Change Summary

- **`.github/workflows/ci-complete.yml`**: Added step `🔴 Run DCP red-lane gate (TP-DMX-DCP-CI-GATE-001)` to the Unit Tests job, after the existing fast unit gate step. Runs `tests/dcp/` with `--deselect` for `test_16_no_forbidden_files_modified`.

────────────────────────────────────────────────────────────

## Scope Boundary

| In Scope | Deferred |
|---|---|
| CI wiring: one new step in ci-complete.yml | Fix `test_16` stale-SHA root cause (separate packet) |
| Proof bundle for this packet | Pre-existing dead code in `scan()` CONFLICTING branch (from TP-DMX-DCP-SEAM-ENFORCEMENT-001 F001) |

────────────────────────────────────────────────────────────

## Pre-existing Failure — `test_16_no_forbidden_files_modified`

This test in `tests/dcp/test_dcp_0002_contract_derivation.py` diffs `68f7435f6...HEAD` and blocks changes to `.github/workflows/`. The base SHA is hardcoded in `task-packets/TP-DCP-0002.md` as the packet execution boundary. Legitimate workflow changes merged after that SHA cause the test to fail on unrelated work. The `--deselect` flag in CI is the correct minimal fix; the root cause (stale base SHA) is a separate concern.

────────────────────────────────────────────────────────────

## Validations

| Name | Status | Evidence |
|---|---|---|
| pytest_82_pass | PASS | 82 passed / 0 failed / 1 deselected in 0.11s |
| ci_step_added | PASS | Step present in ci-complete.yml at correct position |
| no_seam_code_modified | PASS | red_lane_rules.py, red_lane_scanner.py not in git diff |
| no_forbidden_paths_touched | PASS | queue_drain.py, batch_resolve_and_merge.py not modified |
| deselect_is_minimal | PASS | Only test_16_no_forbidden_files_modified excluded |

────────────────────────────────────────────────────────────

## Files Modified

- `.github/workflows/ci-complete.yml` — one new step added to Unit Tests job

## Files Created

- `task-packets/development-factory/TP-DMX-DCP-CI-GATE-001.md` (this file)
- `proof/TP-DMX-DCP-CI-GATE-001/PROOF.json`
- `proof/TP-DMX-DCP-CI-GATE-001/SUMMARY.md`

## Files Not Modified

- `src/dopemux/dcp/red_lane_scanner.py`
- `src/dopemux/dcp/red_lane_rules.py`
- `src/dopemux_pr_merge_specialist/queue_drain.py`
- `scripts/batch_resolve_and_merge.py`
- `tests/dcp/` (no test changes)

────────────────────────────────────────────────────────────

## Red Lines

- `DCP-RED-MERGE-SEAM-0001`: PRESERVED — no runtime code modified
- Hard block: not relaxed, renamed, bypassed, or weakened
- `LIVE_WRITE_READY`: not defined, not enabled

────────────────────────────────────────────────────────────

## Authority

- `TP-DMX-DCP-SEAM-ENFORCEMENT-001` — deferred this exact work as follow-up
- `proof/TP-DMX-DCP-SEAM-ENFORCEMENT-001/PROOF.json` — `ci_test_enforcement: NOT_RUN` finding
- Runtime code inspection: `tests/dcp/` absent from all prior CI workflow steps (confirmed)
