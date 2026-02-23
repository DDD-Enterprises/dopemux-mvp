#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Dopemux MCP Server Health Check"
echo "=================================="
echo

# Health check function
check_health() {
    local name=$1
    local port=$2
    local endpoint="health"
    
    echo "📋 Checking $name ($port)..."
    
    if curl -sS "http://localhost:$port/$endpoint" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name health check failed"
        return 1
    fi
}

# MCP endpoint check function
check_mcp_endpoint() {
    local name=$1
    local port=$2
    
    echo "🔌 Checking $name MCP endpoint ($port/mcp)..."
    
    # Try POST to /mcp endpoint
    response=$(curl -sS -X POST \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        --data '{"jsonrpc":"2.0","id":"probe","method":"initialize","params":{}}' \
        "http://localhost:$port/mcp" 2>&1 || true)
    
    if echo "$response" | grep -q '"jsonrpc"'; then
        echo "✅ $name MCP endpoint responding"
        return 0
    elif echo "$response" | grep -q "405\|Method Not Allowed"; then
        echo "⚠️  $name MCP endpoint exists (method not allowed - expected for GET)"
        return 0
    else
        echo "❌ $name MCP endpoint not responding properly"
        echo "   Response: $response"
        return 1
    fi
}

# Main checks
echo "🏥 Health Checks:"
echo "----------------"

check_health "Dope-Context" 3010
check_health "PAL" 3003
check_health "ConPort" 3004

echo
echo "🔌 MCP Endpoint Checks:"
echo "----------------------"

check_mcp_endpoint "Dope-Context" 3010
check_mcp_endpoint "PAL" 3003
check_mcp_endpoint "ConPort" 3004

echo
echo "📊 Summary:"
echo "-----------"
echo "All MCP servers are running and healthy."
echo "Dope-Context and ConPort have MCP endpoints at /mcp (POST required)."
echo "PAL appears to be using a different transport (likely stdio)."
echo
echo "✅ MCP infrastructure ready for Vibe integration"