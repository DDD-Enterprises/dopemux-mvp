---
id: ports_table
title: Ports_Table
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Ports_Table (explanation) for dopemux documentation and developer workflows.
---
# Port Configuration: Before vs After G31

## BEFORE G31 ❌

### Port Sources (Multiple, Conflicting)

| Source | conport | dopecon-bridge | task-orchestrator | Notes |
|--------|---------|----------------|-------------------|-------|
| docker-compose.unified.yml | `3004:3004` \| `3016:3016` \| `8000:8000` | Hardcoded |
| Service code defaults | `3004` \| `3016` \| `8000` | May differ |
| Health check tool | (none) | (none) | (none) | Didn't exist |
| Validation | ❌ None | ❌ None | ❌ None | Silent drift |

**Problem:** If compose says 3004 but service expects 3005, services fail to start with cryptic connection errors.

---

## AFTER G31 ✅

### Single Truth Source
**Location:** `services/registry.yaml`

```yaml
# Infrastructure
- postgres: 5432 (pg_isready)
- redis: 6379 (redis-cli ping)
- qdrant: 6333 (GET /)

# MCP
- conport: 3004 (GET /health)

# Coordination
- dopecon-bridge: 3016 (GET /health)

# Cognitive
- task-orchestrator: 8000 (GET /health)
```

### Derived Artifacts (Generated, Never Edited)

| Artifact | Source | Purpose | Auto-generated |
|----------|--------|---------|----------------|
| `.env.smoke` \| registry.yaml \| Environment variables for compose \| ✅ `generate_smoke_env.py` |
| Port mappings in compose | `.env.smoke` \| Parametric port config \| ✅ Uses `${VAR:-default}` |
| Health check URLs | registry.yaml | Runtime validation | ✅ `ports_health_audit.py` |

### Validation (Enforced)

| Tool | Mode | What It Checks | Fails If |
|------|------|----------------|----------|
| `ports_health_audit.py` \| `--mode static` | Registry completeness | Missing port/health_path |
| `ports_health_audit.py` \| `--mode static --explain-drift` | Registry ↔ Compose alignment | Port mismatch |
| `pytest tests/arch/...alignment.py` | Architecture test | Compose references registry | Service missing, ports differ |
| `ports_health_audit.py` \| `--mode runtime` | Live health checks | Service down/unhealthy |

---

## Example: Adding a New Service

### OLD WAY ❌
1. Edit docker-compose.yml: hardcode port `9000:9000`
1. Edit service code: default `PORT=9000`
1. Hope they match
1. Debug connection errors for 30 minutes

### NEW WAY ✅
1. Edit registry.yaml:
```yaml
- name: new-service
  port: 9000
  health_path: /health
  enabled_in_smoke: true
```

1. Regenerate: `python tools/generate_smoke_env.py`
1. Validate: `pytest tests/arch/test_registry_compose_alignment.py`
1. Deploy: `docker compose -f docker-compose.smoke.yml up -d --build`
1. Verify: `python tools/ports_health_audit.py --mode runtime`

If ports don't match → **test fails immediately**, not at runtime.

---

## Port Alignment Table (Current State)

| Service | Registry Port | Compose Port Pattern | .env.smoke | Status |
|---------|---------------|----------------------|------------|--------|
| postgres | 5432 | `${POSTGRES_PORT:-5432}:5432` \| `POSTGRES_PORT=5432` | ✅ Aligned |
| redis | 6379 | `${REDIS_PORT:-6379}:6379` \| `REDIS_PORT=6379` | ✅ Aligned |
| qdrant | 6333 | `${QDRANT_PORT:-6333}:6333` \| `QDRANT_PORT=6333` | ✅ Aligned |
| conport | 3004 | `${CONPORT_PORT:-3004}:3004` \| `CONPORT_PORT=3004` | ✅ Aligned |
| dopecon-bridge | 3016 | `${DOPECON_BRIDGE_PORT:-3016}:3016` \| `DOPECON_BRIDGE_PORT=3016` | ✅ Aligned |
| task-orchestrator | 8000 | `${TASK_ORCHESTRATOR_PORT:-8000}:8000` \| `TASK_ORCHESTRATOR_PORT=8000` | ✅ Aligned |

**Drift Detection:** `python tools/ports_health_audit.py --mode static --explain-drift`
**Current Status:** ✅ No drift detected

---

## Health Endpoint Standardization

### BEFORE G31
- Health endpoints scattered across service code
- No validation that they work
- Inconsistent response formats

### AFTER G31
- Health paths defined in registry
- Validation tool probes each endpoint
- Expected status codes declared
- Timeouts configured per service

### Registry Health Configuration
```yaml
# Example: conport
health_path: /health
health_method: GET
health_timeout_ms: 10000
health_expected_status: 200
```

### Runtime Validation
```bash
$ python tools/ports_health_audit.py --mode runtime --services conport,dopecon-bridge
🏥 Runtime Health Checks
============================================================
✅ conport               UP (HTTP 200)
✅ dopecon-bridge        UP (HTTP 200)
```

---

## Files Changed Summary

### Created
- `services/registry.yaml` - **Truth source**
- `docker-compose.smoke.yml` - Parametric compose
- `.env.smoke` - Generated env (never edit)
- `tools/generate_smoke_env.py` - Generator
- `tools/ports_health_audit.py` - Validator
- `tests/arch/test_registry_compose_alignment.py` - Enforcer
- `docs/engineering/ports_and_registry_truth.md` - Documentation

### Modified
- `.gitignore` - Added `.env.smoke`

### Decommissioned
- None (G31 is additive, doesn't remove old files)
