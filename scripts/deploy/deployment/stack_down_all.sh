#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

compose_down() {
  local file="$1"; shift
  local name="$1"; shift
  if [ -f "$file" ]; then
    echo "\n==> Stopping: $name ($file)"
    docker-compose -f "$file" down --remove-orphans || true
  else
    echo "• Skipping $name (not found): $file"
  fi
}

echo "== Dopemux: Stopping all stacks (volumes preserved) =="

# Order: utilities → workflow → critical → infra
compose_down "$ROOT_DIR/docker/leantime/docker-compose.yml" "Leantime"
compose_down "$ROOT_DIR/docker/conport-kg/docker-compose.yml" "ConPort KG"
compose_down "$ROOT_DIR/docker/memory-stack/docker-compose.yml" "Memory Stack"
compose_down "$ROOT_DIR/docker/docker-compose.event-bus.yml" "Event Bus (Redis + UI)"

pushd "$ROOT_DIR/docker/mcp-servers" >/dev/null
echo "\n==> MCP Servers"
docker-compose down --remove-orphans || true
popd >/dev/null

echo "\n✅ All stacks requested to stop. Data volumes remain intact."

