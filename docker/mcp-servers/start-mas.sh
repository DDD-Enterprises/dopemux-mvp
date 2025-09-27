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

echo "🏥 Health check:"
if curl -sf http://localhost:3001/health >/dev/null; then
  echo "✅ mas-sequential-thinking healthy at http://localhost:3001/health"
else
  echo "❌ Health endpoint not responding yet"
  echo "📄 Tailing logs (Ctrl+C to exit)"
  docker-compose logs -f mas-sequential-thinking
fi

