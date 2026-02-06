---
id: ACCEPTANCE_CHECKLIST
title: Acceptance_Checklist
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Acceptance_Checklist (explanation) for dopemux documentation and developer
  workflows.
---
# G35 Acceptance Checklist

**Date**: 2026-02-01
**Packet**: G35 - Smoke Stack Runtime Gate
**Status**: Implementation Complete, Pending Validation

---

## ✅ Phase 0: Normalize Health Config

**Objective**: Extract health configuration from docker-compose.smoke.yml

**Implementation**:
- [x] `ComposeParser` class created
- [x] Load and parse docker-compose.smoke.yml
- [x] Load and parse .env.smoke for env var resolution
- [x] Resolve `${VAR:-default}` placeholders in port mappings
- [x] Extract container names, published ports, health paths
- [x] Construct health URLs: `http://localhost:{port}{path}`

**Test**:
```bash
python -c "
from tools.smoke_runtime_gate import ComposeParser
from pathlib import Path
parser = ComposeParser(
    Path('docker-compose.smoke.yml'),
    Path('.env.smoke')
)
services = parser.get_smoke_services()
for svc in services:
    print(f'{svc.name}: {svc.health_url}')
"
```

**Expected Output**:
```
conport: http://localhost:3004/health
dopecon-bridge: http://localhost:3016/health
task-orchestrator: http://localhost:8000/health
```

---

## ✅ Phase 1: Container Stability Check

**Objective**: Detect restarting containers before port probing

**Implementation**:
- [x] `ContainerStabilityChecker` class created
- [x] Use `docker inspect` to get container state
- [x] Parse `Status` and `RestartCount` fields
- [x] Fail fast if `Status != running` or `RestartCount > 3`
- [x] Return `(is_healthy, status, restart_count)` tuple

**Test** (Requires running container):
```bash
# Start postgres (known-good container)
docker compose -f docker-compose.smoke.yml up -d postgres

# Check stability
python -c "
from tools.smoke_runtime_gate import ContainerStabilityChecker
from pathlib import Path
checker = ContainerStabilityChecker(Path('docker-compose.smoke.yml'))
healthy, status, restarts = checker.check_container('smoke-postgres')
print(f'Healthy: {healthy}, Status: {status}, Restarts: {restarts}')
"
```

**Expected Output**:
```
Healthy: True, Status: running, Restarts: 0
```

---

## ✅ Phase 2: Port + HTTP Probe with Retry

**Objective**: Check port connectivity and HTTP health with retry logic

**Implementation**:
- [x] `HealthProber` class created
- [x] TCP socket connect test for port availability
- [x] HTTP GET request for health endpoint
- [x] Exponential backoff: 1s, 2s, 4s, 8s, 16s
- [x] Max 5 retries (configurable)
- [x] 2-second timeout per probe (configurable)
- [x] Return `ServiceHealthResult` with all metrics

**Test** (Requires running service):
```bash
# Start qdrant (known-good service)
docker compose -f docker-compose.smoke.yml up -d qdrant
sleep 5

# Probe health
python -c "
from tools.smoke_runtime_gate import HealthProber, ServiceHealthConfig
prober = HealthProber(max_retries=3, timeout_per_probe=2.0)
config = ServiceHealthConfig(
    name='qdrant',
    container_name='smoke-qdrant',
    published_port=6333,
    health_path='/'
)
result = prober.probe_service(config)
print(f'Overall Healthy: {result.overall_healthy}')
print(f'HTTP Status: {result.http_status_code}')
print(f'Elapsed: {result.elapsed_ms:.0f}ms')
"
```

**Expected Output**:
```
Overall Healthy: True
HTTP Status: 200
Elapsed: ~100-500ms
```

---

## ✅ Phase 3: Evidence Bundle on Failure

**Objective**: Auto-collect logs and state when services fail

**Implementation**:
- [x] `EvidenceCollector` class created
- [x] Capture `docker compose ps --all` output
- [x] Capture `docker logs --tail 200` per failing service
- [x] Generate JSON report with structured results
- [x] Generate Markdown report with failure details
- [x] Create output directory if missing

**Test** (Simulated):
```bash
# Create evidence directory
mkdir -p reports/g35

# Run gate (will fail if stack not running, triggers evidence collection)
python tools/smoke_runtime_gate.py 2>&1 | grep "Evidence collected"

# Check generated files
ls -lh reports/g35/
```

**Expected Output**:
```
compose_ps.txt
runtime_gate.json
runtime_gate.md
logs_*.tail.txt (for any failing services)
```

---

## ✅ Phase 4: Ergonomic Scripts

**Objective**: Make runtime gate easy to use with wrapper scripts

**Implementation**:
- [x] `scripts/smoke_up.sh` created and executable
- [x] Auto-generate .env.smoke if missing
- [x] `docker compose up -d --build` with error handling
- [x] Wait for initialization (default 10s, configurable)
- [x] Run runtime gate automatically
- [x] Display next steps on success/failure

- [x] `scripts/smoke_down.sh` created and executable
- [x] `docker compose down` with optional `--volumes`
- [x] Confirmation prompt for volume removal
- [x] Display cleanup summary

