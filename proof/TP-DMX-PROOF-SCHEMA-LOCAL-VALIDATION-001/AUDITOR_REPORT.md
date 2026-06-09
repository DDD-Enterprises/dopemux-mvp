---
id: TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001-AUDITOR-REPORT
title: Embedded Audit Report — TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001
type: auditor_report
owner: '@hu3mann'
date: '2026-06-07'
---

# Embedded Audit Report — TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001

**Auditor**: claude-code-cli (implementer_standard self-audit)
**Model**: claude-sonnet-4.6
**Stage**: self_audit
**Invocation**: post-implementation review inside Claude Code
**Exit code**: 0
**Verdict**: PASS_WITH_RISKS

---

## Scope Verified

Diff contains only allowlisted files:

- `.pre-commit-config.yaml` — `proof-embedded-audit-schema` hook added to `local` repo block
- `task-packets/INDEX.md` — `TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001` registered Active
- `task-packets/TEMPLATE_TASK_PACKET.md` — Local Proof Validation section added
- `tests/audit/test_audit_proof.py` — `TestPR839Regressions` class added (3 tests)
- `proof/TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001/PROOF.json` — created
- `proof/TP-DMX-PROOF-SCHEMA-LOCAL-VALIDATION-001/AUDITOR_REPORT.md` — created (this file)

No runtime code, schemas (other than pre-commit config), or CI workflows touched.

---

## Key Finding

`scripts/audit/validate_audit_proof.py` already existed as the canonical CI validator with the exact sub-object extraction behavior required. No new script was written. The task reduced to: wire the pre-commit hook, add regression tests for the three PR #839 wounds, and document the local command in TEMPLATE_TASK_PACKET.md.

---

## Validation Results

| Gate | Result |
| --- | --- |
| Existing script validates known-good proofs (3/3 PASS) | PASS |
| `TestPR839Regressions` all three tests pass | PASS |
| Pre-commit hook fires correctly on `proof/*/PROOF.json` pattern | PASS |
| Pre-commit hook passes on known-good proofs | PASS |
| TEMPLATE updated with local validation command | PASS |
| INDEX registered Active | PASS |
| diff --stat shows only allowlisted files | PASS |
| No runtime/schema/CI workflow changes | PASS |

---

## Findings

### F1 — LOW — Intermediate fixture files not committed

**Status**: ACCEPTED_RISK

Three fixture files (`bad_*.PROOF.json`) were generated locally under `tests/fixtures/proof_schema/` to verify validator behavior, but were not committed. The equivalent coverage is provided by `TestPR839Regressions` using `tmp_path` fixtures, which is the correct pytest pattern. No committed fixtures needed.

### F2 — INFO — Hook pattern excludes nested proof paths

**Status**: ACCEPTED_RISK

Pattern `^proof/[^/]+/PROOF\.json$` covers top-level packet directories only. Nested paths like `proof/TP-X/review_bundle/PROOF.json` are not matched. This is consistent with CI Audit Proof Validator scope (governed by `proof/.validator_scope.json` include_patterns). No expansion needed at this time.

---

## Remaining Risks

- **R1**: Local pre-commit hook is advisory; operators who skip `pre-commit install` will not get local validation. CI Audit Proof Validator remains the authoritative gate.
- **R2**: Nested proof paths excluded from hook scope — consistent with CI, but not documented in the hook comment. Acceptable for now.
