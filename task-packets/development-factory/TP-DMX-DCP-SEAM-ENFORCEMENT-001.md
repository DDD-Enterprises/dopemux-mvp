---
id: TP-DMX-DCP-SEAM-ENFORCEMENT-001
title: "Wire RedLaneScanner as Invokable Gate \u2014 Preserve Hard Block"
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-06'
status: READY_FOR_REVIEW
prelude: Wire existing RedLaneScanner into an auditable gate path while preserving
  DCP-RED-MERGE-SEAM-0001 intact. Scanner was fully implemented (288 lines, 16 tests)
  but had no invokable entrypoint and was absent from all CI workflows. This packet
  adds the entrypoint and closes two FORBIDDEN_PATH test gaps. CI enforcement wiring
  is deferred to a follow-up packet.
---
# Task Packet: TP-DMX-DCP-SEAM-ENFORCEMENT-001 · Development Factory · Wire RedLaneScanner

════════════════════════════════════════════════════════════

## Objective

Wire the existing `RedLaneScanner` into an auditable gate path without lifting, removing, or relaxing `DCP-RED-MERGE-SEAM-0001`. If wiring requires lifting the seam: stop. If wiring is purely additive read-only: proceed.

────────────────────────────────────────────────────────────

## Why This Packet Exists Now

`TP-RTE-S7-DRIFT-FIX-001` recommended this packet as the next enforcement step. Investigation confirmed:
- `RedLaneScanner` fully implemented at `src/dopemux/dcp/red_lane_scanner.py` (288 lines)
- 16 existing tests in `tests/dcp/test_dcp_0005_red_lane_scanner.py` — all passing
- **No invokable entrypoint**: no `__main__`, no `console_scripts`, no entry in `scripts/`
- **Not in CI**: `tests/dcp/` absent from all `.github/workflows/*.yml`
- Two FORBIDDEN_PATH test gaps: `scripts/batch_resolve_and_merge.py` (file-path match only) and `dopemux_pr_merge_specialist/queue_drain.py` (non-src/ variant) had no covering path tests

────────────────────────────────────────────────────────────

## Outcome

**WIRED** — gate is now invokable as `python -m dopemux.dcp.red_lane_scanner`.

### CLI Entrypoint Added

`main()` + `if __name__ == "__main__": raise SystemExit(main())` added to `src/dopemux/dcp/red_lane_scanner.py`, mirroring `validate_pre_live_gate_v25.py`:

```bash
# Invocation form
PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner \
  --repo-root . \
  --files path/to/changed_file.py \
  --proof-paths proof/TP-XXXX/PROOF.json \
  --expected-sha <HEAD_SHA>

# Exit codes: 0=PASS, 1=BLOCKED/UNKNOWN/CONFLICTING (fail-closed)
# Output: RedLaneReport JSON to stdout (or --output FILE)
```

Constraints preserved:
- Read-only: does not import or execute `queue_drain`, `batch_resolve_and_merge`, or any merge-seam module
- Fail-closed: exits 1 on any non-PASS status (BLOCKED, UNKNOWN, CONFLICTING)
- Emits full `RedLaneReport` JSON as audit artifact

### Two Test Gaps Closed

1. `test_batch_resolve_script_path_returns_blocked` — `scripts/batch_resolve_and_merge.py` as FORBIDDEN_PATH file-path match (FORBIDDEN_PATHS[2])
2. `test_queue_drain_bare_path_returns_blocked` — `dopemux_pr_merge_specialist/queue_drain.py` (non-src/ prefix, FORBIDDEN_PATHS[1]) as file-path match

### Smoke Test Results

| Invocation | Status | Exit |
|---|---|---|
| `--files src/dopemux/dcp/red_lane_scanner.py` (no proof) | UNKNOWN → fail-closed | 1 |
| `--files src/dopemux_pr_merge_specialist/queue_drain.py` | BLOCKED, 39 blockers | 1 |

────────────────────────────────────────────────────────────

## Scope

