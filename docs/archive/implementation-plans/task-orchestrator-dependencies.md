---
id: task-orchestrator-dependencies
title: Task Orchestrator Dependencies
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Task Orchestrator Dependencies (explanation) for dopemux documentation and
  developer workflows.
---
# Task-Orchestrator Dependencies Audit

**Task**: 1.1 - Inventory External Dependencies
**Date**: 2025-10-19
**Status**: Complete
**Complexity**: 0.4 (moderate-low)
**Duration**: 45 minutes

## Executive Summary

Task-Orchestrator is a **Kotlin-based system with 37 specialized tools** wrapped by a Python MCP server. It has dependencies spanning Python packages, external services, environment variables, and event bus infrastructure.

**Key Finding**: Task-Orchestrator is architected as a hybrid system:
- Core orchestration: Kotlin (8,889 lines with 37 tools)
- MCP interface: Python wrapper (`server.py`)
- Integration: Dopemux event bus

## Directory Structure

```
services/task-orchestrator/
├── enhanced_orchestrator.py       # Main orchestration logic
├── server.py                      # MCP wrapper (Python)
├── adhd_engine.py                 # ADHD optimizations
├── automation_workflows.py        # Workflow automation
├── deployment_orchestration.py    # Deployment coordination
├── multi_team_coordination.py     # Multi-team features
├── predictive_risk_assessment.py  # ML risk analysis
├── external_dependency_integration.py  # External systems
├── performance_optimizer.py       # Performance tuning
├── event_coordinator.py           # Event coordination
├── claude_context_manager.py      # Claude integration
└── sync_engine.py                 # Synchronization

Total: 13 Python modules (wrapper layer)
Kotlin core: 37 specialized tools (documented in ADR-207)
```

## Python Dependencies

### Core Framework (from requirements.txt)
```txt
# Web Framework & API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0

# Async Support
asyncio>=3.4.3
aiohttp>=3.12.14  # Used by task-orchestrator

# Environment & Configuration
python-dotenv>=1.0.0
typer>=0.9.0

# Utilities
rich>=13.0.0
```

### Additional Dependencies (from imports)
```python
# Redis async client (not in requirements.txt - needs adding!)
redis.asyncio

# Standard library (no installation needed)
asyncio, json, logging, datetime, pathlib, typing
dataclasses, enum, collections, hashlib, os, re
statistics, subprocess, sys, uuid, math
```

**⚠️ ISSUE FOUND**: `redis.asyncio` is imported but not in `requirements.txt`
**Resolution**: Add `redis>=4.5.0` to requirements or create service-specific requirements

### Internal Module Dependencies
```python
# Task-Orchestrator specialized engines
multi_team_coordination.py         # MultiTeamCoordinationEngine
predictive_risk_assessment.py      # PredictiveRiskAssessmentEngine
external_dependency_integration.py  # ExternalDependencyIntegrationEngine
```

### Event Bus Integration
```python
# Dopemux event bus (optional, graceful degradation)
from dopemux.event_bus import (
    RedisStreamsAdapter,
    DopemuxEvent,
    Priority,
    CognitiveLoad,
    ADHDMetadata
)
from dopemux.producers.mcp_producer import MCPEventProducer
```

## Service Dependencies

### Required Services

| Service | Port | Purpose | Health Check | Required |
|---------|------|---------|-------------|----------|
| **Redis** | 6379 | Event bus, caching, async coordination | `redis-cli ping` | ✅ Critical |
| **Leantime** | 8080 | PM system, task visualization | HTTP /api/health | ✅ Critical |
| **ConPort** | 5455 | Knowledge graph, decision storage | PostgreSQL connection | ✅ Critical |

### Optional Services

| Service | Port | Purpose | Fallback |
|---------|------|---------|----------|
| **Redis Commander** | 8081 | Redis UI monitoring | Can operate without |
| **OpenAI API** | N/A | AI analysis features | Degrades gracefully |

### Service Architecture
```
┌─────────────────────────────────────────────────┐
│  LEANTIME (Visualization Layer) - Port 8080    │
│  Multi-project PM dashboards                    │
└─────────────┬───────────────────────────────────┘
              ▼
┌─────────────────────────────────────────────────┐
│  TASK-ORCHESTRATOR (Intelligence Layer)         │
│  37 Kotlin tools + Python MCP wrapper           │
│  Ports: MCP stdio interface                     │
└─────────────┬───────────────────────────────────┘
              ▼
┌─────────────────────────────────────────────────┐
│  CONPORT (Storage Authority) - Port 5455        │
│  Tasks, decisions, knowledge graph              │
└─────────────────────────────────────────────────┘
              ▲
              │
┌─────────────┴───────────────────────────────────┐
│  REDIS EVENT BUS - Port 6379                    │
│  Async coordination, caching                    │
└─────────────────────────────────────────────────┘
```

## Environment Variables

### Required
```bash
# Redis Configuration
REDIS_URL="redis://localhost:6379"
# Default: redis://localhost:6379
# Format: redis://[password@]host:port[/database]

# Leantime Integration
LEANTIME_URL="http://localhost:8080"
# Default: http://localhost:8080

# AI Features
OPENAI_API_KEY="sk-..."
# Required for: predictive risk assessment, ML-based dependency analysis
# Source: OpenAI API dashboard
```

