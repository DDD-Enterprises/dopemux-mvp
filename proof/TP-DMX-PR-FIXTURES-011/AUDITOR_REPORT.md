# Auditor Report — TP-DMX-PR-FIXTURES-011

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-PR-FIXTURES-011 — PR Steward and Action Bridge fixture suite
**Status**: PASS_WITH_RISKS (MEDIUM finding resolved; LOW findings accepted)

---

## Scope

Files reviewed:

- `tests/fixtures/pr_steward/proof_stale_blocks/harvest.json`
- `tests/fixtures/pr_steward/proof_missing_blocks/harvest.json`
- `tests/fixtures/pr_steward/unknown_pr_author_blocks/harvest.json`
- `tests/fixtures/pr_action_bridge/ready_green.json`
- `tests/fixtures/pr_action_bridge/needs_supervisor_proof_stale.json`
- `tests/fixtures/pr_action_bridge/needs_supervisor_proof_missing.json`
- `tests/fixtures/pr_action_bridge/needs_supervisor_unknown_author.json`
- `tests/fixtures/pr_action_bridge/needs_implementer_failed_check.json`
- `tests/pr_steward/test_intake.py` (BLOCKING_CASES update)
- `tests/pr_action_bridge/test_compiler_fixtures.py`
- `docs/ops/pr-fixtures.md`
- `tools/pr_steward/classifier.py` (consumer verification)
- `tools/pr_action_bridge/compiler.py` (consumer verification)
- `tools/pr_steward/known_reviewers.json` (author trust list verification)
- `schemas/pr_steward/merge_readiness.schema.json`
- `schemas/pr_action_bridge/action_plan.schema.json`

---

## Findings

### F-011-MED-1 — `compile_action_plan` aliased as `compile`, shadowing Python builtin

**Severity**: MEDIUM
**Status**: RESOLVED

`test_compiler_fixtures.py` originally imported `compile_action_plan as compile`, matching the
existing pattern in `test_compiler.py` but shadowing Python's built-in `compile()`. While there
is no behavioral risk (the builtin is not used in this module), the alias reduces clarity.

**Fix applied**:
- Removed alias; all calls now use `compile_action_plan(...)` directly.

---

### F-011-LOW-1 — `mixed_sha_checks_block` fixture not covered by `BLOCKING_CASES`

**Severity**: LOW
**Status**: ACCEPTED_RISK

The `mixed_sha_checks_block` fixture exists in `tests/fixtures/pr_steward/` but is not in
the `BLOCKING_CASES` parametrized loop in `test_intake.py`. This is a pre-existing gap
not introduced by TP-011. `tests/pr_steward/test_classifier_mixed_sha.py` provides
dedicated coverage for the mixed-SHA classifier path.

---

### F-011-LOW-2 — `proof_stale_blocks` uses non-hex `proof_head_sha`

**Severity**: LOW
**Status**: ACCEPTED_RISK

`proof_stale_blocks/harvest.json` uses `"proof_head_sha": "old0000000000000000000000000000000000000"`
(the prefix `old` is not valid hex). The classifier accepts any non-empty string as the SHA value
and does not enforce hex format. The fixture correctly exercises the STALE freshness path.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/pr_steward/ + tests/pr_action_bridge/test_compiler_fixtures.py (38 tests) | PASS |
| pytest full suite (304 tests) | PASS |
| proof_stale_blocks → PROOF_STALE blocker via _proof() STALE path | PASS |
| proof_missing_blocks → PROOF_MISSING blocker via _proof() MISSING path | PASS |
| unknown_pr_author_blocks → UNKNOWN_PR_AUTHOR blocker (external-bot not in known_reviewers.json) | PASS |
| All 5 action_bridge fixtures validate against action_plan.schema.json | PASS |
| needs_implementer_failed_check → source_item_id="unit" from ci_triage.checks | PASS |
| BLOCKING_CASES updated with 3 new entries | PASS |
| No compile() builtin shadowing in test_compiler_fixtures.py | PASS |
| All files within TP-011 allowlist | PASS |
| No branch protection mutation | PASS |
| No pull_request_target introduced | PASS |
| No new secrets or elevated permissions | PASS |
| No forbidden imports (tools.pr_merge) | PASS |
| No trailing whitespace | PASS |
| mypy | NOT_RUN (fixture/test files only; no new typed source) |

---

## Remaining Risks

- `mixed_sha_checks_block` has no BLOCKING_CASES entry — pre-existing gap; covered by dedicated test file.
- `action_plan.schema.json` `generated_at` field has no ISO format constraint — pre-existing; any string accepted.
- `mypy` not run — no new typed source files introduced.
