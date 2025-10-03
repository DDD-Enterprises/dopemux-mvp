# ADHD Accommodation Engine

Standalone microservice providing intelligent ADHD-optimized task assessment and workflow support.

**Part of Path C Migration** (Decision #140) - extracted from task-orchestrator.

## Features

- Real-time energy level monitoring (5 states)
- Attention state tracking (5 states)
- Cognitive load assessment
- Break timing and hyperfocus protection
- Personalized user profiles
- 6 background async monitors

## Quick Start

```bash
# Build and start with Docker
docker-compose up -d adhd-engine

# Check health
curl http://localhost:8095/health

# View logs
docker-compose logs -f adhd-engine
```

## API Endpoints

**Assessment**:
- `POST /api/v1/assess-task` - Assess task suitability for user's ADHD state
- `GET /api/v1/energy-level/{user_id}` - Get current energy level
- `GET /api/v1/attention-state/{user_id}` - Get attention state

**Management**:
- `POST /api/v1/recommend-break` - Get break recommendation
- `POST /api/v1/user-profile` - Create/update user ADHD profile
- `PUT /api/v1/activity/{user_id}` - Log user activity event

**Monitoring**:
- `GET /health` - Service health and monitor status
- `GET /docs` - Interactive API documentation (Swagger)

## Architecture

```
ADHD Engine (Port 8095)
├── FastAPI Web Server
├── Redis (DB 6) - State persistence
├── Integration Bridge HTTP - ConPort data access
└── 6 Background Monitors
    ├── Energy Level (5min)
    ├── Attention State (3min)
    ├── Cognitive Load (2min)
    ├── Break Timing (1min)
    ├── Hyperfocus Protection (5min)
    └── Context Switch Analyzer (5min)
```

## Configuration

See `.env.example` for all configuration options.

Key settings:
- `REDIS_URL`: Redis connection URL
- `INTEGRATION_BRIDGE_URL`: Integration Bridge for ConPort data
- `WORKSPACE_ID`: Workspace path

## Week 3 Integration

Currently uses Integration Bridge HTTP API for ConPort data.
Week 3 will optimize with direct database access if needed.

## Development

```bash
# Install dependencies
cd services/adhd_engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
python main.py

# Run tests
pytest tests/ -v --cov
```

## Performance Targets

- API response time: <200ms (P95) - ADHD optimized
- Monitor overhead: <50ms each
- Memory usage: <100MB
- Test coverage: >80%
