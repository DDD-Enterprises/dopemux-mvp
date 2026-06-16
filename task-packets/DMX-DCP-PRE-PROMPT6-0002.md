---
id: DMX-DCP-PRE-PROMPT6-0002
title: Routing Classifier Status Precedence Fix
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Reorders DCP routing-classifier status derivation to most-severe-first (BLOCKED > UNKNOWN) so a hard-BLOCKED reason is no longer masked as UNKNOWN by the default unknown-authority guard. Pure status-discoverability fix; no fail-closed weakening.
---

# DMX-DCP-PRE-PROMPT6-0002 — Routing Classifier Status Precedence Fix

**Series**: DMX-DCP-PRE-PROMPT6
**Packet**: 0002
**Type**: Bugfix (status precedence) + reconciliation tests
**Status**: IMPLEMENTED
**Branch**: `feat/dcp-pre-p6-precedence-fix` (off `main` @ `a740edc40`, post-#902)
**Implementer**: Claude Code (Opus, TDD red→green)
**Embedded auditor**: Claude Opus (separate subagent)
**Date**: 2026-06-16

---

## Objective

Fix routing-classifier status precedence so a hard-BLOCKED reason (BLOCKED authority,
missing proof on a mutating/non-trivial route, stale proof) is reported in
`RouteDecision.status` even when authority is also unknown — instead of being masked
as `RouteStatus.UNKNOWN` by the default `has_unknown_authority=True` guard.

## The bug (observed on `main`)

In `_derive_route_status`, the UNKNOWN-authority guard ran **before** the hard-BLOCKED gates:

```
red_lane                                  → BLOCKED
has_unknown_authority OR authority UNKNOWN → UNKNOWN   ← returned first
authority BLOCKED                          → BLOCKED
missing_proof (+ mutating/non-trivial)     → BLOCKED
stale_proof                                → BLOCKED
```

`has_unknown_authority` defaults to `True` (conservative), so any stale/missing-proof
or BLOCKED-authority route with default authority returned `status=UNKNOWN`. The block
reason was still present in `stop_conditions` (e.g. `"stale_proof"`), but `status` —
the field callers read to learn *why* a route is blocked — reported UNKNOWN. A
readiness/reporting footgun, not a security hole. (Deferred from 0002R reconciliation.)

## The fix (minimal)

Reorder to most-severe-first (BLOCKED > UNKNOWN): the three hard-BLOCKED checks now run
**before** the UNKNOWN-authority guard. A 2-line move + a precedence docstring. No new
fields, no enum changes, no public-API change.

## Why it is safe (no fail-closed weakening)

`RouteDecision.is_runnable()` (`routing_model.py`) already returns `False` for UNKNOWN
authority, so an unknown-authority route was — and remains — non-runnable. The reorder
only changes what `status` *reports*, never what is runnable. Red-lane is still derived
first (`_derive_red_lane_state` → RED_LANE → `status=BLOCKED`), so `requires_mcp_call` /
`requires_live_write` / `requires_dopetask_execution` / `touches_secrets` remain
hard-blocked ahead of everything. A guardrail test pins that a route whose *only* defect
is unknown authority still reports UNKNOWN (no over-blocking).

## Files touched

| File | Op | Lines |
|---|---|---|
| `src/dopemux/dcp/routing_classifier.py` | reorder + docstring | +17/-4 |
| `tests/unit/dcp/test_routing_classifier.py` | 1 test loosened + 2 added | +74/-21 |
| `task-packets/DMX-DCP-PRE-PROMPT6-0002.md` | new (this file) | new |

## Tests (TDD: RED → GREEN)

- **RED** (unmodified source): `test_unresolved_review_threads_block_readiness` (bypass
  dropped) + `test_hard_blocked_reason_wins_over_unknown_authority` **failed** (status
  UNKNOWN ≠ BLOCKED); guardrail `test_unknown_authority_alone_still_reports_unknown`
  **passed** → `2 failed, 1 passed`.
- **GREEN** (after reorder): all 3 pass.

## Validation — PASS

| Gate | Result |
|---|---|
| `compileall src/dopemux/dcp` | PASS (exit 0) |
| precedence tests (3) | PASS (3/3) |
| `tests/unit/dcp/test_routing_classifier.py` | PASS (77/77, exit 0) |
| `tests/unit/dcp/ tests/dcp/test_dcp_model_routing_0001_domain.py` | PASS (193/193, exit 0) |
| `git diff --check` | PASS (exit 0) |
| diff scope = allowlisted files only | PASS (3 files) |

**NOT_RUN**: full-repo suite, networked/MCP integration — out of packet scope (classifier
is a pure function with no I/O). Residual risk: none beyond the classifier surface.

## Invariants preserved

- Classifier remains a pure function (no I/O / shell / network / fs / connector / MCP / runner).
- `requires_mcp_call → RED_LANE → BLOCKED` unchanged (red-lane derived first).
- `requires_live_write` / `requires_dopetask_execution` / `touches_secrets` hard-blocks unchanged.
- Unknown authority cannot grant mutation (`is_runnable()` unchanged).
- No new classifier fields; no public enum changes.

## Embedded audit

**VERDICT: PASS** — independent Opus subagent (read-only, adversarial; agent `aa3b96f911ab51542`).

Method: faithful reconstruction of the BEFORE order (= `main`) vs the AFTER working tree,
swept exhaustively over **41,472** input combinations (`AuthorityClass` × stale/missing-proof
× mutating/non-trivial scope × source/type/risk/complexity/impact/CI).

- **18,144** status changes, **100% UNKNOWN→BLOCKED**; zero other deltas — monotonically more conservative.
- `is_runnable()` differs in **0 / 41,472**; non-runnable→runnable: **0**.
- status UNKNOWN→ALLOWED: **0 / 41,472**.
- `allowed_actions` broadening: **0**.
- red-lane / MCP (`requires_mcp_call`) / live-write / dopetask hard-blocks verified BLOCKED +
  non-runnable under best-case bypass; `_derive_red_lane_state`, `_derive_allowed_actions`,
  `_derive_forbidden_actions`, `is_runnable()` confirmed unchanged.
- Tests non-tautological: monkeypatching the old order makes the precedence assertions fail;
  the over-block guardrail passes under both orders (a naive always-BLOCK fix would fail it).
- **No counterexample found** across all four hunted transition classes.

Integration UNKNOWN (out of this file's scope): a downstream caller treating `status==UNKNOWN`
as soft/retryable now sees `BLOCKED` for stale/missing-proof/BLOCKED-authority routes — the
intended more-conservative signal; callers keying on the literal value should fail-closed on BLOCKED.

## Rollback

```bash
git checkout main -- src/dopemux/dcp/routing_classifier.py tests/unit/dcp/test_routing_classifier.py
git rm -f task-packets/DMX-DCP-PRE-PROMPT6-0002.md
# or: git branch -D feat/dcp-pre-p6-precedence-fix
```

## Residual risk

- Pre-existing Pyright nits (`_normalize_enum` bare `type`; string-literal enum args in
  normalization tests) are untouched and out of scope.
- Behaviour change is observable to any caller that branched on `status==UNKNOWN` for a
  stale/missing-proof route; such a caller now sees `BLOCKED`. No in-repo caller does so —
  the classifier is read-only and consumed by the net-new 0004 lane engine.

## Expected output

```
TP: DMX-DCP-PRE-PROMPT6-0002
STATUS: IMPLEMENTED
BRANCH: feat/dcp-pre-p6-precedence-fix
COMMIT: <filled at commit>
PR: <filled at PR>
VALIDATION: PASS (compileall + 193 DCP tests + diff check)
AUDIT_VERDICT: PASS (independent Opus; 41,472-combo exhaustive sweep — 0 newly-runnable, 0 UNKNOWN→ALLOWED, 0 allowed_actions broadening; red-lane/MCP/live-write/dopetask intact)
RESIDUAL_RISKS: status-report change only; no fail-closed weakening
```
