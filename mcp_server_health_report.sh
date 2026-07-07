#!/bin/bash
# MCP Server Health Report
#
# Sources per-worktree port variables from .envrc.dopemux-mcp so that the
# correct (potentially hash-offset) ports are tested, not hardcoded defaults.
# Probes each transport type correctly:
#   - Streamable HTTP ("type": "http"): POST JSON-RPC initialize
#   - SSE           ("type": "sse"):   GET with Accept: text/event-stream
#
# Usage: ./mcp_server_health_report.sh [--workspace /path/to/workspace] [-v]

set -euo pipefail

WORKSPACE_PATH=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace|-w) WORKSPACE_PATH="$2"; shift 2 ;;
        --verbose|-v)   VERBOSE=true; shift ;;
        --help|-h)
            cat <<'HELP'
Usage: ./mcp_server_health_report.sh [OPTIONS]

OPTIONS:
    --workspace, -w PATH    Workspace directory (default: current directory)
    --verbose, -v           Show detailed curl output
    --help, -h              Show this help message

EXAMPLES:
    ./mcp_server_health_report.sh
    ./mcp_server_health_report.sh -w ~/code/other-project
HELP
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

WORKSPACE="${WORKSPACE_PATH:-$(pwd)}"
ENVRC="$WORKSPACE/.envrc.dopemux-mcp"

echo "=========================================="
echo "MCP Server Health Report"
echo "Workspace: $WORKSPACE"
echo "=========================================="
echo ""
date
echo ""

# Source per-worktree port variables if available
if [[ -f "$ENVRC" ]]; then
    echo "Sourcing port variables from: $ENVRC"
    # Use set -a so exported variables are available for subshells
    set -a
    # shellcheck source=/dev/null
    source "$ENVRC"
    set +a
    echo ""
else
    echo "⚠️  No .envrc.dopemux-mcp found at $WORKSPACE — using catalog default ports."
    echo "   Run: dopemux mcp init  (from inside the workspace)"
    echo ""
fi

# Resolve ports (env vars take precedence over defaults)
CONPORT_HTTP_PORT="${CONPORT_HTTP_PORT:-3004}"
CONPORT_MCP_PORT="${CONPORT_MCP_PORT:-3005}"
DOPE_MEMORY_PORT="${DOPE_MEMORY_PORT:-3020}"
TASK_ORCHESTRATOR_HTTP_PORT="${TASK_ORCHESTRATOR_HTTP_PORT:-7890}"

echo "=== Per-Worktree MCP Servers ==="
echo ""

# ---------------------------------------------------------------------------
# Helper: probe Streamable HTTP (type: "http") via JSON-RPC initialize POST
# These servers speak the MCP Streamable HTTP protocol, NOT SSE.
# A GET request returns 406; the correct probe is a POST.
# ---------------------------------------------------------------------------
probe_http() {
    local name="$1"
    local port="$2"
    local path="${3:-/mcp}"

    local response
    response=$(curl -s --max-time 2 -o /tmp/mcp_probe_$$.json -w "%{http_code}" \
        -X POST "http://localhost:${port}${path}" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"health-probe","version":"0.1"}}}' \
        2>/dev/null) || response="000"

    if [[ "$response" =~ ^2 ]]; then
        echo "✅ $name (port $port, HTTP/Streamable): OK (HTTP $response)"
        if $VERBOSE; then
            cat /tmp/mcp_probe_$$.json 2>/dev/null | head -3
        fi
    elif [[ "$response" == "000" ]]; then
        echo "❌ $name (port $port, HTTP/Streamable): Connection refused — is the container running?"
    else
        echo "⚠️  $name (port $port, HTTP/Streamable): Unexpected HTTP $response"
        if $VERBOSE; then
            cat /tmp/mcp_probe_$$.json 2>/dev/null | head -3
        fi
    fi
    rm -f /tmp/mcp_probe_$$.json
}

# ---------------------------------------------------------------------------
# Helper: probe SSE (type: "sse") via GET with Accept: text/event-stream
# ---------------------------------------------------------------------------
probe_sse() {
    local name="$1"
    local port="$2"
    local path="${3:-/sse}"

    local response
    response=$(curl -s --max-time 2 -o /dev/null -w "%{http_code}" \
        -X GET "http://localhost:${port}${path}" \
        -H "Accept: text/event-stream" \
        2>/dev/null) || response="000"

    if [[ "$response" =~ ^2 ]]; then
        echo "✅ $name (port $port, SSE): OK (HTTP $response)"
    elif [[ "$response" == "000" ]]; then
        echo "❌ $name (port $port, SSE): Connection refused — is the container running?"
    else
        echo "⚠️  $name (port $port, SSE): Unexpected HTTP $response"
    fi
}

# ---------------------------------------------------------------------------
# Helper: probe a /health REST endpoint
# ---------------------------------------------------------------------------
probe_health() {
    local name="$1"
    local port="$2"

    local response
    response=$(curl -s --max-time 2 -o /dev/null -w "%{http_code}" \
        "http://localhost:${port}/health" 2>/dev/null) || response="000"

    if [[ "$response" =~ ^2 ]]; then
        echo "✅ $name (port $port, /health): OK"
    elif [[ "$response" == "404" ]]; then
        echo "✅ $name (port $port, /health): Responding (no /health endpoint)"
    elif [[ "$response" == "000" ]]; then
        echo "❌ $name (port $port, /health): Not responding"
    else
        echo "⚠️  $name (port $port, /health): HTTP $response"
    fi
}

# --- Per-worktree servers ---
# conport: SSE transport at /sse
probe_sse "conport      " "$CONPORT_MCP_PORT"
probe_health "conport (health)" "$CONPORT_HTTP_PORT"

# dope-memory: Streamable HTTP at /mcp  (NOT SSE — POST only)
probe_http "dope-memory  " "$DOPE_MEMORY_PORT"

# task-orchestrator: Streamable HTTP at /mcp (wrapper-singleton, fixed port)
probe_http "task-orch    " "$TASK_ORCHESTRATOR_HTTP_PORT"

echo ""
echo "=== Singleton MCP Servers (shared) ==="
echo ""

# Singletons have hardcoded ports declared in mcp_catalog.yaml
probe_http "pal          " 3003
probe_http "serena       " 3006
probe_http "dope-context " 3010
probe_sse  "desktop-cmd  " 3012

echo ""
echo "=== Docker Containers ==="
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(conport|dope-memory|task-orchestrator|pal|serena|dope-context|desktop)" || echo "(no matching containers running)"

echo ""
echo "=== Port Listeners ==="
echo ""
lsof -iTCP -sTCP:LISTEN -n -P 2>/dev/null | \
    grep -E ":(${CONPORT_HTTP_PORT}|${CONPORT_MCP_PORT}|${DOPE_MEMORY_PORT}|${TASK_ORCHESTRATOR_HTTP_PORT}|3003|3006|3010|3012)" \
    | awk '{print $9}' | sort -t: -k2 -n || echo "None found"

echo ""
echo "=========================================="
echo "TRANSPORT REMINDER:"
echo "  dope-memory, task-orchestrator → type: http (Streamable HTTP, POST /mcp)"
echo "  conport, desktop-commander     → type: sse  (SSE, GET /sse)"
echo "  pal, serena, dope-context      → type: http (Streamable HTTP, POST /mcp)"
echo "=========================================="
