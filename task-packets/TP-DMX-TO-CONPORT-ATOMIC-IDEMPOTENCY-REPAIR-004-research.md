---
id: TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004-research
title: Tp Dmx To Conport Atomic Idempotency Repair 004 Research
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-30'
last_review: '2026-07-30'
next_review: '2026-10-28'
prelude: Tp Dmx To Conport Atomic Idempotency Repair 004 Research (explanation) for
  dopemux documentation and developer workflows.
---
# TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004 — Research Trace

## Status

`READY_AFTER_CUSTODY_PREFLIGHT` — recovery packet for the stopped atomic-idempotency repair.

## Binding

- Repository: `DDD-Enterprises/dopemux-mvp`
- PR: #1164
- Branch: `codex/to-conport-persistence-repair`
- Authorized parent: `c78c45b0e06a729d51f329e510f0a8069c46fca6`
- Reported candidate: `34ffb53dfb3b29548a9d076aae3c24be84e75575`
- Observed trusted main: `72af781e42e0702d9047946e0f5a250e7dff0fa5`

## Defect 1: ConPort owner tests cannot import `enhanced_server`

`enhanced_server.py` (lines 66-81) wraps the `aiohttp`/`asyncpg`/`redis` imports in a
try/except that, on `ImportError`, runs `pip install` via `subprocess.check_call`. In a
test environment where `asyncpg` is not installed (and no root-conftest asyncpg stub is
present), importing `enhanced_server` triggers the auto-install, which fails with
`CalledProcessError`.

The test file `test_custom_data_atomic_claim.py` stubs `asyncpg`/`redis`/`aioredis` with
`sys.modules.setdefault`, which never replaces an existing module. If the root conftest
asyncpg stub is absent, `import asyncpg` inside `enhanced_server` can reach the
auto-install path before the test's stub takes effect, depending on module ordering.

**Established convention** (adjacent tests `test_ensure_schema.py`, `test_mcp_custom_data.py`):
insert `CONPORT_DIR` into `sys.path`, then guard MCP stubs with
`if "mcp.server.fastmcp" not in sys.modules`, then import `EnhancedConPortServer` from
`enhanced_server`. The test-only repair follows this convention and forces stub
registration so the server's dependency auto-install can never fire during tests.

## Defect 2: Route tests cannot collect — FastMCP stub rejects `name=`/`description=`

Production `app/main.py` registers MCP tools with the decorator shape:

```python
@mcp.tool(name=tool_def["name"], description=tool_def["description"])
```

When the real `mcp` package is absent, `app.main` falls back to its own `FastMCP` class
which accepts keyword arguments. However, a no-kwargs `_FastMCPStub.tool(self)` (as used
by several conport test files) that lands in `sys.modules["mcp.server.fastmcp"]` before
`app.main` is imported makes the production decorator raise `TypeError` during module
import, which fails test collection.

**Test-only repair**: register a kwargs-accepting FastMCP stub
(`tool(*, name=None, description=None)` returning a decorator that preserves the wrapped
callable) in the route-certification test before importing `app.main`. Production MCP
registration code is unchanged.

## Defect 3: Fingerprint v1 sorts ordered immutable lists

`compute_epic_fingerprint` in `app/models/workflow.py` applied `sorted()` to
`acceptance_criteria` and `tags`. The request model (`CreateEpicRequest`) normalizes these
lists preserving order (trim + de-dupe, no sorting). Sorting in the fingerprint means two
requests that differ only by list order hash identically — treating distinct immutable
requests as the same idempotent replay, which is incorrect: reordered list values are
distinct immutable requests and must conflict.

**Fix**: use `list(...)` (Pydantic-normalized order) instead of `sorted(...)`. The
fingerprint contract version (`workflow_epic_create:v1`) and field set are unchanged.

| Request difference             | Result                |
| ------------------------------ | --------------------- |
| Same normalized payload        | Same fingerprint      |
| Reordered acceptance criteria  | Different fingerprint |
| Reordered tags                 | Different fingerprint |
| Different description or value | Different fingerprint |
| Volatile timestamps            | Excluded              |
| Idempotency key                | Excluded              |

## Defect 4: Prior diff evidence omits newly added files

A plain `git diff` over an unstaged tree omits untracked (new) files. The REPAIR-003
evidence must be captured as a complete commit patch (`git show --binary --stat --patch
<sha>`) plus a changed-file inventory (`git diff --name-status`), and the final
implementation commit patch must include every newly added packet and test file.

## Files traced

- `docker/mcp-servers-source/conport/enhanced_server.py` — claim endpoint, dependency auto-install block
- `docker/mcp-servers-source/conport/tests/test_custom_data_atomic_claim.py` — owner tests (defect 1)
- `services/task-orchestrator/app/main.py` — production MCP registration shape (defect 2)
- `services/task-orchestrator/app/models/workflow.py` — fingerprint v1 (defect 3)
- `tests/unit/test_task_orchestrator_workflow_route_certification.py` — route tests (defect 2, 4)
- `tests/unit/test_task_orchestrator_workflow_atomic_idempotency.py` — fingerprint tests
- `tests/integration/test_task_orchestrator_concurrent_idempotency.py` — integration proof

## Out of scope

- Atomic owner protocol changes
- ConPort schema migrations
- New persistence providers
- Runtime import-path hacks
- Production MCP registration changes merely to satisfy tests
- Redis or in-process locking
- Force push, rebase, reset, merge, deployment, branch deletion, or ready-state transition
- LTAIP loader retry
