# Current-Main DCP Execution-Gating Audit (after #904 → #906 → 0006 hardening)

**Target:** `main` @ `556ffff1b` · **Mode:** read-only audit + already-built remediation
**Date:** 2026-06-16 · **Auditor:** Claude Code (Opus 4.8)
**Supersedes:** "PR #906 post-merge triage" (that framing assumed the world stopped at #906)

```
CURRENT_MAIN_DCP_AUDIT_STATUS: NEEDS_FIX_PACKET
  (fix packet already built — branch feat/dcp-lane-engine-postmerge-fix @ af6b4c346;
   once merged → READY_FOR_PROMPT6, modulo the deferred-and-tracked 0007 contract)

CURRENT_MAIN_SHA: 556ffff1b

POST_906_COMMITS (02fa9b30a..556ffff1b):
  b460047eb feat(dcp): implement 0006 classifier provenance hardening
  d14dbda80 fix(dcp): wire provenance fields through CLI
  5c7663c0a fix(dcp): keep read-only audits out of provenance block
  ea4871e0f fix(dcp): preserve blocked bridge authority
  556ffff1b fix(dcp): strict CLI parsing for trust-raising provenance booleans
  (none touch src/dopemux/dcp/lane_engine.py)
```

## PR906_THREAD_CLASSIFICATIONS (vs CURRENT MAIN CODE, not GitHub status)

13 threads, all from `chatgpt-codex-connector`. Proof = current code, not "resolved in GitHub".

| # | Path:Line | GitHub | Classification | Evidence on main `556ffff1b` |
|---|-----------|--------|----------------|------------------------------|
| 0 | lane_engine.py | resolved/outdated | AUTO_APPLIED_BY_MERGED_906 | `_compute_is_executable` delegates to `decision.is_runnable()` (L158) |
| 1 | lane_engine.py | resolved/outdated | AUTO_APPLIED_BY_MERGED_906 | classifier `_normalize_input`; engine consumes normalized enums |
| 2 | lane_engine.py:354 | resolved | AUTO_APPLIED_BY_MERGED_906 | `_narrow_allowed_actions_for_non_runnable` strips mutating on non-exec |
| 3 | lane_engine.py | resolved/outdated | AUTO_APPLIED_BY_MERGED_906 | row-8 `_has_mutating_scope` precedes read-only fallback |
| 4 | lane_engine.py | resolved/outdated | AUTO_APPLIED_BY_MERGED_906 | row-8 `touches_files` routes out of evidence |
| 5 | lane_engine.py | resolved/outdated | AUTO_APPLIED_BY_MERGED_906 | row-3 `not _has_mutating_intent` guards PR-readiness |
| 6 | lane_engine.py:158 | resolved | AUTO_APPLIED_BY_MERGED_906 | `_has_unknown_decision_contract` UNKNOWN-enum gate |
| 7 | lane_engine.py:128 | resolved | AUTO_APPLIED_BY_MERGED_906 | gate checks `ProofRequirement.UNKNOWN` |
| 8 | lane_engine.py:158 | resolved | AUTO_APPLIED_BY_MERGED_906 | `_has_blocking_stop_or_escalation` (stop_conditions + escalation) |
| 9 | lane_engine.py:354 | resolved | AUTO_APPLIED_BY_MERGED_906 (extended by F1) | passive `_strip_mutating_actions` present; its blocklist gap = thread 11 |
| 10 | lane_engine.py:248 | resolved | AUTO_APPLIED_BY_MERGED_906 | row-8 `touches_public_behavior` routes to implementation |
| **11** | **lane_engine.py:70** | **unresolved** | **MUST_FIX** (remediated on branch) | `_MUTATING_ACTIONS` blocklist omits 7 `_ALWAYS_FORBIDDEN` tokens; passive *executable* lane keeps them |
| **12** | **lane_engine.py:128** | **unresolved** | **MUST_FIX** (remediated on branch) | neither `is_runnable()` nor `_has_unknown_decision_contract` checks `decision.unknowns` |

**Result: 11 AUTO_APPLIED by the merged #906 code · 2 MUST_FIX** — both reproduced against
current main and remediated on `feat/dcp-lane-engine-postmerge-fix` @ `af6b4c346`.

## Execution-gating checklist (current main)

| Concern | Status on main | Evidence |
|---------|----------------|----------|
| Hard-forbidden actions leak into passive lanes | **GAP (F1)** → fixed on branch | `_MUTATING_ACTIONS` ⊉ `_ALWAYS_FORBIDDEN` (7 tokens leak) |
| Restored decision w/ unknown markers executable | **GAP (F2)** → fixed on branch | `decision.unknowns` unchecked in lane gate |
| Unknown proof requirements executable | CLOSED | `any(req is ProofRequirement.UNKNOWN ...)` in lane gate |
| Stop conditions / escalation still executable | CLOSED | `_has_blocking_stop_or_escalation` |
| Caller-supplied provenance laundering via CLI JSON | HARDENED (residual = 0007) | see below |

## 0006 / provenance / CLI status

```
0006_IMPLEMENTATION_STATUS: IMPLEMENTED on main (b460047eb)
PROVENANCE_HARDENING_STATUS: classifier-side COMPLETE
CLI_INPUT_PROVENANCE_STATUS: WIRED + HARDENED (residual = 0007 unforgeable contract, deferred)
LANE_ENGINE_SAFETY_STATUS: main = 2 latent gaps (F1/F2); branch af6b4c346 = both closed
```

- **Provenance can only LOWER trust.** `_apply_provenance_coercion`: `authority_via_bridge_proxy`
  → `authority_class=UNKNOWN` (overrides claimed authority, never raises). `_provenance_blocks_executable`:
  retrieval-derived-unverified / ECC intake / unproven-wrapper backend → BLOCK on *mutating* routes only
  (read-only unaffected). Wired into status, escalation, and stop_conditions derivation. Default = no-op (zero regression).
- **Trust asymmetry is correct.** CLI `_input_from_dict`: trust-*lowering* flags use plain `bool()`
  (coercion is fail-safe → more restrictive); trust-*raising* flags (`exact_source_fetched`,
  `has_backend_wrapper_proof`) use `_parse_strict_bool` — must be real JSON booleans, no truthy coercion.
- **CLI is a projection, not an authority.** `classify` runs the hardened `classify_route`;
  `recommend-backend` deserializes via `RouteDecision.from_dict` into the **inert** `select_backend_policy`.
  **`decide_lane` has NO CLI entry point** → F1/F2 are *latent* (deserialization-only; not reachable
  through the shipped CLI today). They arm only when a lane-engine consumer/executor ships — which is
  exactly when they must already be closed.

## TEST_RESULTS
- `pytest tests/unit/dcp/` (main + branch fix) → **all passed** (full DCP unit suite, 0 failures)
- New regressions `test_passive_lane_strips_hard_forbidden_execute_and_write_actions` (F1) +
  `test_restored_decision_with_unknowns_marker_not_executable` (F2): RED on main, GREEN on branch
- `compileall src/dopemux/dcp` exit 0 · `ruff check` clean · `git diff --check` clean

## UNKNOWNs / residual risk
- **0007 (trusted input-provenance) not implemented** (docs packets #908/#909 merged). Caller-asserted
  provenance/authority is still trusted by the `classify` projection and by `RouteDecision.from_dict`.
  No runtime executor consumes these today, so not a live exploit — but it is the named blocker before
  ANY execution surface. Tracked.
- `recommend-backend` deserializes forged `RouteDecision` into inert advice — scoped to 0007 (commit `0c521642c`).
- **Minor OBS:** CLI `has_unknown_authority` clearing uses coercible `bool()` (e.g. `0`/`""` → False),
  unlike the strict trust-raising parsing. It is an authority signal, not a provenance flag, and the
  surface is projection-only — candidate for a one-line strict-parse hardening or fold into 0007. Non-blocking.

## NEXT_ACTION
Land the already-built focused fix packet (`feat/dcp-lane-engine-postmerge-fix` @ `af6b4c346`) via PR
(operator merges), then assemble the Prompt 6 bundle from the resulting main. No 0005 rerun, no new mega-audit.
