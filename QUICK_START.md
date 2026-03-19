# Dopemux MVP Quick Start

This quick start brings up the ADHD MVP inner loop:

- `postgres` with Apache AGE
- `redis`
- `conport`
- `dopecon-bridge`
- `workspace-watcher`
- `activity-capture`
- `adhd-engine`
- `adhd-dashboard`
- `ui-dashboard` as a separate Vite app

The goal is a live graph:

`workspace change -> Redis stream -> Activity Capture -> ADHD Engine -> Redis pub/sub -> ADHD Dashboard -> UI`

## Prerequisites

- Docker with `docker compose`
- Python 3.11+ for local test runs
- Node 18+ for `ui-dashboard`

## 1. Start the MVP stack

```bash
docker compose -f compose.adhd-stack.yml up -d --build
```

Check service health:

```bash
docker compose -f compose.adhd-stack.yml ps
curl http://localhost:8095/health
curl http://localhost:8096/health
curl http://localhost:8097/health
curl http://localhost:3016/health
```

## 2. Start the dashboard UI

The React UI stays separate for MVP.

```bash
cd ui-dashboard
npm install
VITE_DASHBOARD_API_URL=http://localhost:8097 \
VITE_DASHBOARD_WS_URL=ws://localhost:8097 \
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## 3. First 5 minutes

1. Bring the stack up with `docker compose -f compose.adhd-stack.yml up -d --build`.
2. Start the UI from `ui-dashboard`.
3. Open the dashboard and confirm the top status chip shows a live or degraded connection state.
4. Trigger one workspace switch event with the manual watcher command below.
5. Watch the dashboard update its live signal feed and cognitive state panels.

## 4. Trigger a smoke-test workspace switch

Inside the running `workspace-watcher` container:

```bash
docker compose -f compose.adhd-stack.yml exec workspace-watcher \
  python main.py \
  --emit-switch \
  --redis-url redis://redis:6379 \
  --from-app Terminal \
  --to-app "Claude Code" \
  --from-workspace /Users/hue/code/other-project \
  --to-workspace /Users/hue/code/dopemux-mvp
```

That injects one canonical `workspace.switched` event into `dopemux:events` without needing host window focus visibility from inside Docker.

## 5. Verify the live graph

Check the aggregate dashboard API:

```bash
curl http://localhost:8097/api/adhd-state | jq
curl http://localhost:8097/api/cognitive-load | jq
curl http://localhost:8097/api/task-recommendations | jq
```

Check Activity Capture metrics:

```bash
curl http://localhost:8096/metrics | jq
```

Check Redis-backed event flow:

```bash
docker compose -f compose.adhd-stack.yml exec redis \
  redis-cli XRANGE dopemux:events - + COUNT 5
```

## 6. Verify DopeconBridge auth

Unauthenticated KG and event inspection routes should fail:

```bash
curl -i http://localhost:3016/kg/decisions
curl -i http://localhost:3016/events/history
```

Fetch a dev JWT:

```bash
curl -s -X POST http://localhost:3016/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dopemux-dev-admin&password=dopemux-bridge-local-2026"
```

Use the returned bearer token:

```bash
TOKEN="<paste-access-token>"

curl -s http://localhost:3016/events/history \
  -H "Authorization: Bearer ${TOKEN}" | jq
```

## 7. Local verification commands

Python:

```bash
python -m pytest \
  services/adhd_engine/tests/test_api.py \
  services/adhd-dashboard/tests/test_task_recommender.py \
  services/workspace-watcher/tests \
  services/activity-capture/tests -q
```

Frontend:

```bash
cd ui-dashboard
npm run build
npm test -- --run
```

## 8. Key MVP defaults

- ADHD engine API key: `dopemux-adhd-engine-local-2026`
- Bridge username: `dopemux-dev-admin`
- Bridge password: `dopemux-bridge-local-2026`
- Bridge JWT secret is seeded only for local MVP compose
- UI talks only to `adhd-dashboard` on `8097`
- Producer event names remain mixed; consumers normalize dotted and underscored legacy forms

## 9. Troubleshooting

If the UI loads but stays stale:

```bash
curl http://localhost:8097/api/adhd-state | jq
docker compose -f compose.adhd-stack.yml logs adhd-dashboard
docker compose -f compose.adhd-stack.yml logs activity-capture
docker compose -f compose.adhd-stack.yml logs adhd-engine
```

If the watcher container cannot see host focus changes, use the manual `--emit-switch` command above for smoke tests. That is the expected MVP fallback in containerized local dev.

If you want to stop everything:

```bash
docker compose -f compose.adhd-stack.yml down
```
