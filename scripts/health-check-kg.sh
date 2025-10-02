#!/bin/bash
# CONPORT-KG Health Check Script
# Status: READY TO USE - Set up cron when deploying to production
#
# Usage:
#   ./scripts/health-check-kg.sh
#
# Cron setup (every 5 minutes):
#   */5 * * * * /path/to/scripts/health-check-kg.sh >> /var/log/conport-kg-health.log 2>&1

set -e

ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"  # Optional: Slack/Discord webhook
EXIT_CODE=0
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "======================================================================"
echo "CONPORT-KG Health Check: $TIMESTAMP"
echo "======================================================================"

# 1. Check PostgreSQL AGE
echo -n "[1/5] PostgreSQL AGE Database: "
if docker exec conport-kg-postgres-age pg_isready -U dopemux_age -d dopemux_knowledge_graph >/dev/null 2>&1; then
  echo "✅ Healthy"
else
  echo "❌ UNHEALTHY"
  EXIT_CODE=1
fi

# 2. Check Integration Bridge API
echo -n "[2/5] Integration Bridge API: "
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3016/kg/health 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
  echo "✅ Healthy (HTTP $HTTP_STATUS)"
else
  echo "❌ UNHEALTHY (HTTP $HTTP_STATUS)"
  EXIT_CODE=1
fi

# 3. Check Redis (if running)
if docker ps --filter "name=conport-kg-redis" --format "{{.Names}}" 2>/dev/null | grep -q conport-kg-redis; then
  echo -n "[3/5] Redis Event Bus: "
  if docker exec conport-kg-redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Healthy"
  else
    echo "❌ UNHEALTHY"
    EXIT_CODE=1
  fi
else
  echo "[3/5] Redis Event Bus: ⊘ Not running (optional)"
fi

# 4. Check Container Health
echo -n "[4/5] Container Status: "
UNHEALTHY=$(docker ps --filter "name=conport-kg" --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null | wc -l)
if [ "$UNHEALTHY" -eq 0 ]; then
  echo "✅ All containers healthy"
else
  echo "❌ $UNHEALTHY containers unhealthy"
  docker ps --filter "name=conport-kg" --format "table {{.Names}}\t{{.Status}}\t{{.Health}}"
  EXIT_CODE=1
fi

# 5. Check Data Integrity
echo -n "[5/5] Data Integrity: "
DECISION_COUNT=$(docker exec conport-kg-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -t -c "
  LOAD 'age';
  SET search_path = ag_catalog, conport_knowledge, public;
  SELECT * FROM cypher('conport_knowledge', \$\$ MATCH (d:Decision) RETURN COUNT(d) \$\$) as (count agtype);
" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$DECISION_COUNT" -ge 100 ]; then
  echo "✅ $DECISION_COUNT decisions present"
else
  echo "❌ Only $DECISION_COUNT decisions (expected ~113)"
  EXIT_CODE=1
fi

# Summary
echo "======================================================================"
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ ALL CHECKS PASSED"
else
  echo "❌ HEALTH CHECK FAILED"

  # Send alert if webhook configured
  if [ -n "$ALERT_WEBHOOK" ]; then
    curl -X POST "$ALERT_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{\"text\": \"⚠️ CONPORT-KG health check failed at $TIMESTAMP\"}" \
      >/dev/null 2>&1 || true
  fi
fi
echo "======================================================================"

exit $EXIT_CODE
