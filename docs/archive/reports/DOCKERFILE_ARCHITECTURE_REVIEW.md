---
id: DOCKERFILE_ARCHITECTURE_REVIEW
title: Dockerfile_Architecture_Review
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Dockerfile Architecture Review (G34 Option B)

**Date**: 2026-02-01
**Scope**: 3 smoke-enabled services (conport, dopecon-bridge, task-orchestrator)
**Finding**: Architectural pattern inconsistency causing runtime failures

---

## 🔍 Current State Analysis

### Pattern Comparison Matrix

| Aspect | conport | dopecon-bridge | task-orchestrator |
|--------|---------|----------------|-------------------|
| **Build Context** | Repo root (`.`) | Repo root (`.`) | Repo root (`.`) |
| **WORKDIR** | `/app/services/conport` | `/app` ❌ | `/app` ❌ |
| **Code Location** | `/app/services/conport/` | `/app/services/dopecon-bridge/` | `/app/services/task-orchestrator/` |
| **CMD** | `python app.py` ✅ | `python main.py` ❌ | `python server.py` ❌ |
| **Works?** | No (import errors) | No (wrong path) | No (wrong path) |

### Root Cause: Build Context Migration Incomplete

**History**:
- Original design: Each service Dockerfile used `context: ./services/<name>`
- With service-dir context, `COPY . .` copied just that service's code to `/app/`
- **G34 Change**: Fixed context to `.` (repo root) to access `src/`, `pyproject.toml`
- **Side Effect**: `COPY . .` now copies ENTIRE repo, not just service code
- **Impact**: Code is now at `/app/services/<name>/` but CMD expects `/app/`

---

## 🏗️ Design Intent vs Reality

### Conport Pattern (Line-by-Line)

```dockerfile
# Lines 18-21: Install shared dopemux package
COPY pyproject.toml README.md src /app/
RUN pip install --no-cache-dir /app

# Lines 24: Copy legacy shared library
COPY services/shared /app/services/shared

# Lines 27-28: Copy service code and SET WORKDIR ✅
COPY services/conport /app/services/conport
WORKDIR /app/services/conport  # This is KEY!

# Line 52: Run from correct directory ✅
CMD ["python", "app.py"]
```

**Intent**: Multi-layer approach (shared lib + service-specific code)
**Reality**: Shared lib doesn't work (dopemux.logging missing), BUT directory structure is correct

### Dopecon-Bridge Pattern (Broken)

```dockerfile
# Line 13: WORKDIR set to repo root
WORKDIR /app

# Line 22: Copy EVERYTHING from build context (now repo root)
COPY . .  # Copies: src/, services/, pyproject.toml, etc.

# Line 46: Run from wrong directory ❌
CMD ["python", "main.py"]  # Looks for /app/main.py, but it's at /app/services/dopecon-bridge/main.py
```

**Intent**: Simple single-service Dockerfile (legacy design)
**Reality**: Build context changed, CMD path assumption broken

### Task-Orchestrator Pattern (Broken)

```dockerfile
# Line 3: WORKDIR /app
WORKDIR /app

# Line 18: Copy everything
COPY . .  # Now copies entire repo

# Line 37: Run from wrong directory ❌
CMD ["python", "server.py"]  # Looks for /app/server.py, but it's at /app/services/task-orchestrator/server.py
```

**Intent**: Same as dopecon-bridge
**Reality**: Same broken pattern

---

## 🎯 Architectural Decisions Required

### Decision 1: Shared Library Strategy

**Current State**: conport tries to use `dopemux.logging`, `dopemux.runtime`, `dopemux.service_base`
**Problem**: These modules don't exist (empty directories with only `__pycache__`)

**Options**:

**A. Abandon Shared Library (Recommended)**
- ✅ Make each service fully standalone
- ✅ Remove all `from dopemux.X import Y` statements
- ✅ Simplify Dockerfiles - no multi-stage shared lib install
- ✅ Easier to understand, deploy, debug
- ❌ Code duplication for common utilities

**B. Implement Shared Library**
- Create actual modules: `src/dopemux/logging/__init__.py`, etc.
- Ensure all services use same shared utilities
- ❌ Complexity: Versioning, breaking changes across services
- ❌ Tight coupling between services

**Recommendation**: **Option A** - Services should be autonomous. The shared lib was aspirational but never implemented.

### Decision 2: Dockerfile Standard Pattern

**Option A: Service-Specific Context (Original Design)**
```yaml
# docker-compose.yml
conport:
  build:
    context: ./services/conport  # Service directory only
    dockerfile: Dockerfile
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # Just this service's code
CMD ["python", "app.py"]
```

**Pros**: Simple, self-contained, no path confusion
**Cons**: Can't access repo root files (pyproject.toml, src/)

**Option B: Repo Root Context with Explicit Service WORKDIR (Hybrid)**
```yaml
# docker-compose.yml
conport:
  build:
    context: .  # Repo root
    dockerfile: services/conport/Dockerfile
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Copy only what's needed from repo root
COPY services/conport /app/service
WORKDIR /app/service

# Install service dependencies
RUN pip install -r requirements.txt

# Run from service directory
CMD ["python", "app.py"]
```

