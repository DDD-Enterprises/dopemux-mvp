# ADHD Dashboard Service

**Category**: Cognitive Plane  
**Status**: Production  
**Port**: 8097  
**Purpose**: ADHD-optimized metrics and accommodations dashboard

## Overview

ADHD Dashboard provides specialized visualization of ADHD accommodation metrics, energy levels, attention state, and cognitive load tracking.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d adhd-dashboard

# Access dashboard
open http://localhost:8097
```

## Health Check

```bash
curl http://localhost:8097/health
```

## API Endpoints

- `GET /health` - Service health status
- `GET /api/metrics` - Current ADHD metrics
- `GET /api/adhd-state` - Real-time ADHD state
- `GET /api/sessions/today` - Today's session data
- `GET /api/tasks` - Work and queue items from the Task Orchestrator (see Task queue below)
- `POST /api/tasks/{item_id}/transition` - Start or Finish one item; needs `DASHBOARD_API_KEY` (see Start and Finish below)
- `GET /api/analytics/trends` - Energy/attention trends
- `GET /api/breaks/recommendations` - Break suggestions

## Task queue (`GET /api/tasks`)

Reads work and queue items from the Task Orchestrator MCP on `127.0.0.1:7890`. Read-only.

That port serves whichever project's container publishes it, so the route first proves from the
container's dopemux labels that the owner is the project this backend runs from. It proves it
again after the read. The response is always HTTP 200 with a `status`:

- `ok` - items returned
- `empty` - this project has no work or queue items
- `wrong_project` - another project owns the port; its name is given and no items are returned
- `unavailable` - the owner could not be proven, or the read failed; `reason` says which

The proof needs `docker ps` and a git checkout, so the route works for a host-run backend only:

```bash
cd services/adhd-dashboard
python -m uvicorn backend:app --host 127.0.0.1 --port 8097
```

In the compose container it always answers `unavailable`.

## Start and Finish (`POST /api/tasks/{item_id}/transition`)

The only write the cockpit makes to the Task Orchestrator (operator ruling 2026-11-22: "Yes,
Start/Finish only"). Body:

```json
{"trigger": "start" | "complete", "request_id": "<uuid, one per click>"}
```

- `start` is sent only when the item is in `queue` (it moves to `work`). The orchestrator's `start`
  also moves work to review and review to terminal, so the backend reads the role first and refuses
  otherwise.
- `complete` is sent only when the item is in `work`. The orchestrator refuses it while required
  notes are missing; the response lists them in `missing_notes`.
- No other trigger (cancel, block, hold, resume, reopen) is exposed. `item_id` must be a full
  lowercase UUID.

**Auth.** Unlike the read routes, this route needs `DASHBOARD_API_KEY` set on the backend and the same
value in the `X-API-Key` header. With no key configured it refuses every write (fail closed). The
cockpit sends the key from `VITE_DASHBOARD_API_KEY`, so the key is in the browser bundle: run the
backend on `127.0.0.1` only.

**Actor.** Every write carries the actor `{id: "operator:cockpit", kind: "user"}`. The orchestrator
records it but does not verify it until actor authentication lands (Wave 2C), so a cockpit write is
attributed, not authenticated. Responses say so in `actor.verification`.

**Ownership.** Before each write the backend proves which project owns port 7890 (the same Docker-label
check as the read), reads the item's role, proves ownership again and requires the same container id
both times. The role read, the second check and the write run under one lock in the backend process,
so two clicks cannot both see `queue`. Another writer (a runner) can still move the item in between;
the response then reports the move the orchestrator actually made.

**Response.** Always a JSON body, never a bare error:

| `status` | HTTP | Meaning |
|---|---|---|
| `applied` | 200 | Written; `previous_role` and `new_role` are the orchestrator's |
| `refused` | 409 (400 bad body, 401 wrong key, 403 no key set) | Not written; `reason` says why |
| `wrong_project` | 409 | Another project owns port 7890; nothing was written |
| `unavailable` | 503 (500 on an unexpected backend error) | Owner unproven or the orchestrator unreachable; `reason` says whether anything was written or the outcome is unknown |

Like the read route, it works from a host-run backend only.

## Configuration

Environment variables:
- `PORT` - Service port (default: 8097)
- `DASHBOARD_API_KEY` - Optional for read routes (open when unset); required for the write route, which refuses when it is unset
- `ADHD_ENGINE_URL` - ADHD Engine URL (default: http://localhost:8080)
- `DOPECON_BRIDGE_URL` - DopeconBridge URL (default: http://localhost:3016)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## Features

- **Energy Level Tracking** - Real-time energy state visualization
- **Attention Monitoring** - Focus/distraction patterns
- **Cognitive Load** - Current cognitive load measurement
- **Break Recommendations** - Intelligent break suggestions (25-min cycles)
- **Session Analytics** - Daily/weekly ADHD metrics

## ADHD Engine Integration

Queries ADHD Engine APIs:
- `/api/v1/energy-level` - Current energy state
- `/api/v1/attention-state` - Attention monitoring
- `/api/v1/cognitive-load` - Cognitive load assessment
- `/api/v1/break-recommendation` - Break suggestions

## Development

```bash
cd services/adhd-dashboard
python backend.py
```

## Documentation

See [docs/03-reference/systems/adhd-intelligence/](../../docs/03-reference/systems/adhd-intelligence/) for ADHD Engine details.
