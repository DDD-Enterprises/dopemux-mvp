# G30 Runtime Fixes Summary

## Executive Summary

**Task**: Fix three runtime blockers preventing Smoke Stack services from running
**Result**: ✅ ALL SERVICES HEALTHY

**Critical Discovery**: The task packet error descriptions were completely incorrect. The actual issue was health endpoint contract violations (missing/incorrect fields), not syntax errors or missing modules.

## Services Fixed

### conport
**Baseline Error**: No runtime error - service started successfully  
**Actual Issue**: Health endpoint returned non-compliant response:
- Used `"timestamp"` field instead of required `"ts"` 
- Returned status value `"healthy"` instead of required `"ok"`/`"degraded"`/`"error"`

**Fix Applied**:
- File: `src/dopemux/service_base/health.py`
- Line 68: Changed `timestamp: str` field definition to `ts: str`
- Line 115 & 123: Changed `"timestamp"` keys to `"ts"` in response dictionaries
- Line 113: Changed status `"unavailable"` to `"error"` (contract compliance)
- Line 121: Changed status `"healthy"` to `"ok"` (contract compliance)

**Post-Fix Status**: ✅ HEALTHY  
**Logs**: See `reports/runtime/after_logs_conport.txt`

---

### task-orchestrator
**Baseline Error**: 
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for HealthResponse
ts
  Field required [type=missing, input_value={'status': 'ok', 'servi...cy_status', 'last_check'}}}, input_type=dict]
```

**Actual Issue**: Health endpoint missing required `ts` timestamp field in HealthResponse

**Fix Applied**:
- File: `services/task-orchestrator/coordination_api.py`
- Line 200-204 (normal path): Added `ts=datetime.utcnow().isoformat() + "Z"` to HealthResponse
- Line 208-212 (error path): Added `ts=datetime.utcnow().isoformat() + "Z"` to HealthResponse
- Line 200 (dependencies): Changed `v.dict()` to `v.status` to return string status values per contract

**Post-Fix Status**: ✅ HEALTHY  
**Logs**: See `reports/runtime/after_logs_task_orchestrator.txt`

---

### dopecon-bridge
**Baseline Error**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for HealthResponse
ts
  Field required [type=missing, input_value={'status': 'ok', 'servi... 'ok', 'event_bus': 'ok'}}, input_type=dict]
```

**Actual Issue**: Health endpoint missing required `ts` timestamp field AND dependencies format violation (dict objects instead of strings)

**Fix Applied**:
- File: `services/dopecon-bridge/main.py`
- Line 1803-1807 (normal path): Added `ts=datetime.utcnow().isoformat() + "Z"` to HealthResponse
- Line 1811-1815 (error path): Added `ts=datetime.utcnow().isoformat() + "Z"` to HealthResponse
- Line 1807 (dependencies): Changed `v.dict()` to `v.status` to return string status values per contract

**Post-Fix Status**: ✅ HEALTHY  
**Logs**: See `reports/runtime/after_logs_dopecon_bridge.txt`

---

## Health Audit Results

```
Audit complete in runtime mode. Reports in /Users/hue/code/dopemux-mvp/reports

Runtime Summary:
conport: HEALTHY
task-orchestrator: HEALTHY
dopecon-bridge: HEALTHY
```

**All Three Services**: 
- ✅ Running in Docker (status: Up)
- ✅ Passing Docker health checks
- ✅ Responding to /health endpoint
- ✅ Returning contract-compliant health responses

---

## Changed Files

### Core Fixes
- ✅ `src/dopemux/service_base/health.py` - Fixed health contract compliance for all services using build_app()
  - Changed field name from `timestamp` to `ts`
  - Changed status values from `"healthy"/"unavailable"` to `"ok"/"error"`
  
- ✅ `services/task-orchestrator/coordination_api.py` - Added missing `ts` field and fixed dependencies format
  - Added timestamp to both normal and error response paths
  - Changed dependencies serialization from dict objects to status strings
  
- ✅ `services/dopecon-bridge/main.py` - Added missing `ts` field and fixed dependencies format
  - Added timestamp to both normal and error response paths  
  - Changed dependencies serialization from dict objects to status strings

### Documentation/Evidence
- 📄 `reports/runtime/error_evidence_summary.md` - Complete baseline error analysis
- 📄 `reports/runtime/baseline_ps.txt` - Initial container status
- 📄 `reports/runtime/baseline_logs_*.txt` - Baseline service logs
- 📄 `reports/runtime/final_ps.txt` - Final container status
- 📄 `reports/runtime/final_audit_success.txt` - Final health audit results
- 📄 `reports/runtime/summary.md` - This file

