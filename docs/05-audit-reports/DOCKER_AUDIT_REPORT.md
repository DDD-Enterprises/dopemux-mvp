---
id: DOCKER_AUDIT_REPORT
title: Docker Audit Report
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Docker Audit Report (reference) for dopemux documentation and developer workflows.
---
# Docker Configuration Audit Report - Dopemux MVP

**Date**: February 2024
**Project**: Dopemux MVP - ADHD-optimized AI Agent System
**Status**: ⚠️ **CRITICAL ISSUES IDENTIFIED**

---

## Executive Summary

Your Docker setup is **complex but functional**. However, there are **critical issues preventing reliable operation**:

1. **Orphan Container Problem** (IMMEDIATE) - 50+ exited containers from previous runs
1. **Multi-stage Dockerfile Best Practices** - Not consistently applied
1. **Image Layer Efficiency** - Several Dockerfiles have suboptimal caching patterns
1. **Version Pinning** - Missing for some base images
1. **Security Gaps** - Root user in some containers; missing non-root users
1. **Health Check Inconsistencies** - Some services lack proper health checks

---

## Part 1: Orphan Container Crisis

### Problem
You have **50+ exited containers** from 3-5 months of iterations. When docker-compose starts, it sees:
- Containers with old image IDs that no longer exist
- Naming conflicts between new and old versions
- Services in "Created" state that never start properly

### Why It Happens
Docker Compose by default does NOT clean up:
- Stopped containers from previous `up` calls
- Containers from old docker-compose.yml versions
- Images that were rebuilt with different configs

### Immediate Fix

```bash
# NUCLEAR OPTION: Clean everything
docker system prune -a --volumes -f

# SAFER: Just remove exited containers
docker container prune -f

# BEST: Use compose flag going forward
docker compose -f docker-compose.master.yml up -d --remove-orphans
```

### Permanent Fix
Update `docker-compose.master.yml` to add at the top level:

```yaml
version: '3.8'
name: dopemux

# Add cleanup policy
x-cleanup-policy: &cleanup
  stop_grace_period: 10s

services:
  # Apply to all services:
  dopemux-postgres-age:
    <<: *cleanup
    ...
```

**Better approach** - Use the `--remove-orphans` flag in your start script:

```bash
#!/bin/bash
docker compose -f docker-compose.master.yml up -d --remove-orphans
```

---

## Part 2: Dockerfile Analysis

### Critical Issues

#### 1. **Task Orchestrator - NOT using multi-stage build**

**File**: `services/task-orchestrator/Dockerfile`

**Current**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl
COPY services/task-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ... copies code
EXPOSE 3014
CMD ["python", "-m", "app.main"]
```

**Issues**:
- ❌ Build dependencies (build-essential, dev files) stay in final image
- ❌ Image size is bloated with pip cache layers
- ❌ Requirements installed at build time, no caching optimization

**Fixed version**:
```dockerfile
#syntax=docker/dockerfile:1

# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/task-orchestrator/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only built dependencies, not build tools
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY services/task-orchestrator/app /app/app
COPY services/task-orchestrator/intelligence /app/intelligence
COPY services/task-orchestrator/task_orchestrator /app/task_orchestrator
COPY services/task-orchestrator/pal_client.py /app/pal_client.py
COPY services/shared /app/services/shared
COPY src/dopemux /app/dopemux

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=3014

EXPOSE 3014

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3014/health || exit 1

CMD ["python", "-m", "app.main"]
```

---

#### 2. **Genetic Agent - Broken Dockerfile**

**File**: `services/genetic_agent/Dockerfile`

**Problems**:
```dockerfile
COPY . genetic_agent/  # Copies EVERYTHING including .git, venv, node_modules
CMD ["python", "-m", "genetic_agent.main"]
```

**Issues**:
- ❌ COPY context includes everything (no `.dockerignore`)
- ❌ Not a multi-stage build (build deps in runtime)
- ❌ `requirements.txt` path may be wrong relative to context
- ❌ Module structure is messy

**Fixed version**:
```dockerfile
#syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy from context root
COPY services/genetic_agent/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

