# Auditor Report — TP-DMX-PAL-CLINK-RUNNER-003

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-PAL-CLINK-RUNNER-003 — PAL clink audit runner
**Status**: PASS_WITH_RISKS (all HIGH/MEDIUM findings resolved)

---

## Scope

Files reviewed:

- `scripts/audit/pal_clink_runner.py`
- `schemas/audit/pal_clink_audit_output.schema.json`
- `tests/audit/test_pal_clink_runner.py`
- `docs/ops/pal-clink-audit-runner.md`

---

## Findings

### F-003-HIGH-1 — Codex guard checked cli_name only, leaving command="codex" bypass

**Severity**: HIGH
**Status**: RESOLVED

`run_audit()` guarded `route.cli_name in FORBIDDEN_CLI_NAMES` but did not check
`route.command`. A duck-typed or deserialized route with `cli_name="claude-audit"`
and `command="codex"` would pass the guard and invoke the codex binary — bypassing
the operator prohibition.

`AuditRoute.__post_init__` has the same gap (checks cli_name, not command).
Fixing __post_init__ is out of scope for this TP (route_schema.py is not in the
files_allowed list); that is noted as a remaining risk.

**Fix applied**: Extended runner guard to `route.cli_name in FORBIDDEN_CLI_NAMES or route.command == "codex"`.

**Test added**: `test_codex_command_raises_even_with_safe_cli_name` confirms that
a duck-typed route with `cli_name="claude-audit"`, `command="codex"` raises `ValueError`.

---

### F-003-MED-1 — Schema allowed inconsistent state combinations

**Severity**: MEDIUM
**Status**: RESOLVED

`pal_clink_audit_output.schema.json` allowed `timed_out=true` with `exit_code=0`,
or `exit_code=null` with `error=null`. These combinations are impossible in practice
but were not schema-enforced, risking silent downstream misinterpretation.

**Fix applied**: Added `allOf` if/then constraints:
- If `timed_out=true` → `exit_code` must be null and `error` must be a non-empty string.
- If `exit_code=null` → `error` must be a non-empty string.

All four existing schema validation tests continue to pass with the tightened schema.

---

### F-003-LOW-1 — No test for empty prompt

**Severity**: LOW
**Status**: RESOLVED

Empty string prompt encodes to `b""` and passes via stdin. Valid behavior but untested.

**Fix applied**: Added `test_empty_prompt_passed_as_empty_bytes`.

---

### F-003-LOW-2 — Unnecessary forward-reference string in type alias

**Severity**: LOW
**Status**: RESOLVED

`_SubprocessRunFn = Callable[..., "subprocess.CompletedProcess[bytes]"]` — quotes
were unnecessary since `subprocess` is already imported at module level.

**Fix applied**: Removed the quotes.

---

## Remaining Risks

- `mypy` not run — type annotations present but not statically checked in CI.
- `AuditRoute.__post_init__` does not check `command == "codex"` — out of scope
  for this TP (route_schema.py is in TP-002 files_allowed, not TP-003). The runner
  now guards both `cli_name` and `command`, providing defense-in-depth coverage.
- `probe_capability` uses `shutil.which` only; PATH at audit invocation time may
  differ from probe time if the environment changes between the two calls.
- `route.env` overrides system env keys including PATH — documented in docstring
  and ops doc; callers must be aware of shadow semantics.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/audit/ (84 tests) | PASS |
| codex cli_name guard | PASS |
| codex command guard (new) | PASS |
| schema if/then invariants | PASS |
| schema additionalProperties:false | PASS |
| stdin prompt delivery (not argv) | PASS |
| timeout returns data (not raises) | PASS |
| env merge semantics | PASS |
| schema validation tests (4 scenarios) | PASS |
| mypy | NOT_RUN |
