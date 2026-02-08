# G30 Runtime Errors - Evidence Summary

## Phase 0: Baseline Capture Results

**Timestamp**: 2026-02-01 07:30 UTC
**Method**: Clean docker-compose startup with project name `smoke-g30`
**Status**: All services built successfully, 3/5 services running

## Service Status

| Service | Status | Health | Error |
|---------|--------|--------|-------|
| conport | UP | HEALTHY | None - asyncpg working fine |
| task-orchestrator | UP | UNHEALTHY | Pydantic ValidationError: missing `ts` field |
| dopecon-bridge | UP | UNHEALTHY | Pydantic ValidationError: missing `ts` field |
| postgres | UP | HEALTHY | N/A (infrastructure) |
| redis | UP | HEALTHY | N/A (infrastructure) |

## Error Details

### conport: NO ERROR (Baseline Working)

**Status**: ✅ Healthy
**Finding**: Service starts successfully, asyncpg module present and working

Evidence from logs:
```
conport-1  | 2026-02-01 07:28:57,181 [INFO] conport: Built FastAPI app for conport
conport-1  | 2026-02-01 07:28:57,182 [INFO] conport: Started server process [8]
conport-1  | 2026-02-01 07:28:57,183 [INFO] conport: START service=conport host=0.0.0.0 port=8005 version=1.0.0
conport-1  | 2026-02-01 07:28:57,183 [INFO] conport: ✅ conport - READY
conport-1  | 2026-02-01 07:29:00,702 [INFO] conport: 127.0.0.1:57710 - "GET /health HTTP/1.1" 200
```

**Task Packet Claimed Error**: `ModuleNotFoundError: No module named 'asyncpg'`
**Actual State**: No such error exists - asyncpg is installed and working

---

### task-orchestrator: Pydantic ValidationError

**Status**: ❌ Unhealthy (missing required field in health response)
**File**: `/app/services/task-orchestrator/coordination_api.py:208`
**Function**: `health_check`

**Error**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for HealthResponse
ts
  Field required [type=missing, input_value={'service': 'task-orchest...il', 'dependencies': {}}, input_type=dict]
```

**Root Cause**: Health endpoint returns data missing required `ts` (timestamp) field

**Code Location**: `services/task-orchestrator/coordination_api.py` line 208

**Task Packet Claimed Error**: `SyntaxError: expected '(' at async def ...`
**Actual Error**: Pydantic validation error - wrong error type entirely

---

### dopecon-bridge: Pydantic ValidationError

**Status**: ❌ Unhealthy (missing required field in health response)
**File**: `/app/services/dopecon-bridge/main.py:1811`
**Function**: `health_check`

**Error**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for HealthResponse
ts
  Field required [type=missing, input_value={'service': 'dopecon-brid...il', 'dependencies': {}}, input_type=dict]
```

**Root Cause**: Health endpoint returns data missing required `ts` (timestamp) field

**Code Location**: `services/dopecon-bridge/main.py` line 1811

**Task Packet Claimed Error**: `SyntaxError: non-default argument follows default argument`
**Actual Error**: Pydantic validation error - wrong error type entirely

---

## Critical Findings

### Task Packet Errors vs Actual Errors

| Service | Task Packet Claimed | Actual Finding |
|---------|-------------------|----------------|
| conport | Missing asyncpg module | ✅ No error - working perfectly |
| task-orchestrator | Function def SyntaxError | ❌ Missing `ts` field in health response |
| dopecon-bridge | Argument ordering SyntaxError | ❌ Missing `ts` field in health response |

**Conclusion**: Task packet errors are completely incorrect. All syntax errors described do not exist. The actual issue is a health contract violation where both services are missing the required `ts` (timestamp) field in their HealthResponse model.

## Next Steps

### Fix Required: Add `ts` Field to Health Responses

Both task-orchestrator and dopecon-bridge need to:
1. Add `ts` field to their health check response
2. Set it to current timestamp (ISO format recommended)
3. Match the health contract defined in `tests/contracts/test_health_contract.py`

**Files to modify**:
- `services/task-orchestrator/coordination_api.py` (line ~208)
- `services/dopecon-bridge/main.py` (line ~1811)

**Fix pattern** (add to health response dict):
```python
return HealthResponse(
    service="service-name",
    status="ok",
    ts=datetime.utcnow().isoformat(),  # ADD THIS LINE
    # ... other fields
)
```
