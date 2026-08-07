# Rollback Guide: TP-DMX-AIOHTTP-ROOT-W1-1198-001

## Rollback Procedure
If issues are identified with `aiohttp` 3.14.3:
1. Revert commit C1/C2 on `dependabot/uv/aiohttp-3.14.3` or close PR #1198 without merging.
2. `pyproject.toml` and `uv.lock` will remain at their `origin/main` state (`aiohttp` 3.14.1).
3. `uv sync --frozen` to restore previous environment.
