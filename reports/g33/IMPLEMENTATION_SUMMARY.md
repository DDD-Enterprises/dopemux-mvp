# G33 Implementation Summary

**Task**: Unified Service Env Defaults + Drift Scanner  
**Date**: 2026-02-01  
**Status**: ✅ Phases 0-3 Complete, Phase 4 Pending

---

## Phase 0: Inventory ✅ COMPLETE

###0.1 Smoke-enabled services identified

**Total**: 6 services (3 Python, 3 infrastructure)

| Service | Type | Port | Health |
|---------|------|------|---------|
| postgres | Infrastructure | 5432 | pg_isready |
| redis | Infrastructure | 6379 | redis-cli |
| qdrant | Infrastructure | 6333 | / |
| **conport** | Python/MCP | 3004 | /health |
| **dopecon-bridge** | Python/Coordination | 3016 | /health |
| **task-orchestrator** | Python/Cognitive | 8000 | /health |

**Deliverables**:
- ✅ `reports/g33/smoke_services.json`
- ✅ `reports/g33/smoke_services.md`

### 0.2 Environment parsing matrix

**Python services env support**:

| Service | HOST | PORT | LOG_LEVEL | Notes |
|---------|------|------|-----------|-------|
| conport | ❌ | ❌ | ❌ | Uses dopemux.settings.ConPortSettings |
| dopecon-bridge | ❌ | ✅ | ❌ | Uses PORT_BASE + 16 pattern |
| task-orchestrator | ❌ | ❌ | ❌ | Has sys.path.insert violation |

**Deliverables**:
- ✅ `reports/g33/env_support_matrix.md`

---

## Phase 1: Contract Definition ✅ COMPLETE

**Deliverable**: ✅ `docs/engineering/service_env_contract.md`

**Contract summary**:
- **Required**: HOST (default: `0.0.0.0`), PORT (default: registry port), LOG_LEVEL (default: `info`)
- **Optional**: BASE_URL (for bridge/client services only)
- **Behavior**: Missing env must not crash; invalid env should fail fast
- **Exceptions**: Can be documented in `services/registry.yaml` with `env_contract_exceptions`

---

## Phase 2: Drift Scanner Tool ✅ COMPLETE

**Deliverable**: ✅ `tools/env_drift_scan.py`

**Features**:
- Scans all smoke-enabled Python services
- Checks for required env var support (HOST, PORT, LOG_LEVEL)
- Detects risky patterns (os.environ[] without default, sys.path.insert)
- Outputs JSON report and console table
- Exit code 1 if drift detected

**Usage**:
```bash
python tools/env_drift_scan.py          # Full report
python tools/env_drift_scan.py --json   # JSON only
python tools/env_drift_scan.py --verbose  # Detailed
```

**Current scan results**:
- ✅ Scanned: 3 services
- ❌ Violations: 3 services (100%)
- ✅ Errors: 0

**Violations detected**:
1. **conport**: Missing HOST, PORT, LOG_LEVEL
2. **dopecon-bridge**: Missing HOST, LOG_LEVEL
3. **task-orchestrator**: Missing HOST, PORT, LOG_LEVEL + sys.path.insert violation

**Deliverables**:
- ✅ `tools/env_drift_scan.py`
- ✅ `reports/g33/env_drift_report.json`

---

## Phase 3: Architecture Test ✅ COMPLETE

**Deliverable**: ✅ `tests/arch/test_service_env_contract.py`

**Test coverage**:
- ✅ Parametrized tests for each smoke-enabled service
- ✅ Required env var support validation
- ✅ Config source detection
- ✅ Risky pattern detection (sys.path.insert)
- ✅ Meta-tests (all services scanned, no errors)
- ✅ Documentation existence tests

**Current test results**:
```
15 tests total: 11 passed, 4 failed
```

**Failing tests**:
- `test_service_supports_required_env_vars[conport]` - Missing HOST, PORT, LOG_LEVEL
- `test_service_supports_required_env_vars[dopecon-bridge]` - Missing HOST, LOG_LEVEL
- `test_service_supports_required_env_vars[task-orchestrator]` - Missing HOST, PORT, LOG_LEVEL
- `test_service_no_risky_patterns[task-orchestrator]` - Uses sys.path.insert

**Running tests**:
```bash
pytest tests/arch/test_service_env_contract.py -v
```

---

## Phase 4: Service Fixes 🔨 PENDING

**Required fixes**:

