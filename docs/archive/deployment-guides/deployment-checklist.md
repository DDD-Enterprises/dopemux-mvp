---
id: DEPLOYMENT-CHECKLIST
title: Deployment Checklist
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Deployment Checklist (explanation) for dopemux documentation and developer
  workflows.
---
# Deployment Checklist - Security Fixes
**Status**: ✅ Ready for immediate deployment
**Critical Fixes**: All applied and tested
**Risk Level**: LOW (backwards compatible changes)

---

## Pre-Deployment Checklist

### 1. Environment Configuration (5 minutes)

```bash
# Create production .env file
cp .env.example .env

# Edit with production values
nano .env

# Minimum required for security:
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ADHD_ENGINE_API_KEY=<generate-secure-random-key>
SERENA_DB_PASSWORD=<your-secure-db-password>
```

**Generate Secure API Key**:
```bash
# Linux/Mac:
openssl rand -hex 32

# Or Python:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 2. Local Testing (10 minutes)

**Test ADHD Engine with Auth**:
```bash
cd services/adhd_engine

# Start service
python main.py
# Should start on port 8000

# Test WITHOUT API key (should fail in production mode)
curl http://localhost:8000/api/v1/energy-level/test-user
# Expected: {"detail": "Missing API key"}

# Test WITH API key (should work)
curl -H "X-API-Key: your-api-key-from-env" \
     http://localhost:8000/api/v1/energy-level/test-user
# Expected: {"energy_level": "MEDIUM", ...}

# Test CORS (browser console or curl with Origin header)
curl -H "Origin: http://localhost:3000" \
     -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/v1/energy-level/test-user
# Should succeed (localhost in whitelist)

curl -H "Origin: http://evil.com" \
     -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/v1/energy-level/test-user
# Should fail CORS check
```

**Test Database Credentials**:
```bash
cd services/serena/v2/intelligence

# Check environment variable is used
export SERENA_DB_PASSWORD="test-from-env"
python3 -c "
import os
import sys
sys.path.insert(0, '.')
from database import DatabaseConfig
config = DatabaseConfig()
assert config.password == 'test-from-env', 'Env var not loaded!'
print('✅ Database credentials from environment')
"
```

---

### 3. Docker Deployment (if using containers)

**Update docker-compose.yml**:
```yaml
services:
  adhd-engine:
    environment:
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - ADHD_ENGINE_API_KEY=${ADHD_ENGINE_API_KEY}
      - SERENA_DB_PASSWORD=${SERENA_DB_PASSWORD}
    # ... rest of config

  gpt-researcher:
    environment:
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    # ... rest of config

  dopecon-bridge:
    environment:
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    # ... rest of config
```

**Deploy**:
```bash
# Build with new code
docker-compose build

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health  # ADHD Engine
curl http://localhost:3016/kg/health  # DopeconBridge
```

---

### 4. Validation Tests (10 minutes)

**Security Validation**:
- [ ] CORS rejects unauthorized origins ✓
- [ ] API key required for protected endpoints ✓
- [ ] Invalid API key returns 403 ✓
- [ ] Database password from environment ✓

**Functionality Validation**:
- [ ] ADHD Engine endpoints respond correctly ✓
- [ ] Energy level tracking works ✓
- [ ] Attention state monitoring works ✓
- [ ] Health checks return healthy ✓

**Performance**:
- [ ] Response times acceptable (< 500ms) ✓
- [ ] No errors in logs ✓
- [ ] Memory usage stable ✓

---

### 5. Monitoring Setup

**Add to monitoring**:
```bash
# Health check endpoints
curl http://localhost:8000/health  # ADHD Engine
curl http://localhost:8080/health  # GPT-Researcher (if running)
curl http://localhost:3016/kg/health  # DopeconBridge

# Check for security errors in logs
docker logs adhd-engine | grep "403\|401\|CORS"
```

**Expected**: No 401/403 errors with valid API keys

---

## Production Deployment Steps

### Step 1: Staging Environment

1. Deploy to staging with production-like config
2. Run all validation tests
3. Monitor for 24 hours
4. Check: No security bypasses, no credential exposure

### Step 2: Production Deployment

1. Update environment variables in production
2. Deploy new code (git pull on code-audit branch)
3. Restart services
4. Run smoke tests
5. Monitor closely for first hour

### Step 3: Post-Deployment

1. Verify all services healthy
2. Check security logs (no unauthorized access)
3. Validate CORS working (browser console, no errors)
4. Monitor performance (no degradation)

---

## Rollback Plan (If Needed)

**If issues arise**:

```bash
# Quick rollback
git checkout main  # Or previous stable branch
docker-compose restart

# Or rollback specific service
git checkout main -- services/adhd_engine/
docker-compose restart adhd-engine
```

**Rollback triggers**:
- Auth blocking legitimate users
- CORS breaking valid frontends
- Database connection failures
- Unexpected 500 errors

---

## Development Mode (No Breaking Changes)

**Good news**: All changes are backwards compatible!

**Development without API key**:
```bash
# Don't set ADHD_ENGINE_API_KEY
# Auth automatically disabled

python services/adhd_engine/main.py
# Works without authentication (development mode)
```

**Development with wildcard CORS** (if needed):
```bash
# Set single wildcard in ALLOWED_ORIGINS
export ALLOWED_ORIGINS="*"
# Splits to ["*"] - works but logged as insecure
```

---

## Security Notes

**What Changed**:
- CORS: Configurable (was hardcoded wildcard)
- Credentials: From environment (was hardcoded)
- Auth: Optional in dev, required in prod (was none)

**What Didn't Change**:
- API contracts (same endpoints, same params)
- Response formats (unchanged)
- Database schemas (unchanged)
- Service dependencies (unchanged)

**Migration Path**: Zero-downtime (backwards compatible)

---

## Success Criteria

**Deployment Successful If**:
- [x] Services start without errors
- [x] Health checks return 200 OK
- [x] API key authentication works
- [x] CORS allows configured origins only
- [x] Database connections work
- [x] No credential exposure in logs

**All criteria validated locally** ✅

---

**READY FOR PRODUCTION DEPLOYMENT** 🚀

**Next**: Deploy to staging, validate, then production
**Then**: Complete optional audit work (Phase 6, 8) + Week 7 plan
