# Validation Output

See `../VALIDATION_OUTPUT.md` for the full validation log.

Key result: `pytest -q tests/auditor_router` exited 0 with `27 passed`.

Blocked result: `scripts/auditor-preflight --help` exited 127 because the wrapper is not present and is not allowlisted in this packet.

Precommit result: `pre-commit run --files $(cat proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/CHANGED_FILES.txt)` exited 0.