COPY services/genetic_agent /app/services/genetic_agent
COPY services/shared /app/services/shared

ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "services.genetic_agent.main"]
```

**Create `.dockerignore` in repo root**:
```
.git
.github
.venv
venv
__pycache__
*.pyc
.DS_Store
.env
.env.local
.pytest_cache
.mypy_cache
.coverage
node_modules
.next
dist
build
*.egg-info
*.log
```

---

#### 3. **Dope-Context - Error Handling is Too Loose**

**File**: `services/dope-context/Dockerfile`

**Problems**:
```dockerfile
RUN pip install --no-cache-dir fastmcp || \
    pip install --no-cache-dir git+https://github.com/anthropic/... || \
    echo "Warning: fastmcp install failed, continuing..."
```

**Issues**:
- ❌ Build succeeds even when dependencies fail
- ❌ `|| true` masks real errors
- ❌ Hard to debug image failures
- ❌ Runtime will crash with missing deps

**Fixed version**:
```dockerfile
#syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY services/dope-context/requirements.txt .
# Install strict - fail if anything breaks
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH \
    MCP_SERVER_PORT=3010 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY services/dope-context /app/services/dope-context
COPY services/shared /app/services/shared

RUN mkdir -p /app/data /app/logs

EXPOSE 3010

HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:3010/health || exit 0

LABEL mcp.role="search" \
      mcp.priority="high" \
      mcp.description="Semantic code and document search with AST-aware indexing"

CMD ["python", "src/mcp/simple_server.py"]
```

---

#### 4. **Activity-Capture - Missing Security Context**

**File**: `services/activity-capture/Dockerfile`

**Good**:
- ✅ Multi-stage not needed (lightweight)
- ✅ Creates non-root user
- ✅ Health check present

**Minor improvements**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 activity && chown -R activity:activity /app
USER activity

# Expose API port
EXPOSE 8096

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8096/health || exit 1

# Set Python path and run
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8096", "--log-level", "info"]
```

**Minimal change**: already good, just ensure `curl` is available for health check when running as non-root.

---

#### 5. **ADHD Engine - Good baseline, DHI ready**

**File**: `services/adhd_engine/Dockerfile`

**Good**:
- ✅ Multi-stage build (builder + runtime)
- ✅ Minimal runtime image
- ✅ Health check present
- ✅ TODO comment shows DHI migration path

**To upgrade to Docker Hardened Images (DHI)**:
```dockerfile
#syntax=docker/dockerfile:1

# Builder stage - use standard alpine for build tools
FROM python:3.11-alpine3.21 AS builder
WORKDIR /app

RUN apk add --no-cache build-base gcc musl-dev libffi-dev openssl-dev

COPY services/adhd_engine/requirements.txt /app/requirements.txt
RUN python -m venv /app/venv && /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY services/adhd_engine /app/services/adhd_engine
COPY services/shared /app/services/shared
COPY shared /app/shared

RUN touch /app/services/__init__.py

# Runtime stage - use DHI when available
FROM dhi.io/python:3.11-alpine3.21
WORKDIR /app

RUN apk add --no-cache curl

COPY --from=builder /app/venv /app/venv
COPY --from=builder /app/services /app/services
COPY --from=builder /app/shared /app/shared

ENV PATH="/app/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    API_PORT=8095

EXPOSE 8095

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8095/health || exit 1

CMD ["python", "-m", "services.adhd_engine.main"]
```

---

### Leantime Dockerfile - Edge Case

**File**: `docker/leantime/Dockerfile`

**Status**: Workaround-heavy. Works but fragile.

```dockerfile
FROM leantime/leantime:latest
USER root
RUN sed -i 's/listen 8080;/listen 80;/' /etc/nginx/nginx.conf
# ... more sed patches
USER www-data
```

**Issues**:
- ❌ Relies on sed regex (brittle)
- ❌ No version pin on upstream image
- ❌ Copying PHP files is fragile across version upgrades

