#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure external network exists (compose expects it)
if ! docker network inspect mcp-network >/dev/null 2>&1; then
  echo "🌐 Creating external network: mcp-network"
  docker network create mcp-network >/dev/null
fi

echo "🚀 Building + starting gptr-mcp (GPT Researcher)..."
docker-compose up -d --build gptr-mcp

echo "⏳ Waiting for service to boot..."
sleep 5

echo "📋 Status:"
docker-compose ps gptr-mcp || true

echo "🏥 Health check:"
if curl -sf http://localhost:3009/health >/dev/null; then
  echo "✅ gptr-mcp healthy at http://localhost:3009/health"
else
  echo "❌ Health endpoint not responding yet"
  echo "📄 Tailing logs (Ctrl+C to exit)"
  docker-compose logs -f gptr-mcp
fi

