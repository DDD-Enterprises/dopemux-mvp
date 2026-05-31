# Auditor Report — TP-DMX-AUDIT-BUNDLE-001

**TP**: TP-DMX-AUDIT-BUNDLE-001
**Subject**: Deterministic evidence bundle builder (`scripts/audit/build_evidence_bundle.py`)
**Auditor**: Claude Sonnet 4.6 via PAL MCP codereview
**Invocation**: `mcp__pal__codereview` — two-step review (scope analysis + findings pass)
**Exit code**: 0
**Status**: PASS
**Date**: 2026-05-26

---

## Verdict

**PASS.** The implementation is correct, deterministic, and fail-closed. No blocking issues found. Three LOW findings recorded; none require code changes before commit.

---

## Scope Reviewed

- `scripts/audit/build_evidence_bundle.py` (375 lines) — core library + CLI
- `schemas/audit/bundle_manifest.schema.json` — manifest schema
- `tests/audit/test_evidence_bundle.py` — 22 tests

---

## Findings

### F001 — LOW — Untested token patterns

**ID**: F001
**Severity**: LOW
**Status**: ACCEPTED_RISK

The `openai_key` pattern (`sk-[A-Za-z0-9]{20,}`) and `private_key_header` pattern are defined in `_SECRET_PATTERNS` but do not have dedicated positive-match tests in `test_evidence_bundle.py`. The `FAKE_ANT = "sk-ant-" + "X" * 24` test covers Anthropic keys but not bare OpenAI `sk-` keys (which share the same regex prefix minus the `-ant-` infix). If a bare `sk-XXXX` key appears in a source file, it would be detected by the regex, but this path has no explicit test coverage.

**Accepted risk**: The pattern is a superset of the Anthropic key pattern; any bare `sk-` hit results in rejection (fail-closed). The absence of a dedicated test is a test-coverage gap, not a correctness gap. The secret scanning is defensive, not authoritative.

---

### F002 — LOW — Dead assignment in bundle builder

**ID**: F002
**Severity**: LOW
**Status**: ACCEPTED_RISK

In `build_evidence_bundle.py`, within the relationship-tracking loop, there is an assignment `_ = rel` that captures a relationship object but the value is never used. This is a dead assignment — Python discards it immediately. It does not affect correctness or determinism.

**Accepted risk**: No behavioral impact. Can be cleaned up as a future refactor.

---

### F003 — LOW — CLI exit-code 1 path not subprocess-tested

**ID**: F003
**Severity**: LOW
**Status**: ACCEPTED_RISK

The CLI emits `sys.exit(1)` for fatal errors (e.g., missing `--sources`, schema validation failure on manifest). The test suite tests the library API directly and tests the CLI for the exit-2 (success-with-rejections) path via subprocess, but exit-1 is only covered by unit tests that call the library functions directly — not via a subprocess invocation that exercises the CLI's `sys.exit(1)` branch.

**Accepted risk**: Library correctness is tested; the CLI's exit-code mapping is a thin shim. The gap is real but low-risk.

---

## Fixes Applied

None. All findings are LOW and accepted-risk; no code changes required.

---

## Remaining Risks

- Untested token patterns: openai bare `sk-` and PEM private key header (see F001)
- Dead assignment `_ = rel` in bundle builder (cosmetic, see F002)
- CLI exit-1 not subprocess-tested (see F003)
- `mypy` not run — type annotations present but not statically verified
- Binary file content is included as `<binary file: N bytes>` without secret scanning (documented limitation)