### 1. conport (Missing: HOST, PORT, LOG_LEVEL)
- **File to edit**: Find or create `config.py` or update `app.py`
- **Changes**: Add env var support with defaults
- **Default values**: HOST=`0.0.0.0`, PORT=`3004`, LOG_LEVEL=`info`

### 2. dopecon-bridge (Missing: HOST, LOG_LEVEL)
- **File to edit**: `services/dopecon-bridge/main.py`
- **Changes**: Add HOST and LOG_LEVEL support
- **Default values**: HOST=`0.0.0.0`, LOG_LEVEL=`info`
- **Note**: PORT already supported via PORT_BASE pattern

### 3. task-orchestrator (Missing: HOST, PORT, LOG_LEVEL + sys.path.insert)
- **File to edit**: `services/task-orchestrator/server.py`
- **Changes**: 
  - Add env var support with defaults
  - Remove `sys.path.insert` at line 32 (use proper PYTHONPATH or package structure)
- **Default values**: HOST=`0.0.0.0`, PORT=`8000`, LOG_LEVEL=`info`

**Scope constraints**:
- ✅ Minimal changes only (startup/config files)
- ❌ No business logic refactoring
- ❌ No sys.path.insert usage anywhere

---

## Phase 5: Validation 🔬 NOT STARTED

**Checklist** (to be run after Phase 4):
- [ ] `python -m compileall services tools tests` - No syntax errors
- [ ] `pytest -q tests/arch/test_service_env_contract.py` - All tests pass
- [ ] `python tools/env_drift_scan.py` - No violations
- [ ] (Optional) Runtime validation: `docker compose -f docker-compose.smoke.yml up -d --build`
- [ ] (Optional) `python tools/ports_health_audit.py --mode runtime`

---

## Files Created/Modified

**Created**:
- `docs/engineering/service_env_contract.md` (7.2KB) - Canonical contract definition
- `tools/env_drift_scan.py` (12.7KB) - Drift detection tool
- `tests/arch/test_service_env_contract.py` (8.0KB) - Enforcement tests
- `reports/g33/smoke_services.json` - Service inventory (JSON)
- `reports/g33/smoke_services.md` - Service inventory (markdown table)
- `reports/g33/env_support_matrix.md` - Env support status matrix
- `reports/g33/env_drift_report.json` - Full scan results
- `reports/g33/IMPLEMENTATION_SUMMARY.md` - This file

**Modified**:
- None yet (Phase 4 pending)

---

## Summary Status

| Phase | Status | Deliverables | Notes |
|-------|--------|--------------|-------|
| 0.1 Inventory | ✅ | smoke_services.json/md | 6 services, 3 Python |
| 0.2 Env Matrix | ✅ | env_support_matrix.md | All services missing LOG_LEVEL |
| 1 Contract | ✅ | service_env_contract.md | Canonical definition complete |
| 2 Scanner | ✅ | env_drift_scan.py | Tool working, 3 violations found |
| 3 Arch Tests | ✅ | test_service_env_contract.py | 4/15 tests failing as expected |
| 4 Fixes | 🔨 PENDING | Service configs | Awaiting approval to proceed |
| 5 Validation | ⏳ BLOCKED | N/A | Blocked on Phase 4 |

**Exit codes**:
- Drift scanner: Returns 1 (violations detected)
- Arch tests: Returns 1 (4 tests failing)
- Expected after Phase 4: Both return 0

**Compliance rate**: 0% (0/3 services compliant)  
**Target after Phase 4**: 100% (3/3 services compliant)

---

## Recommendations for Phase 4

**Approach**: Minimal config-only changes

1. **For each service**, create or update `config.py`:
   ```python
   import os
   import logging
   
   HOST = os.getenv("HOST", "0.0.0.0")
   PORT = int(os.getenv("PORT", "3004"))  # Use registry port
   LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
   
   logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
   ```

2. **Update entry point** to use config:
   ```python
   from config import HOST, PORT
   
   uvicorn.run(app, host=HOST, port=PORT)
   ```

3. **For task-orchestrator**: Remove line 32 `sys.path.insert(0, str(project_root))`
   - Add parent to PYTHONPATH in Docker/compose instead
   - Or use relative imports

**Estimated effort**: 15-30 minutes per service = ~1 hour total

---

## Questions for Implementer

1. **Proceed with Phase 4 fixes?** (Yes/No/Modify)
2. **Alternative approach?** (Document exceptions in registry instead)
3. **Skip runtime validation?** (Phase 5 optional if confident in fixes)

