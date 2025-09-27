#!/usr/bin/env bash
set -euo pipefail

# Minimal PATH for launchd/systemd contexts
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Project root two levels up from scripts/auto-start
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVERS_DIR="$PROJECT_ROOT/docker/mcp-servers"

cd "$SERVERS_DIR"

echo "[dopemux] Waiting for Docker daemon..."
for i in {1..60}; do
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "[dopemux] Docker is ready"
    break
  fi
  sleep 2
done

# Ensure external network/volumes used by compose
docker network inspect mcp-network >/dev/null 2>&1 || docker network create mcp-network >/dev/null || true
docker volume inspect mcp_logs >/dev/null 2>&1 || docker volume create mcp_logs >/dev/null || true
docker volume inspect mcp_cache >/dev/null 2>&1 || docker volume create mcp_cache >/dev/null || true

echo "[dopemux] Starting MCP servers..."
./start-all-mcp-servers.sh || {
  echo "[dopemux] start-all failed, attempting compose up as fallback" >&2
  docker compose up -d || docker-compose up -d
}

echo "[dopemux] MCP servers started"

