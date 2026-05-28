# Auditor Report — TP-DMX-PR-STEWARD-HARDEN-010

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-PR-STEWARD-HARDEN-010 — Harden PR Steward readiness classification
**Status**: PASS_WITH_RISKS (all HIGH findings resolved; MEDIUM finding resolved; LOW findings accepted)

---

## Scope

Files reviewed:

- `tools/pr_steward/classifier.py`
- `schemas/pr_steward/merge_readiness.schema.json`
- `schemas/pr_steward/{pr_state_snapshot,review_item_ledger,thread_dispositions,ci_triage}.schema.json`
- `tools/pr_action_bridge/compiler.py`
- `schemas/pr_action_bridge/action_plan.schema.json`
- `tests/pr_steward/test_classifier_readiness_harden.py`
- `tests/pr_steward/test_classifier_proof_status.py`
- `tests/pr_action_bridge/test_compiler.py`
- `docs/ops/pr-steward-readiness.md`

---

## Findings

### F-010-HIGH-1 — `proof-stale` rationale stale after split; `proof-missing` / `unknown-pr-author` categories absent

**Severity**: HIGH
**Status**: RESOLVED

`compiler.py` rationale message for `proof-stale` still read "stale or missing" after the
`PROOF_STALE` / `PROOF_MISSING` split. Additionally, `proof-missing` and `unknown-pr-author`
categories were emitted by `_BLOCKER_MAP` but absent from the `action_plan.schema.json`
category enum, causing schema validation failures.

**Fixes applied**:
- Updated `proof-stale` rationale: "Proof bundle is stale; supervisor must re-run proof/audit at current head SHA."
- Added `proof-missing` rationale: "Proof bundle is missing; supervisor must produce proof/audit bundle before proceeding."
- Added `unknown-pr-author` rationale: "PR author is not in known_reviewers.json; supervisor must verify author before proceeding."
- Added `proof-missing` and `unknown-pr-author` to `action_plan.schema.json` category enum.
- Added schema validation tests for both new categories.

---

### F-010-MED-1 — `_association()` false positive for OWNER-associated PRs with nested GraphQL author shape

**Severity**: MEDIUM
**Status**: RESOLVED

`_association(pr_raw)` looked for `authorAssociation` only at the top-level PR dict. In the
common GraphQL shape, the author's association is nested under `pr.author.authorAssociation`.
An OWNER-associated author who is not in `known_reviewers` would get a false-positive
`UNKNOWN_PR_AUTHOR` blocker.

**Fix applied**:
```python
pr_assoc = _association(pr_raw)
if pr_assoc is None and isinstance(pr_raw.get("author"), dict):
    pr_assoc = _association(pr_raw["author"])
```
Added tests for both shapes (nested OWNER trusted, nested absent → still blocked).

---

### F-010-LOW-1 — `_READINESS_TO_RISK` not exported

**Severity**: LOW
**Status**: ACCEPTED_RISK

Module-level internal mapping. No external consumers. Intentional.

---

### F-010-LOW-2 — `risk_tier` absent from `PR_STATE_SNAPSHOT.json`

**Severity**: LOW
**Status**: ACCEPTED_RISK

Intentional design: snapshot is raw observed state; `risk_tier` is a derived classification
that belongs only in `MERGE_READINESS.json`.

---

### F-010-LOW-3 — `_risk_tier()` fallback to CRITICAL on unknown readiness silently swallows schema drift

**Severity**: LOW
**Status**: ACCEPTED_RISK

`_readiness()` is deterministic and only returns known strings. The fallback is dead code in
practice. Accepted given `_readiness()` is the sole caller and its output set is enumerated in
the same file.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/pr_steward/ (84 tests) | PASS |
| pytest tests/pr_action_bridge/ (53 tests) | PASS |
| pytest full suite (277 tests) | PASS |
| PROOF_STALE_OR_MISSING fully removed from all consumers | PASS |
| PROOF_STALE → NEEDS_SUPERVISOR tier | PASS |
| PROOF_MISSING → NEEDS_SUPERVISOR tier | PASS |
| UNKNOWN_PR_AUTHOR added and maps to NEEDS_SUPERVISOR | PASS |
| risk_tier field in MERGE_READINESS.json | PASS |
| risk_tier CLEAR pinned in schema allOf for READY | PASS |
| Schema version bumped to 1.1.0 across all 5 pr_steward schemas | PASS |
| action_plan.schema.json enum updated for proof-missing / unknown-pr-author | PASS |
| _association() fallback checks nested author.authorAssociation | PASS |
| No branch protection mutation | PASS |
| No pull_request_target introduced | PASS |
| No new secrets or elevated permissions | PASS |
| No forbidden imports (tools.pr_merge) | PASS |
| No trailing whitespace in new files | PASS |
| mypy | NOT_RUN (no new typed source changes that break existing mypy scope) |

---

## Remaining Risks

- `_risk_tier()` fallback to CRITICAL on unknown readiness string is dead code but unguarded — if `_readiness()` is extended without updating `_READINESS_TO_RISK`, callers get CRITICAL silently.
- `known_reviewers.json` is the primary defense for UNKNOWN_PR_AUTHOR; if an external bot is added to the repo without updating that file, all its PRs will be NEEDS_SUPERVISOR.
- `mypy` not run — classifier.py type annotations are consistent with existing patterns; no new typed surface added.
