---
id: deployment-guide
title: Dopemux Deployment Guide
type: how-to
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-02'
status: consolidated
supersedes:
- deployment-checklist
- deployment-instructions
- production-deployment-checklist
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopemux Deployment Guide (how-to) for dopemux documentation and developer
  workflows.
---
# Dopemux Production Deployment Guide

**Comprehensive deployment guide for Dopemux platform**

**Status**: Production-Ready ✅
**Risk Level**: LOW (backwards compatible)
**Deployment Time**: 30-60 minutes

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Service Deployment](#service-deployment)
5. [Health Checks](#health-checks)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Deployment Validation](#post-deployment-validation)

---

## Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] Docker and Docker Compose installed
- [ ] PostgreSQL with AGE extension available
- [ ] Redis instance running
- [ ] Qdrant vector database accessible
- [ ] Network connectivity verified
- [ ] SSL certificates ready (if using HTTPS)

### Code Preparation

- [ ] Latest code merged to `main` branch
- [ ] All tests passing (`make test`)
- [ ] Code quality checks passed (`make quality`)
- [ ] Database migrations reviewed
- [ ] Rollback plan documented

### Backup

- [ ] Database backup created
- [ ] Configuration files backed up
- [ ] Previous deployment artifacts saved
- [ ] Rollback procedure tested

---

## Environment Configuration

### Step 1: Create Production Environment File

```bash
# Copy template
cp .env.example .env

# Edit with production values
nano .env
```

### Step 2: Required Environment Variables

```bash
# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ADHD_ENGINE_API_KEY=$(openssl rand -hex 32)
SERENA_DB_PASSWORD=<your-secure-password>
AGE_PASSWORD=<your-secure-age-password>

# Architecture
USE_DOPECON_BRIDGE=true  # Full architecture compliance

# Services
DOPECON_BRIDGE_URL=http://localhost:3016
DEFAULT_WORKSPACE_PATH=/workspace

# LLM Integration (optional)
OPENROUTER_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
XAI_API_KEY=<your-key>

# Database
POSTGRES_PASSWORD=<secure-password>
POSTGRES_HOST=dopemux-postgres-age
POSTGRES_PORT=5432
POSTGRES_DB=dopemux_knowledge_graph

# Redis
REDIS_HOST=dopemux-redis
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=dopemux-qdrant
QDRANT_PORT=6333
```

### Step 3: Validate Configuration

```bash
# Check for sensitive data leaks
grep -r "password\|secret\|key" .env | grep -v "EXAMPLE"

# Verify all required variables set
make validate-env  # or manually check
```

---

## Database Setup

### Step 1: Database Migrations

```bash
# Check migration status
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT * FROM schema_migrations ORDER BY version;"

# Expected migrations:
# - 001: Initial schema
# - 002: AGE graph setup
# - 003: Multi-tenancy foundation
# - 004: Unified query indexes
```

### Step 2: Run Pending Migrations

```bash
# Copy migration to container
docker cp docker/mcp-servers/conport/migrations/00X_migration.sql \
  mcp-conport:/tmp/migration.sql

# Execute migration
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph \
  -f /tmp/migration.sql

# Verify
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT version, applied_at FROM schema_migrations;"
```

### Step 3: Database Validation

```bash
# Verify tables exist
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "\dt"

# Check graph schema
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "SELECT * FROM ag_catalog.ag_graph;"

# Verify indexes
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph \
  -c "\di"
```

---

## Service Deployment

### Deployment Option 1: Full Stack (Recommended)

```bash
# Deploy all services with docker-compose
docker-compose -f docker-compose.master.yml up -d

# Monitor startup
docker-compose -f docker-compose.master.yml logs -f
```

### Deployment Option 2: Core Services Only

```bash
# Deploy core services (minimal setup)
docker-compose -f docker-compose.unified.yml up -d

# Services included:
# - PostgreSQL with AGE
# - Redis
# - Qdrant
# - ConPort
# - ADHD Engine
# - Task Orchestrator
# - DopeconBridge
```

### Deployment Option 3: Staging Environment

```bash
# Use staging configuration
docker-compose -f docker-compose.staging.yml up -d

# Staging includes:
# - Same services as production
# - Debug logging enabled
# - Development tools included
```

---

## Health Checks

### Automated Health Check Script

```bash
# Run comprehensive health check
python services/monitoring/health_checks.py

# Expected output:
# ✅ ConPort MCP (port 3004): HEALTHY
# ✅ DopeconBridge (port 3016): HEALTHY
# ✅ ADHD Engine (port 8080): HEALTHY
# ✅ Task Orchestrator (port 8000): HEALTHY
# ✅ PostgreSQL (port 5432): HEALTHY
# ✅ Redis (port 6379): HEALTHY
# ✅ Qdrant (port 6333): HEALTHY
```

### Manual Health Checks

```bash
# Check individual services
curl http://localhost:3016/health  # DopeconBridge
curl http://localhost:8080/health  # ADHD Engine
curl http://localhost:8000/health  # Task Orchestrator
curl http://localhost:3004/health  # ConPort MCP

# Check databases
docker exec dopemux-postgres-age pg_isready
docker exec dopemux-redis redis-cli ping
curl http://localhost:6333/  # Qdrant
```

### Service Status

```bash
# Check all containers
docker ps --filter "name=dopemux"

# Expected: All containers in "Up" state
# - dopemux-postgres-age
# - dopemux-redis
# - dopemux-qdrant
# - mcp-conport
# - dopemux-adhd-engine
# - dopemux-task-orchestrator
# - dopemux-dopecon-bridge
```

---

## Rollback Procedures

### Scenario 1: Database Migration Failure

```bash
# Stop services
docker-compose -f docker-compose.master.yml down

# Restore database backup
docker exec dopemux-postgres-age psql -U dopemux_age \
  -d dopemux_knowledge_graph < backup-YYYY-MM-DD.sql

# Restart with previous version
git checkout <previous-tag>
docker-compose -f docker-compose.master.yml up -d
```

### Scenario 2: Service Startup Failure

```bash
# Check logs for failing service
docker logs <container-name>

# Rollback to previous image
docker tag dopemux/<service>:latest dopemux/<service>:broken
docker pull dopemux/<service>:<previous-tag>
docker tag dopemux/<service>:<previous-tag> dopemux/<service>:latest

# Restart
docker-compose -f docker-compose.master.yml restart <service>
```

### Scenario 3: Complete Rollback

```bash
# Full system rollback
docker-compose -f docker-compose.master.yml down

# Restore all data
./scripts/restore-backup.sh <backup-date>

# Deploy previous version
git checkout <previous-tag>
docker-compose -f docker-compose.master.yml up -d
```

---

## Post-Deployment Validation

### Step 1: Smoke Tests

```bash
# Run smoke tests
docker-compose -f docker-compose.smoke.yml up --abort-on-container-exit

# Expected: All tests pass
```

### Step 2: Integration Tests

```bash
# Run integration test suite
make test-integration

# Expected: All integration tests pass
# - DopeconBridge connectivity
# - ConPort graph operations
# - ADHD Engine API
# - Task Orchestrator workflows
```

### Step 3: Service Registry Validation

```bash
# Validate service registry
python scripts/validate_service_registry.py

# Expected: All services registered correctly
# - Port mappings correct
# - Health endpoints responsive
# - Dependencies satisfied
```

### Step 4: End-to-End Test

```bash
# Test complete workflow
dopemux start
dopemux mobile start
dopemux mobile notify "Deployment test"

# Expected: Notification received on mobile
```

---

## Production Deployment Timeline

### Preparation Phase (15 minutes)
- [ ] Review deployment checklist
- [ ] Create backups
- [ ] Prepare environment files
- [ ] Review migration scripts

### Deployment Phase (30 minutes)
- [ ] Stop existing services (if upgrading)
- [ ] Run database migrations (5 min)
- [ ] Deploy services (10 min)
- [ ] Run health checks (5 min)
- [ ] Validate deployment (10 min)

### Validation Phase (15 minutes)
- [ ] Run smoke tests
- [ ] Run integration tests
- [ ] Validate service registry
- [ ] End-to-end workflow test
- [ ] Monitor logs for errors

**Total Time**: 60 minutes (with buffer)

---

## Security Hardening

### SSL/TLS Configuration

```bash
# Generate SSL certificates (if needed)
certbot certonly --standalone -d yourdomain.com

# Update nginx/reverse proxy config
# Point to certificate files
```

### API Key Rotation

```bash
# Generate new API keys
export NEW_ADHD_ENGINE_API_KEY=$(openssl rand -hex 32)

# Update .env
sed -i "s/ADHD_ENGINE_API_KEY=.*/ADHD_ENGINE_API_KEY=$NEW_ADHD_ENGINE_API_KEY/" .env

# Restart affected services
docker-compose restart adhd-engine
```

### Network Security

```bash
# Create isolated network
docker network create --driver bridge dopemux-private

# Update docker-compose.yml to use private network
# Expose only necessary ports to host
```

---

## Monitoring and Maintenance

### Log Monitoring

```bash
# Tail all service logs
docker-compose logs -f

# Specific service logs
docker logs -f dopemux-adhd-engine

# Export logs for analysis
docker logs dopemux-adhd-engine > adhd-engine-$(date +%Y%m%d).log
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Database performance
docker exec dopemux-postgres-age psql -U dopemux_age \
  -d dopemux_knowledge_graph \
  -c "SELECT * FROM pg_stat_activity;"
```

### Backup Schedule

```bash
# Daily database backup (cron)
0 2 * * * /path/to/backup-script.sh

# Weekly full system backup
0 3 * * 0 /path/to/full-backup.sh
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs <container-name>

# Common issues:
# - Port already in use
# - Environment variable missing
# - Database not ready
# - Network connectivity

# Verify networks
docker network ls | grep dopemux

# Verify env vars
docker exec <container> env
```

### Database Connection Errors

```bash
# Verify PostgreSQL running
docker ps | grep postgres

# Test connection
docker exec mcp-conport psql -U dopemux_age -d dopemux_knowledge_graph -c "SELECT 1;"

# Check password
docker exec mcp-conport env | grep DATABASE_URL
```

### Health Check Failures

```bash
# Check service logs
docker logs <failing-service>

# Verify dependencies
# E.g., if DopeconBridge fails, check Redis and PostgreSQL

# Restart service
docker-compose restart <service>
```

---

## Service-Specific Guides

For service-specific deployment details, see:

- **Serena v2**: [serena-v2-production-deployment.md](serena-v2-production-deployment.md)
- **Leantime Integration**: See integration guides in `docs/02-how-to/integrations/`
- **MCP Servers**: Individual READMEs in `docker/mcp-servers/*/`

---

## Quick Reference Commands

```bash
# Start full stack
docker-compose -f docker-compose.master.yml up -d

# Check all service health
for port in 3004 3016 8000 8080; do
  curl -s http://localhost:$port/health | jq .
done

# View logs
docker-compose logs -f

# Restart service
docker-compose restart <service-name>

# Stop all services
docker-compose -f docker-compose.master.yml down

# Full cleanup (WARNING: destroys data)
docker-compose -f docker-compose.master.yml down -v
```

---

## Additional Resources

- **Installation Guide**: [INSTALL.md](../../INSTALL.md)
- **Quick Start**: [QUICK_START.md](../../QUICK_START.md)
- **Service Registry**: [services/registry.yaml](../../services/registry.yaml)
- **Architecture**: [docs/04-explanation/architecture/](../04-explanation/architecture/)

---

**Last Updated**: 2026-02-02
**Consolidated From**:
- deployment-checklist.md (security fixes deployment)
- deployment-instructions.md (general production deployment)
- production-deployment-checklist.md (comprehensive checklist)

**Next Review**: 2026-05-02
