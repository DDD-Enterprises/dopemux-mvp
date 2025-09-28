#!/usr/bin/env bash
set -euo pipefail

echo "[MCP] Starting configured servers (best-effort)"

# fast-markdown via Docker exec
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^devdocs-mcp$'; then
  echo "[MCP] fast-markdown in Docker (devdocs-mcp) — starting server inside container"
  docker exec -i devdocs-mcp python -m fast_markdown_mcp.server /app/storage/markdown &
else
  echo "[MCP] fast-markdown: container 'devdocs-mcp' not running. Skip (see .claude/mcp.config.json)."
fi

# OpenMemory via npx
if command -v npx >/dev/null 2>&1; then
  if [[ -n "${OPENMEMORY_API_KEY:-}" ]]; then
    echo "[MCP] openmemory — launching via npx"
    OPENMEMORY_API_KEY="${OPENMEMORY_API_KEY}" npx -y openmemory &
  else
    echo "[MCP] openmemory: OPENMEMORY_API_KEY not set; skipping"
  fi
else
  echo "[MCP] openmemory: npx not found; skipping"
fi

# Zen MCP via uvx
UVX_BIN=$(command -v uvx || true)
if [[ -n "$UVX_BIN" ]]; then
  if [[ -n "${OPENAI_API_KEY:-}" || -n "${GEMINI_API_KEY:-}" || -n "${GOOGLE_API_KEY:-}" ]]; then
    echo "[MCP] zen — launching via uvx from Git"
    PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:${PATH}" \
    OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    GEMINI_API_KEY="${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}" \
    "$UVX_BIN" --from git+https://github.com/BeehiveInnovations/zen-mcp-server.git zen-mcp-server &
  else
    echo "[MCP] zen: no OPENAI_API_KEY / GEMINI_API_KEY; skipping"
  fi
else
  echo "[MCP] zen: uvx not found; skipping"
fi

echo "[MCP] Start attempts issued. Use scripts/mcp/check.sh to verify."
