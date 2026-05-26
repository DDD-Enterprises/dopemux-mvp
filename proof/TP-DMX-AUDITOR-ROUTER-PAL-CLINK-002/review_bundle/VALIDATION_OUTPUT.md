# Validation Output

See `../VALIDATION_OUTPUT.md` for the full validation log.

Key result: `pytest -q tests/auditor_router/test_pal_clink.py` exited 0 with `29 passed`.

Key result: `pytest -q tests/auditor_router` exited 0 with `33 passed`.

Historical blocked result: `scripts/auditor-preflight --help` exited 127 because the wrapper was not present and was not allowlisted in PAL-CLINK-002.

Resolved by follow-up: `TP-DMX-AUDITOR-ROUTER-WRAPPER-003` adds and validates `scripts/auditor-preflight`.

Precommit result: `pre-commit run --files $(cat proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/CHANGED_FILES.txt)` exited 0.
