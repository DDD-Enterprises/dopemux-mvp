# TP-PR-STEWARD-POLICY-RESTORE-001

## Purpose

Restore `config/pr_steward/policy.json` **byte-for-byte** from:

`src/dopemux/templates/init/config/pr_steward/policy.json`

L2 governance prerequisite for ConPort clean recovery (PR #1188).

## Guarantees

| Field | Value |
|---|---|
| mode | `check_only` |
| mutates_github | `false` |
| automerge | not present |
| scaffold SHA-256 | `41d28d3e83a8fa572ea8cf82911532292b8c9ded0a88e4c80991cfdca377107e` |
| content head | `c9038b5a1e2031e19b7245b8ac5e0dd8761b3be3` |
| schema enum extension | **NOT INCLUDED / DEFERRED** |

## Validation

- doctor PASS (config_schema + scaffold_skew)
- Formal Codex audit PASS_WITH_RISKS (see AUDITOR_REPORT.md)
- Policy-only exception: `provider_attested=UNKNOWN` non-blocking for this PR only

## Status

Not auto-merged. Operator merge under
`PR_1187_READY_FOR_OPERATOR_MERGE_WITH_CODEX_EXCEPTION`
when repaired tip validation passes.
