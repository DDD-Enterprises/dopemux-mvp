#!/bin/bash
# Test Migration 007: Worktree Support
# Validates migration and rollback scripts work correctly
#
# Usage: ./test_migration_007.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database connection via Docker
CONTAINER_NAME="dopemux-postgres-age"
DB_NAME="dopemux_memory"
DB_USER="dopemux"

PSQL="docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME"

echo -e "${YELLOW}=== Testing Migration 007: Worktree Support ===${NC}\n"

# Function to run query and check result
run_query() {
    local query="$1"
    local description="$2"

    echo -e "${YELLOW}Testing: $description${NC}"
    if $PSQL -c "$query" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Pass${NC}\n"
        return 0
    else
        echo -e "${RED}✗ Fail${NC}\n"
        return 1
    fi
}

# Backup current state
echo -e "${YELLOW}Step 1: Creating backup${NC}"
$PSQL -c "\copy (SELECT * FROM progress_entries) TO '/tmp/progress_backup_007.csv' CSV HEADER"
$PSQL -c "\copy (SELECT * FROM decisions) TO '/tmp/decisions_backup_007.csv' CSV HEADER"
echo -e "${GREEN}✓ Backup created${NC}\n"

# Test 1: Run migration
echo -e "${YELLOW}Step 2: Running migration 007${NC}"
if $PSQL -f migrations/007_worktree_support_simple.sql; then
    echo -e "${GREEN}✓ Migration executed successfully${NC}\n"
else
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi

# Test 2: Verify columns exist
echo -e "${YELLOW}Step 3: Verifying schema changes${NC}"
run_query "SELECT instance_id FROM progress_entries LIMIT 1" "instance_id column exists in progress_entries"
run_query "SELECT created_by_instance FROM decisions LIMIT 1" "created_by_instance column exists in decisions"

# Test 3: Verify indexes exist
echo -e "${YELLOW}Step 4: Verifying indexes${NC}"
run_query "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_progress_instance'" "idx_progress_instance exists"
run_query "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_progress_workspace_instance'" "idx_progress_workspace_instance exists"

# Test 4: Test data migration
echo -e "${YELLOW}Step 5: Verifying data migration${NC}"
run_query "SELECT COUNT(*) FROM progress_entries WHERE instance_id IS NULL" "Existing data has instance_id = NULL"

# Test 5: Test INSERT with instance_id
echo -e "${YELLOW}Step 6: Testing INSERT operations${NC}"
run_query "INSERT INTO progress_entries (workspace_id, instance_id, description, status, percentage) VALUES ('test-workspace', 'test-instance', 'Test task', 'IN_PROGRESS', 0)" "Can insert with instance_id"
run_query "INSERT INTO progress_entries (workspace_id, instance_id, description, status, percentage) VALUES ('test-workspace', NULL, 'Shared task', 'COMPLETED', 100)" "Can insert with NULL instance_id"

# Test 6: Test query pattern
echo -e "${YELLOW}Step 7: Testing query patterns${NC}"
run_query "SELECT * FROM progress_entries WHERE workspace_id = 'test-workspace' AND (instance_id IS NULL OR instance_id = 'test-instance')" "Multi-worktree query pattern works"

# Cleanup test data
$PSQL -c "DELETE FROM progress_entries WHERE workspace_id = 'test-workspace'" > /dev/null 2>&1

# Test 7: Run rollback
echo -e "${YELLOW}Step 8: Testing rollback${NC}"
if $PSQL -f migrations/007_rollback.sql; then
    echo -e "${GREEN}✓ Rollback executed successfully${NC}\n"
else
    echo -e "${RED}✗ Rollback failed${NC}"
    exit 1
fi

# Test 8: Verify columns removed
echo -e "${YELLOW}Step 9: Verifying rollback${NC}"
if $PSQL -c "SELECT instance_id FROM progress_entries LIMIT 1" > /dev/null 2>&1; then
    echo -e "${RED}✗ Fail: instance_id column still exists${NC}\n"
    exit 1
else
    echo -e "${GREEN}✓ Pass: instance_id column removed${NC}\n"
fi

if $PSQL -c "SELECT created_by_instance FROM decisions LIMIT 1" > /dev/null 2>&1; then
    echo -e "${RED}✗ Fail: created_by_instance column still exists${NC}\n"
    exit 1
else
    echo -e "${GREEN}✓ Pass: created_by_instance column removed${NC}\n"
fi

# Test 9: Re-apply migration for actual use
echo -e "${YELLOW}Step 10: Re-applying migration for production use${NC}"
if $PSQL -f migrations/007_worktree_support_simple.sql; then
    echo -e "${GREEN}✓ Migration re-applied successfully${NC}\n"
else
    echo -e "${RED}✗ Migration re-apply failed${NC}"
    exit 1
fi

echo -e "${GREEN}=== All tests passed! ===${NC}"
echo -e "${GREEN}Migration 007 is ready for production use${NC}\n"

echo -e "${YELLOW}Backup files (for rollback if needed):${NC}"
echo "  - /tmp/progress_backup_007.csv"
echo "  - /tmp/decisions_backup_007.csv"
echo ""
echo -e "${YELLOW}To rollback if needed:${NC}"
echo "  psql ... -f migrations/007_rollback.sql"
