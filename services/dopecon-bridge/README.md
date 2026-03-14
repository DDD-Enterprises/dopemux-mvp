# DopeconBridge Active Runtime

## Role

DopeconBridge is the active PM-plane adapter, router, and translator layer. It is **not** a canonical authority for tasks, workflow state, decisions, progress, or chronicle memory.

Canonical authorities remain:

- **Leantime** for PM operational records
- **Task Orchestrator** for workflow legality, blockers, and next-action
- **ConPort** for decisions, progress, and durable context
- **dope-memory** for chronicle memory

## Active runtime boundary

The active runtime is limited to:

- `services/dopecon-bridge/main.py`
- `services/dopecon-bridge/dopecon_bridge/`

Legacy or excluded modules at the service root are not part of the sanctioned runtime unless explicitly reactivated by a separate decision.

## Sanctioned active surfaces

- `GET /health`
- `GET /`
- `POST /auth/token`
- `POST /auth/refresh`
- `POST /events` and convenience `POST /events/*`
  - authenticated
  - event transport only
- `GET /events/stream`
- `GET /events/history`
- `GET /events/{stream}`
- `POST /route/pm`
  - adapter-safe Leantime-backed PM operations only
  - rejects workflow-significant mutations
- `GET/POST /kg/custom_data`
- `GET/POST /kg/decisions`
- `GET/POST /kg/progress`
- `GET /ddg/decisions`
- `GET /ddg/search`

## Blocked or deprecated active surfaces

- `POST /tasks/parse-prd`
- `GET /tasks/next/{project_id}`
- `PATCH /tasks/{task_id}/status`
- `/route/cognitive`
- `/ddg/decisions/related`
- `/ddg/decisions/related-text`
- `/kg/links`

These paths are blocked or unsupported because they previously depended on bridge-local authority or on backend contracts that are not part of the sanctioned active runtime.

## Local persistence posture

Bridge-local SQL tables such as `TaskRecord`, `DdgDecision`, and `DdgProgress` are transitional and non-canonical. They must not be used as PM-plane truth.

## Authentication

- Event write routes require authentication.
- The default admin user is initialized for local development only.
- PM-plane operators should prefer service-to-service tokens over interactive use.

## Verification

```bash
python3 -m pytest tests/shared/test_dopecon_bridge_client.py \
  services/dopecon-bridge/tests/test_leantime_route_contract.py \
  services/dopecon-bridge/tests/test_task_integration_unit.py
```
