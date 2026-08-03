# TP-PR-STEWARD-POLICY-RESTORE-001

## Purpose

Restore `config/pr_steward/policy.json` **byte-for-byte** from the packaged scaffold:

`src/dopemux/templates/init/config/pr_steward/policy.json`

L2 governance prerequisite for ConPort clean recovery readiness (PR #1188).

## Guarantees

| Field | Value |
|---|---|
| mode | `check_only` |
| mutates_github | `false` |
| automerge | not present / not enabled |
| scaffold SHA-256 | `41d28d3e83a8fa572ea8cf82911532292b8c9ded0a88e4c80991cfdca377107e` |

## Validation

- `dopemux-pr-steward doctor` → **PASS** (config_schema + scaffold_skew)
- jsonschema vs `schemas/pr_steward/config.schema.json` → PASS
- `cmp` scaffold == repo policy → PASS
- Formal audit → see `AUDITOR_REPORT.md` / `PROOF.json`

## Status

**NOT operator-merged.** After formal audit + Steward READY on proof tip, operator may merge.

Do not treat this packet as ConPort recovery complete.
