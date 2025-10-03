#!/bin/bash
# MCP Server Health Report
# Checks all dopemux MCP servers and generates status report

echo "=========================================="
echo "MCP Server Health Report"
echo "=========================================="
echo ""
date
echo ""

echo "=== MCP Servers Status ==="
echo ""

# Function to test HTTP endpoint
test_endpoint() {
    local port=$1
    local name=$2

    http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health --max-time 2 2>/dev/null)

    if [ "$http_code" = "200" ]; then
        echo "✅ $name (port $port): Healthy (HTTP 200)"
    elif [ "$http_code" = "404" ]; then
        echo "✅ $name (port $port): Responding (HTTP 404 - no /health endpoint)"
    else
        echo "⚠️  $name (port $port): Not responding or error"
    fi
}

# Test each MCP server
test_endpoint 3002 "context7        "
test_endpoint 3003 "zen             "
test_endpoint 3004 "conport         "
test_endpoint 3006 "serena          "
test_endpoint 3008 "exa             "
test_endpoint 3009 "gptr-mcp        "
test_endpoint 3012 "desktop-commander"

echo ""
echo "=== MCP Server Containers ==="
echo ""

docker ps --filter "name=mcp-" --format "table {{.Names}}\t{{.Status}}" | grep -v "metamcp-pg"

echo ""
echo "=== Port Listeners ==="
echo ""

lsof -iTCP -sTCP:LISTEN -n -P | grep -E ":(3001|3002|3003|3004|3006|3007|3008|3009|3012)" | awk '{print $9}' | sort -t: -k2 -n || echo "None found"

echo ""
echo "=== Summary ==="
echo ""

# Count healthy containers
healthy_count=$(docker ps --filter "name=mcp-" --filter "health=healthy" | grep -v "metamcp-pg" | wc -l | tr -d ' ')
total_count=$(docker ps --filter "name=mcp-" | grep -v "metamcp-pg\|NAMES" | wc -l | tr -d ' ')

echo "Healthy containers: $healthy_count/$total_count"
echo ""

# List ports listening
listening_ports=$(lsof -iTCP -sTCP:LISTEN -n -P | grep -E ":(3001|3002|3003|3004|3006|3007|3008|3009|3012)" | awk '{print $9}' | cut -d: -f2 | sort -n | tr '\n' ' ')

echo "Ports listening: $listening_ports"
echo ""
echo "=========================================="
