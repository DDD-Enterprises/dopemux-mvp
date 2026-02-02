---
id: coordination
title: Coordination
type: system-doc
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Plane Coordinator - Two-Plane Architecture Coordination Service

## Overview

The Plane Coordinator provides unified coordination between Dopemux's two-plane architecture:

- **PM Plane**: Leantime, Task-Master, Task-Orchestrator (Project Management)
- **Cognitive Plane**: Serena, ConPort, ADHD Engine (Development/Cognitive)

## Features

### 🔄 Unified Coordination API
- Single entry point for cross-plane operations
- RESTful endpoints with comprehensive error handling
- WebSocket support for real-time event streaming

### 📡 Event-Driven Coordination
- Real-time event routing between planes
- Priority-based event processing
- Conflict detection and intelligent resolution

### 🏥 Health Monitoring
- Continuous plane health assessment
- Automatic alerting for service issues
- Performance metrics and analytics

### 🧠 ADHD Optimizations
- Cognitive load-aware task coordination
- 25-minute focus session support
- Break recommendation integration

## API Endpoints

### REST Endpoints
- `GET /health` - Service health check
- `POST /api/coordination/operations` - Execute coordination operations
- `GET /api/coordination/health` - Plane health status
- `GET /api/coordination/metrics` - Coordination analytics
- `POST /api/coordination/events` - Emit coordination events
- `GET /api/coordination/conflicts` - Active conflicts
- `POST /api/coordination/conflicts/{id}/resolve` - Resolve conflicts

### WebSocket Endpoint
- `GET /ws/coordination` - Real-time event streaming

## Deployment

### Docker Compose (Master Stack)
```bash
# Start the complete Dopemux stack including plane coordinator
docker-compose -f docker-compose.master.yml up -d plane-coordinator

# Check logs
docker-compose -f docker-compose.master.yml logs plane-coordinator
```

### MCP Servers Stack
```bash
# Start individual MCP servers including plane coordinator
docker-compose -f docker/mcp-servers/docker-compose.yml up -d plane-coordinator
```

### Environment Variables
```bash
COORDINATION_API_PORT=8090          # API port (default: 8090)
WORKSPACE_ID=/workspace             # Workspace path
REDIS_URL=redis://localhost:6379    # Redis connection
CONPORT_URL=http://localhost:3004   # ConPort service URL
ADHD_ENGINE_URL=http://localhost:8095 # ADHD Engine URL
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097 # CORS origins
```

## Usage Examples

### Coordinate Task Creation
```bash
curl -X POST http://localhost:8090/api/coordination/operations \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create_task",
    "source_plane": "cognitive",
    "data": {
      "task": {
        "id": "task_001",
        "title": "Implement feature X",
        "complexity_score": 0.7,
        "energy_required": "high"
      }
    }
  }'
```

### Monitor Plane Health
```bash
curl http://localhost:8090/api/coordination/health
```

### Get Coordination Metrics
```bash
curl http://localhost:8090/api/coordination/metrics
```

## Testing

### Integration Tests
```bash
cd services/task-orchestrator
python test_coordination_integration.py
```

### API Testing
```bash
# Health check
curl http://localhost:8090/health

# Test coordination
curl -X POST http://localhost:8090/api/coordination/test
```

## Architecture

### Components
- **PlaneCoordinator**: Core coordination engine
- **CoordinationAPI**: FastAPI-based REST/WebSocket service
- **SyncEngine**: Multi-directional synchronization
- **TaskCoordinator**: ADHD-aware task management
- **ConPortAdapter**: Bidirectional data transformation

### Dependencies
- **Redis**: Event processing and caching
- **ConPort**: Knowledge graph and decision logging
- **ADHD Engine**: Cognitive state monitoring
- **Task Orchestrator**: Advanced task management

### Data Flow
```
PM Plane ──┐
           ├── Plane Coordinator ── REST/WebSocket API
Cognitive Plane ─┘
                      │
                      ├── Sync Engine
                      ├── Conflict Resolution
                      └── Health Monitoring
```

## Configuration

### Docker Environment
```yaml
plane-coordinator:
  environment:
    - COORDINATION_API_PORT=8090
    - REDIS_URL=redis://dopemux-redis-events:6379
    - CONPORT_URL=http://conport:3004
    - ADHD_ENGINE_URL=http://dopemux-adhd-engine:8095
  ports:
    - "8090:8090"
  depends_on:
    - dopemux-redis-events
    - conport
    - dopemux-adhd-engine
```

### Health Checks
- **HTTP Endpoint**: `GET /health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## Monitoring

### Metrics Available
- Events processed
- Conflicts detected/resolved
- Sync operations completed
- Health check status per plane
- API response times

### Logging
- Structured JSON logging
- Correlation IDs for request tracing
- Error categorization and alerting
- Performance monitoring

## Troubleshooting

### Common Issues
- **Connection refused**: Check service dependencies (Redis, ConPort, ADHD Engine)
- **Health check failures**: Verify API endpoints are responding
- **Event processing delays**: Check Redis connectivity and queue depth
- **Conflict resolution errors**: Review plane synchronization settings

### Debug Commands
```bash
# Check service logs
docker logs dopemux-plane-coordinator

# Test API connectivity
curl -v http://localhost:8090/health

# Check Redis connectivity
docker exec dopemux-plane-coordinator redis-cli ping
```

## Development

### Local Development
```bash
cd services/task-orchestrator

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_coordination_integration.py

# Start API server
python -m uvicorn coordination_api:app --host 0.0.0.0 --port 8090 --reload
```

### Code Structure
```
services/task-orchestrator/
├── plane_coordinator.py      # Core coordination engine
├── coordination_api.py       # FastAPI service
├── sync_engine.py           # Synchronization logic
├── task_coordinator.py      # Task management
├── test_coordination_integration.py  # Integration tests
├── Dockerfile.coordination   # Docker configuration
└── adapters/                # Data adapters
    └── conport_adapter.py
```

## Integration with Dopemux

The Plane Coordinator integrates seamlessly with the existing Dopemux ecosystem:

- **ConPort**: Bidirectional decision and progress synchronization
- **ADHD Engine**: Cognitive state monitoring and break recommendations
- **Task Orchestrator**: Advanced task coordination and dependency management
- **Leantime Bridge**: Project management integration
- **Serena**: Code intelligence and navigation

This provides a unified coordination layer that bridges the PM and Cognitive planes while maintaining ADHD-friendly workflows throughout the development process.
