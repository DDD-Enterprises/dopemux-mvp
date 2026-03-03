---
id: OPERATIONS
title: Operations
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Operations (explanation) for dopemux documentation and developer workflows.
---
# MCP Server Operations Runbook
**Version**: 1.0
**Last Updated**: 2026-02-05
**Purpose**: Standard operating procedures for MCP server management

---

## 📋 Table of Contents

1. [Daily Operations](#1%EF%B8%8F⃣-daily-operations)
2. [Starting & Stopping Servers](#2%EF%B8%8F⃣-starting--stopping-servers)
3. [Health Monitoring](#3%EF%B8%8F⃣-health-monitoring)
4. [Adding New Servers](#4%EF%B8%8F⃣-adding-new-servers)
5. [Resource Management](#5%EF%B8%8F⃣-resource-management)
6. [Backup & Recovery](#6%EF%B8%8F⃣-backup--recovery)
7. [Emergency Procedures](#7%EF%B8%8F⃣-emergency-procedures)

---

## 1️⃣ Daily Operations

### Morning Startup Checklist
```bash
# Navigate to MCP servers directory
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers

# Check what's already running
docker ps | grep dopemux

# Start all servers (if not running)
docker-compose up -d

# Verify health (wait 60s for startup)
sleep 60
./scripts/check-health.sh
```

### Quick Health Check
```bash
# One-liner health check
docker ps --format "table {{.Names}}\t{{.Status}}" | grep dopemux | grep -v "healthy"

# Should show minimal output (only unhealthy/starting servers)
```

### End of Day Shutdown (Optional)
```bash
# Graceful shutdown of all servers
docker-compose down

# OR keep running (recommended for development)
# Servers will auto-restart with Docker Desktop
```

---

## 2️⃣ Starting & Stopping Servers

### Start All Servers
```bash
cd docker/mcp-servers
docker-compose up -d
```

**What happens:**
1. Creates dopemux-network if missing
2. Builds images if not built
3. Starts containers in dependency order
4. Returns when containers are running (not necessarily healthy)

**Wait for health:**
```bash
# Watch logs until all healthy
docker-compose logs -f | grep -E "(healthy|ready|started)"

# Or use health check script
./scripts/check-health.sh
```

### Start Specific Server
```bash
# Single server
docker-compose up -d pal

# Multiple servers
docker-compose up -d pal serena dope-context

# With logs
docker-compose up pal  # Runs in foreground with logs
```

### Stop All Servers
```bash
# Graceful stop (recommended)
docker-compose down

# Keep volumes (data preserved)
docker-compose down --volumes=false

# Force stop (if graceful fails)
docker-compose down --timeout 10
```

### Stop Specific Server
```bash
docker-compose stop pal

# Remove container (but keep image)
docker-compose rm -f pal
```

### Restart Server
```bash
# Graceful restart
docker-compose restart pal

# Stop, rebuild, start (for code changes)
docker-compose stop pal
docker-compose build --no-cache pal
docker-compose up -d pal
```

---

## 3️⃣ Health Monitoring

### Health Check Methods

#### Method 1: Docker Status
```bash
# Quick overview
docker ps | grep dopemux

# Detailed status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

#### Method 2: Health Endpoints
```bash
# Create health check script
cat > check-health.sh << 'EOF'
#!/bin/bash
echo "🏥 MCP Server Health Check"
echo "=========================="

servers=(
  "pal:3003"
  "context7:3002"
  "serena:3006"
  "exa:3008"
  "gptr-mcp:3009"
  "dope-context:3010"
  "desktop-commander:3012"
  "task-orchestrator:3014"
  "leantime-bridge:3015"
  "activity-capture:8096"
)

for server in "${servers[@]}"; do
  name="${server%%:*}"
  port="${server##*:}"

  echo -n "Checking $name..."

  if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
    echo " ✅ Healthy"
  else
    echo " ❌ Unhealthy or unreachable"
  fi
done
EOF

chmod +x check-health.sh
./check-health.sh
```

#### Method 3: Docker Health
```bash
# Get health status for all containers
docker ps --format "table {{.Names}}\t{{.Status}}" | grep "(healthy)\|(unhealthy)\|(starting)"
```

### Automated Monitoring

#### Create cron job for daily health checks
```bash
# Edit crontab
crontab -e

# Add daily 9 AM health check
0 9 * * * cd /Users/hue/code/dopemux-mvp/docker/mcp-servers && ./check-health.sh >> logs/health-$(date +\%Y-\%m-\%d).log 2>&1
```

#### Slack/Email Notifications
```bash
# Add to check-health.sh
if [ $unhealthy_count -gt 0 ]; then
  # Send alert
  curl -X POST https://hooks.slack.com/YOUR_WEBHOOK \
    -d "{\"text\": \"⚠️ $unhealthy_count MCP servers unhealthy!\"}"
fi
```

---

## 4️⃣ Adding New Servers

### Step-by-Step Process

#### Step 1: Create Server Directory
```bash
cd docker/mcp-servers
mkdir my-new-server
cd my-new-server
```

#### Step 2: Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start server
CMD ["python", "server.py"]
```

#### Step 3: Create Environment File
```bash
# Create .env.example
cat > .env.example << EOF
# API Keys
OPENAI_API_KEY=your_key_here

# Server Configuration
PORT=8080
LOG_LEVEL=INFO
EOF

# Copy to .env
cp .env.example .env
# Edit .env with actual values
```

#### Step 4: Add to docker-compose.yml
```yaml
  my-new-server:
    build:
      context: ./my-new-server
      dockerfile: Dockerfile
    container_name: "${DOPEMUX_STACK_PREFIX:-dopemux}-mcp-my-new-server"
    restart: unless-stopped
    networks:
      - dopemux-network
    env_file:
      - ./my-new-server/.env
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      timeout: 10s
      retries: 3
      interval: 30s
      start_period: 45s
    labels:
      - "mcp.role=custom"
      - "mcp.priority=medium"
      - "mcp.description=My new server description"
```

#### Step 5: Build and Test
```bash
# Build
docker-compose build my-new-server

# Test build
docker-compose up my-new-server

# Start in background
docker-compose up -d my-new-server

# Check logs
docker-compose logs -f my-new-server
```

#### Step 6: Update Documentation
```bash
# Add to SERVER_REGISTRY.md
# Add to SERVER_STATUS_SUMMARY.md
# Document in .claude/CLAUDE.md if needed
```

### Validation Checklist
- [ ] Dockerfile builds successfully
- [ ] Container starts without errors
- [ ] Health check endpoint responds
- [ ] Server appears in `docker ps`
- [ ] Server marked healthy within 2 minutes
- [ ] Logs show no errors
- [ ] Documentation updated

---

## 5️⃣ Resource Management

### Monitor Resource Usage

#### Real-time Monitoring
```bash
# All containers
docker stats

# Specific container
docker stats dopemux-mcp-pal --no-stream

# Format output
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

#### Disk Usage
```bash
# Docker system usage
docker system df

# Detailed breakdown
docker system df -v

# Clean up space
docker system prune -a
```

### Set Resource Limits

#### Edit docker-compose.yml
```yaml
services:
  my-server:
    deploy:
      resources:
        limits:
          memory: 512M      # Maximum memory
          cpus: '0.5'       # Maximum 50% of one CPU
        reservations:
          memory: 256M      # Guaranteed memory
          cpus: '0.25'      # Guaranteed 25% of one CPU
```

#### Apply limits to running container
```bash
# Stop container
docker-compose stop my-server

# Update docker-compose.yml with limits

# Restart
docker-compose up -d my-server
```

### Performance Optimization

#### Enable Docker BuildKit
```bash
# Add to ~/.bash_profile or ~/.zshrc
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Rebuild with BuildKit
docker-compose build --no-cache
```

#### Multi-stage builds
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["python", "server.py"]
```

---

## 6️⃣ Backup & Recovery

### What to Backup

**Critical:**
- docker-compose.yml
- .env files (encrypted!)
- Server configuration files
- Database volumes

**Optional:**
- Docker images (can rebuild)
- Logs (if needed for audit)

### Backup Procedures

#### Backup Configuration
```bash
# Create backup directory
mkdir -p backups/$(date +%Y-%m-%d)

# Backup docker-compose
cp docker-compose.yml backups/$(date +%Y-%m-%d)/

# Backup .env files (ENCRYPT THESE!)
tar czf backups/$(date +%Y-%m-%d)/env-files.tar.gz --exclude='*.pyc' */.env

# Encrypt backup
gpg --symmetric backups/$(date +%Y-%m-%d)/env-files.tar.gz
rm backups/$(date +%Y-%m-%d)/env-files.tar.gz
```

#### Backup Docker Volumes
```bash
# List volumes
docker volume ls | grep mcp

# Backup specific volume
docker run --rm \
  -v mcp_conport_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/conport-$(date +%Y-%m-%d).tar.gz -C /data .
```

### Recovery Procedures

#### Restore Configuration
```bash
# Restore docker-compose.yml
cp backups/2026-02-05/docker-compose.yml docker-compose.yml

# Restore .env files
gpg --decrypt backups/2026-02-05/env-files.tar.gz.gpg | tar xzf -
```

#### Restore Volume
```bash
# Restore volume data
docker run --rm \
  -v mcp_conport_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/conport-2026-02-05.tar.gz"
```

#### Disaster Recovery
```bash
# 1. Clone repository
git clone https://github.com/yourusername/dopemux-mvp.git
cd dopemux-mvp/docker/mcp-servers

# 2. Restore configuration
cp backups/latest/docker-compose.yml .

# 3. Restore .env files
gpg --decrypt backups/latest/env-files.tar.gz.gpg | tar xzf -

# 4. Rebuild and start
docker-compose build
docker-compose up -d

# 5. Restore data volumes (if needed)
# ... restore volume commands ...
```

---

## 7️⃣ Emergency Procedures

### Server Unresponsive

```bash
# 1. Check if container is running
docker ps | grep <server>

# 2. Try graceful restart
docker-compose restart <server>

# 3. If still unresponsive, force restart
docker-compose stop <server>
docker-compose start <server>

# 4. If still failing, check logs
docker logs dopemux-mcp-<server> --tail 100

# 5. Nuclear option: rebuild
docker-compose stop <server>
docker-compose rm -f <server>
docker-compose build --no-cache <server>
docker-compose up -d <server>
```

### All Servers Down

```bash
# 1. Check Docker daemon
docker info

# 2. Check docker-compose file
docker-compose config

# 3. Restart Docker Desktop
# macOS: Restart Docker Desktop app

# 4. Start services
docker-compose up -d

# 5. Monitor startup
docker-compose logs -f
```

### Out of Disk Space

```bash
# 1. Check disk usage
docker system df

# 2. Remove stopped containers
docker container prune

# 3. Remove unused images
docker image prune -a

# 4. Remove unused volumes (CAUTION!)
docker volume prune

# 5. Clean everything (EXTREME CAUTION!)
docker system prune -a --volumes

# 6. Rebuild if needed
docker-compose up -d --build
```

### Port Conflicts

```bash
# 1. Find conflicting process
lsof -i :<port>

# 2. Kill process
kill -9 <PID>

# 3. Or change server port in docker-compose.yml
# Edit ports section: "3013:3003" instead of "3003:3003"

# 4. Restart server
docker-compose up -d <server>
```

---

## 📊 Common Operational Workflows

### Update Server Code
```bash
# 1. Stop server
docker-compose stop <server>

# 2. Pull latest code (if from git)
cd <server-directory>
git pull

# 3. Rebuild
docker-compose build --no-cache <server>

# 4. Start
docker-compose up -d <server>

# 5. Verify
docker logs dopemux-mcp-<server> --tail 20
```

### Update Dependencies
```bash
# 1. Update requirements.txt or package.json
# ... edit file ...

# 2. Rebuild with no cache
docker-compose build --no-cache <server>

# 3. Restart
docker-compose up -d <server>
```

### Scale Server (if supported)
```bash
# Note: Only works for stateless servers
docker-compose up -d --scale <server>=3
```

### View Aggregated Logs
```bash
# All servers, real-time
docker-compose logs -f

# Specific servers
docker-compose logs -f pal serena dope-context

# Last 100 lines
docker-compose logs --tail 100

# Search logs
docker-compose logs | grep -i error
```

---

## 🔐 Security Operations

### Rotate API Keys
```bash
# 1. Update .env file
vi docker/mcp-servers/<server>/.env

# 2. Restart server (to pick up new env)
docker-compose stop <server>
docker-compose up -d <server>

# 3. Verify new key works
docker logs dopemux-mcp-<server> --tail 20
```

### Update Secrets
```bash
# 1. Use Docker secrets (recommended for production)
echo "new_secret_value" | docker secret create my_secret -

# 2. Or update .env and restart
```

### Security Audit
```bash
# Check for exposed ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Check for privileged containers
docker ps --filter "label=privileged=true"

# Scan images for vulnerabilities
docker scan dopemux-mcp-pal
```

---

## 📞 Operations Support

### Before Escalating
1. ✅ Check TROUBLESHOOTING.md
2. ✅ Check server logs
3. ✅ Try graceful restart
4. ✅ Check disk space and resources
5. ✅ Search GitHub issues

### Escalation Checklist
Include:
- What you were trying to do
- What happened instead
- Server names and versions
- Relevant logs (`docker logs`)
- Output of `docker-compose config <server>`
- Steps already attempted

---

**Last Updated**: 2026-02-05
**Maintained By**: Dopemux Infrastructure Team
**On-Call**: Check #infrastructure Slack channel
