#!/bin/bash
# Dopemux MCP Server Startup Script
# Ensures all MCP servers are running and healthy before Claude Code starts

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Dopemux MCP Servers..."
echo "📁 Project root: $PROJECT_ROOT"

# Function to check if docker container is healthy
check_container_health() {
    local container_name="$1"
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $container_name to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if docker ps --filter "name=$container_name" --filter "status=running" --format "{{.Names}}" | grep -q "^${container_name}$"; then
            health_status=$(docker inspect "$container_name" --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")
            if [ "$health_status" = "healthy" ] || [ "$health_status" = "none" ]; then
                echo "✅ $container_name is ready"
                return 0
            fi
        fi

        echo "⏳ $container_name not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
        ((attempt++))
    done

    echo "❌ $container_name failed to become healthy"
    return 1
}

# Function to check if port is responding
check_port_health() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts=15
    local attempt=1

    echo "⏳ Checking $service_name on $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name is responding on $host:$port"
            return 0
        fi

        echo "⏳ $service_name not responding yet (attempt $attempt/$max_attempts)..."
        sleep 1
        ((attempt++))
    done

    echo "❌ $service_name not responding on $host:$port"
    return 1
}

# Start Docker MCP servers
echo "🐳 Starting Docker-based MCP servers..."

# Start core infrastructure first
echo "🏗️ Starting infrastructure services..."
docker compose -f "$PROJECT_ROOT/compose.yml" up -d dopemux-postgres-age dopemux-redis-primary dopemux-redis-events mcp-qdrant

# Wait for infrastructure
check_container_health "dopemux-postgres-age"
check_container_health "dopemux-redis-primary"
check_container_health "mcp-qdrant"

# Start MCP servers
echo "🔧 Starting MCP servers..."
docker compose -f "$PROJECT_ROOT/compose.yml" up -d mcp-conport mcp-zen mcp-pal mcp-serena mcp-dope-context mcp-exa mcp-gptr-mcp mcp-leantime-bridge mcp-desktop-commander mcp-task-orchestrator mcp-clear-thought

# Wait for MCP servers to be ready
echo "🏥 Checking MCP server health..."

# Core critical path servers
check_container_health "mcp-conport"
check_port_health "localhost" "3004" "ConPort"

check_container_health "mcp-zen"
check_port_health "localhost" "3003" "Zen"

check_container_health "mcp-pal"
check_port_health "localhost" "3003" "PAL apilookup"

check_container_health "mcp-serena"
# Serena doesn't have a health endpoint, just check if port is open

check_container_health "mcp-dope-context"
check_port_health "localhost" "3010" "Dope Context"

# Additional servers (may not be critical)
check_container_health "mcp-exa" || echo "⚠️ Exa MCP container not healthy, but continuing..."
check_port_health "localhost" "3008" "Exa" || echo "⚠️ Exa MCP not responding, but continuing..."

check_container_health "mcp-gptr-mcp" || echo "⚠️ GPT Researcher container not healthy, but continuing..."
check_port_health "localhost" "3009" "GPT Researcher" || echo "⚠️ GPT Researcher not responding, but continuing..."

check_container_health "mcp-leantime-bridge" || echo "⚠️ Leantime Bridge container not healthy, but continuing..."
check_port_health "localhost" "3015" "Leantime Bridge" || echo "⚠️ Leantime Bridge not responding, but continuing..."

check_container_health "mcp-desktop-commander" || echo "⚠️ Desktop Commander container not healthy, but continuing..."
check_port_health "localhost" "3012" "Desktop Commander" || echo "⚠️ Desktop Commander not responding, but continuing..."

check_container_health "mcp-task-orchestrator" || echo "⚠️ Task Orchestrator container not healthy, but continuing..."
# Task Orchestrator may restart, so don't check port

check_container_health "mcp-clear-thought" || echo "⚠️ Clear Thought container not healthy, but continuing..."
check_port_health "localhost" "3013" "Clear Thought" || echo "⚠️ Clear Thought not responding, but continuing..."

echo ""
echo "🎉 MCP Server startup complete!"
echo "📊 Status summary:"
docker ps --filter "name=mcp-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "💡 You can now start Claude Code with full MCP server support:"
echo "   claude"
echo ""
echo "🔧 If you encounter issues, check logs with:"
echo "   docker compose -f compose.yml logs [service-name]"