---
id: IMPLEMENTATION_CHECKLIST
title: Implementation Checklist
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Implementation Checklist (reference) for dopemux documentation and developer
  workflows.
---
# Docker Audit Implementation Checklist

## Files Delivered ✅

All files are ready in your repo:

### Documentation (Read These First)
- [x] `DOCKER_AUDIT_REPORT.md` - Full 21KB comprehensive audit
- [x] `DOCKER_FIXES_QUICK_START.md` - 5-min action guide

### Scripts (Executable)
- [x] `scripts/cleanup.sh` - Interactive cleanup tool
- [x] `scripts/start.sh` - Safe startup script

### Configuration
- [x] `.dockerignore` - Build optimization (creates new file)
- [x] `.env.example` - Environment template (creates new file)

### Fixed Dockerfiles
- [x] `services/task-orchestrator/Dockerfile.fixed`
- [x] `services/genetic_agent/Dockerfile.fixed`
- [x] `services/dope-context/Dockerfile.fixed`

---

## Implementation Steps

### Phase 1: Emergency Fix (5 minutes)
These must be done immediately to fix your startup issues.

**Step 1: Clean orphan containers**
```bash
cd ~/code/dopemux-mvp
./scripts/cleanup.sh
```
Expected: Remove 50+ exited containers
Time: 2 min

**Step 2: Create environment file**
```bash
cp .env.example .env
nano .env  # Edit and fill in your API keys
```
Expected: File with your actual API keys
Time: 3 min

**Step 3: Fix docker-compose network**
Edit `docker-compose.master.yml` around line 20:

Find:
```yaml
networks:
  dopemux-network:
    external: true
```

Replace with:
```yaml
networks:
  dopemux-network:
    driver: bridge
```

Expected: Network will auto-create on compose up
Time: 1 min

**Step 4: Test startup**
```bash
cd ~/code/dopemux-mvp
./scripts/start.sh
```

Check status:
```bash
docker compose -f docker-compose.master.yml ps
```

Expected: All services in "running" or "up" state
Time: 3-5 min (actual startup)

---

### Phase 2: Dockerfile Refactoring (This Week)

Once the stack is running, upgrade the problematic Dockerfiles:

**Step 5: Fix Task Orchestrator**
```bash
cd ~/code/dopemux-mvp

# Backup original
cp services/task-orchestrator/Dockerfile services/task-orchestrator/Dockerfile.original

# Apply fix
cp services/task-orchestrator/Dockerfile.fixed services/task-orchestrator/Dockerfile

# Test build
docker compose -f docker-compose.master.yml build task-orchestrator

# Verify
docker compose -f docker-compose.master.yml up -d
docker compose logs task-orchestrator
```

Time: 10 min

**Step 6: Fix Genetic Agent**
```bash
# Backup
cp services/genetic_agent/Dockerfile services/genetic_agent/Dockerfile.original

# Apply fix
cp services/genetic_agent/Dockerfile.fixed services/genetic_agent/Dockerfile

# Test build & start
docker compose -f docker-compose.master.yml build genetic-agent
docker compose up -d
docker compose logs genetic-agent
```

Time: 10 min

**Step 7: Fix Dope Context**
```bash
# Backup
cp services/dope-context/Dockerfile services/dope-context/Dockerfile.original

# Apply fix
cp services/dope-context/Dockerfile.fixed services/dope-context/Dockerfile

# Test build & start
docker compose -f docker-compose.master.yml build dope-context
docker compose up -d
docker compose logs dope-context
```

Time: 10 min

---

### Phase 3: Hardening (This Sprint)

After Dockerfile fixes are verified, implement security improvements:

**Step 8: Add Resource Limits**

Edit `docker-compose.master.yml` and add to high-memory services:

```yaml
dopemux-postgres-age:
  ...
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G

mcp-qdrant:
  ...
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

Time: 15 min

**Step 9: Pin Image Versions**

In `docker-compose.master.yml`, change all `latest` tags:

```yaml
# Find and replace all of these:
image: redis:7-alpine          → redis:7.2-alpine
image: postgres:16-alpine      → postgres:16.2-alpine
image: redislabs/redisinsight:latest  → redislabs/redisinsight:2.52.0
image: qdrant/qdrant:latest    → qdrant/qdrant:v1.10.0
```

Time: 10 min

**Step 10: Add Missing Health Checks**

Find services without health checks (like `leantime`) and add:

```yaml
healthcheck:
  test: [ "CMD-SHELL", "curl -f http://localhost:80 || exit 1" ]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