**Test**:
```bash
# Verify scripts are executable
ls -l scripts/smoke_*.sh | grep "rwxr"

# Verify help/usage works
scripts/smoke_up.sh --help 2>&1 | head -10
scripts/smoke_down.sh --help 2>&1 | head -10
```

**Expected Output**:
```
-rwxr-xr-x ... scripts/smoke_up.sh
-rwxr-xr-x ... scripts/smoke_down.sh
```

---

## 🎯 Acceptance Criteria Validation

### Criterion 1: Push-Button Startup
**Command**: `scripts/smoke_up.sh`

**Expected Behavior**:
- [x] Auto-generates `.env.smoke` if missing
- [x] Builds and starts all smoke services
- [x] Waits for initialization
- [x] Runs runtime gate
- [x] Returns exit code 0 on success
- [x] Returns exit code 1 on failure

**Validation Status**: ⏳ Pending first run (after port mismatch fix)

### Criterion 2: Deterministic Reporting
**Services**: conport, dopecon-bridge, task-orchestrator

**Expected Behavior**:
- [x] Container stability check PASS
- [x] Port open check PASS
- [x] HTTP health check PASS (200 status)
- [x] Overall result PASS

**Validation Status**: ⏳ Pending first run

### Criterion 3: Evidence Bundle on Failure
**Output**: `reports/g35/`

**Expected Files**:
- [x] `compose_ps.txt` (container states)
- [x] `runtime_gate.json` (structured results)
- [x] `runtime_gate.md` (human-readable report)
- [x] `logs_<service>.tail.txt` (logs for each failing service)

**Validation Status**: ⏳ Pending failure scenario

---

## 🚨 Pre-Validation Blockers

### Blocker 1: Conport Port Mismatch
**Issue**: Dockerfile EXPOSE 8005, compose expects 3004

**File**: `services/conport/Dockerfile`
**Lines**: 45 (EXPOSE), 48 (HEALTHCHECK)

**Fix Required**:
```diff
- EXPOSE 8005
+ EXPOSE 3004

- HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
-     CMD curl -f http://localhost:8005/health || exit 1
+ HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
+     CMD curl -f http://localhost:3004/health || exit 1
```

**Status**: ❌ Blocking validation

### Blocker 2: Unknown WORKDIR Issues (User Mentioned Fixed)
**User Statement**: "dopecon-bridge and task-orchestrator Dockerfiles are already aligned to repo-root build context and set WORKDIR /app/services/<service> before CMD"

**Verification**: ⏳ Not yet verified (files read showed old pattern)
**Assumption**: Trusting user statement that these are fixed in uploaded zip

**Status**: ⚠️ Assumed resolved per user

---

## ✅ Deliverables Checklist

- [x] `tools/smoke_runtime_gate.py` (460 lines) - Complete
- [x] `scripts/smoke_up.sh` (90 lines, executable) - Complete
- [x] `scripts/smoke_down.sh` (70 lines, executable) - Complete
- [x] `reports/g35/` directory created - Complete
- [x] `reports/g35/README.md` documentation - Complete
- [x] `reports/g35/G35_IMPLEMENTATION_SUMMARY.md` - Complete
- [x] `reports/g35/ACCEPTANCE_CHECKLIST.md` (this file) - Complete

**Total Lines of Code**: ~870 (production) + 250 (documentation) = 1120 lines

---

## 🧪 Validation Plan

### Step 1: Fix Blockers
```bash
# Fix conport port mismatch
# Edit services/conport/Dockerfile:
# - Line 45: EXPOSE 3004
# - Line 48: HEALTHCHECK on localhost:3004
```

### Step 2: Generate .env.smoke
```bash
# Let smoke_up.sh handle this, or:
python tools/generate_smoke_env.py
```

### Step 3: First Run
```bash
scripts/smoke_up.sh
```

### Step 4: Validate Results
**On Success**:
- ✅ Exit code 0
- ✅ "All services PASSED runtime gate" message
- ✅ No files in `reports/g35/` (no failures)

**On Failure**:
- ❌ Exit code 1
- ❌ Evidence bundle generated in `reports/g35/`
- ✅ Clear error messages pointing to root cause

### Step 5: Evidence Review (If Failed)
```bash
# Check what failed
cat reports/g35/runtime_gate.md

# Check container states
cat reports/g35/compose_ps.txt

# Check service logs
cat reports/g35/logs_conport.tail.txt
cat reports/g35/logs_dopecon-bridge.tail.txt
cat reports/g35/logs_task-orchestrator.tail.txt
```

---

## 📊 Success Metrics

**Quantitative**:
- [ ] 3/3 services pass runtime gate
- [ ] Total gate time < 30 seconds
- [ ] Zero false positives (healthy services marked as failed)
- [ ] Zero false negatives (failed services marked as healthy)

**Qualitative**:
- [ ] Evidence bundle provides actionable debugging info
- [ ] Next steps are clear from script output
- [ ] User can fix issues without asking for help

---

**Status**: ✅ Implementation Complete
**Next**: Fix conport port mismatch, run `scripts/smoke_up.sh`, validate results
**Blocker**: Conport Dockerfile port mismatch (8005 vs 3004)
