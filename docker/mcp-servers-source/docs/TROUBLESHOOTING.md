---
id: TROUBLESHOOTING
title: Troubleshooting
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Troubleshooting (explanation) for dopemux documentation and developer workflows.
---
# MCP Server Troubleshooting Guide
**Version**: 1.0
**Last Updated**: 2026-02-05
**ADHD-Optimized**: Clear steps, visual indicators, quick resolutions

---

## 🎯 Quick Problem Solver

**Use this flowchart to find your section:**

```
Problem type?
├── Server won't start → Section 1
├── Server crashes/restarts → Section 2
├── Port already in use → Section 3
├── Connection refused → Section 4
├── Slow performance → Section 5
├── Unhealthy status → Section 6
└── Build failures → Section 7
```

---

## 1️⃣ Server Won't Start

### Symptoms
- Container not in `docker ps` output
- `docker-compose up` fails
- "Error starting container" messages

### Diagnosis Steps

**Step 1: Check if container exists**
```bash
docker ps -a | grep <server-name>
```

**Step 2: View startup logs**
```bash
docker logs dopemux-mcp-<server-name> --tail 50
```

**Step 3: Check docker-compose errors**
```bash
docker-compose up <server-name>
# Watch for build or startup errors
```

### Common Causes & Solutions

#### ❌ Missing Environment Variables
**Error**: `KeyError: 'REQUIRED_VAR'`
**Solution**:
```bash
# Check .env file exists
ls -la docker/mcp-servers/<server>/.env

# Verify required vars
cat docker/mcp-servers/<server>/.env.example
```

**Fix**: Copy .env.example and fill in values
```bash
cp .env.example .env
# Edit .env with your API keys
```

#### ❌ Missing Dependencies
**Error**: `ModuleNotFoundError`, `ImportError`
**Solution**: Rebuild container
```bash
docker-compose build --no-cache <server-name>
docker-compose up -d <server-name>
```

#### ❌ Port Already in Use
**Error**: `port is already allocated`
**Solution**: See Section 3 (Port Conflicts)

#### ❌ Network Issues
**Error**: `network dopemux-network not found`
**Solution**:
```bash
# Create network
docker network create dopemux-network

# Or restart all services
docker-compose down
docker-compose up -d
```

---

## 2️⃣ Server Crashes or Constantly Restarts

### Symptoms
- Status shows "Restarting (1) X seconds ago"
- Container appears in `docker ps` but keeps restarting
- Health check never passes

### Diagnosis Steps

**Step 1: Watch live logs**
```bash
docker logs -f dopemux-mcp-<server-name>
# Watch for crash patterns
```

**Step 2: Check restart count**
```bash
docker inspect dopemux-mcp-<server-name> | grep RestartCount
```

**Step 3: Check exit code**
```bash
docker inspect dopemux-mcp-<server-name> | grep ExitCode
```

### Common Causes & Solutions

#### ❌ mcp-client: "No response from MCP server"
**Cause**: Trying to connect to stdio servers that don't exist
**Solution**: Either start required servers OR mark as optional
```bash
# Option 1: Start task-master-ai (requires mcp-client)
docker-compose up -d task-master-ai

# Option 2: Mark as optional (comment out in docker-compose.yml)
# mcp-client:
#   ...
```

#### ❌ activity-capture: Redis connection failed
**Cause**: Wrong Redis hostname in environment
**Solution**: Check Redis URL
```bash
# Verify Redis is running
docker ps | grep redis

# Check activity-capture env
docker inspect dopemux-activity-capture | grep REDIS_URL

# Should be: redis://redis-events:6379
# NOT: redis://dopemux-redis-events:6379
```

**Fix**: Update docker-compose.yml
```yaml
environment:
  - REDIS_URL=redis://redis-events:6379  # Correct
```

#### ❌ Application crashes on startup
**Error**: Python/Node exceptions in logs
**Solution**:
```bash
# 1. Check for code errors in logs
docker logs dopemux-mcp-<server> --tail 100 | grep -E "Error|Exception"

# 2. Rebuild with fresh dependencies
docker-compose build --no-cache <server>

# 3. Check for missing files
docker exec dopemux-mcp-<server> ls -la /app
```

---

## 3️⃣ Port Already in Use

