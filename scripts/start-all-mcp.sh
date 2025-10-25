#!/bin/bash
# Start all Dopemux MCP services and infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting Dopemux MCP Services..."
echo "Project root: $PROJECT_ROOT"
echo

cd "$PROJECT_ROOT"

# Start infrastructure and MCP services
echo "📦 Starting Docker services..."
docker-compose up -d

echo
echo "⏳ Waiting for services to be ready (10 seconds)..."
sleep 10

echo
echo "🔍 Running health check..."
python3 "$SCRIPT_DIR/mcp-health-check.py"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo
    echo "✅ All services started successfully!"
    echo "💡 Restart Claude Code to reconnect MCP servers"
else
    echo
    echo "⚠️  Some services may need additional time to start"
    echo "💡 Run: python3 scripts/mcp-health-check.py to check status"
fi

exit $exit_code