IN (modified + created):

* `src/dopemux/dcp/red_lane_scanner.py` — added `main()` + `__main__` block (53 lines net)
* `tests/dcp/test_dcp_0005_red_lane_scanner.py` — added 2 new path tests (22 lines net)
* `task-packets/development-factory/TP-DMX-DCP-SEAM-ENFORCEMENT-001.md` (this file)
* `proof/TP-DMX-DCP-SEAM-ENFORCEMENT-001/PROOF.json`
* `proof/TP-DMX-DCP-SEAM-ENFORCEMENT-001/SUMMARY.md`

OUT (not touched):

* `src/dopemux/dcp/red_lane_rules.py` — rules correct, not modified
* `.github/workflows/` — CI enforcement deferred to follow-up packet
* `src/dopemux_pr_merge_specialist/queue_drain.py` — not imported, not executed
* `scripts/batch_resolve_and_merge.py` — not imported, not executed
* Runtime code, schemas, `config/`, Task-Orchestrator, ConPort, dope-context, dopecon-bridge state
* GitHub state, merge automation

────────────────────────────────────────────────────────────

## Invariants

* `DCP-RED-MERGE-SEAM-0001` not lifted, removed, relaxed, renamed, or bypassed.
* `LIVE_WRITE_READY` not defined or enabled anywhere.
* Entrypoint is read-only (scan → report → exit). No writes.
* No service/task/proof-policy/GitHub state changed.
* No secrets printed.
* `queue_drain.py` / `batch_resolve_and_merge.py` not touched, imported, or executed.

────────────────────────────────────────────────────────────

## Acceptance Criteria

* `python -m dopemux.dcp.red_lane_scanner` is invokable. ✅
* Emits `RedLaneReport` JSON. ✅
* Exits 1 on BLOCKED; exits 1 on UNKNOWN (fail-closed). ✅
* Exits 0 only on PASS. ✅
* Suite: 18 passed / 0 failed. ✅
* Two path test gaps closed. ✅
* No runtime rules code touched. ✅
* `DCP-RED-MERGE-SEAM-0001` preserved. ✅

────────────────────────────────────────────────────────────

## Commands Run

```bash
PYTHONPATH=src python -m pytest -v tests/dcp/test_dcp_0005_red_lane_scanner.py
# 18 passed in 0.05s

PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner \
  --repo-root . --files src/dopemux/dcp/red_lane_scanner.py
# status=UNKNOWN, exit 1 (fail-closed, no proof)

PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner \
  --repo-root . --files src/dopemux_pr_merge_specialist/queue_drain.py
# status=BLOCKED, 39 blockers, exit 1
```

────────────────────────────────────────────────────────────

## Rollback

* `git checkout -- src/dopemux/dcp/red_lane_scanner.py tests/dcp/test_dcp_0005_red_lane_scanner.py`
* `rm -rf task-packets/development-factory/TP-DMX-DCP-SEAM-ENFORCEMENT-001.md proof/TP-DMX-DCP-SEAM-ENFORCEMENT-001/`

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS (preserved — no stop triggered)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Would have stopped if: wiring required lifting or relaxing DCP-RED-MERGE-SEAM-0001, call path or entrypoint form unclear with no convergence after 2 attempts, or evidence conflicted with described scope. None triggered.

## Remaining Uncertainty

- `tests/dcp/` not in CI — gate is locally verified but not CI-enforced; deferred to follow-up CI wiring packet
- PAL codereview not run on this packet — queued for external audit
- **TP-DMX-PROOF-TRACKING-POLICY-001** is READY_FOR_REVIEW but unaudited — branch is NOT PR-clean until that policy receives its own audit classification

## Next Recommended Packets

1. External PAL audit on TP-DMX-DCP-SEAM-ENFORCEMENT-001
2. CI enforcement wiring packet (add `tests/dcp/` to `.github/workflows/`)
3. Audit `TP-DMX-PROOF-TRACKING-POLICY-001` before any PR is called clean
