---
id: DOCKER_FIXES_QUICK_START
title: Docker Fixes Quick Start
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Docker Fixes Quick Start (reference) for dopemux documentation and developer
  workflows.
---
# Docker Audit - Quick Action Items

## 🚨 IMMEDIATE FIXES (Do These First)

### 1. Clean Up Orphan Containers
```bash
cd ~/code/dopemux-mvp
./scripts/cleanup.sh
```

**What this does:**
- Removes all exited containers (you have 50+)
- Optionally removes unused images and volumes
- Shows final status

**Time**: 2 minutes

---

### 2. Create Environment File
```bash
cd ~/code/dopemux-mvp
cp .env.example .env
# Edit .env and fill in your API keys
nano .env
```

**What to fill in:**
- `OPENAI_API_KEY` - Get from OpenAI
- `ANTHROPIC_API_KEY` - Get from Anthropic
- Other API keys for services you use
- Leave database passwords as-is for dev

**Time**: 5 minutes

---

### 3. Test Docker Compose
```bash
cd ~/code/dopemux-mvp
./scripts/start.sh
```

**What this does:**
- Creates network automatically
- Starts all services with `--remove-orphans`
- Shows status of all containers

**Check result:**
```bash
docker compose -f docker-compose.master.yml ps
```

Should show all services in "running" or "healthy" state.

**Time**: 3 minutes (actual startup may take 2-5 minutes)

---

## ⚠️ IMPORTANT CHANGES NEEDED

### Fix docker-compose.master.yml
**Location**: Line with `networks.dopemux-network.external`

**Current** (BROKEN):
```yaml
networks:
  dopemux-network:
    external: true
```

**Change to**:
```yaml
networks:
  dopemux-network:
    driver: bridge
```

**Why**: The `external: true` flag requires you to manually create the network first. Removing it lets Docker create it automatically.

---

## 📝 FILES CREATED FOR YOU

1. **`.dockerignore`** - Speeds up docker builds by excluding unnecessary files
2. **`.env.example`** - Template for environment variables (commit this, not .env)
3. **`scripts/cleanup.sh`** - Removes orphan containers and unused images
4. **`scripts/start.sh`** - Starts the stack with proper setup
5. **`DOCKER_AUDIT_REPORT.md`** - Full detailed audit (read this!)
6. **`services/*/Dockerfile.fixed`** - Fixed versions of problematic Dockerfiles

---

## 🔧 DOCKERFILE FIXES (This Week)

Once the stack is running, fix these Dockerfiles one by one:

### 1. Task Orchestrator
```bash
cd ~/code/dopemux-mvp
cp services/task-orchestrator/Dockerfile.fixed services/task-orchestrator/Dockerfile
docker compose -f docker-compose.master.yml build task-orchestrator
```

### 2. Genetic Agent
```bash
cp services/genetic_agent/Dockerfile.fixed services/genetic_agent/Dockerfile
docker compose -f docker-compose.master.yml build genetic-agent
```

### 3. Dope Context
```bash
cp services/dope-context/Dockerfile.fixed services/dope-context/Dockerfile
docker compose -f docker-compose.master.yml build dope-context
```

**Why fix them:**
- Multi-stage builds reduce image size by 50-70%
- Better caching = faster rebuilds
- Cleaner separation of build vs runtime

---

## ✅ SUCCESS CHECKLIST

After following the immediate fixes, verify:

- [ ] Orphan containers removed: `docker ps -a | wc -l` shows < 5
- [ ] `.env` file created and filled in
- [ ] `docker compose ps` shows all services running/healthy
- [ ] Can curl a service: `curl http://localhost:8095/health` (should respond)
- [ ] No errors in logs: `docker compose logs --tail 50`

---

## 📚 FULL DOCUMENTATION

Read the complete audit report for:
- Detailed security findings
- Recommended image versions to pin
- Resource limit recommendations
- Production deployment strategy
- CI/CD best practices

File: `DOCKER_AUDIT_REPORT.md`

---

## 🆘 IF SOMETHING FAILS

### Containers won't start
```bash
# Check logs
docker compose -f docker-compose.master.yml logs -f SERVICE_NAME

# Check specific container
docker logs CONTAINER_ID

# Most common: Missing env vars - check .env file
```

### Network issues
```bash
# Verify network exists
docker network ls | grep dopemux

# Inspect network
docker network inspect dopemux-network

# Recreate if broken
docker network rm dopemux-network
docker network create dopemux-network
```

### Image build failures
```bash
# Rebuild with output
docker compose -f docker-compose.master.yml build --no-cache SERVICE_NAME

# Check for issues in Dockerfile
docker build -f services/XXX/Dockerfile -t test:latest .
```

---

## 💡 PRO TIPS

### Useful alias in `.bashrc` / `.zshrc`
```bash
alias dc='docker compose -f docker-compose.master.yml'
alias dcup='docker compose -f docker-compose.master.yml up -d --remove-orphans'
alias dclogs='docker compose -f docker-compose.master.yml logs -f'
```

### Monitor in real-time
```bash
docker stats --no-stream | grep dopemux
```

### Clean everything (DESTRUCTIVE)
```bash
docker compose -f docker-compose.master.yml down -v  # removes volumes too
```

---

## 📞 NEXT STEPS

1. ✅ Run cleanup script
2. ✅ Create .env file
3. ✅ Fix docker-compose.master.yml (remove external: true)
4. ✅ Start stack: `./scripts/start.sh`
5. 📋 Once running, apply Dockerfile fixes
6. 📖 Review DOCKER_AUDIT_REPORT.md for security improvements

---

**Questions?** Check the detailed audit report.
**Emergency?** `docker compose down && docker system prune -a && ./scripts/start.sh`
