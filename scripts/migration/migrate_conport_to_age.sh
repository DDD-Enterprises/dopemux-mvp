#!/bin/bash
# Master Migration Script: ConPort SQLite → PostgreSQL AGE + DDG Backfill
#
# This script orchestrates the complete migration:
# 1. Backup SQLite database
# 2. Export SQLite → JSON
# 3. Rebuild postgres-age container with apache/age image
# 4. Import JSON → PostgreSQL AGE
# 5. Backfill DDG with historical decisions
# 6. Verify everything works

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SQLITE_PATH="$PROJECT_ROOT/context_portal/context.db"
BACKUP_PATH="$PROJECT_ROOT/backups/context_$(date +%Y%m%d_%H%M%S).db"
EXPORT_JSON="$SCRIPT_DIR/conport_export.json"
PG_DB_URL="postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ConPort → PostgreSQL AGE Migration + DDG Backfill      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📂 Project:   $PROJECT_ROOT"
echo "📁 SQLite:    $SQLITE_PATH"
echo "💾 Backup:    $BACKUP_PATH"
echo "📝 Export:    $EXPORT_JSON"
echo ""

# Ask for confirmation
read -p "🤔 Ready to proceed with migration? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

# ============================================================================
# PHASE 1: BACKUP
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: BACKUP SQLITE DATABASE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ ! -f "$SQLITE_PATH" ]; then
    echo -e "${RED}❌ SQLite database not found: $SQLITE_PATH${NC}"
    exit 1
fi

mkdir -p "$(dirname "$BACKUP_PATH")"
cp "$SQLITE_PATH" "$BACKUP_PATH"

if [ -f "$BACKUP_PATH" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    echo -e "${GREEN}✅ Backup created: $BACKUP_SIZE${NC}"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

# ============================================================================
# PHASE 2: EXPORT SQLITE → JSON
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: EXPORT SQLITE → JSON${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

python3 "$SCRIPT_DIR/export_sqlite_to_json.py" \
    --sqlite-path "$SQLITE_PATH" \
    --output "$EXPORT_JSON"

if [ ! -f "$EXPORT_JSON" ]; then
    echo -e "${RED}❌ Export failed!${NC}"
    exit 1
fi

# ============================================================================
# PHASE 3: REBUILD POSTGRES-AGE CONTAINER
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 3: REBUILD POSTGRES-AGE WITH APACHE/AGE IMAGE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo "⚠️  This will DESTROY the current dopemux-postgres-age container!"
echo "   (Current container has broken AGE and minimal data)"
read -p "🤔 Continue with rebuild? (yes/no): " rebuild_confirm

if [ "$rebuild_confirm" != "yes" ]; then
    echo "❌ Rebuild cancelled - migration incomplete"
    echo "   Your data is safe in: $BACKUP_PATH"
    exit 1
fi

cd "$PROJECT_ROOT/docker/memory-stack"

echo "🛑 Stopping postgres-age container..."
docker-compose -f docker-compose.age.yml down postgres-age

echo "🗑️  Removing old volume..."
docker volume rm dopemux-mvp_age_data 2>/dev/null || echo "   (Volume already removed)"

echo "🏗️  Building new postgres-age with apache/age:latest..."
docker-compose -f docker-compose.age.yml up -d postgres-age

echo "⏳ Waiting for PostgreSQL to be ready (30 seconds)..."
sleep 30

# Verify AGE is working
echo "🧪 Testing AGE extension..."
docker exec dopemux-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -c "LOAD 'age';" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ AGE extension working!${NC}"
else
    echo -e "${RED}❌ AGE extension still broken!${NC}"
    exit 1
fi

# ============================================================================
# PHASE 4: IMPORT JSON → POSTGRESQL AGE
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 4: IMPORT JSON → POSTGRESQL AGE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

cd "$SCRIPT_DIR"

python3 import_to_postgresql_age.py \
    --json-path "$EXPORT_JSON" \
    --db-url "$PG_DB_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Import failed!${NC}"
    echo "   Your data is safe in backup: $BACKUP_PATH"
    exit 1
fi

# ============================================================================
# PHASE 5: BACKFILL DDG
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 5: BACKFILL DDG WITH HISTORICAL DECISIONS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

python3 backfill_ddg.py \
    --conport-db "$PG_DB_URL" \
    --bridge-url "http://localhost:3016" \
    --batch-size 10

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  DDG backfill had issues (check logs above)${NC}"
    echo "   ConPort migration still successful"
fi

# ============================================================================
# PHASE 6: VERIFICATION
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 6: VERIFICATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo "🧪 Testing ConPort PostgreSQL..."
CONPORT_COUNT=$(docker exec dopemux-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -t -c "SELECT COUNT(*) FROM ag_catalog.decisions;" 2>&1 | tr -d ' ')

echo "   ConPort decisions: $CONPORT_COUNT"

echo "🧪 Testing DDG PostgreSQL..."
DDG_COUNT=$(docker exec dope-decision-graph-postgres psql -U dopemux_age -d dopemux_knowledge_graph -t -c "SELECT COUNT(*) FROM ddg_decisions;" 2>&1 | tr -d ' ')

echo "   DDG decisions: $DDG_COUNT"

echo "🧪 Testing AGE graph queries..."
docker exec dopemux-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -c "SELECT ag_catalog.cypher('conport_knowledge', \$\$MATCH (n) RETURN count(n)\$\$) as (count agtype);" 2>&1

# Final summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  MIGRATION COMPLETE!                                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "✅ SQLite backup:      $BACKUP_PATH"
echo "✅ ConPort PostgreSQL: $CONPORT_COUNT decisions"
echo "✅ DDG PostgreSQL:     $DDG_COUNT decisions"
echo "✅ AGE graph:          Operational"
echo ""
echo "📝 Next Steps:"
echo "   1. Update conport-mcp to use PostgreSQL instead of SQLite"
echo "   2. Test mcp__conport__* tools in Claude Code"
echo "   3. Test ddg-mcp.related_text for global search"
echo "   4. Monitor enhanced_server.py for event publishing"
echo ""
echo "🔄 Rollback: If issues, restore from $BACKUP_PATH"
echo ""