### Optional
```bash
# Event Bus Configuration
EVENTS_ENABLED=true
# Default: Falls back gracefully if not available
# Controls dopemux event bus integration

# Logging Level
LOG_LEVEL="INFO"
# Default: INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Environment Variable Loading
```python
# From enhanced_orchestrator.py
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
leantime_url = os.getenv("LEANTIME_URL", "http://localhost:8080")

# From automation_workflows.py
env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
```

## Docker Infrastructure

### Event Bus Configuration
**File**: `docker/docker-compose.event-bus.yml`

**Services**:
1. **redis-event-bus** (dopemux-redis-events)
   - Image: redis:7-alpine
   - Port: 6379
   - Volume: redis_events_data
   - Config: ./redis/redis.conf
   - Health check: redis-cli ping every 10s
   - Network: dopemux-events (172.25.0.0/16)

2. **redis-commander** (dopemux-redis-ui)
   - Image: rediscommander/redis-commander:latest
   - Port: 8081
   - Credentials: admin/dopemux-redis-ui
   - Depends on: redis-event-bus

### Network Configuration
```yaml
networks:
  dopemux-events:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

## Agent Dependencies

From `AgentType` enum in `enhanced_orchestrator.py`:

```python
class AgentType(str, Enum):
    CONPORT = "conport"       # Knowledge graph operations
    SERENA = "serena"         # Code intelligence
    TASKMASTER = "taskmaster" # Task parsing
    CLAUDE_FLOW = "claude_flow"  # AI workflow orchestration
    ZEN = "zen"               # Multi-model reasoning
```

**Integration Points**:
- ConPort: Task storage, decision logging, knowledge graph
- Serena: Code analysis, complexity scoring, navigation
- TaskMaster: PRD parsing, task decomposition
- Claude Flow: AI agent coordination
- Zen: Consensus building, deep analysis

## Deployment Requirements

### Minimum System Requirements
```yaml
CPU: 2 cores (4 recommended for ML features)
Memory: 4GB (8GB recommended with caching)
Storage: 10GB (for logs, cache, temporary files)
Network: Outbound HTTPS (OpenAI API, package downloads)
```

### Port Allocation
```yaml
6379: Redis event bus (required)
8080: Leantime PM system (required)
8081: Redis Commander UI (optional)
5455: ConPort PostgreSQL (required)
MCP: stdio interface (no network port)
```

### CI/CD Integration
**Status**: Not yet configured
**Requirements**:
- Docker image build pipeline
- Environment variable injection
- Health check integration
- Multi-instance coordination testing

**Planned** (Phase 2):
- Kubernetes deployment manifests
- Helm charts for configuration
- Auto-scaling based on task load
- Blue-green deployment support

## Issue Tracker

### Critical Issues

1. **Missing Redis Dependency**
   - **Issue**: `redis.asyncio` imported but not in `requirements.txt`
   - **Impact**: Import failure in production environments
   - **Fix**: Add `redis>=4.5.0` to requirements.txt or create `requirements-task-orchestrator.txt`
   - **Priority**: HIGH

### Recommendations

1. **Create Service-Specific Requirements**
   ```bash
   # Recommended structure
   requirements.txt              # Root dependencies
   services/task-orchestrator/requirements.txt  # Service-specific
   ```

2. **Document Kotlin Core**
   - Kotlin dependencies not audited (37 tools in Kotlin codebase)
   - Recommendation: Create `kotlin-dependencies.md` in Phase 1.3

3. **Environment Variable Documentation**
   - Create `.env.example` with all required variables
   - Add validation script to check environment before startup

4. **Health Check Endpoints**
   - Add MCP health check tool for dependency validation
   - Check Redis, Leantime, ConPort connectivity on startup

## Next Steps (Component 2 Preview)

**Task 1.2**: Verify Redis Infrastructure (30 min)
- Confirm Redis is running on port 6379
- Test Redis Streams functionality (required for event bus)
- Validate redis.conf configuration
- Check Redis Commander access

**Task 1.3**: Audit ConPort API Usage (90 min)
- Find all ConPort API calls in Task-Orchestrator code
- Document expected schemas and data structures
- Identify version compatibility requirements
- Map ConPort ↔ OrchestrationTask transformation

## Conclusion

**Audit Complete**: ✅
**Issues Found**: 1 (missing redis dependency)
**Services Required**: 3 (Redis, Leantime, ConPort)
**Environment Variables**: 3 required, 2 optional

**Go/No-Go Recommendation**: 🟢 **GO** (with one fix)
- Fix: Add `redis>=4.5.0` to requirements.txt
- All other dependencies are available and documented
- Service architecture is clear and well-defined
- Ready to proceed to Task 1.2 (Redis verification)

---

**Task Status**: COMPLETE
**Deliverable**: task-orchestrator-dependencies.md
**Next Task**: 1.2 - Verify Redis Infrastructure
**Estimated Next Duration**: 30 minutes
**Estimated Next Complexity**: 0.3 (low)
