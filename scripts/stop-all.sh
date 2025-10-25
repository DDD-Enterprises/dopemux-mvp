#!/bin/bash
#
# Stop All Dopemux Services - Complete Stack
#
# Usage:
#   ./scripts/stop-all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🛑 Stopping Complete Dopemux Stack..."
echo "=========================================="
echo ""

# Stop Task Orchestrator first (manual profile)
echo "🤖 Stopping Task Orchestrator..."
cd docker/mcp-servers
docker-compose --profile manual down task-orchestrator 2>/dev/null || true
echo "✅ Task Orchestrator stopped"
echo ""

# Stop Integration Bridge
echo "🔗 Stopping Integration Bridge..."
cd "$PROJECT_ROOT/docker/conport-kg"
docker-compose down integration-bridge 2>/dev/null || true
echo "✅ Integration Bridge stopped"
echo ""

# Stop MCP servers (but keep infrastructure running)
echo "📡 Stopping MCP servers (keeping infrastructure)..."
cd "$PROJECT_ROOT/docker/mcp-servers"
docker-compose stop 2>/dev/null || true
echo "✅ MCP servers stopped"
echo ""

echo "=========================================="
echo "✅ Application services stopped"
echo ""
echo "💡 Infrastructure (PostgreSQL, Redis, Qdrant) still running"
echo "   Use 'docker-compose -f docker/mcp-servers/docker-compose.yml down' to stop infrastructure"
echo ""
echo "🔄 To restart: ./scripts/start-all.sh"
