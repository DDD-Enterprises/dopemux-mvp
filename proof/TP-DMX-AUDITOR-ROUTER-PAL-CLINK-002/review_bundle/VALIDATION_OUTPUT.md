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

## Local PR #713 Schema-Compatible Finding Fix Validation

Generated: 2026-05-26T22:06:50Z

Patched the active PR #713 review blocker where normalized PAL clink findings emitted a `blocking` property not allowed by `schemas/proof/embedded_audit.schema.json`. The router now preserves the raw `blocking=true` signal for FAIL classification but omits it from emitted embedded-audit findings.

```text
pytest -q tests/auditor_router/test_pal_clink.py -> exit 0, 33 passed
python -m compileall -q tools tests -> exit 0
pytest -q tests/auditor_router -> exit 0, 37 passed
python -m json.tool schemas/proof/embedded_audit.schema.json -> exit 0
python -m json.tool proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/PROOF.json -> exit 0
python -m json.tool proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/review_bundle/PROOF.json -> exit 0
git diff --check -> exit 0
pre-commit run --files $(git diff --name-only) -> exit 0
```