---

## Health Contract Violations Found and Fixed

The health endpoint contract (defined in `tests/contracts/test_health_contract.py` and `src/dopemux/health/models.py`) requires:

### Required Fields
- ✅ `status`: Must be one of `"ok"`, `"degraded"`, `"error"` 
- ✅ `service`: Service name string
- ✅ `ts`: ISO8601 timestamp (NOT `timestamp`)

### Optional Fields
- `version`: Service version string
- `dependencies`: Dict[str, str] mapping dependency names to status strings (NOT dict objects)

### Violations Fixed
1. **Field Name**: `timestamp` → `ts` (service_base)
2. **Status Values**: `"healthy"` → `"ok"`, `"unavailable"` → `"error"` (service_base)
3. **Missing ts**: Added to task-orchestrator and dopecon-bridge
4. **Dependencies Format**: Changed from `{k: v.dict()}` to `{k: v.status}` (task-orchestrator, dopecon-bridge)

---

## Task Packet Errors vs Reality

### What Task Packet Claimed
1. **conport**: `ModuleNotFoundError: No module named 'asyncpg'` ❌ FALSE
2. **task-orchestrator**: `SyntaxError: expected '(' at async def ...` ❌ FALSE  
3. **dopecon-bridge**: `SyntaxError: non-default argument follows default argument` ❌ FALSE

### What Actually Existed
1. **conport**: ✅ Started fine, but health endpoint contract violation (wrong field names and status values)
2. **task-orchestrator**: Missing `ts` field in health response + wrong dependencies format
3. **dopecon-bridge**: Missing `ts` field in health response + wrong dependencies format

**Root Cause Analysis**: The task packet described hypothetical errors that never existed in the actual codebase. The evidence-first approach (Phase 0) was critical to discovering the real issues.

---

## Commands to Verify

```bash
# Start smoke stack
docker compose -p smoke-g30 -f docker-compose.smoke.yml up -d --build

# Check container status
docker compose -p smoke-g30 -f docker-compose.smoke.yml ps

# Expected output: All three services showing "Up X seconds (healthy)"

# Run health audit
python tools/ports_health_audit.py --mode runtime --services conport,task-orchestrator,dopecon-bridge

# Expected output:
# Runtime Summary:
# conport: HEALTHY
# task-orchestrator: HEALTHY
# dopecon-bridge: HEALTHY

# Manual health checks
curl http://localhost:8005/health | jq '.'  # conport
curl http://localhost:3014/health | jq '.'  # task-orchestrator
curl http://localhost:3016/health | jq '.'  # dopecon-bridge

# All should return JSON with: {status, service, ts, ...}
```

---

## Remaining Known Issues

**None** - All smoke stack runtime blockers have been resolved.

### Out of Scope (Not G30 Blockers)
- Docker-compose phantom container state corruption (workaround: use `-p smoke-g30` project name)
- Other services in smoke stack not tested (postgres, redis, etc.)

---

## Technical Notes

### Evidence-First Approach Success
The plan emphasized capturing actual runtime errors before applying fixes. This proved essential:
- Prevented wasted effort fixing non-existent syntax errors
- Identified the real problem: health contract violations
- Allowed minimal, surgical fixes

### Health Contract Source of Truth
Multiple sources define the same contract:
- `src/dopemux/health/models.py`: HealthResponse Pydantic model
- `tests/contracts/test_health_contract.py`: Contract validation tests
- `src/dopemux/health/errors.py`: classify_health_response() validation logic

All fixes aligned with these canonical sources.

### Centralized vs Custom Health Endpoints
- **conport**: Uses `build_app()` from `dopemux.service_base` → auto-generated health endpoint
- **task-orchestrator & dopecon-bridge**: Custom health endpoints importing from `dopemux.health`

Fix to `service_base/health.py` benefits ALL services using `build_app()`, not just conport.

---

## Acceptance Criteria Met

- ✅ All three services show STATUS=Up in docker ps
- ✅ All three services pass Docker health checks (showing "healthy" status)
- ✅ All three services respond to /health endpoint
- ✅ Health audit shows 0 DOWN services, all HEALTHY
- ✅ No runtime errors in container logs
- ✅ Health responses comply with contract (status, service, ts fields)

---

**Completion Time**: 2026-02-01  
**Methodology**: Evidence-based debugging with minimal surgical fixes  
**Result**: 100% success - All smoke stack services operational
