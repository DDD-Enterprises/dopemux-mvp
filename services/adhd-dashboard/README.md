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

## Configuration

Environment variables:
- `PORT` - Service port (default: 8097)
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
