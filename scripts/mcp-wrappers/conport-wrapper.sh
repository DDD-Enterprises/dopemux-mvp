#!/usr/bin/env bash
set -euo pipefail

# ConPort MCP Wrapper - Resilient Docker-based MCP server launcher
# Wraps the docker-based ConPort MCP server: workspace detection,
# container name resolution (works with renamed containers), graceful errors.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

workspace_id="$(detect_workspace)"
instance_id="$(detect_instance_id "$workspace_id")"

export DOPEMUX_WORKSPACE_ID="${workspace_id}"
export DOPEMUX_INSTANCE_ID="${instance_id}"

require_docker "conport-wrapper"

# Find the ConPort container (try new name first, then old).
container_name=""
for name_pattern in "dopemux-mcp-conport" "mcp-conport"; do
  if container_name="$(find_container "$name_pattern")"; then
    break
  fi
done

if [[ -z "$container_name" ]]; then
  echo "❌ conport-wrapper: ConPort container not found (tried: dopemux-mcp-conport, mcp-conport)" >&2
  echo "💡 Suggestion: Start your Dopemux stack with: docker-compose up -d" >&2
  exit 1
fi

# Verify container is running.
if ! docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
  echo "❌ conport-wrapper: Container '$container_name' is not running" >&2
  exit 1
fi

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  -e DOPEMUX_INSTANCE_ID="${DOPEMUX_INSTANCE_ID}" \
  "$container_name" \
  uvx --from context-portal-mcp conport-mcp "$@"
