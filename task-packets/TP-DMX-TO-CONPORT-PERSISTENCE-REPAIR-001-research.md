---
id: TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-research
title: Tp Dmx To Conport Persistence Repair 001 Research
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Dmx To Conport Persistence Repair 001 Research (explanation) for dopemux
  documentation and developer workflows.
---
# TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001 Research

## Observed runtime path

1. `services/task-orchestrator/app/services/workflow_store.py` creates an
   `AsyncDopeconBridgeClient` from `DOPECON_BRIDGE_URL`,
   `DOPECON_BRIDGE_TOKEN`, and `DOPECON_BRIDGE_SOURCE_PLANE`.
2. Workflow persistence calls `POST /kg/custom_data` and reads call
   `GET /kg/custom_data`; the store has no direct ConPort writer.
3. `services/shared/dopecon_bridge_client/client.py` emits a bearer
   `Authorization` header only when `DOPECON_BRIDGE_TOKEN` is populated.
4. `services/dopecon-bridge/dopecon_bridge/routes.py` protects both
   `/kg/custom_data` routes with `get_current_user`, then proxies to the
   bridge's `ConPortClient` at `/api/custom_data`.
5. `services/dopecon-bridge/dopecon_bridge/auth.py` accepts only a valid JWT
   for a known user at this boundary; `TASK_ORCHESTRATOR_API_KEY` is not this
   credential type.
6. The active ConPort launch script starts REST `enhanced_server.py` on `3004`
   and MCP `server.py sse` on `3005`. `POST /api/custom_data` uses the unique
   `(workspace_id, category, key)` key and `ON CONFLICT ... DO UPDATE`, so a
   repeated synthetic request is an upsert rather than a second record.

## Compose evidence

- `compose.yml` gives Task Orchestrator `DOPECON_BRIDGE_URL`, but does not
  inject `DOPECON_BRIDGE_TOKEN`. Therefore its bridge client has no bearer
  header and the authenticated custom-data route rejects persistence.
- `compose.yml` gives Task Orchestrator `CONPORT_URL=http://conport:3005`.
  The same compose file exposes ConPort REST on `3004` and its MCP endpoint on
  `3005`. Task Orchestrator contains REST `/api/...` callers, so `3005` is not
  a valid REST base URL.
- DopeconBridge defaults `CONPORT_URL` to `http://conport:3004`; explicit
  bridge compose wiring is absent but its current default matches REST.

## Root-cause hypothesis

The active WorkflowStore-to-bridge path is blocked before ConPort because the
canonical Task Orchestrator compose service omits the only configured bearer
token injection. Separately, the service-level `CONPORT_URL` is an MCP port
despite REST callers. These failures are configuration-contract defects, not a
reason to create a local WorkflowStore or bypass DopeconBridge.

## Required repair constraints

- Keep `Task Orchestrator -> authenticated DopeconBridge -> ConPort REST
  /api/custom_data`.
- Do not use `TASK_ORCHESTRATOR_API_KEY` as a JWT or weaken bridge auth.
- Do not introduce direct ConPort writes from WorkflowStore or point REST
  clients to MCP/SSE/info ports.
- Do not put token material, defaults, or generated credentials in tracked
  files. Missing authentication remains an operator configuration error.
- No live write, compose up, or provider call. Synthetic mocked transport only.

## Candidate minimal implementation

1. Change only Task Orchestrator compose environment: inject externally
   supplied `DOPECON_BRIDGE_TOKEN`, and set `CONPORT_URL` to ConPort REST port
   `3004`.
2. Add a narrow architecture test parsing `compose.yml` and asserting those
   two contracts plus absence of a token value/default.
3. Preserve existing WorkflowStore bridge serialization tests. Add a synthetic
   idempotency test to the ConPort handler seam only when its test fixture can
   prove repeated `(workspace_id, category, key)` writes use the same upsert
   contract; no live database or container is required.

## Candidate validation

```text
uv run pytest -q tests/unit/test_task_orchestrator_workflow_store.py tests/unit/test_task_orchestrator_workflow_write_serialization.py <new-compose-contract-test>
docker compose -f compose.yml config --no-interpolate
python -m jsonschema -i task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```

## Open risks / UNKNOWN

- `DOPECON_BRIDGE_TOKEN` is JWT-shaped and bridge tokens expire. This repair
  wires a configured authenticated token; it does not invent a service-token
  lifecycle or credential rotation system.
- No live container/runtime evidence was taken: live writes require explicit
  confirmation and a synthetic workspace isolation design.
- Task Orchestrator control-plane mutation timed out while root attempted to
  create the lane item, so start/context/note transitions are `NOT_RUN`.
