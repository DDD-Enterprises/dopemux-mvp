#!/usr/bin/env bash
set -euo pipefail

echo "== docker ps =="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | sed -n '1,200p'

echo "\n== Key health checks =="
check() {
  local name="$1"; shift
  local url="$1"; shift
  if curl -sf "$url" >/dev/null; then
    echo "✅ $name: $url"
  else
    echo "❌ $name: $url"
  fi
}

check "PAL apilookup" "http://127.0.0.1:3003/health"

# LiteLLM requires auth; just show raw health
echo -n "LiteLLM: "; curl -s -H "Authorization: Bearer <REDACTED_LITELLM_MASTER_KEY>" http://127.0.0.1:4000/health | head -n 1 || echo "unreachable"

check "ConPort" "http://127.0.0.1:3004/health"
check "Sequential" "http://127.0.0.1:3011/health"

echo "\n✅ Status gathered."
