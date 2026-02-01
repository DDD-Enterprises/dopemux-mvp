# Current State Snapshot - Before G31

## Date
2026-02-01

## Services Identified from docker-compose.unified.yml

### Core Services (Candidates for Smoke Stack)
1. **conport** (MCP server)
   - Host port: 3004
   - Container port: 3004
   - Health: http://localhost:3004/health
   - Dependencies: postgres, redis

2. **dopecon-bridge** (coordination layer)
   - Host port: 3016
   - Container port: 3016
   - Health: (none specified)
   - Dependencies: conport, redis

3. **task-orchestrator**
   - Host port: 8000
   - Container port: 8000
   - Health: http://localhost:8000/health
   - Dependencies: redis, conport

4. **adhd-engine**
   - Host port: 8095
   - Container port: 8095
   - Health: http://localhost:8095/health
   - Dependencies: redis, conport

### Infrastructure Services
1. **postgres**
   - Host port: 5432
   - Container port: 5432
   - Health: pg_isready

2. **redis**
   - Host port: 6379
   - Container port: 6379
   - Health: redis-cli ping

3. **qdrant**
   - Host ports: 6333, 6334
   - Container ports: 6333, 6334
   - Health: (none specified)

## Issues Identified
- No single source of truth for ports
- Health endpoints hardcoded in compose
- No validation that registry ↔ compose ↔ service code agree
- No tools/ports_health_audit.py yet
- No services/registry.yaml yet
- No docker-compose.smoke.yml yet

## Next Steps
Create registry.yaml as canonical truth source, then build validation tooling.
