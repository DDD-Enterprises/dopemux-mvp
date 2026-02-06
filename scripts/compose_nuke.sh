#!/usr/bin/env bash
# Dopemux Compose Cleanup Script
# Removes ghost containers and stale state, then starts the stack cleanly.

set -euo pipefail

PROJECT="${1:-dopemux}"

echo "🧹 Cleaning up Compose project: $PROJECT"

# List current compose projects
echo "Current Compose projects:"
docker compose ls || true

# Bring down the project (ignore errors)
echo "Bringing down project..."
docker compose -p "$PROJECT" -f compose.yml down --remove-orphans || true

# Remove containers by project label
echo "Removing containers with project label..."
docker ps -a --filter "label=com.docker.compose.project=$PROJECT" -q \
  | xargs -r docker rm -f || true

# Recreate external network
echo "Recreating dopemux-network..."
docker network inspect dopemux-network >/dev/null 2>&1 && docker network rm dopemux-network || true
docker network create dopemux-network || true

# Prune dangling networks
echo "Pruning dangling networks..."
docker network prune -f || true

# Start the stack
echo "🚀 Starting stack..."
docker compose -p "$PROJECT" -f compose.yml up -d --remove-orphans --force-recreate

# Show status
echo "📊 Stack status:"
docker compose -p "$PROJECT" -f compose.yml ps

echo "✅ Cleanup complete!"
