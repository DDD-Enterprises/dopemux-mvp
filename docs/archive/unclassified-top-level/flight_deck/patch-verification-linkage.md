---
id: PATCH_VERIFICATION_LINKAGE
title: Patch Verification Linkage
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Patch Verification Linkage (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Patch Verification Linkage

## Verification Burden by Patch Class

| Patch Class | Required Checks |
|-------------|----------------|
| DISALLOWED_PATCH | DISALLOWED (no checks run) |
| SAFE_LOCAL_EDIT | SYNTAX_CHECK, LINT_CHECK |
| SAFE_METADATA_EDIT | SYNTAX_CHECK, LINT_CHECK |
| LOW_RISK_PATCH_PROPOSAL | SYNTAX_CHECK, LINT_CHECK, UNIT_TEST |
| SIGNOFF_REQUIRED_PATCH | SYNTAX_CHECK, LINT_CHECK, UNIT_TEST, INTEGRATION_CHECK |
| SIGNOFF_REQUIRED_PATCH (cross-file) | + CROSS_FILE_IMPACT_CHECK |

## Provenance Linkage

Every verification plan is linked back to its originating patch via:
- `verification_plan_id` in `PatchApplicationTrace`
- `patch_id` in `PATCH_VERIFICATION_REPORT.json`
- `provenance` dict in `PatchPlan`: `{pr_id, run_id, origin_tactic, strategy_id}`

## Verification → Gate Flow

```
APPLIED patch
  → run required checks (by patch class)
  → check all pass? → PASSED
  → check any fail? → FAILED
  → PASSED → gate recompute → APPROVED or PENDING_SIGNOFF
  → FAILED → gate recompute → DEFER
```

## Evidence Requirements

For a verification to count as PASSED, all of the following must be true:
1. All required checks for the patch class ran without error
2. No check returned a non-zero exit code
3. `PatchApplicationTrace.outcome` is not `BLOCKED` or `FAILED`

## Artifact Linkage

The following artifacts chain verification to patch provenance:

| Artifact | Links To |
|----------|---------|
| `PATCH_VERIFICATION_REPORT.json` | patch_id, verification_plan_id, patch_class |
| `PATCH_PROVENANCE_LOG.json` | pr_id, run_id, origin_tactic, strategy_id, outcome |
| `VERIFICATION_GATE_REPORT.json` | trace_id, patch_id, stage outcomes |
| `POST_EDIT_STATE_RECOMPUTE.json` | patch_id, verification_status, gate_decision |
