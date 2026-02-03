#!/bin/bash
# Complete verification of all MCP startup fixes + /info endpoint
# Run this after implementing all changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  MCP Startup Fixes + /info Endpoint - Complete Verification ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

# Test function
run_test() {
    local name="$1"
    shift
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if "$@"; then
        echo "✅ PASS: $name"
        ((PASSED++))
    else
        echo "❌ FAIL: $name"
        ((FAILED++))
    fi
    echo ""
}

# Test 1: Docker Compose Validation
test_compose_validation() {
    docker compose config >/dev/null 2>&1
}

# Test 2: No Duplicate Networks
test_no_duplicate_networks() {
    local compose_file="docker-compose.yml"
    
    # More accurate approach: check each service's networks: section directly
    # Extract just the networks list for each service
    
    # Check plane-coordinator
    local plane_networks=$(awk '/plane-coordinator:/,/^  [a-z-]+:/' "$compose_file" | awk '/networks:/,/^    [a-z]+:/' | grep "^      -" | sort | uniq | wc -l | tr -d ' ')
    local plane_total=$(awk '/plane-coordinator:/,/^  [a-z-]+:/' "$compose_file" | awk '/networks:/,/^    [a-z]+:/' | grep "^      -" | wc -l | tr -d ' ')
    [ "$plane_networks" -eq "$plane_total" ] || return 1
    
    # Check leantime-bridge
    local leantime_networks=$(awk '/leantime-bridge:/,/^  [a-z-]+:/' "$compose_file" | awk '/networks:/,/^    [a-z]+:/' | grep "^      -" | sort | uniq | wc -l | tr -d ' ')
    local leantime_total=$(awk '/leantime-bridge:/,/^  [a-z-]+:/' "$compose_file" | awk '/networks:/,/^    [a-z]+:/' | grep "^      -" | wc -l | tr -d ' ')
    [ "$leantime_networks" -eq "$leantime_total" ] || return 1
    
    # Check activity-capture
    local activity_networks=$(awk '/activity-capture:/,/^  [a-z-]+:/' "$compose_file" | awk '/networks:/,/^    [a-z]+:/' | grep "^      -" | sort | uniq | wc -l | tr -d ' ')
    local activity_total=$(awk '/activity-capture:/,/^  [a-z-]+:/' "$compose_file" | awk '/networks:/,/^    [a-z]+:/' | grep "^      -" | wc -l | tr -d ' ')
    [ "$activity_networks" -eq "$activity_total" ] || return 1
    
    return 0
}

# Test 3: Script Has Validation
test_script_validation() {
    grep -q "docker compose config" start-all-mcp-servers.sh
}

# Test 4: ENABLE_LEANTIME Present
test_enable_leantime() {
    grep -q "ENABLE_LEANTIME" start-all-mcp-servers.sh
}

# Test 5: COMPOSE_PROJECT_NAME Set
test_compose_project_name() {
    grep -q "COMPOSE_PROJECT_NAME" start-all-mcp-servers.sh
}

# Test 6: /info Endpoint Exists in Code
test_info_endpoint_exists() {
    grep -q "handle_info" leantime-bridge/leantime_bridge/http_server.py
}

# Test 7: /info Endpoint Enhanced
test_info_endpoint_enhanced() {
    # Check for leantime section
    grep -A 5 "handle_info" leantime-bridge/leantime_bridge/http_server.py | grep -q "leantime"
}

# Test 8: Test Script Exists
test_test_script_exists() {
    [ -f "leantime-bridge/test_info_endpoint.py" ] && [ -x "leantime-bridge/test_info_endpoint.py" ]
}

# Test 9: Documentation Exists
test_documentation_exists() {
    [ -f "MCP_STARTUP_FIXES.md" ] && \
    [ -f "QUICK_FIX_SUMMARY.md" ] && \
    [ -f "leantime-bridge/INFO_ENDPOINT.md" ] && \
    [ -f "IMPLEMENTATION_COMPLETE.md" ]
}

# Test 10: No Error Swallowing
test_no_error_swallowing() {
    # The critical line should NOT have || true
    ! grep "docker-compose up -d --build.*|| true" start-all-mcp-servers.sh | grep -v "docker start.*|| true"
}

# Run all tests
run_test "Docker Compose Validation" test_compose_validation
run_test "No Duplicate Networks" test_no_duplicate_networks
run_test "Script Has Validation Check" test_script_validation
run_test "ENABLE_LEANTIME Gate Present" test_enable_leantime
run_test "COMPOSE_PROJECT_NAME Set" test_compose_project_name
run_test "/info Endpoint Exists" test_info_endpoint_exists
run_test "/info Endpoint Enhanced" test_info_endpoint_enhanced
run_test "/info Test Script Exists" test_test_script_exists
run_test "Complete Documentation" test_documentation_exists
run_test "No Critical Error Swallowing" test_no_error_swallowing

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Test Summary                                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  🎉 ALL TESTS PASSED - Implementation Complete!            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next Steps:"
    echo "  1. Test startup: ./start-all-mcp-servers.sh"
    echo "  2. With Leantime: ENABLE_LEANTIME=1 ./start-all-mcp-servers.sh"
    echo "  3. Test /info: curl http://localhost:3015/info | jq"
    echo ""
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  SOME TESTS FAILED - Review Implementation             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    exit 1
fi
