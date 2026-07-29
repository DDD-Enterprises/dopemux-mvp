---
id: TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-implementation-notes
title: Tp Dmx To Conport Persistence Repair 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Scoped ConPort persistence wiring repair implementation evidence and residual-risk record.
---
# Implementation Notes — TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001

## Change

- Set DopeconBridge and Task Orchestrator `CONPORT_URL` to ConPort REST
  `http://conport:3004`.
- Require externally supplied `DOPECON_BRIDGE_TOKEN` for Task Orchestrator
  compose interpolation. No default, token value, generator, auth bypass, or
  direct ConPort writer added.
- Add static compose contract and synthetic mocked `WorkflowStore` upsert test.
  Test proves bearer-header propagation plus stable
  `(workspace_id, category, key)` identity for repeated custom-data writes.

## Explicit Exclusions

- Preserved, not staged: `.claude/claude_config.json`.
- Preserved, not staged: `services/task-orchestrator/app/services/workflow_service.py`.
- Preserved, not staged:
  `tests/unit/test_task_orchestrator_workflow_route_certification.py`.
- Those paths are other-lane work. They are outside this commit slice.

## Validation

PASS:

- `UV_CACHE_DIR=/private/tmp/dmx_to_conport_uv_cache uv run pytest -q tests/arch/test_task_orchestrator_conport_persistence_contract.py tests/unit/test_task_orchestrator_workflow_store.py tests/unit/test_task_orchestrator_workflow_write_serialization.py` — 8 passed.
- `UV_CACHE_DIR=/private/tmp/dmx_to_conport_uv_cache uv run pytest -q docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py` — 3 passed.
- `docker compose -f compose.yml config --no-interpolate` — exit 0.
- `UV_CACHE_DIR=/private/tmp/dmx_to_conport_uv_cache uv run python -m jsonschema -i task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` — exit 0.
- Scoped `pre-commit run --files ...` — passed after frontmatter normalization.

NOT_RUN:

- Live container startup, authenticated JWT issuance, bridge reachability, and
  ConPort writes. Packet forbids live writes.
- Independent embedded audit, PR Steward intake, and supervisor acceptance.

## Rollback

Revert this commit. No migration, provider call, credential change, or runtime
write occurred.
