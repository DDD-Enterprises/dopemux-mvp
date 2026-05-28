# Auditor Report — TP-DMX-AUDIT-PROOF-004

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-27
**TP**: TP-DMX-AUDIT-PROOF-004 — Audit proof normalization
**Status**: PASS_WITH_RISKS (2 HIGH findings resolved; 2 MEDIUM findings resolved; 4 LOW findings resolved)

---

## Scope

Files reviewed:

- `scripts/audit/validate_audit_proof.py`
- `tests/audit/test_audit_proof.py`
- `docs/ops/embedded-audit-proof.md`
- `schemas/proof/embedded_audit.schema.json` (read-only, not modified)

---

## Findings

### F-004-HIGH-1 — `SchemaError` unhandled when `--schema` points to invalid schema

**Severity**: HIGH
**Status**: RESOLVED

`check_schema()` raised `SchemaError` if `--schema` referenced an internally
invalid JSON Schema document, crashing with an uncontrolled traceback instead
of exiting with code 2.

**Fix applied**:
- Wrapped `Draft7Validator.check_schema(schema)` in `try/except SchemaError`
  and returned exit code 2 with a clear error message.

---

### F-004-HIGH-2 — `Path.is_relative_to` compatibility

**Severity**: HIGH
**Status**: RESOLVED

`Path.is_relative_to()` is only available in Python ≥ 3.9. While the current
runtime is 3.12, using `try/except ValueError` around `relative_to()` is the
idiomatic pattern and eliminates the API dependency.

**Fix applied**:
- Replaced `is_relative_to` guard with `try/except ValueError` in `_rel_path()`.

---

### F-004-MED-1 — `embedded_audit` type not checked before schema iteration

**Severity**: MEDIUM
**Status**: RESOLVED

If `embedded_audit` was `null` or a string, jsonschema emitted noisy cascade
errors instead of a clean user-facing message.

**Fix applied**:
- Added `isinstance(embedded, dict)` check; returns a clean error message
  for non-object `embedded_audit` values.

---

### F-004-MED-2 — Error sort key used `list(e.path)` which can be unstable

**Severity**: MEDIUM
**Status**: RESOLVED

`e.path` elements can be a mix of `str` and `int` (object keys vs array
indices); `list(e.path)` as a sort key is not comparable across types in all
Python versions.

**Fix applied**:
- Changed sort key to `".".join(map(str, e.path))` — deterministic string
  comparison, handles mixed-type paths correctly.

---

### F-004-LOW-1 — `collect_proof_paths` no deduplication when `--all` + positional overlap

**Severity**: LOW
**Status**: RESOLVED

Passing the same PROOF.json as both a positional arg and via `--all` scan
caused the file to be validated twice.

**Fix applied**:
- Deduplicate via `{p.resolve(): None}` dict, preserving order.
- Added `test_dedup_when_all_and_positional_overlap` to verify.

---

### F-004-LOW-2 — `load_schema` raises `JSONDecodeError` not caught in `main()`

**Severity**: LOW
**Status**: RESOLVED

A syntactically invalid JSON file passed via `--schema` raised an unhandled
`JSONDecodeError`.

**Fix applied**:
- `load_schema` now raises `ValueError` wrapping the JSON error.
- `main()` catches `(FileNotFoundError, ValueError)` for both cases.

---

### F-004-LOW-3 — Subprocess calls in tests had no timeout

**Severity**: LOW
**Status**: RESOLVED

A hung validator process would wedge the CI test run indefinitely.

**Fix applied**:
- Added `timeout=10` to all `subprocess.run()` calls in `_run()`.

---

### F-004-LOW-4 — No test for `AUDITOR_REPAIR_REPORT.md` report_path variants

**Severity**: LOW
**Status**: RESOLVED

The schema `report_path` regex accepts three variants but only the base form
was tested.

**Fix applied**:
- Added `TestReportPathVariants` class with 3 tests:
  `AUDITOR_REPAIR_REPORT.md`, `AUDITOR_REPAIR_1_REPORT.md`, and a negative
  test for a non-matching path.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/audit/test_audit_proof.py (38 tests) | PASS |
| pytest full suite (342 tests) | PASS |
| schemas/proof/embedded_audit.schema.json unchanged | PASS |
| No enum additions to auditor_tool or auditor_model | PASS |
| No import of tools.pr_merge | PASS |
| No GitHub mutation | PASS |
| No trailing whitespace in new/modified files | PASS |
| Validator correctly identifies TP-DMX-CI-TRIGGERS-008 as FAIL | PASS |
| Validator correctly identifies TP-DMX-BRANCH-POLICY-AUDIT-012 as FAIL | PASS |
| Validator correctly identifies TP-DMX-PR-FIXTURES-011 as PASS | PASS |
| All files within TP-004 allowlist | PASS |
| mypy | NOT_RUN (script/test files only; not in src/ package) |

---

## Remaining Risks

- `mypy` not run — `validate_audit_proof.py` and `test_audit_proof.py` are scripts, not `src/` package members; type annotations not checked by CI mypy gate.
- Known non-compliant bundles `TP-DMX-CI-TRIGGERS-008` and `TP-DMX-BRANCH-POLICY-AUDIT-012` remain non-compliant — not in TP-004 allowlist; require dedicated remediation TPs.
