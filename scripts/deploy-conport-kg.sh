#!/bin/bash
# CONPORT-KG Production Deployment Script
# Status: READY TO USE - Run when ready to deploy to production
#
# Usage:
#   ./scripts/deploy-conport-kg.sh
#
# Environment:
#   COMPOSE_FILE - Path to docker-compose.yml (default: docker/conport-kg/docker-compose.yml)
#   BACKUP_BEFORE_DEPLOY - Backup before deployment (default: true)

set -e

COMPOSE_FILE="${COMPOSE_FILE:-docker/conport-kg/docker-compose.yml}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"

echo "======================================================================"
echo "CONPORT-KG Production Deployment"
echo "======================================================================"
echo "Compose file: $COMPOSE_FILE"
echo "Backup before deploy: $BACKUP_BEFORE_DEPLOY"
echo "Date: $(date)"
echo ""

# 1. Pre-deployment backup
if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
  echo "[Step 1/6] Pre-deployment backup..."
  if [ -f scripts/backup-conport-kg.sh ]; then
    ./scripts/backup-conport-kg.sh
  else
    echo "  ⚠️  Backup script not found, skipping..."
  fi
  echo ""
fi

# 2. Pull latest code (if using git)
if [ -d .git ]; then
  echo "[Step 2/6] Pulling latest code..."
  CURRENT_BRANCH=$(git branch --show-current)
  echo "  Current branch: $CURRENT_BRANCH"
  git pull origin "$CURRENT_BRANCH" || echo "  ⚠️  Git pull failed, continuing..."
  echo ""
fi

# 3. Build Docker images
echo "[Step 3/6] Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build --no-cache integration-bridge
echo "  ✅ Images built"
echo ""

# 4. Start services
echo "[Step 4/6] Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
echo "  ⏳ Waiting for services to be healthy (max 60s)..."
for i in {1..12}; do
  sleep 5
  HEALTHY=$(docker-compose -f "$COMPOSE_FILE" ps | grep -c "healthy" || echo "0")
  echo "    Checking... ($((i*5))s) - $HEALTHY services healthy"

  if [ "$HEALTHY" -ge 2 ]; then
    break
  fi
done

echo "  ✅ Services started"
echo ""

# 5. Health validation
echo "[Step 5/6] Running health checks..."

# PostgreSQL
echo -n "  PostgreSQL AGE: "
if docker exec conport-kg-postgres-age pg_isready -U dopemux_age >/dev/null 2>&1; then
  echo "✅"
else
  echo "❌ FAILED"
  echo "  Logs:"
  docker-compose -f "$COMPOSE_FILE" logs --tail=20 postgres-age
  exit 1
fi

# Integration Bridge
echo -n "  Integration Bridge: "
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3016/kg/health 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
  echo "✅ (HTTP $HTTP_STATUS)"
else
  echo "❌ FAILED (HTTP $HTTP_STATUS)"
  echo "  Logs:"
  docker-compose -f "$COMPOSE_FILE" logs --tail=20 integration-bridge
  exit 1
fi

# Redis (optional)
if docker ps --filter "name=conport-kg-redis" --format "{{.Names}}" 2>/dev/null | grep -q conport-kg-redis; then
  echo -n "  Redis: "
  if docker exec conport-kg-redis redis-cli ping >/dev/null 2>&1; then
    echo "✅"
  else
    echo "❌ FAILED"
  fi
fi

echo ""

# 6. Data validation
echo "[Step 6/6] Validating data..."
DECISION_COUNT=$(docker exec conport-kg-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -t -c "
  LOAD 'age';
  SET search_path = ag_catalog, conport_knowledge, public;
  SELECT * FROM cypher('conport_knowledge', \$\$ MATCH (d:Decision) RETURN COUNT(d) \$\$) as (count agtype);
" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$DECISION_COUNT" -ge 100 ]; then
  echo "  ✅ Data validation passed: $DECISION_COUNT decisions"
else
  echo "  ❌ Data validation failed: Only $DECISION_COUNT decisions (expected ~113)"
  exit 1
fi

echo ""
echo "======================================================================"
echo "🎉 Deployment Complete!"
echo "======================================================================"
echo ""
echo "Services:"
echo "  PostgreSQL AGE:      localhost:5455"
echo "  Integration Bridge:  http://localhost:3016/kg"
echo "  Redis:               localhost:6379"
echo ""
echo "Quick Tests:"
echo "  curl http://localhost:3016/kg/health"
echo "  curl http://localhost:3016/kg/decisions/recent"
echo ""
echo "Terminal UI:"
echo "  cd services/conport_kg_ui && npm run dev"
echo ""
echo "Monitor Logs:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "======================================================================"

exit 0
