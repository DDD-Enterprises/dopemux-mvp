# Auditor Report — TP-DMX-PR-STEWARD-FRESHNESS-005

**TP**: TP-DMX-PR-STEWARD-FRESHNESS-005
**Subject**: Mixed-SHA hard fail + proof freshness substates in PR Steward
**Auditor**: Claude Sonnet 4.6 via PAL MCP codereview; external expert pass via PAL (gpt-5.2 / OpenAI)
**Invocation**: `mcp__pal__codereview` — two-step review; expert model called via PAL MCP for independent pass
**Exit code**: 0
**Status**: PASS_WITH_RISKS
**Date**: 2026-05-26

---

## Verdict

**PASS_WITH_RISKS.** The mixed-SHA blocker and proof freshness substates are correctly implemented. One HIGH finding (null SHA handling) was evaluated as a false positive but resolved with a defensive fix. Two MEDIUM findings were evaluated as false positives; one resolved by adding tests, one accepted as correct behavior. One LOW finding resolved by adding a test. No blocking issues remain.

---

## Scope Reviewed

- `tools/pr_steward/classifier.py` — `_detect_mixed_sha_checks()`, `_proof()`, `_readiness()`, `build_artifacts()`
- `schemas/pr_steward/merge_readiness.schema.json`
- `schemas/pr_steward/pr_state_snapshot.schema.json`
- `tests/pr_steward/test_classifier_mixed_sha.py`
- `tests/pr_steward/test_classifier_proof_status.py`
- `tests/fixtures/pr_steward/mixed_sha_checks_block/harvest.json`

---

## Findings

### F001 — HIGH → RESOLVED — Null SHA normalization in `_detect_mixed_sha_checks`

**ID**: F001
**Severity**: HIGH
**Status**: RESOLVED

Expert flagged that the original `str(check.get("headSha") or check.get("head_sha") or "")` expression could produce unexpected behavior with explicit `None` values. Evaluated: `None or None or ""` evaluates to `""` in Python before `str()` is applied, so the original code was safe. However, the expression's intent was unclear, and non-string values in `headSha` (e.g., integer 0) would fall through to `""` silently.

**Fix applied**: Replaced with explicit null-guard:
```python
raw_sha = check.get("headSha") or check.get("head_sha")
sha = (raw_sha or "").strip() if isinstance(raw_sha, str) else ""
```
This explicitly rejects non-string values and makes null-handling intent unambiguous.

---

### F002 — MEDIUM → ACCEPTED_RISK — `_proof()` STALE/MISSING boundary with empty sha + path

**ID**: F002
**Severity**: MEDIUM
**Status**: ACCEPTED_RISK

Expert suggested that a check object with `proof_path` set (non-empty string) but `proof_head_sha: None` would classify as STALE when it might more defensively be MISSING. Re-analysis of the code: the `not proof_head_sha and not proof_path` branch triggers MISSING only when both are absent/falsy. If `proof_path` is present but `proof_head_sha` is None, we fall through to STALE — this is the correct behavior since we have a path but can't verify the SHA, which is a staleness condition (we know a proof exists but can't confirm it's current).

**Accepted risk**: Code is correct. STALE is the right classification when a proof path exists but SHA is absent — it signals "we have evidence but can't verify freshness" rather than "no evidence at all." This is conservative and fail-safe.

---

### F003 — MEDIUM → RESOLVED — Missing explicit null SHA test cases

**ID**: F003
**Severity**: MEDIUM
**Status**: RESOLVED

Tests were missing explicit cases for `headSha: null` and `head_sha: null` (REST field). The existing `test_check_with_null_sha_not_treated_as_mismatch` only tested absent key, not explicit null value.

**Fix applied**: Added three tests:
- `test_explicit_null_headSha_not_treated_as_mismatch` — `headSha: None` explicit
- `test_explicit_null_head_sha_rest_field_not_treated_as_mismatch` — `head_sha: None` explicit
- `test_head_sha_rest_field_stale_blocks` — `head_sha` REST field with stale SHA triggers mismatch

Test count: 28 → 31 (all passing).

---

### F004 — LOW → RESOLVED — `head_sha` REST field not unit-tested for mismatch

**ID**: F004
**Severity**: LOW
**Status**: RESOLVED

The REST API field `head_sha` (as opposed to GraphQL `headSha`) was not covered by any positive-mismatch test. Resolved by `test_head_sha_rest_field_stale_blocks` (see F003).

---

## Fixes Applied

1. `tools/pr_steward/classifier.py`: Defensive null normalization in `_detect_mixed_sha_checks` — explicit `isinstance(raw_sha, str)` guard replaces implicit `or ""` chain.
2. `tests/pr_steward/test_classifier_mixed_sha.py`: Added `test_explicit_null_headSha_not_treated_as_mismatch`, `test_explicit_null_head_sha_rest_field_not_treated_as_mismatch`, `test_head_sha_rest_field_stale_blocks`.

---

## Remaining Risks

- `mypy` not run — type annotations present but not statically verified
- Mixed-SHA detection reads `headSha` (GraphQL) and `head_sha` (REST) fields; a third field name used by a future GitHub API response would silently bypass detection
- MISSING substate requires both `proof_path` and `proof_head_sha` to be absent/falsy; a harvest with only `proof_path` set (no SHA) classifies as STALE — conservative but worth noting
- `schemas/pr_steward/pr_state_snapshot.schema.json` was updated to accept `proof_freshness`; this schema is not validated by the `test_intake.py` fixture tests but is validated inline via `validate_artifacts()`
