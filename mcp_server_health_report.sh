#!/bin/bash
# MCP Server Health Report
# Checks all dopemux MCP servers and generates status report
# Usage: ./mcp_server_health_report.sh [--workspace /path/to/workspace]

# Parse arguments
WORKSPACE_PATH=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace|-w)
            WORKSPACE_PATH="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            cat << 'HELP'
Usage: ./mcp_server_health_report.sh [OPTIONS]

OPTIONS:
    --workspace, -w PATH    Check servers for specific workspace
    --verbose, -v           Show detailed information
    --help, -h             Show this help message

EXAMPLES:
    ./mcp_server_health_report.sh                    # All workspaces
    ./mcp_server_health_report.sh -w ~/code/project  # Specific workspace
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

echo "=========================================="
echo "MCP Server Health Report"
if [ -n "$WORKSPACE_PATH" ]; then
    echo "Workspace: $WORKSPACE_ID"
fi
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
test_endpoint 3003 "pal        "
test_endpoint 3004 "conport         "
test_endpoint 3006 "serena          "
test_endpoint 3008 "exa             "
test_endpoint 3009 "gptr-mcp        "
test_endpoint 3012 "desktop-commander"

echo ""
echo "=== MCP Server Containers ==="
echo ""

docker ps --filter "name=mcp-" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=== Port Listeners ==="
echo ""

lsof -iTCP -sTCP:LISTEN -n -P | grep -E ":(3001|3003|3004|3006|3007|3008|3009|3012)" | awk '{print $9}' | sort -t: -k2 -n || echo "None found"

echo ""
echo "=== Summary ==="
echo ""

# Count healthy containers
healthy_count=$(docker ps --filter "name=mcp-" --filter "health=healthy" | wc -l | tr -d ' ')
total_count=$(docker ps --filter "name=mcp-" | grep -v "NAMES" | wc -l | tr -d ' ')

echo "Healthy containers: $healthy_count/$total_count"
echo ""

# List ports listening
listening_ports=$(lsof -iTCP -sTCP:LISTEN -n -P | grep -E ":(3001|3003|3004|3006|3007|3008|3009|3012)" | awk '{print $9}' | cut -d: -f2 | sort -n | tr '\n' ' ')

echo "Ports listening: $listening_ports"
echo ""
echo "=========================================="
