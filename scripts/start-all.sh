#!/bin/bash
#
# Start All Dopemux Services - Complete Stack
#
# This script starts ALL Dopemux services including:
# - 12 MCP servers (ConPort, Zen, Serena, Context7, etc.)
# - Integration Bridge (event processing, pattern detection)
# - Task Orchestrator (ADHD task coordination)
# - All infrastructure (PostgreSQL, Redis, Qdrant)
#
# Usage:
#   ./scripts/start-all.sh           # Start everything
#   ./scripts/start-all.sh --verify  # Start + verify health

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERIFY=false

# Parse arguments
if [[ "$1" == "--verify" ]] || [[ "$1" == "-v" ]]; then
    VERIFY=true
fi

cd "$PROJECT_ROOT"

echo "🚀 Starting Complete Dopemux Stack..."
echo "=========================================="
echo ""

# Step 1: Start MCP servers (includes infrastructure)
echo "📡 Step 1/3: Starting MCP servers..."
cd docker/mcp-servers
docker-compose up -d
echo "✅ MCP servers started"
echo ""

# Step 2: Start ConPort-KG services (Integration Bridge)
echo "🔗 Step 2/3: Starting Integration Bridge..."
cd "$PROJECT_ROOT/docker/conport-kg"
docker-compose up -d integration-bridge
echo "✅ Integration Bridge started (port 3016)"
echo ""

# Step 3: Start Task Orchestrator (manual profile)
echo "🤖 Step 3/4: Starting Task Orchestrator..."
cd "$PROJECT_ROOT/docker/mcp-servers"
docker-compose --profile manual up -d task-orchestrator
echo "✅ Task Orchestrator started (port 3014)"
echo ""

# Step 4: Start ADHD Engine (background process - Docker version has dependency issues)
echo "🧠 Step 4/5: Starting ADHD Engine..."
cd "$PROJECT_ROOT/services/adhd_engine"

# Kill any existing instances
pkill -9 -f "adhd_engine/main.py" 2>/dev/null || true
sleep 1

# Start ADHD Engine on port 8095
API_PORT=8095 REDIS_URL=redis://localhost:6379 nohup python main.py > /tmp/adhd_engine.log 2>&1 &
ADHD_PID=$!

# Wait for startup
sleep 3

# Verify it started
if lsof -i :8095 2>/dev/null | grep -q LISTEN; then
    echo "✅ ADHD Engine started (port 8095, PID: $ADHD_PID)"

    # Initialize ADHD user profile (ensures statusline works)
    echo ""
    "$PROJECT_ROOT/scripts/init-adhd-profile.sh"
else
    echo "⚠️  ADHD Engine failed to start - check /tmp/adhd_engine.log"
fi
echo ""

# Step 5: Start Workspace Watcher (automatic workspace switch detection)
echo "👁️  Step 5/5: Starting Workspace Watcher..."
cd "$PROJECT_ROOT/services/workspace-watcher"

# Kill any existing instances
pkill -9 -f "workspace-watcher/main.py" 2>/dev/null || true
sleep 1

# Start Workspace Watcher (5s poll interval)
nohup python main.py --interval 5 > /tmp/workspace_watcher.log 2>&1 &
WATCHER_PID=$!

# Wait briefly for startup
sleep 2

# Verify it started
if ps -p $WATCHER_PID >/dev/null 2>&1; then
    echo "✅ Workspace Watcher started (PID: $WATCHER_PID, polling every 5s)"
else
    echo "⚠️  Workspace Watcher failed to start - check /tmp/workspace_watcher.log"
fi
echo ""

echo "=========================================="
echo "🎉 All Dopemux services started!"
echo ""

# Show running services
echo "📊 Running Services:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | \
  grep -E "(NAMES|integration-bridge|task-orchestrator|mcp-|dopemux-|redis|postgres|qdrant)" | \
  head -20

echo ""

# Verification if requested
if [ "$VERIFY" = true ]; then
    echo "🔍 Verifying service health..."
    echo ""

    # Check Integration Bridge
    echo -n "  Integration Bridge (3016): "
    if curl -sf http://localhost:3016/health > /dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "❌ Not responding"
    fi

    # Check Task Orchestrator
    echo -n "  Task Orchestrator (3014): "
    if docker ps | grep -q "mcp-task-orchestrator.*healthy"; then
        echo "✅ Healthy"
    else
        echo "⚠️  Check logs: docker logs mcp-task-orchestrator"
    fi

    # Check Redis Events
    echo -n "  Redis Events (6379): "
    if docker ps | grep -q "dopemux-redis-events.*healthy"; then
        echo "✅ Healthy"
    else
        echo "❌ Not running"
    fi

    # Check PostgreSQL
    echo -n "  PostgreSQL AGE (5455): "
    if docker ps | grep -q "dope-decision-graph-postgres.*healthy"; then
        echo "✅ Healthy"
    else
        echo "❌ Not running"
    fi

    # Check ADHD Engine
    echo -n "  ADHD Engine (8095): "
    if curl -sf http://localhost:8095/health > /dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "❌ Not responding - check /tmp/adhd_engine.log"
    fi

    # Check Activity Capture
    echo -n "  Activity Capture (8096): "
    if curl -sf http://localhost:8096/health > /dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "❌ Not responding - check: docker logs dopemux-activity-capture"
    fi

    echo ""
fi

echo "🔗 Service URLs:"
echo "  Integration Bridge: http://localhost:3016/health"
echo "  Task Orchestrator:  http://localhost:3014/health (stdio MCP)"
echo "  Activity Capture:   http://localhost:8096/health"
echo "  ADHD Engine:        http://localhost:8095/health"
echo "  ConPort MCP:        http://localhost:3004"
echo "  Zen MCP:            http://localhost:3003"
echo "  Redis UI:           http://localhost:8081"
echo ""

echo "📚 Next Steps:"
echo "  1. Run E2E test:    python tests/integration/test_phase3_e2e.py"
echo "  2. Check logs:      docker logs dope-decision-graph-bridge"
echo "  3. Check metrics:   curl http://localhost:3016/metrics"
echo "  4. Stop all:        ./scripts/stop-all.sh"
echo ""

echo "✨ Event system is now LIVE! Agents will emit events automatically."
