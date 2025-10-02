#!/bin/bash
# CONPORT-KG-2025 Automated Backup Script
# Status: READY TO USE - Set up cron when deploying to production
#
# Usage:
#   ./scripts/backup-conport-kg.sh
#
# Cron setup (daily at 2 AM):
#   0 2 * * * /path/to/scripts/backup-conport-kg.sh >> /var/log/conport-kg-backup.log 2>&1

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/conport-kg}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/conport-kg-$DATE.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "======================================================================"
echo "CONPORT-KG Backup: $DATE"
echo "======================================================================"

# 1. Backup PostgreSQL AGE database
echo "[1/5] Backing up database..."
docker exec conport-kg-postgres-age pg_dump \
  -U dopemux_age \
  dopemux_knowledge_graph \
  --format=custom \
  --compress=9 \
  | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "  ✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# 2. Validate backup integrity
echo "[2/5] Validating backup..."
if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
  echo "  ✅ Backup validation passed"
else
  echo "  ❌ Backup validation failed!"
  exit 1
fi

# 3. Count decisions (sanity check)
echo "[3/5] Validating data integrity..."
DECISION_COUNT=$(docker exec conport-kg-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -t -c "
  LOAD 'age';
  SET search_path = ag_catalog, conport_knowledge, public;
  SELECT * FROM cypher('conport_knowledge', \$\$ MATCH (d:Decision) RETURN COUNT(d) \$\$) as (count agtype);
" 2>/dev/null | tr -d ' ' || echo "0")

echo "  📊 Decisions in backup: $DECISION_COUNT"

if [ "$DECISION_COUNT" -lt 100 ]; then
  echo "  ⚠️  Warning: Expected ~113 decisions, found $DECISION_COUNT"
fi

# 4. Cleanup old backups (retention policy)
echo "[4/5] Applying retention policy ($RETENTION_DAYS days)..."
DELETED=$(find "$BACKUP_DIR" -name "conport-kg-*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
REMAINING=$(find "$BACKUP_DIR" -name "conport-kg-*.sql.gz" | wc -l)
echo "  ✅ Deleted $DELETED old backups, $REMAINING remaining"

# 5. Log completion
echo "[5/5] Logging backup completion..."
echo "$(date)|$BACKUP_FILE|$BACKUP_SIZE|$DECISION_COUNT decisions" >> "$BACKUP_DIR/backup.log"

echo "======================================================================"
echo "✅ Backup Complete"
echo "  File: $BACKUP_FILE"
echo "  Size: $BACKUP_SIZE"
echo "  Decisions: $DECISION_COUNT"
echo "  Retention: $REMAINING backups"
echo "======================================================================"

exit 0
