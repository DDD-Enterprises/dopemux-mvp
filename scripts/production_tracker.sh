#!/bin/bash
# Production Readiness Progress Tracker
# Usage: ./scripts/production_tracker.sh [day]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DAY="${1:-check}"

echo "=========================================="
echo "Multi-Workspace Production Tracker"
echo "=========================================="
echo ""

# Function to count tests in a file
count_tests() {
    local file="$1"
    if [ -f "$file" ]; then
        grep -c "^def test_\|^async def test_" "$file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Function to check if file exists and has content
check_integration() {
    local file="$1"
    local pattern="$2"
    if [ -f "$file" ] && grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# Service Status
echo "📊 Service Completion Status:"
echo ""

# 1. dope-context
echo -n "1. dope-context:         "
if [ -f "services/dope-context/tests/test_mcp_server.py" ]; then
    tests=$(count_tests "services/dope-context/tests/test_mcp_server.py")
    echo -e "${GREEN}✅ COMPLETE${NC} (${tests} tests)"
else
    echo -e "${RED}❌ NOT STARTED${NC}"
fi

# 2. serena
echo -n "2. serena:               "
mcp_integration=$(check_integration "services/serena/v2/mcp_server.py" "workspace_path.*Optional")
wrapper_tests=$(count_tests "services/serena/tests/test_multi_workspace.py")
if [ "$mcp_integration" = "$(echo -e ${GREEN}✓${NC})" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC} (${wrapper_tests} tests)"
else
    echo -e "${YELLOW}🟡 70% - MCP integration needed${NC} (${wrapper_tests} wrapper tests)"
fi

# 3. conport_kg
echo -n "3. conport_kg:           "
age_integration=$(check_integration "services/conport_kg/age_client.py" "workspace_path")
kg_tests=$(count_tests "services/conport_kg/tests/test_workspace_support.py")
if [ "$age_integration" = "$(echo -e ${GREEN}✓${NC})" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC} (${kg_tests} tests)"
else
    echo -e "${YELLOW}🟡 60% - AGE integration needed${NC} (${kg_tests} utility tests)"
fi

# 4. orchestrator
echo -n "4. orchestrator:         "
orch_integration=$(check_integration "services/orchestrator/src/router.py" "workspace_context")
orch_tests=$(count_tests "services/orchestrator/tests/test_workspace_support.py")
if [ "$orch_integration" = "$(echo -e ${GREEN}✓${NC})" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC} (${orch_tests} tests)"
else
    echo -e "${YELLOW}🟢 90% - Router integration needed${NC} (${orch_tests} utility tests)"
fi

# 5. activity-capture
echo -n "5. activity-capture:     "
activity_integration=$(check_integration "services/activity-capture/activity_tracker.py" "workspace")
if [ "$activity_integration" = "$(echo -e ${GREEN}✓${NC})" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${YELLOW}🟢 85% - Tracker integration needed${NC}"
fi

# 6-10. Future services
echo -n "6. task-orchestrator:    "
if [ -d "services/task-orchestrator/tests" ] && [ -f "services/task-orchestrator/tests/test_workspace.py" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}⚪ 0% - Not started${NC}"
fi

echo -n "7. session_intelligence: "
if [ -d "services/session_intelligence/tests" ] && [ -f "services/session_intelligence/tests/test_workspace.py" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}⚪ 0% - Not started${NC}"
fi

echo -n "8. mcp-client:           "
if [ -d "services/mcp-client/tests" ] && [ -f "services/mcp-client/tests/test_workspace.py" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}⚪ 0% - Not started${NC}"
fi

echo -n "9. adhd_engine:          "
if [ -f "services/adhd_engine/tests/test_workspace.py" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}⚪ 0% - Not started${NC}"
fi

echo -n "10. intelligence:        "
if [ -d "services/intelligence/tests" ] && [ -f "services/intelligence/tests/test_workspace.py" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}⚪ 0% - Not started${NC}"
fi

echo ""
echo "=========================================="

# Test Summary
echo "🧪 Test Summary:"
echo ""

total_tests=0
workspace_tests=$(find services -name "test_workspace*.py" -o -name "test_multi_workspace*.py" 2>/dev/null | wc -l | xargs)
all_tests=$(find services -name "test_*.py" 2>/dev/null | wc -l | xargs)

echo "Total test files:          ${all_tests}"
echo "Workspace-specific tests:  ${workspace_tests}"
echo ""

# Run tests if requested
if [ "$DAY" = "test" ]; then
    echo "Running multi-workspace tests..."
    echo ""
    ./run_all_multi_workspace_tests.sh
fi

# Day-specific checklist
if [ "$DAY" = "1" ]; then
    echo "=========================================="
    echo "📋 Day 1 Checklist:"
    echo "=========================================="
    echo ""
    echo "[ ] 1. Complete orchestrator integration (1.5h)"
    echo "    - Modify services/orchestrator/src/router.py"
    echo "    - Add workspace_context helper"
    echo "    - Run: pytest services/orchestrator/tests/"
    echo ""
    echo "[ ] 2. Complete activity-capture integration (1.5h)"
    echo "    - Modify services/activity-capture/activity_tracker.py"
    echo "    - Add workspace enrichment"
    echo "    - Run: pytest services/activity-capture/tests/"
    echo ""
    echo "[ ] 3. Start serena MCP integration (4h)"
    echo "    - Modify 10 MCP tools in services/serena/v2/mcp_server.py"
    echo "    - Add workspace_path params"
    echo "    - Test with: pytest services/serena/tests/"
    echo ""
    echo "Target: 15+ new tests passing"
    echo ""
elif [ "$DAY" = "2" ]; then
    echo "=========================================="
    echo "📋 Day 2 Checklist:"
    echo "=========================================="
    echo ""
    echo "[ ] 1. Finish serena MCP (2h if not done)"
    echo "[ ] 2. ConPort AGE integration (4h)"
    echo "[ ] 3. task-orchestrator (2h)"
    echo ""
    echo "Target: 30+ new tests passing"
    echo ""
fi

echo "=========================================="
echo "📁 Key Files to Track:"
echo "=========================================="
echo ""
echo "Documentation:"
echo "  - COMPLETION_CHECKLIST.md (detailed tasks)"
echo "  - PRODUCTION_READINESS_QUICK_REF.md (daily goals)"
echo "  - PRODUCTION_READINESS_PLAN.md (full context)"
echo ""
echo "Scripts:"
echo "  - ./scripts/production_tracker.sh [day] (this script)"
echo "  - ./run_all_multi_workspace_tests.sh (test runner)"
echo ""
echo "=========================================="
echo ""

# Final summary
completed=1  # dope-context
started=4    # serena, conport_kg, orchestrator, activity-capture
total=10

completion_pct=$((completed * 100 / total))

echo "Overall Progress: ${completed}/${total} services complete (${completion_pct}%)"
echo "In Progress: ${started} services"
echo "Remaining: $((total - completed - started)) services"
echo ""
echo -e "${BLUE}Ready to execute Day 1! 🚀${NC}"
echo ""