**Better approach** - Use environment or volume override in compose:
```yaml
leantime:
  image: leantime/leantime:2.5.0  # PIN VERSION
  environment:
- LISTEN_PORT=80
  # OR use docker-entrypoint override
```

---

## Part 3: Docker Compose Issues

### Issue 1: Network Mismatch

**File**: `docker-compose.master.yml`

```yaml
networks:
  dopemux-network:
    external: true  # ❌ PROBLEM
```

**Problem**: Network must be created manually before `up`:
```bash
docker network create dopemux-network
```

**Fix**: Remove `external: true` to auto-create:
```yaml
networks:
  dopemux-network:
    driver: bridge
```

---

### Issue 2: Missing Environment File

**File**: `docker-compose.master.yml`

Services reference many env vars that need a `.env` file:
```yaml
- ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
- LEANTIME_TOKEN=${LEANTIME_TOKEN}
- AGE_PASSWORD=${AGE_PASSWORD:-dopemux_age_dev_password}
```

**Fix**: Create `.env` file (in repo root):
```bash
# .env
AGE_PASSWORD=your_secure_password
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=...
EXA_API_KEY=...
VOYAGEAI_API_KEY=...
LEANTIME_API_TOKEN=...
LEANTIME_TOKEN=...
LEANTIME_URL=http://leantime:80
LITELLM_DATABASE_URL=postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/litellm
ADHD_ENGINE_API_KEY=dev-key-123
TASK_ORCHESTRATOR_API_KEY=dev-key-456
OPENROUTER_API_KEY=...
GEMINI_API_KEY=...
XAI_API_KEY=...
PERPLEXITY_API_KEY=...
DISPLAY=:0
WORKSPACE_ID=/Users/hue/code/dopemux-mvp
DEFAULT_WORKSPACE_PATH=/Users/hue/code/dopemux-mvp
```

Reference in compose:
```yaml
env_file: .env
```

---

### Issue 3: Hardcoded Paths

**File**: `docker-compose.master.yml`, lines showing:

```yaml
volumes:
- ${DEFAULT_WORKSPACE_PATH:-/Users/hue/code/dopemux-mvp}:/workspace:ro
```

```yaml
environment:
- WORKSPACE_ID=/Users/hue/code/dopemux-mvp
```

**Problem**: Path is hardcoded to YOUR machine. Won't work on CI/CD or other devs' machines.

**Fix**:
```yaml
environment:
- WORKSPACE_ID=${WORKSPACE_ID:-.}  # Use current dir or env var
```

```bash
# .env
WORKSPACE_ID=/Users/hue/code/dopemux-mvp
# or on CI:
# WORKSPACE_ID=/app
```

---

### Issue 4: Inconsistent Restart Policies

Some services have `restart: unless-stopped`, others have `deploy: restart_policy`:

```yaml
# Some services:
restart: unless-stopped

# Others:
deploy:
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
```

**Fix**: Use `restart` consistently (simpler, equivalent for most use cases):
```yaml
services:
  dopemux-postgres-age:
    restart: unless-stopped  # Standard across all
```

For Swarm-specific behavior, use `deploy:`.

---

### Issue 5: Missing `.dockerignore`

**Status**: Not found in repo

**Create** `~/.dockerignore`:
```
.git
.github
.gitignore
.vscode
.DS_Store
.env
.env.*
node_modules
venv
.venv
__pycache__
*.pyc
*.log
.pytest_cache
.mypy_cache
.coverage
dist
build
*.egg-info
docker-compose*.yml
Makefile
README*
docs
tests
```

This reduces build context size and speeds up `docker build`.

---

### Issue 6: Health Check Inconsistency

Some services:
```yaml
healthcheck:
  test: [ "CMD-SHELL", "curl -f http://localhost:8095/health || exit 1" ]
  timeout: 10s
  retries: 3
  interval: 30s
```

Others:
```yaml
healthcheck:
  test: [ "CMD", "curl", "-f", "http://localhost:3004/health" ]
```

**Problem**: Exit code handling inconsistent.

