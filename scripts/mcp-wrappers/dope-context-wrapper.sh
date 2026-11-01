#!/usr/bin/env bash
set -euo pipefail

# Dope-Context MCP Wrapper - Docker-based semantic search launcher
# Wraps the docker-based Dope-Context MCP server with workspace detection
# and exact container name resolution.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

workspace_id="$(detect_workspace)"

require_docker "dope-context-wrapper"

# Exact container name only. Created by compose.yml:392
# (container_name: mcp-dope-context). No substring fallback: never attach to
# another worktree's/project's container.
expected_name="mcp-dope-context"
if ! container_name="$(find_container "$expected_name")"; then
  echo "❌ dope-context-wrapper: Dope-Context container '$expected_name' not found or not running" >&2
  echo "💡 Suggestion: start it with 'dopemux mcp start'" >&2
  exit 1
fi

export DOPEMUX_WORKSPACE_ID="$workspace_id"

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  "$container_name" \
  python /app/server.py "$@"
