#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

compose_up() {
  local file="$1"; shift
  local name="$1"; shift
  if [ -f "$file" ]; then
    echo "\n==> Bringing up: $name ($file)"
    if docker-compose -f "$file" up -d --no-build 2>/dev/null; then
      echo "✅ $name up (cached images)"
    else
      echo "🧱 $name missing images; building"
      docker-compose -f "$file" up -d --build
    fi
  else
    echo "• Skipping $name (not found): $file"
  fi
}

ensure_network() {
  local net="$1"
  if ! docker network inspect "$net" >/dev/null 2>&1; then
    echo "🌐 Creating network: $net"
    docker network create "$net" >/dev/null
  else
    echo "✅ Network exists: $net"
  fi
}

echo "== Dopemux: Bringing up all stacks (cached images preferred) =="

# Core shared networks
ensure_network mcp-network
ensure_network dopemux-unified-network
ensure_network leantime-net

# Event bus (optional)
compose_up "$ROOT_DIR/docker/docker-compose.event-bus.yml" "Event Bus (Redis + UI)"

# Memory stack (optional: AGE/Milvus/etc.)
compose_up "$ROOT_DIR/docker/memory-stack/docker-compose.yml" "Memory Stack"

# Leantime (optional PM stack)
compose_up "$ROOT_DIR/docker/leantime/docker-compose.yml" "Leantime"

# ConPort KG (optional)
compose_up "$ROOT_DIR/docker/conport-kg/docker-compose.yml" "ConPort KG"

# MCP Servers (full stack orchestrator)
echo "\n==> MCP Servers (orchestrated)"
pushd "$ROOT_DIR/docker/mcp-servers" >/dev/null
./start-all-mcp-servers.sh
popd >/dev/null

echo "\n== Summary: docker ps =="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | sed -n '1,200p'

echo "\n== Helpful endpoints =="
cat <<EOF
ConPort:      http://localhost:3004
Zen:          http://localhost:3003
Context7:     http://localhost:3002
LiteLLM:      http://localhost:4000 (Authorization header required)
Sequential:   http://localhost:3011
Redis UI:     http://localhost:8081 (if Event Bus started)
Leantime:     http://localhost:8080 (if Leantime started)
Qdrant:       http://localhost:6333
Postgres:     5432 (docker: dopemux-postgres-age)
EOF

echo "\n✅ All available stacks attempted. Use 'scripts/stack_status.sh' for a live snapshot."

