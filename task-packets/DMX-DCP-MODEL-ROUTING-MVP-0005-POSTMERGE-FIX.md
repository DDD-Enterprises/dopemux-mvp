---
id: DMX-DCP-MODEL-ROUTING-MVP-0005-POSTMERGE-FIX
title: DCP Lane Engine — Post-merge fail-closed hardening (PR #906 threads)
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Closes the two unresolved, non-outdated review threads left on merged PR #906 (DCP 0005 lane engine). Both are fail-closed gaps against forged/restored RouteDecisions — the threat 0007 (trusted input-provenance) will own, but cheap to close in the lane engine now. No new lane, no execution surface, no widened actions.
---

# DMX-DCP-MODEL-ROUTING-MVP-0005-POSTMERGE-FIX

**Series**: DMX-DCP-MODEL-ROUTING-MVP
**Packet**: 0005-POSTMERGE-FIX (hardening follow-up to 0005 / PR #906)
**Depends on**: PR #906 merged onto `main` (`02fa9b30a`); 0006 provenance hardening on `main` (`556ffff1b`).
**Base**: cut from `main` @ `556ffff1b`.
**Branch**: `feat/dcp-lane-engine-postmerge-fix`.

---

## Objective

Merged PR #906 left two unresolved, non-outdated Codex-reviewer threads on
`src/dopemux/dcp/lane_engine.py`. Both are reproducible fail-closed gaps reachable only
via a **forged/restored `RouteDecision`** (the trusted classifier never emits them). Close
both with minimal, fail-closed changes and reproduction tests. No behavior change for
classifier-produced decisions; no new lane; no execution surface; allowed actions are only
ever narrowed, never widened.

## Findings closed

### F1 — Hard-forbidden actions leak onto passive lanes (PR #906 `lane_engine.py:70`)
`_MUTATING_ACTIONS` omitted 7 classifier `_ALWAYS_FORBIDDEN` tokens
(`call_connector`, `execute_dopetask`, `execute_runner`, `mutate_task_orchestrator`,
`run_destructive_command`, `touch_secrets`, `write_github_state`). Passive **executable**
lanes ran `_strip_mutating_actions` (a blocklist), so a restored `READ_ONLY` decision
carrying e.g. `execute_runner` in `allowed_actions` kept it on the `READ_ONLY_EVIDENCE`
lane.

**Fix**: passive lanes now filter through an explicit read-only allowlist
(`_read_only_safe_actions` → `_READ_ONLY_PROOF_SAFE_ACTIONS`) instead of a mutating
blocklist. Fail-closed: anything not provably read-only/proof-safe is dropped. This makes
the passive-executable branch symmetric with the non-executable narrowing branch.

### F2 — Restored `unknowns` markers not blocked (PR #906 `lane_engine.py:128`)
`_has_unknown_decision_contract` enumerated UNKNOWN enum fields but never checked
`decision.unknowns`. A restored decision with every enum known plus `unknowns=[...]`,
`status=ALLOWED`, `red_lane_state=CLEAR` is `is_runnable()` → `LOCAL_CODE_IMPLEMENTATION`
became executable with mutating actions, even though the sibling backend policy blocks
`unknowns_present`.

**Fix**: `_has_unknown_decision_contract` now also returns True when
`bool(decision.unknowns)`, so the executability gate fails closed on any unresolved
unknown marker.

## Non-goals
- No change to `is_runnable()` / `routing_model.py` (the lane engine owns its stricter gate).
- No new lane kind, no execution, no runner/connector/MCP/live-write/dopetask path.
- No change to classifier output for well-formed decisions.

## Validation
- `pytest tests/unit/dcp/test_lane_engine.py tests/unit/dcp/test_routing_classifier.py` → **131 passed** (129 prior + 2 new regressions).
- New tests: `test_restored_decision_with_unknowns_marker_not_executable` (F2),
  `test_passive_lane_strips_hard_forbidden_execute_and_write_actions` (F1) — both verified
  RED before the fix, GREEN after.
- `compileall src/dopemux/dcp` exit 0 · `ruff check` clean · `git diff --check` clean.

## Files touched
- `src/dopemux/dcp/lane_engine.py` (+22/-3)
- `tests/unit/dcp/test_lane_engine.py` (+89)
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0005-POSTMERGE-FIX.md` (this packet)

## Rollback
`git checkout main -- src/dopemux/dcp/lane_engine.py tests/unit/dcp/test_lane_engine.py`
and delete this packet, or drop branch `feat/dcp-lane-engine-postmerge-fix`.
