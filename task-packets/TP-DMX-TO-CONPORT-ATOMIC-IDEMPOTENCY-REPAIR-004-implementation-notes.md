---
id: TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004-implementation-notes
title: Tp Dmx To Conport Atomic Idempotency Repair 004 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-30'
last_review: '2026-07-30'
next_review: '2026-10-28'
prelude: Tp Dmx To Conport Atomic Idempotency Repair 004 Implementation Notes (explanation)
  for dopemux documentation and developer workflows.
---
# TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-004 — Implementation Notes

## Execution log

- **Implementer**: DeepSeek V4 Pro through the operator-approved shell surface
  (Command Code session).
- **Custody preflight (Phase 0)**: PASS — PR head = remote branch head = reported
  candidate `34ffb53d` (Case A). Lineage verified. Worktrees created at
  `RUN_ROOT/worktree` (candidate) and `RUN_ROOT/trusted-main` (origin/main).
- `RULES.md` absent from repo history; the tracked equivalent
  `docs/03-reference/governance/rules.md` was used for the preflight root-marker check.

## Phase 1 — Owner test import repair

File: `docker/mcp-servers-source/conport/tests/test_custom_data_atomic_claim.py`

Change: guard MCP stubs with `if "mcp.server.fastmcp" not in sys.modules`; force-register
asyncpg/redis/aioredis stubs only when the real package is absent; keep the real
`EnhancedConPortServer` under test. The server's `pip install` auto-install path
(`enhanced_server.py` lines 66-81) can no longer fire during tests.

Gate result: 7 collected, 7 executed, 7 passed.

## Phase 2 — FastMCP stub repair

File: `tests/unit/test_task_orchestrator_workflow_route_certification.py`

Change: register `_FastMCPStub.tool(*, name=None, description=None)` returning a
decorator that preserves the wrapped callable, before `from app.main import app`.
Production `app/main.py` registration code unchanged.

Gate result: module imports; 3 route-certification tests collect and pass.

## Phase 3 — Fingerprint v1 ordering

File: `services/task-orchestrator/app/models/workflow.py`

Change: `acceptance_criteria` and `tags` use `list(...)` (Pydantic-normalized order)
instead of `sorted(...)`. Prefix `workflow_epic_create:v1` and field set unchanged.

New tests:
- `test_fingerprint_equivalent_normalized_requests_hash_identically`
- `test_fingerprint_reordered_acceptance_criteria_differ`
- `test_fingerprint_reordered_tags_differ`
- `test_reordered_lists_replay_returns_conflict_and_winner_unchanged`

Gate result: 6 fingerprint tests pass; 2 conflict tests pass.

## Phase 4 — Validation matrix

- Packet JSON validated against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- Owner tests, route tests, atomic idempotency tests, store/serialization/mcp_custom_data
  tests, integration concurrent tests all pass
- ruff clean; `git diff --check` clean; root hygiene clean

## Phase 5 — Diff custody and commit

- Precommit status/stat/binary diff captured
- Staged inventory matches allowlist
- Single commit with final head and complete commit patch captured

## Phase 6 — Push

- Pre-push remote verified equal to PR head
- Normal fast-forward push; post-push PR head equals final implementation head
- PR remains draft

## Phase 7 — Two-replica concurrency proof

- Disposable isolated compose project, unique loopback ports, unique network/volumes,
  synthetic data, short-lived credentials
- 20 identical + 20 conflicting concurrent rounds via synchronization barrier,
  1 restart replay, 0 failed, 0 overwrites, 1 row max per identity, 0 token leaks,
  0 residual resources

## Phase 8 — Trusted exact-head audit

- Embedded audit binds to final PR head; substantive step executes
- Inspects complete diff, test harness repairs, fingerprint semantics, owner transaction,
  concurrency proof, bridge auth, token handling, evidence custody, allowlist compliance
- Verdict recorded with tool, model, invocation, exit code, findings, fixes, risks

## Phase 9 — Bundle, PR Steward, handoff

- Clean bundle with all receipts; exclusions enforced
- `tools.pr_steward.intake --strict`; `MERGE_READINESS.json` schema-validated
- `HANDOFF.json` produced; supervisor handoff issued

## Completion state

```text
ATOMIC_IDEMPOTENCY_REPAIR_PROVEN
TRUSTED_AUDIT_CURRENT
PR_STEWARD_READY_OR_SECURITY_RELEASE_ONLY
MERGE_AUTHORIZED=false
DEPLOYMENT_AUTHORIZED=false
LOADER_RETRY_AUTHORIZED=false
```
