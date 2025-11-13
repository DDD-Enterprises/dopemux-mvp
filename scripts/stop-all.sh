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

# Stop F-NEW-8 Break Suggester
echo "🎯 Stopping Break Suggester..."
pkill -9 -f "break-suggester" 2>/dev/null || true
echo "✅ Break Suggester stopped"
echo ""

# Stop ADHD Notifier (background process)
echo "🔔 Stopping ADHD Notifier..."
pkill -9 -f "adhd-notifier/main.py" 2>/dev/null || true
echo "✅ ADHD Notifier stopped"
echo ""

# Stop Workspace Watcher (background process)
echo "👁️  Stopping Workspace Watcher..."
pkill -9 -f "workspace-watcher/main.py" 2>/dev/null || true
echo "✅ Workspace Watcher stopped"
echo ""

# Stop ADHD Engine (background process)
echo "🧠 Stopping ADHD Engine..."
pkill -9 -f "adhd_engine/main.py" 2>/dev/null || true
if lsof -i :8095 2>/dev/null | grep -q LISTEN; then
    echo "⚠️  ADHD Engine still running - force killing port..."
    lsof -ti :8095 2>/dev/null | xargs kill -9 2>/dev/null || true
fi
echo "✅ ADHD Engine stopped"
echo ""

# Stop Task Orchestrator (manual profile)
echo "🤖 Stopping Task Orchestrator..."
cd docker/mcp-servers
docker-compose --profile manual down task-orchestrator 2>/dev/null || true
echo "✅ Task Orchestrator stopped"
echo ""

# Stop DopeconBridge
echo "🔗 Stopping DopeconBridge..."
cd "$PROJECT_ROOT/docker/conport-kg"
docker-compose down dopecon-bridge 2>/dev/null || true
echo "✅ DopeconBridge stopped"
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
