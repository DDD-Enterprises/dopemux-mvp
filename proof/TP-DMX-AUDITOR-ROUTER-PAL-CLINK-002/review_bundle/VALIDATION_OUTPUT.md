# Validation Output

See `../VALIDATION_OUTPUT.md` for the full validation log.

Key result: `pytest -q tests/auditor_router/test_pal_clink.py` exited 0 with `29 passed`.

Key result: `pytest -q tests/auditor_router` exited 0 with `33 passed`.

Historical blocked result: `scripts/auditor-preflight --help` exited 127 because the wrapper was not present and was not allowlisted in PAL-CLINK-002.

Resolved by follow-up: `TP-DMX-AUDITOR-ROUTER-WRAPPER-003` adds and validates `scripts/auditor-preflight`.

Precommit result: `pre-commit run --files $(cat proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/CHANGED_FILES.txt)` exited 0.

## Local PR #713 Review Fix Validation

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
