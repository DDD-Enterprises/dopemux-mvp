# Ultra UI Dashboard Backend

FastAPI backend for `/Users/hue/code/dopemux-mvp/ui-dashboard` with deterministic fallback data and optional live pull integration.

## Endpoints

- `GET /health`
- `GET /api/cognitive-state?user_id=<id>`
- `GET /api/team-members`
- `GET /api/tasks?limit=<n>`
- `GET /api/dashboard?user_id=<id>&limit=<n>`

## Data Sources

- ADHD Engine (`ADHD_ENGINE_URL`) for cognitive state:
  - `/api/v1/energy-level/{user_id}`
  - `/api/v1/attention-state/{user_id}`
- Task Orchestrator query API (`TASK_ORCHESTRATOR_URL`) for tasks:
  - `/tasks?limit=<n>`

If upstream services are unavailable, the backend returns deterministic fallback payloads and reports source metadata.

## Environment Variables

- `DASHBOARD_BACKEND_HOST` (default: `127.0.0.1`)
- `DASHBOARD_BACKEND_PORT` (default: `3001`)
- `ADHD_ENGINE_URL` (default: `http://localhost:8095`)
- `ADHD_ENGINE_API_KEY` (optional)
- `TASK_ORCHESTRATOR_URL` (default: `http://localhost:3017`)

## Run

```bash
uvicorn app:app --host 127.0.0.1 --port 3001
```

or:

```bash
python main.py
```
