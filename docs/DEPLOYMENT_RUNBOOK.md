# Architecture 3.0 Deployment Runbook

**Purpose**: Step-by-step deployment procedures for Architecture 3.0
**Audience**: DevOps engineers, SREs, deployment operators
**Status**: Production-Ready Deployment Guide

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Staging Deployment](#staging-deployment)
3. [Production Deployment](#production-deployment)
4. [Rollback Procedures](#rollback-procedures)
5. [Health Check Verification](#health-check-verification)
6. [Performance Validation](#performance-validation)
7. [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment Checklist

### Prerequisites

**Infrastructure**:
- [ ] Redis 7+ available (PORT 6379)
- [ ] PostgreSQL 16+ with AGE extension (PORT 5455)
- [ ] Docker 24+ installed
- [ ] Docker Compose 2.20+ installed
- [ ] Ports 3016, 3017 available

**Environment Variables**:
```bash
# Required
PORT_BASE=3000
REDIS_URL=redis://localhost:6379
POSTGRES_HOST=localhost
POSTGRES_PORT=5455
POSTGRES_DB=dopemux_staging
POSTGRES_USER=dopemux_staging
POSTGRES_PASSWORD=<secure_password>

# Optional
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
USE_MOCK_FALLBACK=false  # true for development
REDIS_TTL_SECONDS=30  # Cache TTL
```

**Code Validation**:
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] No security vulnerabilities (`trivy fs .`)
- [ ] Code quality checks pass (Black, Flake8, MyPy)
- [ ] Git tag created (`git tag v3.0.0`)

**Documentation**:
- [ ] Architecture 3.0 implementation doc reviewed
- [ ] Performance analysis reviewed
- [ ] This runbook reviewed

### Pre-Deployment Testing

```bash
# 1. Run unit tests
pytest tests/unit -v
# Expected: All tests pass, < 2 minutes

# 2. Run integration tests (requires services)
docker-compose -f docker/staging/docker-compose.staging.yml up -d
pytest tests/integration/test_architecture_3_0_e2e.py -v
# Expected: All tests pass, < 15 minutes

# 3. Run performance validation
pytest tests/integration/test_architecture_3_0_e2e.py::TestPerformanceValidation -v -s
# Expected: All ADHD targets met (< 70ms queries, < 200ms P95)

# 4. Cleanup
docker-compose -f docker/staging/docker-compose.staging.yml down
```

---

## Staging Deployment

### Step 1: Prepare Environment

```bash
# Navigate to staging directory
cd docker/staging

# Create .env file
cat > .env <<EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
GRAFANA_PASSWORD=$(openssl rand -base64 32)
PORT_BASE=3000
LOG_LEVEL=INFO
USE_MOCK_FALLBACK=false
EOF

# Secure .env file
chmod 600 .env

# Verify environment
cat .env
```

### Step 2: Start Infrastructure Services

```bash
# Start Redis and PostgreSQL first
docker-compose -f docker-compose.staging.yml up -d redis postgres

# Wait for health checks (30 seconds)
sleep 30

# Verify services are healthy
docker-compose -f docker-compose.staging.yml ps
# Expected: redis and postgres show "healthy"

# Check Redis
docker exec dopemux-staging-redis redis-cli ping
# Expected: PONG

# Check PostgreSQL
docker exec dopemux-staging-postgres pg_isready -U dopemux_staging
# Expected: accepting connections
```

### Step 3: Start Application Services

```bash
# Start Integration Bridge and Task-Orchestrator
docker-compose -f docker-compose.staging.yml up -d integration-bridge task-orchestrator

# Wait for application startup (30 seconds)
sleep 30

# Verify services are healthy
docker-compose -f docker-compose.staging.yml ps
# Expected: All services show "healthy"
```

### Step 4: Verify Deployment

```bash
# Check Integration Bridge health
curl -f http://localhost:3016/health
# Expected: {"status": "healthy", ...}

# Check Task-Orchestrator health
curl -f http://localhost:3017/health
# Expected: {"status": "healthy", ...}

# Test query endpoint
curl -f http://localhost:3016/orchestrator/tasks?limit=5
# Expected: JSON array of tasks

# Test ADHD state endpoint
curl -f http://localhost:3016/orchestrator/adhd-state
# Expected: {"energy_level": "...", "attention_level": "...", ...}
```

### Step 5: Performance Validation

```bash
# Run performance test script
python services/mcp-integration-bridge/test_component5_performance.py

# Expected Output:
# ✅ All endpoints ADHD-safe
# Average latency: < 70ms
# P95 latency: < 200ms
# Connection overhead: < 50ms
```

### Step 6: Enable Monitoring (Optional)

```bash
# Start Prometheus and Grafana
docker-compose -f docker-compose.staging.yml --profile monitoring up -d

# Access Grafana
open http://localhost:3030
# Login: admin / <GRAFANA_PASSWORD from .env>

# Import Architecture 3.0 dashboard
# Navigate to Dashboards → Import → Upload dashboard JSON
```

---

## Production Deployment

### Phase 1: Blue-Green Preparation

**Blue Environment** (Current Production):
- Keep running until Green validated
- No changes during deployment

**Green Environment** (New Version):
- Deploy Architecture 3.0
- Run validation tests
- Monitor for 1 hour

### Step 1: Deploy Green Environment

```bash
# Create production environment
mkdir -p /opt/dopemux/production-green
cd /opt/dopemux/production-green

# Clone repository
git clone https://github.com/DDD-Enterprises/dopemux-mvp.git .
git checkout v3.0.0  # Use specific version tag

# Configure production environment
cp docker/staging/docker-compose.staging.yml docker-compose.production.yml

# Edit docker-compose.production.yml:
# - Change container names: dopemux-prod-green-*
# - Change ports: 4016, 4017 (avoid conflict with Blue)
# - Update volume names: dopemux_prod_green_*
# - Update network: dopemux-production-green-network

# Create production .env
cat > .env <<EOF
POSTGRES_PASSWORD=$(vault read -field=password secret/dopemux/prod/postgres)
GRAFANA_PASSWORD=$(vault read -field=password secret/dopemux/prod/grafana)
PORT_BASE=4000  # Different from Blue
LOG_LEVEL=INFO
USE_MOCK_FALLBACK=false
REDIS_URL=redis://redis:6379
EOF

# Start Green environment
docker-compose -f docker-compose.production.yml up -d

# Wait for startup
sleep 60
```

### Step 2: Validate Green Environment

```bash
# Health checks
curl -f http://localhost:4016/health || exit 1
curl -f http://localhost:4017/health || exit 1

# Run smoke tests
pytest tests/integration/test_architecture_3_0_e2e.py -v \
  --integration-bridge-url=http://localhost:4016 \
  --orchestrator-url=http://localhost:4017

# Performance validation
pytest tests/integration/test_architecture_3_0_e2e.py::TestPerformanceValidation -v -s

# Monitor for 1 hour
# - Check logs for errors
# - Monitor Prometheus metrics
# - Verify ADHD latency targets maintained
```

### Step 3: Traffic Cutover

**Load Balancer Configuration**:
```nginx
# Option 1: Immediate cutover (if confident)
upstream dopemux_backend {
    server localhost:4016;  # Green
}

# Option 2: Canary deployment (10% → 50% → 100%)
upstream dopemux_backend {
    server localhost:3016 weight=9;  # Blue (90%)
    server localhost:4016 weight=1;  # Green (10%)
}
```

**Canary Progression**:
1. **10% traffic** (1 hour) → Monitor errors, latency
2. **50% traffic** (1 hour) → Monitor errors, latency
3. **100% traffic** (30 min) → Full cutover
4. **Decommission Blue** (after 24 hours)

### Step 4: Decommission Blue Environment

```bash
# After 24 hours of Green stability
cd /opt/dopemux/production-blue

# Stop Blue services
docker-compose -f docker-compose.production.yml down

# Backup Blue data (if needed)
docker run --rm -v dopemux_prod_blue_postgres_data:/data -v /backups:/backup alpine tar czf /backup/blue-postgres-$(date +%Y%m%d).tar.gz /data

# Remove Blue containers and volumes
docker-compose -f docker-compose.production.yml down -v

# Archive Blue directory
mv /opt/dopemux/production-blue /opt/dopemux/production-blue-archived-$(date +%Y%m%d)
```

---

## Rollback Procedures

### Scenario 1: Rollback During Green Validation (Before Cutover)

**Condition**: Green environment has issues, Blue still serving traffic

**Procedure**:
```bash
# 1. Stop Green environment
cd /opt/dopemux/production-green
docker-compose -f docker-compose.production.yml down

# 2. Blue continues serving traffic (no action needed)

# 3. Investigate Green issues
docker-compose -f docker-compose.production.yml logs > /tmp/green-failure-logs.txt

# 4. Fix issues and redeploy
```

**Impact**: Zero downtime, Blue unaffected

### Scenario 2: Rollback After Partial Cutover (10-50% traffic)

**Condition**: Green serving 10-50% traffic, issues detected

**Procedure**:
```bash
# 1. Immediate: Route 100% traffic to Blue
# Load balancer configuration:
upstream dopemux_backend {
    server localhost:3016;  # Blue only
}

# 2. Reload load balancer
sudo nginx -t && sudo nginx -s reload

# 3. Stop Green environment
cd /opt/dopemux/production-green
docker-compose -f docker-compose.production.yml down

# 4. Investigate issues
```

**Impact**: < 5 seconds traffic shift, minor user disruption

### Scenario 3: Rollback After Full Cutover (100% traffic)

**Condition**: Green serving 100% traffic, Blue still available

**Procedure**:
```bash
# 1. Immediate: Route traffic back to Blue
upstream dopemux_backend {
    server localhost:3016;  # Blue
}

# 2. Reload load balancer
sudo nginx -t && sudo nginx -s reload

# 3. Restart Blue services if stopped
cd /opt/dopemux/production-blue
docker-compose -f docker-compose.production.yml up -d

# 4. Verify Blue health
curl -f http://localhost:3016/health
curl -f http://localhost:3017/health

# 5. Stop Green environment
cd /opt/dopemux/production-green
docker-compose -f docker-compose.production.yml down
```

**Impact**: 30-60 seconds downtime (Blue restart + health check)

### Scenario 4: Emergency Rollback (Blue Decommissioned)

**Condition**: Green has critical issues, Blue already removed

**Procedure**:
```bash
# 1. Restore Blue from backup
cd /opt/dopemux
tar xzf production-blue-archived-$(date +%Y%m%d).tar.gz

# 2. Start Blue services
cd production-blue
docker-compose -f docker-compose.production.yml up -d

# 3. Wait for startup (2-5 minutes)
sleep 120

# 4. Verify Blue health
curl -f http://localhost:3016/health

# 5. Route traffic to Blue
# (Load balancer configuration)

# 6. Stop Green
cd /opt/dopemux/production-green
docker-compose -f docker-compose.production.yml down
```

**Impact**: 2-5 minutes downtime

---

## Health Check Verification

### Automated Health Check Script

```bash
#!/bin/bash
# health-check.sh - Comprehensive health validation

set -e

BRIDGE_URL="${BRIDGE_URL:-http://localhost:3016}"
ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://localhost:3017}"

echo "🏥 Architecture 3.0 Health Check"
echo "================================="

# Integration Bridge health
echo -n "Integration Bridge... "
if curl -sf "$BRIDGE_URL/health" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# Task-Orchestrator health
echo -n "Task-Orchestrator... "
if curl -sf "$ORCHESTRATOR_URL/health" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
    exit 1
fi

# Query endpoint test
echo -n "Query endpoint... "
if curl -sf "$BRIDGE_URL/orchestrator/tasks?limit=1" > /dev/null; then
    echo "✅ Responding"
else
    echo "❌ Not responding"
    exit 1
fi

# ADHD state endpoint test
echo -n "ADHD state endpoint... "
if curl -sf "$BRIDGE_URL/orchestrator/adhd-state" > /dev/null; then
    echo "✅ Responding"
else
    echo "❌ Not responding"
    exit 1
fi

# Performance check (latency)
echo -n "Performance check... "
RESPONSE_TIME=$(curl -o /dev/null -sf -w '%{time_total}' "$BRIDGE_URL/orchestrator/tasks?limit=1")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

if (( $(echo "$RESPONSE_TIME_MS < 200" | bc -l) )); then
    echo "✅ ${RESPONSE_TIME_MS}ms (< 200ms target)"
else
    echo "⚠️  ${RESPONSE_TIME_MS}ms (exceeds 200ms target)"
fi

echo "================================="
echo "✅ All health checks passed"
```

### Usage

```bash
# Make executable
chmod +x health-check.sh

# Run health check
./health-check.sh

# Run with custom URLs
BRIDGE_URL=http://prod.dopemux.com:3016 \
ORCHESTRATOR_URL=http://prod.dopemux.com:3017 \
./health-check.sh
```

---

## Performance Validation

### Latency Benchmark Script

```bash
#!/bin/bash
# latency-benchmark.sh - ADHD performance validation

set -e

BRIDGE_URL="${BRIDGE_URL:-http://localhost:3016}"
ITERATIONS="${ITERATIONS:-20}"

echo "⚡ ADHD Performance Validation"
echo "=============================="
echo "Target: < 70ms avg, < 200ms P95"
echo ""

# Test /tasks endpoint
echo "Testing /orchestrator/tasks..."
declare -a latencies

for i in $(seq 1 $ITERATIONS); do
    LATENCY=$(curl -o /dev/null -sf -w '%{time_total}' "$BRIDGE_URL/orchestrator/tasks?limit=10")
    LATENCY_MS=$(echo "$LATENCY * 1000" | bc)
    latencies+=($LATENCY_MS)
    echo "  Request $i: ${LATENCY_MS}ms"
done

# Calculate statistics
TOTAL=0
for lat in "${latencies[@]}"; do
    TOTAL=$(echo "$TOTAL + $lat" | bc)
done
AVG=$(echo "scale=2; $TOTAL / $ITERATIONS" | bc)

# Sort for P95
IFS=$'\n' sorted=($(sort -n <<<"${latencies[*]}"))
P95_INDEX=$(echo "($ITERATIONS * 0.95) / 1" | bc)
P95=${sorted[$P95_INDEX]}

echo ""
echo "Results:"
echo "  Average: ${AVG}ms"
echo "  P95: ${P95}ms"

# Validate
if (( $(echo "$AVG < 70" | bc -l) )); then
    echo "  ✅ Average meets ADHD target (< 70ms)"
else
    echo "  ❌ Average exceeds ADHD target (< 70ms)"
fi

if (( $(echo "$P95 < 200" | bc -l) )); then
    echo "  ✅ P95 meets ADHD target (< 200ms)"
else
    echo "  ❌ P95 exceeds ADHD target (< 200ms)"
fi
```

---

## Emergency Procedures

### Critical: All Services Down

**Symptoms**: All health checks failing

**Procedure**:
```bash
# 1. Check Docker daemon
sudo systemctl status docker
sudo systemctl restart docker

# 2. Check container status
docker ps -a

# 3. Restart all services
cd /opt/dopemux/production
docker-compose -f docker-compose.production.yml restart

# 4. If restart fails, recreate
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# 5. Verify health
./health-check.sh
```

**Escalation**: If issue persists > 5 minutes, initiate rollback

### Critical: Redis Unavailable

**Symptoms**: Event propagation failing, caching errors

**Procedure**:
```bash
# 1. Check Redis container
docker exec dopemux-prod-redis redis-cli ping

# 2. If unresponsive, restart Redis
docker-compose -f docker-compose.production.yml restart redis

# 3. Verify recovery
docker exec dopemux-prod-redis redis-cli ping
# Expected: PONG

# 4. Check application logs
docker-compose -f docker-compose.production.yml logs integration-bridge
docker-compose -f docker-compose.production.yml logs task-orchestrator

# 5. If persistent, check Redis data corruption
docker exec dopemux-prod-redis redis-cli --scan --pattern '*' | head -10
```

**Impact**: Component 3 (event propagation) degraded, Components 4-5 continue

### Critical: PostgreSQL Unavailable

**Symptoms**: ConPort MCP calls failing, state sync errors

**Procedure**:
```bash
# 1. Check PostgreSQL container
docker exec dopemux-prod-postgres pg_isready -U dopemux_prod

# 2. If unresponsive, restart PostgreSQL
docker-compose -f docker-compose.production.yml restart postgres

# 3. Wait for startup (30 seconds)
sleep 30

# 4. Verify recovery
docker exec dopemux-prod-postgres pg_isready -U dopemux_prod

# 5. Check for data corruption
docker exec dopemux-prod-postgres psql -U dopemux_prod -c "SELECT version();"
```

**Impact**: Component 4 (ConPort sync) degraded, Component 5 continues

### Critical: Performance Degradation

**Symptoms**: Latency > 200ms P95, ADHD targets violated

**Procedure**:
```bash
# 1. Run performance benchmark
./latency-benchmark.sh

# 2. Check container resource usage
docker stats --no-stream

# 3. Check system resources
top -b -n 1 | head -20
free -m
df -h

# 4. If memory/CPU constrained:
# - Scale up infrastructure
# - Restart services to clear memory leaks

# 5. Check for slow queries
docker-compose -f docker-compose.production.yml logs task-orchestrator | grep "slow"

# 6. Enable Redis caching (if not enabled)
# Edit .env: REDIS_TTL_SECONDS=30
docker-compose -f docker-compose.production.yml up -d
```

**Escalation**: If P95 > 300ms for > 10 minutes, initiate rollback

---

## Post-Deployment Checklist

- [ ] All health checks passing
- [ ] Performance validation passing (< 70ms avg, < 200ms P95)
- [ ] No errors in logs (first 1 hour)
- [ ] Monitoring dashboards configured
- [ ] Alerts configured (Prometheus)
- [ ] Rollback plan reviewed
- [ ] On-call rotation notified
- [ ] Deployment documented in changelog
- [ ] Blue environment backed up (if production)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-20
**Owner**: DevOps Team
**Review Frequency**: Quarterly
