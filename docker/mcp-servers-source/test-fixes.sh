#!/bin/bash
# Quick verification of MCP startup fixes

set -e

echo "=== MCP Startup Fixes Verification ==="
echo ""

# Test 1: Compose validation
echo "Test 1: docker-compose.yml validation"
if docker compose config >/dev/null 2>&1; then
    echo "✅ PASS: docker-compose.yml is valid"
else
    echo "❌ FAIL: docker-compose.yml validation failed"
    exit 1
fi
echo ""

# Test 2: Check for duplicate networks
echo "Test 2: Verify no duplicate networks in compose file"
duplicates=$(grep -A 5 "networks:" docker-compose.yml | grep -E "^\s+- dopemux-network$" | wc -l | tr -d ' ')
echo "   Found $duplicates instances of '- dopemux-network' entries"

# Count services that SHOULD have dopemux-network
services_with_dopemux=$(grep -B 10 "networks:" docker-compose.yml | grep -E "^\s+[a-z-]+:" | wc -l | tr -d ' ')
echo "   Found approx $services_with_dopemux services with network sections"

if [ "$duplicates" -eq "$services_with_dopemux" ]; then
    echo "❌ FAIL: Likely duplicates still present (each service should only list network once)"
    exit 1
fi
echo "✅ PASS: Network assignments appear deduplicated"
echo ""

# Test 3: Check script has validation
echo "Test 3: Verify script validates compose before startup"
if grep -q "docker compose config" start-all-mcp-servers.sh; then
    echo "✅ PASS: Script includes compose validation"
else
    echo "❌ FAIL: Script missing compose validation"
    exit 1
fi
echo ""

# Test 4: Check ENABLE_LEANTIME gate
echo "Test 4: Verify ENABLE_LEANTIME integration"
if grep -q "ENABLE_LEANTIME" start-all-mcp-servers.sh; then
    echo "✅ PASS: Script includes ENABLE_LEANTIME gate"
else
    echo "❌ FAIL: Script missing ENABLE_LEANTIME gate"
    exit 1
fi
echo ""

# Test 5: Check project name
echo "Test 5: Verify COMPOSE_PROJECT_NAME set"
if grep -q "COMPOSE_PROJECT_NAME" start-all-mcp-servers.sh; then
    echo "✅ PASS: Script sets COMPOSE_PROJECT_NAME"
else
    echo "❌ FAIL: Script missing COMPOSE_PROJECT_NAME"
    exit 1
fi
echo ""

echo "=== All Verification Tests Passed ==="
echo ""
echo "Next steps:"
echo "1. Stop existing containers: docker compose down"
echo "2. Test startup without Leantime: ./start-all-mcp-servers.sh"
echo "3. Test startup with Leantime: ENABLE_LEANTIME=1 ./start-all-mcp-servers.sh"
