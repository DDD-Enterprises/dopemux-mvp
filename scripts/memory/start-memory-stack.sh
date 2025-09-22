#!/bin/bash
# Start Dopemux Unified Memory Stack
# Brings up Milvus, PostgreSQL, Zep, and ConPort memory services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MEMORY_STACK_DIR="$PROJECT_ROOT/docker/memory-stack"

echo "🚀 Starting Dopemux Unified Memory Stack"
echo "========================================"

# Check if .env file exists for API keys
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Warning: No .env file found. Creating template..."
    cat > "$ENV_FILE" << EOF
# Dopemux Memory Stack Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
VOYAGE_API_KEY=your_voyage_api_key_here
EOF
    echo "📝 Please edit $ENV_FILE with your API keys before continuing"
    exit 1
fi

# Source environment variables
source "$ENV_FILE"

# Validate required API keys
if [ -z "$VOYAGE_API_KEY" ] || [ "$VOYAGE_API_KEY" = "your_voyage_api_key_here" ]; then
    echo "❌ Error: VOYAGE_API_KEY not set in $ENV_FILE"
    echo "   This is required for vector embeddings"
    exit 1
fi

echo "✅ Environment variables loaded"

# Change to memory stack directory
cd "$MEMORY_STACK_DIR"

echo "🐳 Starting Docker services..."

# Start the memory stack
docker-compose up -d

echo "⏱️  Waiting for services to be healthy..."

# Wait for services to be ready
for service in postgres milvus-standalone zep conport-memory; do
    echo "   Checking $service..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose ps "$service" | grep -q "healthy\|Up"; then
            echo "   ✅ $service is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done

    if [ $timeout -le 0 ]; then
        echo "   ❌ $service failed to start within 60 seconds"
        echo "   Check logs: docker-compose logs $service"
        exit 1
    fi
done

echo ""
echo "🎉 Memory Stack is ready!"
echo ""
echo "📊 Service URLs:"
echo "   • ConPort Memory MCP:     http://localhost:3004"
echo "   • Zep API:                http://localhost:8000"
echo "   • Milvus:                 localhost:19530"
echo "   • Milvus Web UI:          http://localhost:9001"
echo "   • PostgreSQL:             localhost:5432"
echo ""
echo "🔧 Management Commands:"
echo "   • View logs:              docker-compose logs -f"
echo "   • Stop services:          docker-compose down"
echo "   • Restart service:        docker-compose restart <service_name>"
echo "   • View status:            docker-compose ps"
echo ""
echo "📚 Next Steps:"
echo "   1. Test ConPort MCP:      curl http://localhost:3004/health"
echo "   2. Import histories:      python -m conport.importers --help"
echo "   3. Add to Claude Code:    claude mcp add conport-memory http://localhost:3004"
echo ""

# Test ConPort health
echo "🧪 Testing ConPort Memory health..."
if curl -s http://localhost:3004/health >/dev/null 2>&1; then
    echo "✅ ConPort Memory is responding"
else
    echo "⚠️  ConPort Memory health check failed (may still be starting up)"
fi

echo ""
echo "🎯 Memory stack startup complete!"