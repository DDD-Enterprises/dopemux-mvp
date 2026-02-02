# Monitoring Dashboard Service

**Category**: Cognitive Plane  
**Status**: Production  
**Port**: 8097  
**Purpose**: System monitoring and metrics visualization

## Overview

Monitoring Dashboard provides real-time metrics visualization and system health monitoring for the Dopemux platform, with ADHD-optimized dashboard layouts.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d monitoring-dashboard

# Access dashboard
open http://localhost:8097
```

## Health Check

```bash
curl http://localhost:8097/health
```

## API Endpoints

- `GET /health` - Service health status
- `GET /api/metrics` - Current system metrics
- `GET /api/services` - Service status overview
- `GET /api/adhd-state` - ADHD Engine state
- `GET /api/analytics/trends` - Historical trends

## Configuration

Environment variables:
- `PORT` - Service port (default: 8097)
- `DOPECON_BRIDGE_URL` - DopeconBridge URL (default: http://localhost:3016)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## DopeconBridge Integration

Uses `bridge_adapter.py` to:
- Fetch system metrics via DopeconBridge
- Query service health status
- Retrieve ADHD state data

## Development

```bash
cd services/monitoring-dashboard
python bridge_adapter.py
```

## Documentation

See [services/.claude/](../.claude/) for service development standards.
