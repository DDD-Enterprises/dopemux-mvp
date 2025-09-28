#!/usr/bin/env bash
set -euo pipefail

echo "[MCP] Checking server processes/containers"

echo "- fast-markdown (Docker devdocs-mcp):"
docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null | (grep devdocs-mcp || true)

echo "- openmemory (npx):"
pgrep -fl "openmemory" 2>/dev/null || echo "  not running"

echo "- zen (uvx zen-mcp-server):"
pgrep -fl "zen-mcp-server" 2>/dev/null || echo "  not running"

echo "[MCP] Done."
