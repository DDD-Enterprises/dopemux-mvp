#!/bin/bash
# MCP Server Startup Helper
# Safe startup script for Dopemux MCP servers
# Does NOT modify existing volumes

set -e

echo "🚀 Dopemux MCP Server Startup Helper"
echo "======================================"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if networks exist
echo "📡 Checking Docker networks..."
for network in mcp-network dopemux-unified-network leantime-net; do
    if ! docker network inspect $network > /dev/null 2>&1; then
        echo "  Creating network: $network"
        docker network create $network
    else
        echo "  ✅ Network exists: $network"
    fi
done
echo

# Function to start a service if not running
start_service() {
    local service=$1
    local port=$2
    
    echo "🔍 Checking $service..."
    
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        echo "  ✅ Already running on port $port"
    else
        echo "  🚀 Starting $service..."
        # Ensure we are in the project root if needed, but assuming running from root or script dir
        # cd /Users/hue/code/dopemux-mvp
        docker compose -f compose.yml up -d --no-recreate $service 2>&1 | grep -v "level=warning" || true
        echo "  ✅ Started $service"
    fi
    echo
}

# Start infrastructure first (required by MCP servers)
echo "=== Infrastructure Services ==="
start_service "dopemux-postgres-age" "5432"
start_service "dopemux-redis-primary" "6379"
start_service "mcp-qdrant" "6333"

echo "⏳ Waiting for infrastructure to be healthy..."
sleep 10
echo

# Start MCP servers
echo "=== MCP Servers ==="
start_service "conport" "3004"
start_service "dope-context" "3010"
start_service "serena-v2" "3006"
start_service "leantime-bridge" "3015"
start_service "gpt-researcher" "3009"
start_service "exa" "3011"
start_service "desktop-commander" "3012"

echo
echo "✅ MCP Server startup complete!"
echo
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(dopemux|mcp)"
echo
echo "💡 Tip: Use 'docker compose -f compose.yml ps' to check all services"
echo "💡 Tip: Use 'docker logs <container-name>' to view logs"
