---
id: PHASE2_SECURITY_REVIEW
title: Phase2_Security_Review
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Phase2_Security_Review (explanation) for dopemux documentation and developer
  workflows.
---
# Phase 2: Security Warnings - Manual Review Required

**Date**: 2025-11-18
**Status**: Requires Manual Review

## Summary

During Phase 2 code quality fixes, the automated scanner identified potential hardcoded secrets.
Most of these are **false positives** (e.g., Redis keys, dictionary keys), but require manual verification.

## High Priority (Actual Credentials)

### 1. Database Credentials in Test Files

**File**: `services/serena/v2/intelligence/test_database.py`
- Line 57: `password="serena_test_pass"`
- Line 458: `password="fake_pass"`

**Recommendation**:
- ✅ These are test credentials - acceptable
- Consider using `pytest.fixture` for test DB setup
- Ensure test DB is isolated and not accessible in production

## Medium Priority (Configuration Keys)

### 2. Redis/Cache Keys (False Positives)

These are Redis key names, NOT secrets:

- `services/conport/src/context_portal_mcp/v2/vector_store.py`:
  - Lines 221, 230, 367, 500, 606: `key="workspace_id"` etc.

- `services/serena/v2/untracked_work_storage.py`:
  - Lines 877, 931: `key="untracked_work_config"`

- `services/serena/v2/bridge_adapter.py`:
  - Lines 297, 324: `key="latest_state"`

**Recommendation**: ✅ No action needed - these are configuration keys, not secrets

### 3. Hardcoded Database URL in Config

**File**: `shared/config.py`
- Line 29: `url: str = "postgresql://dopemux_age:dopemux_age_dev_password@..."`

**Recommendation**:
- ⚠️ Replace with environment variable
- Should be: `url: str = os.getenv("DATABASE_URL", "postgresql://...")`

## Low Priority (Metrics/Test Keys)

### 4. Test/Metrics Keys

- `services/adhd_engine/engine.py` Line 1228: `key="cognitive_load_avg"` - Metrics key
- `services/serena/v2/redis_optimizer.py` Line 182: `key = "adhd_perf_test"` - Test key
- `services/task-orchestrator/intelligence/cognitive_load_balancer.py` Lines 374-459: Multiple metrics keys

**Recommendation**: ✅ No action needed - these are metrics/test keys

## Action Items

### Immediate Actions

1. **Fix hardcoded DB URL in shared/config.py**:
   ```python
   # Before
   url: str = "postgresql://dopemux_age:dopemux_age_dev_password@..."

   # After
   url: str = os.getenv(
       "DATABASE_URL",
       "postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph"
   )
   ```

### Best Practices Going Forward

1. **All credentials must use environment variables**:
   - Database URLs → `DATABASE_URL`
   - API keys → `{SERVICE}_API_KEY`
   - Passwords → `{SERVICE}_PASSWORD`

2. **Test credentials**:
   - Use fixtures/factories
   - Keep in dedicated test config files
   - Never commit real credentials even to test files

3. **Redis/Cache keys**:
   - These are safe as string literals
   - Use constants for consistency: `CACHE_KEY_WORKSPACE = "workspace_id"`

## Verification

Run this command to verify no real secrets remain:
```bash
git secrets --scan
```

Or use this grep pattern:
```bash
grep -r "password.*=.*['\"][^'\"]*['\"]" --include="*.py" . | grep -v test_ | grep -v ".venv"
```

---

**Status**: 1 fix required (shared/config.py), rest are false positives
