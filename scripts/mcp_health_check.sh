#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Dopemux MCP Server Health Check"
echo "=================================="
echo

# Accumulate failures so we can report every check, then exit non-zero if any failed.
FAILURES=0
record_failure() {
    FAILURES=$((FAILURES + 1))
}

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
    local path=${3:-mcp}
    
    echo "🔌 Checking $name MCP endpoint ($port/$path)..."
    
    if [ "$path" = "sse" ]; then
        response=$(curl -sS -m 2 -H "Accept: text/event-stream" "http://localhost:$port/sse" 2>&1 || true)
        if echo "$response" | grep -q 'event: endpoint'; then
            echo "✅ $name MCP endpoint responding"
            return 0
        else
            echo "❌ $name MCP endpoint not responding properly"
            echo "   Response: $response"
            return 1
        fi
    else
        # Try POST to /mcp endpoint
        response=$(curl -sS -X POST \
            -H 'Content-Type: application/json' \
            -H 'Accept: application/json' \
            --data '{"jsonrpc":"2.0","id":"probe","method":"initialize","params":{}}' \
            "http://localhost:$port/$path" 2>&1 || true)
        
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
    fi
}

# Stdio MCP check function (exec-based servers have no port).
# Probes the actual MCP protocol via an `initialize` handshake over `docker exec`.
check_stdio_mcp() {
    local name=$1
    local container=$2

    echo "🔌 Checking $name stdio ($container)..."

    if [ "$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || echo false)" != "true" ]; then
        echo "❌ $name container '$container' not running"
        return 1
    fi

    local init='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"healthcheck","version":"0"}}}'
    local tbin=""
    for c in timeout gtimeout; do command -v "$c" >/dev/null 2>&1 && { tbin="$c"; break; }; done

    local out
    if [ -n "$tbin" ]; then
        out="$(printf '%s\n' "$init" | "$tbin" 30 docker exec -i "$container" /app/.venv/bin/python server.py 2>/dev/null | head -c 4000 || true)"
    else
        out="$(printf '%s\n' "$init" | docker exec -i "$container" /app/.venv/bin/python server.py 2>/dev/null | head -c 4000 || true)"
    fi

    if printf '%s' "$out" | grep -q '"serverInfo"'; then
        echo "✅ $name stdio server responding (initialize OK)"
        return 0
    else
        echo "❌ $name stdio server not responding — try: scripts/ensure_pal_stdio.sh"
        return 1
    fi
}

# Main checks — report everything, then fail closed if any check failed.
echo "🏥 Health Checks:"
echo "----------------"

check_health "Dope-Context" 3010 || record_failure
check_health "PAL" 3003 || record_failure
check_health "ConPort" 3004 || record_failure

echo
echo "🔌 MCP Endpoint Checks:"
echo "----------------------"

check_mcp_endpoint "Dope-Context" 3010 "mcp" || record_failure
check_mcp_endpoint "PAL" 3003 "sse" || record_failure
check_mcp_endpoint "ConPort" 3004 "mcp" || record_failure

echo
echo "🔌 Stdio MCP Checks:"
echo "-------------------"

check_stdio_mcp "PAL (stdio)" "mcp-pal-stdio" || record_failure

echo
echo "📊 Summary:"
echo "-----------"
echo "Dope-Context and ConPort have MCP endpoints at /mcp (POST required)."
echo "PAL runs two servers: HTTP :3003 (mcp-pal) and stdio (mcp-pal-stdio, exec-based)."
echo "A healthy stdio probe means server+registry are OK; model calls still depend on"
echo "provider credentials (OpenAI/Gemini/OpenRouter)."
if [ "$FAILURES" -gt 0 ]; then
    echo "❌ $FAILURES check(s) failed"
    exit 1
fi
echo "✅ All checks passed"
exit 0
