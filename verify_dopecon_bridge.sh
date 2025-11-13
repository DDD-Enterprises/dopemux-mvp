#!/usr/bin/env bash
# DopeconBridge Migration Verification Script
# Usage: ./verify_dopecon_bridge.sh [--workspace /path/to/workspace]

set -e

# Parse arguments
WORKSPACE_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace|-w)
            WORKSPACE_PATH="$2"
            shift 2
            ;;
        --help|-h)
            cat << 'HELP'
Usage: ./verify_dopecon_bridge.sh [OPTIONS]

OPTIONS:
    --workspace, -w PATH    Verify for specific workspace
    --help, -h             Show this help message

EXAMPLES:
    ./verify_dopecon_bridge.sh                    # Verify current workspace
    ./verify_dopecon_bridge.sh -w ~/code/project  # Verify specific workspace
HELP
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Determine workspace
if [ -n "$WORKSPACE_PATH" ]; then
    WORKSPACE_ID="$WORKSPACE_PATH"
elif [ -n "$DEFAULT_WORKSPACE_PATH" ]; then
    WORKSPACE_ID="$DEFAULT_WORKSPACE_PATH"
else
    WORKSPACE_ID="$(pwd)"
fi

echo "🔍 DopeconBridge Migration Verification"
if [ -n "$WORKSPACE_PATH" ]; then
    echo "Workspace: $WORKSPACE_ID"
fi
echo "========================================"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((FAIL++))
    fi
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN++))
}

echo "1. Checking for old ConPort direct access patterns..."
if ! rg "ConPortSQLiteClient" services/ --type py 2>/dev/null | grep -v "test_" | grep -v "__pycache__" > /dev/null 2>&1; then
    check "No direct SQLite clients found"
else
    warn "Found ConPortSQLiteClient usage - review needed"
fi

echo
echo "2. Checking for DopeconBridge client imports..."
if rg "from services.shared.dopecon_bridge_client import" services/ --type py > /dev/null 2>&1; then
    check "DopeconBridge client imports found"
else
    warn "No bridge client imports found"
fi

echo
echo "3. Checking service adapters..."
ADAPTER_COUNT=$(find services -name "*bridge*adapter*.py" -o -name "dopecon_integration.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$ADAPTER_COUNT" -ge 15 ]; then
    check "Found $ADAPTER_COUNT service adapters (expected 15+)"
else
    warn "Only found $ADAPTER_COUNT adapters (expected 15+)"
fi

echo
echo "4. Checking Docker Compose files..."
if grep "DOPECON_BRIDGE_URL" docker-compose.master.yml > /dev/null 2>&1; then
    check "docker-compose.master.yml has DOPECON_BRIDGE_URL"
else
    warn "docker-compose.master.yml missing DOPECON_BRIDGE_URL"
fi

if grep "DOPECON_BRIDGE_URL" docker-compose.unified.yml > /dev/null 2>&1; then
    check "docker-compose.unified.yml has DOPECON_BRIDGE_URL"
else
    warn "docker-compose.unified.yml missing DOPECON_BRIDGE_URL"
fi

echo
echo "5. Checking environment templates..."
if grep "DOPECON_BRIDGE_URL" .env.example > /dev/null 2>&1; then
    check ".env.example has DOPECON_BRIDGE_URL"
else
    warn ".env.example missing DOPECON_BRIDGE_URL"
fi

if [ -f ".env.dopecon_bridge.example" ]; then
    check ".env.dopecon_bridge.example exists"
else
    warn ".env.dopecon_bridge.example not found"
fi

echo
echo "6. Checking shared client library..."
if [ -d "services/shared/dopecon_bridge_client" ]; then
    check "Shared client library exists"
else
    warn "Shared client library not found"
fi

if [ -f "services/shared/dopecon_bridge_client/client.py" ]; then
    check "Main client module exists"
else
    warn "Main client module not found"
fi

echo
echo "7. Checking key service adapters..."
SERVICES=(
    "adhd_engine/bridge_integration.py"
    "voice-commands/bridge_adapter.py"
    "task-orchestrator/bridge_adapter.py"
    "serena/v2/bridge_adapter.py"
    "dopemux-gpt-researcher/bridge_adapter.py"
    "genetic_agent/dopecon_integration.py"
)

for service in "${SERVICES[@]}"; do
    if [ -f "services/$service" ]; then
        check "Found adapter: $service"
    else
        warn "Missing adapter: $service"
    fi
done

echo
echo "8. Checking documentation..."
DOCS=(
    "DOPECONBRIDGE_MASTER_INDEX.md"
    "DOPECONBRIDGE_SERVICE_CATALOG.md"
    "DOPECONBRIDGE_COMPLETE_FINAL.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check "Found doc: $doc"
    else
        warn "Missing doc: $doc"
    fi
done

echo
echo "========================================"
echo "📊 Verification Summary"
echo "========================================"
echo -e "${GREEN}✅ Passed: $PASS${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARN${NC}"
echo -e "${RED}❌ Failed: $FAIL${NC}"
echo

if [ $FAIL -eq 0 ] && [ $WARN -le 5 ]; then
    echo -e "${GREEN}🎉 DopeconBridge migration verified successfully!${NC}"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Migration mostly complete, minor issues found${NC}"
    exit 0
else
    echo -e "${RED}❌ Migration has issues that need attention${NC}"
    exit 1
fi
