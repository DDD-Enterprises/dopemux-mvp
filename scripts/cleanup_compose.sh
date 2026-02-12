#!/usr/bin/env bash
# Dopemux Compose Cleanup Script
#
# Safely stops all compose projects without removing volumes.
# This fixes orphaned containers and stale project state.
#
# Usage: bash scripts/cleanup_compose.sh

set -euo pipefail

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Dopemux Cleanup (no volumes) - Safe Restart          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 1) Stop canonical project cleanly (compose.yml)
if [ -f "compose.yml" ]; then
  echo "📦 Stopping canonical dopemux project..."
  docker compose -p dopemux -f compose.yml down --remove-orphans || true
  echo "✓ Stopped dopemux"
  echo ""
fi

# 2) Stop other compose projects that may be running
# These are projects found in your environment that might cause conflicts
OTHER_PROJECTS=(
  "mcp-servers"
  "observability"
  "leantime"
  "conport-kg"
  "working-memory-assistant"
  "genetic_agent"
  "docker"
  "test-task-orchestrator"
)

for project in "${OTHER_PROJECTS[@]}"; do
  echo "📦 Stopping project: $project"
  docker compose -p "$project" down --remove-orphans 2>/dev/null || true
done

echo ""
echo "✓ All projects stopped"
echo ""

# 3) Remove any remaining stopped containers with dopemux label
echo "🧹 Removing exited/stale dopemux containers..."
STALE_CONTAINERS=$(docker ps -a \
  --filter "label=com.docker.compose.project=dopemux" \
  --filter "status=exited" \
  --format '{{.ID}}' || true)

if [ -n "$STALE_CONTAINERS" ]; then
  echo "$STALE_CONTAINERS" | xargs -r docker rm
  echo "✓ Removed stale containers"
else
  echo "✓ No stale containers found"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                   Cleanup Complete                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Start canonical stack:"
echo "     docker compose -p dopemux -f compose.yml up -d --remove-orphans --force-recreate"
echo ""
echo "  2. Check status:"
echo "     docker compose -p dopemux -f compose.yml ps"
echo ""
