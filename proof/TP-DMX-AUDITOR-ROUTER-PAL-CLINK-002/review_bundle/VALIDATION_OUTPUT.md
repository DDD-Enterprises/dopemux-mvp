# Validation Output

See `../VALIDATION_OUTPUT.md` for the full validation log.

Key result: bundle-local PAL MCP clink audit returned `PASS_WITH_RISKS` after reading 12 evidence files.

## Local Review Fix Validation

Generated: 2026-05-26T12:01:41.823532Z

```text
python -m compileall -q tools tests -> exit 0
pytest -q tests/auditor_router/test_pal_clink.py -> exit 0, 33 passed
pytest -q tests/auditor_router -> exit 0, 37 passed
python -m tools.auditor_router.preflight --fixture-dir tests/fixtures/auditor_router/pal_clink_no_configs_found --out /private/tmp/auditor-route-pr713-fallback --packet-id TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002 --allow-fallback -> exit 0
```

## PAL MCP Clink Audit Attempt

Generated: 2026-05-26T22:10:30Z

```text
PAL MCP clink cli_name=claude role=codereviewer -> exit 1, Executable 'claude' not found in PATH
PAL MCP clink cli_name=gemini role=codereviewer -> exit 1, Executable 'gemini' not found in PATH
PAL MCP clink cli_name=codex role=codereviewer -> exit 1, Executable 'codex' not found in PATH
```

Result: `NEEDS_SUPERVISOR`. No external CLI audit verdict was produced.

## Local PR #713 Command / Override Review Fix Validation

Generated: 2026-05-26T22:27:00Z

```text
python -m compileall -q tools tests -> exit 0
pytest -q tests/auditor_router/test_pal_clink.py -> exit 0, 35 passed
pytest -q tests/auditor_router -> exit 0, 39 passed
```

Patched active review blockers:

- PAL clink audit configs must use a command that exactly matches the expected CLI executable.
- PAL clink config discovery now models clink override order so later override configs replace built-in audit configs.

## Local PR #713 Config Shape Review Fix Validation

Generated: 2026-05-26T22:32:00Z

```text
python -m compileall -q tools tests -> exit 0
pytest -q tests/auditor_router/test_pal_clink.py -> exit 0, 38 passed
pytest -q tests/auditor_router -> exit 0, 42 passed
```

Patched active review blockers:

- PAL clink audit configs must explicitly define `name` and `runner`.
- PAL clink role scanning rejects non-object `roles` and role values without crashing preflight.
