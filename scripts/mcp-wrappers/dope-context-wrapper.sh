#!/usr/bin/env bash
set -euo pipefail

# Dope-Context MCP Wrapper - Docker-based semantic search launcher
# Wraps the docker-based Dope-Context MCP server with workspace detection
# and resilient container name resolution.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

workspace_id="$(detect_workspace)"

require_docker "dope-context-wrapper"

# Find the Dope-Context container (try new name first, then old).
container_name=""
for name_pattern in "dopemux-mcp-dope-context" "dopemux-dope-context" "dope-context"; do
  if container_name="$(find_container "$name_pattern")"; then
    break
  fi
done

if [[ -z "$container_name" ]]; then
  echo "❌ dope-context-wrapper: Dope-Context container not found" >&2
  echo "   (tried: dopemux-mcp-dope-context, dopemux-dope-context, dope-context)" >&2
  echo "💡 Suggestion: Start your Dopemux stack with: docker-compose up -d" >&2
  exit 1
fi

# Verify container is running.
if ! docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
  echo "❌ dope-context-wrapper: Container '$container_name' is not running" >&2
  exit 1
fi

export DOPEMUX_WORKSPACE_ID="$workspace_id"

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  "$container_name" \
  python /app/server.py "$@"
