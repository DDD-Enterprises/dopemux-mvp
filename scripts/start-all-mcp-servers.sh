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
for network in dopemux-network; do
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
    local container_name=$3
    
    echo "🔍 Checking $service ($container_name)..."
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo "  ✅ Already running on port $port"
    else
        echo "  🚀 Starting $service..."
        docker compose -f compose.yml up -d --no-recreate $service 2>&1 | grep -v "level=warning" || true
        echo "  ✅ Started $service"
    fi
    echo
}

# Start infrastructure first
echo "=== Infrastructure Services ==="
start_service "postgres" "5432" "dopemux-postgres-age"
start_service "redis-events" "6379" "redis-events"
start_service "redis-primary" "6380" "redis-primary"
start_service "mcp-qdrant" "6333" "mcp-qdrant"

echo "⏳ Waiting for infrastructure to be healthy..."
sleep 5
echo

# Start coordination
echo "=== Coordination Layer ==="
start_service "dopecon-bridge" "3016" "dope-decision-graph-bridge"

# Start MCP servers
echo "=== MCP Servers ==="
start_service "conport" "3005" "mcp-conport"
start_service "dope-context" "3010" "mcp-dope-context"
start_service "serena" "3006" "dopemux-mcp-serena"
start_service "leantime-bridge" "3015" "dopemux-mcp-leantime-bridge"
start_service "gptr-mcp" "3009" "dopemux-mcp-gptr-mcp"
start_service "exa" "3011" "mcp-exa"
start_service "desktop-commander" "3012" "dopemux-mcp-desktop-commander"
start_service "pal" "3003" "mcp-pal"

echo
echo "✅ MCP Server startup complete!"
echo
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(dopemux|mcp|redis|postgres|leantime|dope)"
echo
echo "💡 Tip: Use 'docker compose -f compose.yml ps' to check all services"
echo "💡 Tip: Use 'docker logs <container-name>' to view logs"
