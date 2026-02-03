# Conport Port Mismatch Fix

**Date**: 2026-02-01
**Issue**: Dockerfile port didn't match docker-compose configuration
**Status**: ✅ Fixed

---

## Problem

**File**: `services/conport/Dockerfile`
**Lines**: 45 (EXPOSE), 49 (HEALTHCHECK)

**Original**:
```dockerfile
EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1
```

**Expected by docker-compose.smoke.yml**:
```yaml
environment:
  - MCP_SERVER_PORT=${CONPORT_CONTAINER_PORT:-3004}
ports:
  - "${CONPORT_PORT:-3004}:${CONPORT_CONTAINER_PORT:-3004}"
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:${CONPORT_CONTAINER_PORT:-3004}/health || exit 1"]
```

**Impact**: Container would start but health checks would fail, causing restart loops

---

## Solution

**Changed**:
```dockerfile
EXPOSE 3004

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1
```

**Verification**:
```bash
# Check Dockerfile
grep -n "EXPOSE\|HEALTHCHECK" services/conport/Dockerfile

# Expected output:
# 45:EXPOSE 3004
# 48:HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
# 49:    CMD curl -f http://localhost:3004/health || exit 1
```

---

## Next Steps

Ready to validate smoke stack:

```bash
scripts/smoke_up.sh
```

Expected outcome:
- ✅ All 3 services (conport, dopecon-bridge, task-orchestrator) pass runtime gate
- ✅ Exit code 0
- ✅ "All services PASSED runtime gate" message

---

**Fix Applied**: ✅ 2026-02-01
**Ready for Validation**: ✅
