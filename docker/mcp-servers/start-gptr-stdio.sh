#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure external network exists
if ! docker network inspect mcp-network >/dev/null 2>&1; then
  echo "🌐 Creating external network: mcp-network"
  docker network create mcp-network >/dev/null
fi

echo "🚀 Building + starting gptr-mcp-stdio helper container..."
docker-compose up -d --build gptr-mcp-stdio

echo "⏳ Waiting briefly..."
sleep 3

echo "📋 Status:"
docker-compose ps gptr-mcp-stdio || true

echo "🔧 Test exec availability:"
if timeout 5 docker exec mcp-gptr-stdio python -c "print('ok')" >/dev/null 2>&1; then
  echo "✅ docker exec working; ready for proxy stdio"
  echo "   Example proxy cmd: docker exec -i mcp-gptr-stdio python /app/scripts/gpt-researcher/mcp_server.py"
else
  echo "❌ docker exec test failed"
  docker-compose logs -f gptr-mcp-stdio
fi