**Pros**: Access to repo root, clear separation, explicit paths
**Cons**: Slightly more verbose

**Recommendation**: **Option B** - Explicit is better than implicit. Clear WORKDIR prevents path confusion.

---

## ✅ Recommended Standard Pattern

### Template Dockerfile (All Services)

```dockerfile
# ============================================
# Standard Dopemux Service Dockerfile v1.0
# ============================================
FROM python:3.11-slim

# System dependencies (customize per service)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up application directory
WORKDIR /app

# Copy ONLY the service directory from repo root
COPY services/<SERVICE_NAME> /app/service

# Switch to service directory
WORKDIR /app/service

# Install service dependencies
COPY services/<SERVICE_NAME>/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Compile check (catch syntax errors at build time)
RUN python -m compileall -q .

# Import proof (fail build if critical deps missing)
RUN python -c "import fastapi, uvicorn; print('✅ <SERVICE_NAME> deps verified')"

# Security: Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check (adjust port per service)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:<PORT>/health || exit 1

# Expose service port
EXPOSE <PORT>

# Run service (ALWAYS from /app/service directory)
CMD ["python", "<ENTRYPOINT>"]
```

### docker-compose.yml Standard

```yaml
services:
  <service-name>:
    build:
      context: .  # Always repo root
      dockerfile: services/<service-name>/Dockerfile
    environment:
      - PORT=${PORT}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENVIRONMENT=${ENVIRONMENT:-dev}
    ports:
      - "${PORT}:${PORT}"
```

---

## 🔧 Required Fixes (Priority Order)

### Fix 1: Remove Broken Shared Library Imports (conport)

**File**: `services/conport/app.py`

**Remove**:
```python
from dopemux.logging import configure_logging
from dopemux.runtime import lifespan_context, record_crash
from dopemux.service_base import build_app
from dopemux.service_base.logging import startup_banner, shutdown_banner
```

**Replace with**: Standard Python logging + FastAPI patterns

### Fix 2: Align WORKDIR to Code Location (dopecon-bridge)

**File**: `services/dopecon-bridge/Dockerfile`

**Current** (Line 13):
```dockerfile
WORKDIR /app
```

**Fix** (Add after COPY):
```dockerfile
WORKDIR /app
COPY . .  # Now copies entire repo
WORKDIR /app/services/dopecon-bridge  # Navigate to service code
```

**OR Preferred** (Explicit copy):
```dockerfile
WORKDIR /app
COPY services/dopecon-bridge /app/service
WORKDIR /app/service
```

### Fix 3: Align WORKDIR to Code Location (task-orchestrator)

**File**: `services/task-orchestrator/Dockerfile`

**Same fix as dopecon-bridge**:
```dockerfile
WORKDIR /app
COPY services/task-orchestrator /app/service
WORKDIR /app/service
```

---

## 📊 Impact Analysis

### Before Fixes
```
Infrastructure: ✅ UP (postgres, redis, qdrant)
Applications:   ❌ ALL DOWN
  - conport: Import errors (dopemux.logging)
  - dopecon-bridge: Wrong path (/app/main.py)
  - task-orchestrator: Wrong path (/app/server.py)
```

### After Fix 2 & 3 (WORKDIR alignment)
```
Infrastructure: ✅ UP
Applications:   🟡 PARTIAL
  - conport: ❌ Still import errors
  - dopecon-bridge: ✅ Should start
  - task-orchestrator: ✅ Should start
```

### After Fix 1 (Remove dopemux imports)
```
Infrastructure: ✅ UP
Applications:   ✅ ALL UP (expected)
  - conport: ✅ Standalone
  - dopecon-bridge: ✅ Running
  - task-orchestrator: ✅ Running
```

---

## 🚀 Implementation Plan

### Phase 1: Quick Wins (WORKDIR fixes)
1. Fix dopecon-bridge Dockerfile (add WORKDIR line)
2. Fix task-orchestrator Dockerfile (add WORKDIR line)
3. Rebuild and test

**Expected Result**: 2/3 services working

### Phase 2: Conport Standalone
1. Analyze conport's dopemux imports usage
2. Replace with standard Python equivalents
3. Update app.py to be standalone
4. Rebuild and test

**Expected Result**: 3/3 services working

### Phase 3: Standardization (Future)
1. Create Dockerfile template
2. Migrate all 3 services to standard pattern
3. Document pattern in `docs/engineering/dockerfile-standard.md`

---

## 📋 Acceptance Criteria

**Phase 1 Success**:
- [ ] dopecon-bridge container stays running (not restarting)
- [ ] task-orchestrator container stays running
- [ ] Health endpoints respond (200 OK)

**Phase 2 Success**:
- [ ] conport container stays running
- [ ] No import errors in logs
- [ ] All 3 services respond to health checks

**Phase 3 Success**:
- [ ] All Dockerfiles follow template pattern
- [ ] Documentation exists for standard
- [ ] Zero path-related or import-related errors

---

**Recommendation**: Execute Phase 1 immediately (surgical WORKDIR fixes), then Phase 2 (conport standalone). Phase 3 can be deferred to future cleanup.