### Symptoms
- Error: "Bind for 0.0.0.0:XXXX failed: port is already allocated"
- Server won't start due to port conflict

### Diagnosis

**Find what's using the port:**
```bash
# macOS/Linux
lsof -i :3003

# Alternative
netstat -anp | grep 3003
```

### Solutions

#### ✅ Kill the conflicting process
```bash
# Find PID
lsof -i :3003

# Kill it
kill -9 <PID>

# Restart server
docker-compose up -d <server>
```

#### ✅ Change server port
**Edit docker-compose.yml:**
```yaml
ports:
  - "3013:3003"  # Host:Container (change 3013 to available port)
```

#### ✅ Stop conflicting container
```bash
# Find container using port
docker ps | grep 3003

# Stop it
docker stop <container-name>
```

### Port Reference
| Port | Server | Can Change? |
|------|--------|-------------|
| 3002 | context7 | ✅ Yes |
| 3003 | pal | ✅ Yes |
| 3006, 4006 | serena | ✅ Yes |
| 3008 | exa | ✅ Yes |
| 3009 | gptr-mcp | ✅ Yes |
| 3010 | dope-context | ✅ Yes |
| 3012 | desktop-commander | ✅ Yes |
| 3014 | task-orchestrator | ✅ Yes |
| 3015 | leantime-bridge | ✅ Yes |
| 3016 | dopecon-bridge | ✅ Yes |
| 8090 | plane-coordinator | ✅ Yes |
| 8096 | activity-capture | ✅ Yes |
| 6333-6334 | qdrant | ⚠️ May affect configs |

---

## 4️⃣ Connection Refused / Cannot Connect

### Symptoms
- "Connection refused" errors
- Server appears running but not accessible
- Health check fails

### Diagnosis Steps

**Step 1: Verify server is actually running**
```bash
docker ps | grep <server-name>
# Should show "Up" status
```

**Step 2: Check if port is exposed**
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep <server>
# Should show port mapping like "0.0.0.0:3003->3003/tcp"
```

**Step 3: Test from inside container**
```bash
# Enter container
docker exec -it dopemux-mcp-<server> /bin/bash

# Test locally
curl http://localhost:3003/health
```

**Step 4: Check network**
```bash
# Verify container is on correct network
docker inspect dopemux-mcp-<server> | grep -A 10 "Networks"
```

### Common Causes & Solutions

#### ❌ Server not listening on 0.0.0.0
**Cause**: Server bound to 127.0.0.1 instead of 0.0.0.0
**Solution**: Check server configuration
```bash
# Example for Python servers
# Ensure: app.run(host="0.0.0.0", port=3003)
# NOT: app.run(host="localhost", port=3003)
```

#### ❌ Wrong network
**Cause**: Container not on dopemux-network
**Solution**:
```bash
# Check which network
docker inspect dopemux-mcp-<server> | grep NetworkMode

# Reconnect to correct network
docker network connect dopemux-network dopemux-mcp-<server>
docker-compose restart <server>
```

#### ❌ Firewall blocking
**Cause**: Local firewall blocking Docker ports
**Solution (macOS)**:
```bash
# Check Docker Desktop network settings
# System Preferences → Docker → Resources → Network
```

---

## 5️⃣ Slow Performance

### Symptoms
- Server responds slowly (>2 seconds)
- High CPU/memory usage
- Docker system sluggish

### Diagnosis

**Check resource usage:**
```bash
# Real-time stats
docker stats

# Single server
docker stats dopemux-mcp-<server> --no-stream
```

**Check disk usage:**
```bash
docker system df
```

### Solutions

#### ✅ Clean up Docker resources
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (CAUTION: may delete data!)
docker volume prune

# Clean everything (CAUTION!)
docker system prune -a --volumes
```