Time: 10 min

---

## Validation Checklist

### After Phase 1 (Immediate)
- [ ] Ran cleanup.sh successfully
- [ ] Created .env file with API keys
- [ ] Fixed docker-compose.master.yml network
- [ ] `docker compose ps` shows services running
- [ ] Can curl a health endpoint: `curl http://localhost:8095/health`

### After Phase 2 (This Week)
- [ ] task-orchestrator Dockerfile updated and tested
- [ ] genetic_agent Dockerfile updated and tested
- [ ] dope-context Dockerfile updated and tested
- [ ] All services still running after updates
- [ ] Build times improved (faster rebuilds)

### After Phase 3 (This Sprint)
- [ ] Resource limits added to docker-compose.yml
- [ ] All image tags pinned (no `latest`)
- [ ] Health checks added to all services
- [ ] No containers exceeding memory limits
- [ ] Compose file reviewed for security

---

## Troubleshooting

### If cleanup fails
```bash
# Manual cleanup
docker container prune -f --filter "status=exited"
docker image prune -f
docker volume prune -f
```

### If compose won't start
```bash
# Check network
docker network ls | grep dopemux

# If missing, create it
docker network create dopemux-network

# Then start
docker compose -f docker-compose.master.yml up
```

### If services won't start
```bash
# Check specific service logs
docker compose logs SERVICE_NAME

# Check compose file syntax
docker compose config

# Check env vars loaded
docker compose config | grep OPENAI_API_KEY
```

### If build fails
```bash
# Rebuild from scratch (no cache)
docker compose build --no-cache SERVICE_NAME

# See full build output
docker build -f services/XXX/Dockerfile -t test:latest .
```

---

## Quick Reference

### Most-Used Commands
```bash
# Start everything
./scripts/start.sh

# View logs
docker compose logs -f SERVICE_NAME

# Stop everything
docker compose down

# Clean up (safe)
./scripts/cleanup.sh

# Full nuke (careful!)
docker compose down -v
```

### File Locations
- Audit report: `DOCKER_AUDIT_REPORT.md`
- Quick guide: `DOCKER_FIXES_QUICK_START.md`
- Cleanup script: `scripts/cleanup.sh`
- Start script: `scripts/start.sh`
- Environment: `.env` (edit this, don't commit)
- Fixed Dockerfiles: `services/*/Dockerfile.fixed`

---

## Timeline

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| 1 | Cleanup orphans | 5 min | 🔴 CRITICAL |
| 1 | Create .env | 3 min | 🔴 CRITICAL |
| 1 | Fix network | 1 min | 🔴 CRITICAL |
| 1 | Test startup | 5 min | 🔴 CRITICAL |
| 2 | Fix task-orchestrator | 10 min | 🟡 HIGH |
| 2 | Fix genetic-agent | 10 min | 🟡 HIGH |
| 2 | Fix dope-context | 10 min | 🟡 HIGH |
| 3 | Add resource limits | 15 min | 🟠 MEDIUM |
| 3 | Pin image versions | 10 min | 🟠 MEDIUM |
| 3 | Fix health checks | 10 min | 🟠 MEDIUM |

**Total Time**: ~1.5 hours to complete all phases

---

## Success Criteria

✅ **Phase 1 Complete When:**
- All services start without errors
- `docker compose ps` shows healthy containers
- Can make HTTP requests to services
- No orphaned containers in `docker ps -a`

✅ **Phase 2 Complete When:**
- Dockerfiles use multi-stage builds
- Image builds succeed
- Services still run after rebuild
- Build time improved

✅ **Phase 3 Complete When:**
- Resource limits in place
- All images pinned to versions
- All services have health checks
- No runaway containers

---

**Start with Phase 1. Everything is ready to go!**

Questions? Check `DOCKER_AUDIT_REPORT.md` for detailed explanations.
