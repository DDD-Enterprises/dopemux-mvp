---
id: TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004-plan
title: Tp Dmx To Conport Atomic Idempotency Repair 004 Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-30'
last_review: '2026-07-30'
next_review: '2026-10-28'
prelude: Tp Dmx To Conport Atomic Idempotency Repair 004 Plan (explanation) for dopemux
  documentation and developer workflows.
---
# TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004 — Plan

## Approach

Recover the stopped atomic-idempotency repair without reopening its architecture. Fix the
four verified defects with test-only and minimal source changes, then rerun the complete
validation matrix, prove concurrency across two Task Orchestrator processes, obtain
trusted exact-head audit evidence, package every authoritative artifact, and run PR
Steward check-only.

## Custody decision

The reported candidate `34ffb53d` was observed as both the live PR head and the remote
branch head (Case A). The authorized parent `c78c45b0` is an ancestor of the candidate.
No force push, rebase, or history rewrite is used; the existing draft PR is fast-forwarded
only after all repairs and validations pass.

## Changes per slice

### Slice 1: Packet and design records
- `TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004.json` — schema-conformant packet
- `-research.md`, `-plan.md`, `-implementation-notes.md` — design records

### Slice 2: Owner test import repair
- `docker/mcp-servers-source/conport/tests/test_custom_data_atomic_claim.py`
  - Move `CONPORT_DIR` insertion and MCP stubs ahead of any server import
  - Guard stubs with `if ... not in sys.modules`
  - Force-register asyncpg/redis/aioredis stubs only when the real package is absent,
    so `enhanced_server`'s auto-install never fires
  - Keep `EnhancedConPortServer` as the real owner under test (no fake)

### Slice 3: FastMCP stub repair
- `tests/unit/test_task_orchestrator_workflow_route_certification.py`
  - Register `_FastMCPStub.tool(*, name=None, description=None)` returning a decorator
    that preserves the wrapped callable, before `from app.main import app`
  - Production registration code unchanged

### Slice 4: Fingerprint v1 ordering
- `services/task-orchestrator/app/models/workflow.py`
  - `acceptance_criteria: sorted(...)` → `list(...)`
  - `tags: sorted(...)` → `list(...)`
- `tests/unit/test_task_orchestrator_workflow_atomic_idempotency.py`
  - Equivalent normalized requests hash identically
  - Reordered acceptance criteria differ
  - Reordered tags differ
- `tests/unit/test_task_orchestrator_workflow_route_certification.py`
  - Reordered replay returns conflict
  - Persisted winner remains unchanged

### Slice 5: Complete scoped validation
- Packet JSON vs `dopetask-canonical-spec.json`
- Owner tests; route + atomic idempotency tests; store/serialization/mcp_custom_data
  tests; integration concurrent tests
- ruff, `git diff --check`, root hygiene

### Slice 6: Diff custody and commit
- Precommit status/stat/binary diff capture
- Stage only allowlisted files; compare staged inventory to allowlist
- Single commit `test(task-orchestrator): complete atomic idempotency proof gates`
- Capture final head and complete commit patch

### Slice 7: Fast-forward push
- Pre-push remote == PR head; push normally; post-push PR head == final head; PR stays draft

### Slice 8: Two-replica concurrency proof
- Disposable compose project: one ConPort owner, one authenticated DopeconBridge, two
  independently addressable Task Orchestrator processes
- Unique loopback ports, network, volumes, synthetic data, short-lived credentials
- 20 identical + 20 conflicting concurrent rounds through a synchronization barrier,
  1 restart replay, 1 row max per identity, 0 overwrites, 0 token leaks, 0 residual
  resources

### Slice 9: Trusted exact-head audit
- Embedded audit binds to final PR head; substantive step executes (not skipped)
- Inspects complete diff, test harness repairs, fingerprint semantics, owner transaction,
  concurrency proof, bridge auth, token handling, evidence custody, allowlist compliance
- Accept only PASS or PASS_WITH_RISKS with no blocking finding

### Slice 10: Bundle, PR Steward, handoff
- Ledger every receipt; exclude `.DS_Store`, AppleDouble, caches, env files, secrets,
  raw auth headers
- `python -m tools.pr_steward.intake --strict`
- Validate `MERGE_READINESS.json` against `schemas/pr_steward/merge_readiness.schema.json`
- `HANDOFF.json` + supervisor handoff

## Files touched

| File | Change |
|------|--------|
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004.json` | NEW — packet |
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004-research.md` | NEW |
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004-plan.md` | NEW |
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004-implementation-notes.md` | NEW |
| `docker/mcp-servers-source/conport/tests/test_custom_data_atomic_claim.py` | MODIFY — test-only import repair |
| `tests/unit/test_task_orchestrator_workflow_route_certification.py` | MODIFY — stub + conflict tests |
| `tests/unit/test_task_orchestrator_workflow_atomic_idempotency.py` | MODIFY — fingerprint ordering tests |
| `services/task-orchestrator/app/models/workflow.py` | MODIFY — drop sorted() in fingerprint |
| `proof/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004/**` | NEW — proof, audit, handoff |

## No changes
- Atomic owner protocol, schema, persistence providers
- Runtime `sys.path` mutation in production code
- Production MCP registration code
- Redis or in-process locking
- Canonical services

## Stop conditions
Live head mismatch, lineage mismatch, incomplete candidate, out-of-allowlist file,
owner tests failing to import, route tests failing to collect, reordered lists matching,
any scoped test failure, incomplete commit patch, non-fast-forward push, shared-resource
collision, failed concurrency round, overwrite, >1 row per identity, token leak, cleanup
uncertainty, skipped/stale audit, unledgered artifact, PR Steward blocker beyond pending
supervisor security-release approval, or any request to merge/deploy/mark-ready/retry
the LTAIP loader.
