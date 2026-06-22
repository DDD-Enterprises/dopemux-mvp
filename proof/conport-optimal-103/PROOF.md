# DMX-CONPORT-OPTIMAL-103 Proof

## Scope

TP: `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-103-retire-dead-codebases.json`

Worktree: `/Users/hue/.codex/worktrees/conport-optimal-103-retire-dead-codebases`

Branch: `codex/conport-optimal-103-retire-dead-codebases`

## Authority

- `AGENTS.md`
- Packet 103 task packet
- Runtime import grep over `src/`, `services/`, and `docker/`

## Changes

- Added a deprecation notice to `src/conport/memory_server.py` while preserving
  the existing code below it.
- Added `services/conport_kg/QUARANTINE.md`.
- Added a `Canonical Codebase` section to
  `docker/mcp-servers-source/conport/SURFACE_INVENTORY.md`.

## Import Checks

`src/conport/memory_server.py` runtime import grep:

```text
NONE
```

`services/conport_kg` runtime import grep:

```text
services/dope-query/tests/test_password_utils.py:6:    from conport_kg.auth.password_utils import PasswordResetConfirm, PasswordValidationError
```

Assessment: the `conport_kg` hit is a test-only import under
`services/dope-query/tests`, not a runtime import path. The referenced
`conport_kg.auth.password_utils` module is not present under
`services/conport_kg/` in this checkout.

## Validation

PASS:

- `python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-103-retire-dead-codebases.json >/dev/null`
  - Result: exit 0
- `python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-103-retire-dead-codebases.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Result: exit 0; `jsonschema` CLI deprecation warning only
- `python3 -m py_compile src/conport/memory_server.py`
  - Result: exit 0
- `grep -rn 'from src.conport.memory_server\|import src.conport.memory_server\|from conport.memory_server\|import conport.memory_server' src/ services/ docker/ --include='*.py' || echo 'NO RUNTIME IMPORTS FOUND'`
  - Result: `NO RUNTIME IMPORTS FOUND`
- `grep -rn 'from services.conport_kg\|import services.conport_kg\|from conport_kg\|import conport_kg' src/ services/ docker/ --include='*.py' | grep -v 'services/conport_kg/' || echo 'NO RUNTIME IMPORTS FOUND'`
  - Result: one test-only import in `services/dope-query/tests/test_password_utils.py`
- `git diff --check`
  - Result: exit 0
- `pre-commit run --files src/conport/memory_server.py services/conport_kg/QUARANTINE.md docker/mcp-servers-source/conport/SURFACE_INVENTORY.md proof/conport-optimal-103/PROOF.md`
  - Result: exit 0; applicable hooks passed and unrelated hooks skipped

## Residual Risk

- The packet allowlist and step S5 require a documentation update under the
  canonical ConPort directory, while one invariant says not to alter the
  canonical codebase. This proof treats that as a docs-only exception because
  S5 specifically names `SURFACE_INVENTORY.md` and no runtime code under the
  canonical directory was changed.
