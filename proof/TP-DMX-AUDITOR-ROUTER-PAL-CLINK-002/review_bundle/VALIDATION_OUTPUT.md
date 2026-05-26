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
