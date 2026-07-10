# Complete CI Pipeline Failure Fix

**Head (fix commit):** `2f947530b9fe796c8c419212e1a303f3303f27a2`  
**Prior failing head:** `e2c684eaa0686c99f558a60b73119c6cfe27b4f9`  
**Failing run:** `29067426650`

## Failure A — Unit Tests

### First causal error

```text
tests/unit/test_task_orchestrator_http_singleton.py::test_reuses_running_singleton_with_http_env
TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER: :7890 occupied by unlabeled container
```

### Root cause

Launcher `refuse_foreign_port_owner` requires ownership labels or matching container name.
Test docker stub answered `ps`/`port`/`Config.Image`/`Config.Env` but not
`dopemux.project_root` or `.Name`, so the simulated healthy singleton was treated as unlabeled.

### Fix

Extend the docker stub to return:

- `dopemux.project_root` label from `DOPEMUX_PROJECT_ROOT`
- a container name for `.Name` inspect

### Local pass

```bash
uv run --frozen pytest -q tests/unit/test_task_orchestrator_http_singleton.py --disable-warnings --no-cov
# pass
```

## Failure B — Code Quality root hygiene

### First causal error

```text
top-level directory 'proofs' is not allowlisted
```

### Fix

Add `proofs` to `config/repo_hygiene/root_hygiene_policy.json`.

## Additional review fixes in same commit

- R1 parallel-safe lease registry isolation
- R2 restored docker_inspect coverage
- R3 reverted `.claude/claude_config.json` PR delta
- R4 fail-closed identity matching (root+id mismatch → CONFLICT)

## Local MCP suite

```bash
uv run --frozen pytest -q tests/unit/test_mcp_*.py tests/unit/test_task_orchestrator_http_singleton.py -n auto --maxfail=3 --disable-warnings --no-cov
# all passed
```