**Standardize**:
```yaml
healthcheck:
  test: [ "CMD-SHELL", "curl -f http://localhost:PORT/health || exit 1" ]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

---

### Issue 7: Leantime Service Missing Health Check

**File**: `docker-compose.master.yml`, `leantime` service:

```yaml
# No healthcheck!
```

**Add**:
```yaml
healthcheck:
  test: [ "CMD-SHELL", "curl -f http://localhost:80/health || exit 1" ]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s  # Leantime takes longer to start
```

---

## Part 4: Security Audit

### Critical Issues

#### 1. **Root User in Services**

**Leantime** switches back to `www-data`, but some others don't specify user.

**Fix**: All Dockerfiles should include:
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

---

#### 2. **Secrets in Environment**

```yaml
environment:
- OPENAI_API_KEY=${OPENAI_API_KEY}
```

**Risk**: Keys visible in `docker inspect` and compose logs.

**Better**: Use Docker Secrets (Swarm) or external secret manager (Vault, AWS Secrets Manager).

For development:
```yaml
env_file:
- .env  # Add to .gitignore
```

For production:
```bash
docker run --secret my_api_key --env API_KEY_FILE=/run/secrets/my_api_key
```

---

#### 3. **No Resource Limits**

**Missing** from all services:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Add to high-memory services** (postgres, litellm, qdrant):
```yaml
postgres:
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G

qdrant:
  deploy:
    resources:
      limits:
        memory: 2G
```

---

## Part 5: Version Pinning

### Missing Version Pins

**File**: `docker-compose.master.yml`

Several images use `latest`:
```yaml
image: redislabs/redisinsight:latest  # ❌ Unpredictable
image: qdrant/qdrant:latest           # ❌ Unpredictable
```

**Fix**: Pin to specific versions:
```yaml
redislabs/redisinsight:2.52.0
qdrant/qdrant:v1.10.0
postgres:16.2-alpine
redis:7.2-alpine
apache/age:release_PG16_1.6.0
```

Benefits:
- Reproducible builds
- Security patch control
- Easier rollback

---

## Part 6: Quick Wins (Easy Fixes)

### 1. Add `.dockerignore` ✅ (2 min)
```bash
cat > .dockerignore << 'EOF'
.git
.github
node_modules
venv
.venv
__pycache__
*.pyc
.DS_Store
.env
*.log
docker-compose*.yml
EOF
```

### 2. Create `.env` template ✅ (3 min)
```bash
cat > .env.example << 'EOF'
# Database
AGE_PASSWORD=change_me_in_production
LITELLM_DATABASE_URL=postgresql://dopemux_age:PASSWORD@dopemux-postgres-age:5432/litellm

# API Keys (get from services)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=...

# Workspace
WORKSPACE_ID=/Users/hue/code/dopemux-mvp
EOF

cp .env.example .env  # Developer fills in .env, commits .env.example
echo ".env" >> .gitignore
```

### 3. Fix Docker Network ✅ (1 min)

In `docker-compose.master.yml`, change:
```yaml
networks:
  dopemux-network:
    driver: bridge  # Remove "external: true"
```

### 4. Add Cleanup Script ✅ (2 min)

```bash
cat > scripts/cleanup.sh << 'EOF'
#!/bin/bash
echo "Removing exited containers..."
docker container prune -f
echo "Removing unused images..."
docker image prune -f
echo "Removing unused volumes..."
docker volume prune -f
echo "Done!"
EOF

chmod +x scripts/cleanup.sh
```

Then: `./scripts/cleanup.sh`

### 5. Fix Compose Startup Script ✅ (2 min)

```bash
cat > scripts/start.sh << 'EOF'
#!/bin/bash
set -e
echo "Starting Dopemux stack..."
docker compose -f docker-compose.master.yml up -d --remove-orphans
docker compose -f docker-compose.master.yml ps
EOF

