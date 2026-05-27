# Auditor Report — TP-DMX-AUDIT-ROUTER-002

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-AUDIT-ROUTER-002 — host auditor route registry
**Status**: PASS_WITH_RISKS (all findings resolved or accepted)

---

## Scope

Files reviewed:

- `scripts/audit/route_schema.py`
- `scripts/audit/auditor_router.py`
- `schemas/audit/audit_route.schema.json`
- `tests/audit/test_auditor_router.py`

---

## Findings

### F-002-HIGH-1 — Unused import: FORBIDDEN_CLI_NAMES in auditor_router.py

**Severity**: HIGH
**Status**: RESOLVED

`auditor_router.py` imported `FORBIDDEN_CLI_NAMES` from `route_schema` but never referenced it
directly. The forbidden-name enforcement is correctly delegated to `AuditRoute.__post_init__`.
The stale import added noise and created a misleading impression that the router performed its
own name check.

**Fix applied**: Removed `FORBIDDEN_CLI_NAMES` from the import line in `auditor_router.py`.

---

### F-002-MED-1 — Missing encoding in path.read_text()

**Severity**: MEDIUM
**Status**: RESOLVED

`load_route_from_clink_config` called `path.read_text()` without specifying `encoding="utf-8"`.
On hosts where the default locale is not UTF-8, this can silently misread config files that
contain non-ASCII characters (e.g., model names or role prompts in future clink configs).

**Fix applied**: Changed to `path.read_text(encoding="utf-8")`.

---

### F-002-MED-2 — No role validation against clink config roles block

**Severity**: MEDIUM
**Status**: RESOLVED

`load_route_from_clink_config` accepted a `role` parameter but never verified that the role
existed in the config file's `roles` block. A caller passing a nonexistent role would silently
produce an `AuditRoute` with a role that the clink config cannot honour, leading to a
hard-to-diagnose runtime failure at invocation time.

**Fix applied**: Added explicit role validation — raises `KeyError` with a helpful message
listing available roles if the requested role is absent.

**Test added**: `test_load_route_raises_when_role_not_in_config` in `test_auditor_router.py`.
**Existing test updated**: `test_partial_conf_dir_returns_available_routes` fixture now
includes a `codereviewer` roles block to satisfy the new validation.

---

### F-002-MED-3 — Schema allows "codex" as command value

**Severity**: MEDIUM
**Status**: RESOLVED

`schemas/audit/audit_route.schema.json` blocked `"codex"` and `"codex-audit"` in the
`cli_name` field but did not apply the same restriction to the `command` field. A document
could therefore pass schema validation with `cli_name="some-wrapper"` and `command="codex"`,
bypassing the spirit of the Codex exclusion.

**Fix applied**: Added `"not": {"enum": ["codex"]}` constraint to the `command` property.

---

## Remaining Risks

- `mypy` not run — type annotations present but not statically checked in CI.
- `docs/ops/auditor-routing.md` not written — deferred; non-blocking for correctness.
- `probe_capability` uses `shutil.which` only; PATH at audit invocation time may differ
  from probe time (e.g., if invoked in a subprocess with a different environment).
- `default_routes` does not auto-discover additional clink configs beyond the two
  hardcoded names; adding a new config requires updating `_DEFAULT_ROUTE_NAMES`.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/audit/ (49 tests) | PASS |
| codex forbidden at dataclass layer | PASS |
| codex forbidden at schema layer (cli_name + command) | PASS |
| role validation raises KeyError | PASS |
| real clink configs load cleanly | PASS |
| unused import removed | PASS |
| mypy | NOT_RUN |
| docs/ops/auditor-routing.md | NOT_RUN |
