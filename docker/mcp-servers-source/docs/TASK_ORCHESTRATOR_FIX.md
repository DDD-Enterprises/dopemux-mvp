---
id: TASK_ORCHESTRATOR_FIX
title: Task Orchestrator Fix
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Task Orchestrator Fix (explanation) for dopemux documentation and developer
  workflows.
---
# Task-Orchestrator Fix Documentation
**Date**: 2026-02-05
**Issue**: task-orchestrator container failing to start
**Status**: ✅ RESOLVED

## Problem Summary

task-orchestrator was configured in docker-compose.yml but not running, making 37 workflow tools unavailable.

## Root Cause Analysis

### Issue 1: Incorrect Command Override
**Problem**: docker-compose.yml overrode the Dockerfile CMD with incorrect command:
```yaml
command: ["python", "/app/server.py"]  # ❌ Wrong - server.py doesn't exist
```

**Root Cause**: The Dockerfile uses uvicorn to run a FastAPI app at `app.main:app`, not a standalone server.py script.

### Issue 2: Missing Redis Connection
**Problem**: task-orchestrator failed with:
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Root Cause**:
- task-orchestrator requires Redis for coordination
- Environment didn't specify `REDIS_URL`
- Default localhost:6379 doesn't exist in container

### Issue 3: Port Mismatch
**Problem**: docker-compose mapped port 3014:3014, but Dockerfile exposes port 8000

## Solution

### Fix 1: Remove Command Override
Let Dockerfile CMD handle startup:
```yaml
# OLD:
command: ["python", "/app/server.py"]

# NEW:
# command defaults to: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Fix 2: Add Redis Configuration
```yaml
environment:
  - MCP_SERVER_PORT=8000
  - JVM_HEAP_SIZE=512m
  - REDIS_URL=redis://dopemux-redis-primary:6379  # ✅ Added
```

### Fix 3: Fix Port Mapping
```yaml
ports:
  - "3014:8000"  # Map external 3014 to internal 8000
```

### Fix 4: Update Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]  # Use correct port
  timeout: 10s
  retries: 3
  interval: 30s
  start_period: 45s  # Give FastAPI time to start
```

## Verification

### Health Check
```bash
$ curl http://localhost:3014/health
{
    "status": "healthy",
    "service": "task-orchestrator-coordination-api",
    "timestamp": "2026-02-05T22:53:52.653305+00:00"
}
```

### Container Status
```bash
$ docker ps --filter "name=mcp-task-orchestrator"
NAME STATUS                    PORTS
dopemux-mcp-task-orchestrator   Up (healthy)   0.0.0.0:3014->8000/tcp
```

## Key Learnings

### 1. **Always Check Dockerfile CMD**
When docker-compose command override fails, verify against Dockerfile:
- Dockerfile: `CMD ["uvicorn", "app.main:app", ...]`
- docker-compose should either use this OR override correctly

### 2. **Docker Networking != Localhost**
Containers can't access localhost services. Must use:
- Service names: `redis://dopemux-redis-primary:6379`
- NOT: `redis://localhost:6379`

### 3. **Port Mapping Format**
```yaml
ports:
  - "EXTERNAL:INTERNAL"
  - "3014:8000"  # Access via localhost:3014, app listens on 8000
```

### 4. **Health Check Port Matters**
Health check runs INSIDE container, so use internal port:
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]  # Use 8000, not 3014
```

## Future Prevention

### Checklist for New MCP Servers
- [ ] Verify Dockerfile CMD matches service expectations
- [ ] Don't override CMD unless necessary
- [ ] Use service names for inter-container communication
- [ ] Map ports correctly (external:internal)
- [ ] Health check uses internal port
- [ ] Test after adding to docker-compose

### Documentation Requirements
All MCP servers should document:
- **Correct startup command** (from Dockerfile)
- **Required environment variables** (especially URLs)
- **Port mappings** (what's exposed vs what's used)
- **Dependencies** (Redis, Postgres, etc.)
- **Health check endpoint** and expected response

## Related Files Modified

1. `/docker/mcp-servers/docker-compose.yml` - task-orchestrator service config
2. `/docker/mcp-servers/MCP_HEALTH_REPORT.md` - Updated status to healthy
3. This file - Fix documentation

## Tools Now Available

With task-orchestrator running, these 37 tools are now accessible:
- Task creation and management
- Breakdown and decomposition
- Priority and complexity scoring
- Multi-team coordination
- Risk assessment
- Dependency tracking
- And 31 more workflow tools

## References

- task-orchestrator Dockerfile: `/services/task-orchestrator/Dockerfile`
- FastAPI docs: app listens on port specified in uvicorn command
- Docker networking: https://docs.docker.com/network/
