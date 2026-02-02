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
- `GET /api/analytics/trends` - Energy/attention trends
- `GET /api/breaks/recommendations` - Break suggestions

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
