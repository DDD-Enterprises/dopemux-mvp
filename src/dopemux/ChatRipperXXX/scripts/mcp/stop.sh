#!/usr/bin/env bash
set -euo pipefail

echo "[MCP] Stopping servers (best-effort)"

# fast-markdown runs in container; do not stop container here (may be shared)
echo "- fast-markdown (Docker devdocs-mcp): leaving container running. Stop manually if desired: docker stop devdocs-mcp"

echo "- openmemory:"
pkill -f "openmemory" 2>/dev/null || echo "  not running"

echo "- zen:"
pkill -f "zen-mcp-server" 2>/dev/null || echo "  not running"

echo "[MCP] Done."
