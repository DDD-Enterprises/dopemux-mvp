#!/bin/bash
# CONPORT-KG Database Restoration Script
# Status: READY TO USE
#
# Usage:
#   ./scripts/restore-conport-kg.sh <backup-file.sql.gz>

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file.sql.gz>"
  echo ""
  echo "Available backups:"
  ls -lh /var/backups/conport-kg/*.sql.gz 2>/dev/null | tail -10 || echo "  No backups found"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "======================================================================"
echo "CONPORT-KG Database Restoration"
echo "======================================================================"
echo "Backup file: $BACKUP_FILE"
echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""
echo "⚠️  WARNING: This will REPLACE the current database!"
echo "⚠️  All existing data will be lost!"
echo ""
read -p "Continue? Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Restoration cancelled"
  exit 0
fi

echo ""
echo "[Step 1/5] Stopping Integration Bridge..."
docker-compose -f docker/conport-kg/docker-compose.yml stop integration-bridge 2>/dev/null || \
  docker stop conport-kg-integration-bridge 2>/dev/null || \
  echo "  Integration Bridge not running"

echo ""
echo "[Step 2/5] Dropping existing database..."
docker exec conport-kg-postgres-age psql -U dopemux_age -c "
  DROP DATABASE IF EXISTS dopemux_knowledge_graph;
  CREATE DATABASE dopemux_knowledge_graph;
"
echo "  ✅ Database recreated"

echo ""
echo "[Step 3/5] Restoring from backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i conport-kg-postgres-age pg_restore \
  -U dopemux_age \
  -d dopemux_knowledge_graph \
  --format=custom \
  --no-owner \
  --no-acl
echo "  ✅ Backup restored"

echo ""
echo "[Step 4/5] Validating restoration..."
DECISION_COUNT=$(docker exec conport-kg-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -t -c "
  LOAD 'age';
  SET search_path = ag_catalog, conport_knowledge, public;
  SELECT * FROM cypher('conport_knowledge', \$\$ MATCH (d:Decision) RETURN COUNT(d) \$\$) as (count agtype);
" | tr -d ' ')

echo "  ✅ Decisions restored: $DECISION_COUNT"

echo ""
echo "[Step 5/5] Restarting Integration Bridge..."
docker-compose -f docker/conport-kg/docker-compose.yml start integration-bridge 2>/dev/null || \
  docker start conport-kg-integration-bridge 2>/dev/null || \
  echo "  Start manually with: docker-compose up -d"

echo ""
echo "======================================================================"
echo "✅ Restoration Complete"
echo "  Decisions: $DECISION_COUNT"
echo "  From backup: $BACKUP_FILE"
echo "======================================================================"

exit 0
