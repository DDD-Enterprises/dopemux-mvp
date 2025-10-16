#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting all Dopemux MCP servers..."
echo "=========================================="

# Validate environment
echo "📋 Checking server configurations..."
for server_dir in */; do
    if [ -f "$server_dir/.env" ]; then
        echo "✅ Found configuration for ${server_dir%/}"
    elif [ -d "$server_dir" ]; then
        echo "⚠️  ${server_dir%/} - using environment variables"
    fi
done

echo ""
echo "🔧 Checking required environment variables..."

# Check for critical API keys
missing_keys=()
[ -z "$OPENAI_API_KEY" ] && missing_keys+=("OPENAI_API_KEY")
[ -z "$EXA_API_KEY" ] && missing_keys+=("EXA_API_KEY")

if [ ${#missing_keys[@]} -gt 0 ]; then
    echo "⚠️  Warning: Missing API keys: ${missing_keys[*]}"
    echo "   Some servers may not function properly"
fi

echo ""
echo "🔨 Building and starting containers..."

# Start infrastructure first (vector database for dope-context)
echo "🗄️  Starting infrastructure..."
docker-compose up -d --build qdrant

echo "⏳ Waiting for Qdrant to be ready..."
sleep 5

# Start critical path servers (staggered for ADHD optimizations)
echo "⚡ Starting critical path servers..."
docker-compose up -d --build context7 zen litellm mas-sequential-thinking

echo "⏳ Waiting for critical servers to stabilize..."
sleep 10

# Start workflow servers
echo "🔄 Starting workflow servers..."
docker-compose up -d --build conport serena  # Removed task-master-ai (crashes)

echo "⏳ Waiting for workflow servers to stabilize..."
sleep 10

# Start research + quality & utility servers
echo "🧠 Starting research + quality & utility servers..."
docker-compose up -d --build gptr-mcp gptr-mcp-stdio exa morphllm-fast-apply desktop-commander

echo ""
echo "⏳ Final startup wait..."
sleep 5

echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "🏥 Health check summary:"
echo "========================"

# Health check each critical server
servers=("context7:3002" "zen:3003" "litellm:4000" "mas-sequential-thinking:3001")
for server in "${servers[@]}"; do
    name="${server%:*}"
    port="${server#*:}"

    if curl -sf "http://localhost:$port/health" &>/dev/null; then
        echo "✅ $name - Healthy"
    else
        echo "❌ $name - Unhealthy (port $port)"
    fi
done

echo ""
echo "🔎 Research servers:"
research_servers=("gptr-mcp:3009")
for server in "${research_servers[@]}"; do
    name="${server%:*}"
    port="${server#*:}"
    if curl -sf "http://localhost:$port/health" &>/dev/null; then
        echo "✅ $name - Healthy"
    else
        echo "❌ $name - Unhealthy (port $port)"
    fi
done

echo ""
echo "✅ All MCP servers started successfully!"
echo ""
echo "📋 Management commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop all:  docker-compose down"
echo "   Restart:   ./start-all-mcp-servers.sh"
echo ""
echo "🔍 Server endpoints:"
echo ""
echo "📚 Critical Path Servers:"
echo "   Context7:     http://localhost:3002"
echo "   Zen:          http://localhost:3003"
echo "   LiteLLM:      http://localhost:4000"
echo "   Sequential:   http://localhost:3001"
echo ""
echo "🔄 Workflow Servers:"
echo "   ConPort:      http://localhost:3004"
echo "   Task Master:  http://localhost:3005"
echo "   Serena:       http://localhost:3006"
echo "   Claude Ctx:   http://localhost:3007"
echo ""
echo "🔧 Quality & Utility Servers:"
echo "   GPT Research: http://localhost:3009"
echo "   Exa:          http://localhost:3008"
echo "   MorphLLM:     http://localhost:3011"
echo "   Desktop Cmd:  http://localhost:3012"
echo ""
echo "📋 PM Integration:"
echo "   Leantime:     http://localhost:8080 (external)"
echo ""
echo "🎯 Ready for MetaMCP orchestration!"
