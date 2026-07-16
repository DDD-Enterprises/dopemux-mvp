# ADHD Dashboard

The dashboard consists of a FastAPI backend in this directory and the React
operator UI in `ui-dashboard/`.

## Run

Start the backend and its dependencies:

```bash
docker compose -p dopemux -f compose.yml up -d --build adhd-dashboard
```

Start the React development server:

```bash
npm --prefix ui-dashboard ci
npm --prefix ui-dashboard run dev
```

The React UI is available at `http://localhost:5173`. The backend is
loopback-bound at `http://127.0.0.1:8097`.

## Backend Endpoints

- `GET /health` - backend health and dependency configuration
- `GET /api/metrics` - local dashboard metrics
- `GET /api/task-recommendations` - task recommendations
- `GET /api/cognitive-load` - current cognitive load
- `GET /api/adhd-state` - aggregate state consumed by the React UI
- `GET /api/sessions/today` - current session summary
- `GET /metrics` - Prometheus metrics
- `WS /ws/state` - live state updates consumed by the React UI

The removed `activity-capture` service is not a runtime dependency. Local
dashboard metrics remain bounded stubs, while state data is read from ADHD
Engine and Redis.

## Configuration

- `REDIS_URL` - Redis connection, set to `redis://redis-primary:6379` in compose
- `ADHD_ENGINE_URL` - ADHD Engine base URL, set to `http://adhd-engine:8095`
- `ADHD_ENGINE_REDIS_PREFIX` - shared engine/dashboard Redis namespace
- `ADHD_ENGINE_API_KEY` - optional key forwarded to ADHD Engine
- `DASHBOARD_API_KEY` - optional dashboard API key
- `DASHBOARD_USER_ID` - operator state key, default `default`
- `ALLOWED_ORIGINS` - comma-separated CORS origins

See
[`docs/03-reference/systems/adhd-intelligence/`](../../docs/03-reference/systems/adhd-intelligence/)
for ADHD Engine details.
