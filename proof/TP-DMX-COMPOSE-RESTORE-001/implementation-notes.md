# TP-DMX-COMPOSE-RESTORE-001 Implementation Notes

## Scope

- Restore `compose.yml` as the canonical root Docker Compose file.
- Remove root-level non-canonical compose drift.
- Harden compose guard checks against future root-level compose variants.

## Authority

- `AGENTS.md`
- `compose.yml`
- `scripts/compose_guard.py`
- `services/registry.yaml`

## Changes

- Restored `compose.yml` from the hand-authored canonical version at `67a3ffcf5`.
- Reapplied current root build contexts and Dockerfile paths.
- Removed the missing `leantime-bridge` env file dependency.
- Deleted root `docker-compose.unified.yml`.
- Updated active helper scripts to reference canonical `compose.yml`.
- Added compose guard coverage for root-level compose drift.
- Added a changelog entry and task packet traceability.

## Verification

- `python scripts/compose_guard.py` exited 0.
- `docker compose -f compose.yml config --services` exited 0 and emitted the canonical service list. Docker reported unset local environment variables as warnings only.
- `/Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m pytest tests/arch/test_registry_compose_alignment.py tests/arch/test_service_env_contract.py tests/arch/test_compose_guard.py` exited 0 with 39 passed and 2 existing warnings.
- Semantic YAML comparison against `HEAD:compose.yml` with `services.leantime-bridge.env_file` removed reported `semantic_diff_ok: only leantime-bridge env_file removed`.
- `python -m json.tool task-packets/TP-DMX-COMPOSE-RESTORE-001.json` exited 0.
- Manual task packet required-field check exited 0.
- `git diff --check` exited 0.
- `pre-commit run --files CHANGELOG.md compose.yml install.sh scripts/compose_guard.py tests/arch/test_compose_guard.py verify_dopecon_bridge.sh task-packets/INDEX.md task-packets/TP-DMX-COMPOSE-RESTORE-001.json proof/TP-DMX-COMPOSE-RESTORE-001/implementation-notes.md` exited 0.