#### ✅ Limit container resources
**Edit docker-compose.yml:**
```yaml
services:
  <server>:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

#### ✅ Optimize build cache
```bash
# Rebuild with fresh cache
docker-compose build --no-cache --pull <server>
```

---

## 6️⃣ Unhealthy Status

### Symptoms
- `docker ps` shows "(unhealthy)" status
- Health check endpoint returns errors

### Diagnosis

**Check health check logs:**
```bash
docker inspect dopemux-mcp-<server> | grep -A 20 "Health"
```

**Test health endpoint manually:**
```bash
curl -v http://localhost:3003/health
```

### Common Issues

#### ❌ Health check endpoint not implemented
**Solution**: Verify server has /health endpoint
```bash
docker exec dopemux-mcp-<server> curl localhost:3003/health
```

#### ❌ Dependencies not ready
**Cause**: Server healthy but dependencies (DB, Redis) not ready
**Solution**: Add depends_on with condition
```yaml
depends_on:
  redis:
    condition: service_healthy
  postgres:
    condition: service_healthy
```

#### ❌ Health check too aggressive
**Cause**: Health check interval too short
**Solution**: Increase intervals
```yaml
healthcheck:
  interval: 60s       # Was: 30s
  timeout: 15s        # Was: 10s
  retries: 5          # Was: 3
  start_period: 90s   # Was: 45s
```

---

## 7️⃣ Build Failures

### Symptoms
- `docker-compose build` fails
- "Error building image" messages
- Missing files during COPY

### Common Causes & Solutions

#### ❌ plane-coordinator: Build context path errors
**Error**: `failed to solve: failed to compute cache key` or missing `app/` files
**Cause**: Running build from the wrong working directory or stale Docker cache
**Solution**:
```bash
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
docker compose build --no-cache plane-coordinator
docker compose up -d plane-coordinator
```

#### ❌ Build context too large
**Error**: "Sending build context to Docker daemon..."  (hangs)
**Solution**: Add .dockerignore
```bash
# Create docker/mcp-servers/<server>/.dockerignore
node_modules
__pycache__
*.pyc
.git
.env
logs/
data/
```

#### ❌ Network issues during build
**Error**: `Could not resolve host`, `Connection timed out`
**Solution**:
```bash
# Check Docker DNS
docker-compose build --no-cache --pull

# Or use host network for build
docker build --network=host -f Dockerfile .
```

---

## 🚨 Emergency Procedures

### Complete System Reset
```bash
# ⚠️ CAUTION: Destroys all containers and data!

# 1. Stop everything
docker-compose down

# 2. Remove all Dopemux containers
docker ps -a | grep dopemux | awk '{print $1}' | xargs docker rm -f

# 3. Clean system
docker system prune -a --volumes

# 4. Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Restore from Known Good State
```bash
# 1. Check git for last working docker-compose.yml
git log --oneline docker-compose.yml

# 2. Restore previous version
git checkout <commit-hash> docker-compose.yml

# 3. Rebuild
docker-compose down
docker-compose up -d --build
```

### Individual Server Reset
```bash
# Stop and remove container
docker-compose stop <server>
docker-compose rm -f <server>

# Remove image
docker rmi mcp-servers-<server>

# Rebuild and start
docker-compose build --no-cache <server>
docker-compose up -d <server>
```

---

## 📞 Getting Help

### Before Asking for Help
1. ✅ Check this troubleshooting guide
2. ✅ Check server logs: `docker logs <container> --tail 100`
3. ✅ Try rebuilding: `docker-compose build --no-cache <server>`
4. ✅ Search GitHub issues for similar problems

### When Reporting Issues
Include:
- Server name and version
- Full error message from logs
- Output of `docker-compose config <server>`
- Output of `docker inspect <container>`
- Steps to reproduce

### Useful Debug Commands
```bash
# Full server configuration
docker-compose config <server>

# Container details
docker inspect dopemux-mcp-<server>

# Network information
docker network inspect dopemux-network

# All logs
docker-compose logs --tail 200

# System information
docker info
docker version
```

---

## 🔍 Common Error Messages

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `port is already allocated` | Port conflict | Section 3 |
| `No such container` | Container not created | `docker-compose up -d <server>` |
| `Connection refused` | Server not listening | Section 4 |
| `No response from MCP server` | mcp-client issue | Section 2 |
| `Name or service not known` | DNS/network issue | Section 4 |
| `not found during COPY` | Missing implementation | Section 7 |
| `Cannot connect to Docker daemon` | Docker not running | Start Docker Desktop |

---

**Last Updated**: 2026-02-05
**Maintained By**: Dopemux Infrastructure Team
**Feedback**: Create GitHub issue with `documentation` label
