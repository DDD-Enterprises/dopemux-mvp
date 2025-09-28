#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Building + starting mas-sequential-thinking..."
docker-compose up -d --build mas-sequential-thinking

echo "⏳ Waiting for service to boot..."
sleep 5

echo "📋 Status:"
docker-compose ps mas-sequential-thinking || true

echo "🏥 Liveness check (port 3001):"
if nc -z localhost 3001 >/dev/null 2>&1; then
  echo "✅ mas-sequential-thinking listening on port 3001"
  echo "ℹ️  Note: MAS does not expose /health; broker uses ping"
else
  echo "❌ Port 3001 not open yet"
  echo "📄 Tailing logs (Ctrl+C to exit)"
  docker-compose logs -f mas-sequential-thinking
fi
