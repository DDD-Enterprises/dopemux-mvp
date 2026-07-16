#!/usr/bin/env bash
# ensure_pal_stdio.sh — make the pal-stdio MCP server usable, idempotently.
#
# Why this exists:
#   pal-stdio is an exec-based MCP server (Docker MCP Toolkit / Claude Code run
#   `docker exec -i mcp-pal-stdio /app/.venv/bin/python server.py`). It has NO
#   port, so scripts/mcp_health_check.sh (port/HTTP based) never covers it. The
#   container can be "Up" yet fail every tool call — the exact state seen during
#   the 2026-07-16 installer audit ("No module named 'utils.model_context'").
#   This script probes the *actual* stdio protocol and self-heals once.
#
#   Diagnosis: claudedocs/pal-stdio-model-context-diagnosis-2026-07-16.md
#
# Behaviour (fail-closed):
#   1. ensure the container is running (docker compose up -d pal-stdio if not)
#   2. probe stdio health via an MCP `initialize` handshake
#   3. if the probe fails, restart the container once and re-probe
#      (NOTE: a restart drops any active exec'd stdio sessions in that container)
#   4. exit 0 only when a valid serverInfo response is observed; else exit 1
#
# Health here means "server imports + MCP registry are OK" — it is independent of
# model-provider credentials (initialize makes no provider call). A healthy probe
# with failing tool calls points at provider creds, not this server.
set -euo pipefail

CONTAINER="mcp-pal-stdio"
COMPOSE_SERVICE="pal-stdio"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ensure_pal_stdio","version":"1"}}}'

log() { printf '%s\n' "$*" >&2; }

# Portable bounded-timeout wrapper (macOS lacks GNU timeout by default).
TIMEOUT_BIN=""
for c in timeout gtimeout; do
  if command -v "$c" >/dev/null 2>&1; then TIMEOUT_BIN="$c"; break; fi
done

is_running() {
  [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || echo false)" = "true" ]
}

# Returns 0 iff server.py answers `initialize` with a serverInfo result.
probe() {
  local out
  if [ -n "$TIMEOUT_BIN" ]; then
    out="$(printf '%s\n' "$INIT_REQ" | "$TIMEOUT_BIN" 30 docker exec -i "$CONTAINER" /app/.venv/bin/python server.py 2>/dev/null | head -c 4000 || true)"
  else
    out="$(printf '%s\n' "$INIT_REQ" | docker exec -i "$CONTAINER" /app/.venv/bin/python server.py 2>/dev/null | head -c 4000 || true)"
  fi
  printf '%s' "$out" | grep -q '"serverInfo"'
}

# 1. Ensure the container is running.
if ! is_running; then
  log "⚠️  $CONTAINER is not running — starting via docker compose"
  ( cd "$REPO_ROOT" && docker compose up -d "$COMPOSE_SERVICE" >/dev/null )
  sleep 2
fi

# 2. Probe stdio health.
if probe; then
  log "✅ $CONTAINER healthy (MCP initialize OK)"
  exit 0
fi

# 3. Self-heal: restart once, then re-probe.
log "❌ $CONTAINER is up but the stdio probe failed — restarting once"
docker restart "$CONTAINER" >/dev/null 2>&1 || {
  log "🚨 docker restart $CONTAINER failed"
  exit 1
}
sleep 2
if probe; then
  log "✅ $CONTAINER healthy after restart"
  exit 0
fi

# 4. Fail closed.
log "🚨 $CONTAINER still unhealthy after restart — needs manual investigation"
log "   see: claudedocs/pal-stdio-model-context-diagnosis-2026-07-16.md"
exit 1
