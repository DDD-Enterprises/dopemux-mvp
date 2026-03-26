# Active Endpoint Inventory

Source of truth: `services/dopecon-bridge/dopecon_bridge/routes.py`

Total active endpoints: `23`

## Health and root

- `GET /`
- `GET /health`

## Authentication

- `POST /auth/token`
- `POST /auth/refresh`

## Event surfaces

- `POST /events` (authenticated)
- `GET /events/stream` (authenticated)
- `GET /events/history` (authenticated)
- `GET /events/{stream:path}` (authenticated)
- `POST /events/tasks-imported` (authenticated)
- `POST /events/session-started` (authenticated)
- `POST /events/progress-updated` (authenticated)

## Fail-closed task surfaces

- `POST /tasks/parse-prd`
- `GET /tasks/next/{project_id}`
- `PATCH /tasks/{task_id}/status`

## Narrow PM routing surface

- `POST /route/pm` (authenticated, policy-wrapped, Leantime-backed only)

## ConPort-backed KG surfaces

- `POST /kg/custom_data` (authenticated)
- `GET /kg/custom_data` (authenticated)
- `POST /kg/decisions` (authenticated)
- `GET /kg/decisions` (authenticated)
- `POST /kg/progress` (authenticated)
- `GET /kg/progress` (authenticated)

## ConPort-backed DDG compatibility surfaces

- `GET /ddg/decisions` (authenticated)
- `GET /ddg/search` (authenticated)

## Excluded or unsupported surfaces

- `/route/cognitive`
- `/ddg/decisions/related`
- `/ddg/decisions/related-text`
- `/kg/links`
- legacy root modules such as `kg_endpoints.py` and `orchestrator_endpoints.py`