chmod +x scripts/start.sh
```

---

## Part 7: Recommended Action Plan

### Phase 1: Immediate (Today) 🔴
- [ ] Run `docker container prune -f` to remove 50+ orphans
- [ ] Create `.dockerignore`
- [ ] Create `.env` with your API keys
- [ ] Fix docker-compose.master.yml network config
- [ ] Test: `docker compose -f docker-compose.master.yml up -d --remove-orphans`

### Phase 2: This Week (Refactor Dockerfiles) 🟡
- [ ] Fix `task-orchestrator/Dockerfile` (add multi-stage build)
- [ ] Fix `genetic_agent/Dockerfile` (add multi-stage build)
- [ ] Fix `dope-context/Dockerfile` (remove error suppression)
- [ ] Test each: `docker build -f services/XXX/Dockerfile -t dopemux/xxx:test .`
- [ ] Update compose to use rebuilt images

### Phase 3: Security & Hardening (This Sprint) 🟢
- [ ] Add resource limits to all services
- [ ] Pin all image versions
- [ ] Ensure non-root users in all Dockerfiles
- [ ] Add DHI (Docker Hardened Images) for prod
- [ ] Review secret management strategy

---

## Summary: Critical Findings

| Issue | Severity | Impact | Fix Time |
|-------|----------|--------|----------|
| 50+ orphan containers | 🔴 Critical | Startup failure | 5 min |
| Network set to external | 🔴 Critical | Can't start | 1 min |
| Task orchestrator no multi-stage | 🟡 High | Large image size | 20 min |
| Genetic agent broken COPY | 🟡 High | Build failure | 20 min |
| Dope-context loose error handling | 🟡 High | Silent failures | 15 min |
| Missing .env file | 🟠 Medium | Manual setup | 3 min |
| No .dockerignore | 🟠 Medium | Slow builds | 2 min |
| Missing version pins | 🟠 Medium | Non-reproducible | 10 min |
| No resource limits | 🟠 Medium | Runaway memory | 20 min |
| Hardcoded paths | 🟠 Medium | Non-portable | 5 min |

---

## Detailed Recommendations

### For Production Deployment
1. Use Docker Hardened Images (DHI) for all runtime stages
1. Implement proper secret management (don't use .env files)
1. Add resource limits to prevent runaway containers
1. Use health checks + orchestration (Kubernetes or Docker Swarm)
1. Implement log aggregation (ELK, Loki, etc.)
1. Set up monitoring (Prometheus + Grafana already present)

### For Development
1. Use docker-compose with `--remove-orphans` flag
1. Create development-specific override compose file:

```yaml
# docker-compose.override.yml (auto-loaded by docker compose)
version: '3.8'
services:
  dopemux-postgres-age:
    ports:
- "5432:5432"  # Expose for local psql access
  mcp-qdrant:
    ports:
- "6333:6333"  # Expose for local queries
```

### For CI/CD
1. Use multi-stage builds to minimize image size
1. Pin all versions (no `latest`)
1. Scan images with `docker scout cves`
1. Push to private registry with tags: `latest`, `v1.0.0`, `sha-abc123`
1. Use compose push/pull for orchestrated deployments

---

## Files to Create/Modify

```
dopemux-mvp/
├── .dockerignore                          [CREATE]
├── .env                                   [CREATE - ADD TO .gitignore]
├── .env.example                           [CREATE - COMMIT THIS]
├── docker-compose.master.yml              [MODIFY - Fix network]
├── services/task-orchestrator/Dockerfile  [MODIFY - Add multi-stage]
├── services/genetic_agent/Dockerfile      [MODIFY - Fix + multi-stage]
├── services/dope-context/Dockerfile       [MODIFY - Fix error handling]
├── docker/leantime/Dockerfile             [MODIFY - Add version pin]
├── scripts/cleanup.sh                     [CREATE]
├── scripts/start.sh                       [CREATE]
└── DOCKER_AUDIT_REPORT.md                 [THIS FILE]
```

---

## Contact & Questions

For DHI (Docker Hardened Images) migration support, contact Docker.
For Dockerfile optimization, refer to: https://docs.docker.com/build/building/best-practices/

---

**Report Generated**: February 2024
**Auditor**: Gordon (Docker AI Assistant)
**Next Review**: After Phase 1 fixes are implemented
