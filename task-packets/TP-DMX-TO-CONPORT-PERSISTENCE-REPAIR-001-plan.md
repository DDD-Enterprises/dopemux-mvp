---
id: TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-plan
title: Tp Dmx To Conport Persistence Repair 001 Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Dmx To Conport Persistence Repair 001 Plan (explanation) for dopemux documentation
  and developer workflows.
---
# Implementation Plan — TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001

## Scope

Only compose wiring and targeted static/synthetic contracts. Existing bridge
authentication and WorkflowStore routing remain unchanged.

## Ordered execution

1. Add a failing architecture test that parses canonical `compose.yml` and
   requires:
   - Task Orchestrator injects the external `DOPECON_BRIDGE_TOKEN` expression,
     without a literal token or fallback credential.
   - Task Orchestrator uses `http://conport:3004` for REST.
   - DopeconBridge explicitly uses `http://conport:3004` for its REST proxy.
2. Run that test and record its expected RED failure against current compose.
3. Add one synthetic `WorkflowStore` test using `httpx.MockTransport`; it must
   prove a configured bridge token becomes a bearer header and the request is
   a `POST /kg/custom_data` with stable workspace/category/key identity.
   Run it before production changes; it should pass because the client is
   already correct and isolates compose as the root cause.
4. Make the minimal `compose.yml` environment changes:
   - require `DOPECON_BRIDGE_TOKEN` at compose interpolation for Task
     Orchestrator; the explicit error names the authenticated JWT requirement;
   - change Task Orchestrator `CONPORT_URL` to `http://conport:3004`;
   - explicitly set DopeconBridge `CONPORT_URL=http://conport:3004`.
5. Re-run static, synthetic, existing serialization, and ConPort custom-data
   tests. Run `docker compose -f compose.yml config --no-interpolate`; this is
   syntax-only, not a container startup or write.
6. Run packet schema and diff checks. Then inspect allowed paths and run
   applicable pre-commit hooks.
7. Obtain independent embedded audit. If unavailable, create a schema-valid
   proof only if the policy permits a `SKIPPED` result; do not call it passing.
   Push branch and open a draft PR. Run PR Steward intake/check only and report
   `NOT_RUN`/non-ready states without waiting for human supervisor acceptance.

## Verification commands

```text
uv run pytest -q tests/arch/test_task_orchestrator_conport_persistence_contract.py
uv run pytest -q tests/unit/test_task_orchestrator_workflow_store.py tests/unit/test_task_orchestrator_workflow_write_serialization.py
uv run pytest -q docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py
docker compose -f compose.yml config --no-interpolate
uv run python -m jsonschema -i task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```

## Rollback

Revert only the repair commit. No data migration, runtime mutation, or secret
rotation occurs in this packet. Missing external token configuration now fails
compose interpolation before startup; it does not silently bypass auth.
