#!/usr/bin/env bash
set -euo pipefail

# ConPort MCP Wrapper - Resilient Docker-based MCP server launcher
# Wraps the docker-based ConPort MCP server: workspace detection,
# exact container name resolution, graceful errors.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

workspace_id="$(detect_workspace)"
instance_id="$(detect_instance_id "$workspace_id")"

export DOPEMUX_WORKSPACE_ID="${workspace_id}"
export DOPEMUX_INSTANCE_ID="${instance_id}"

require_docker "conport-wrapper"

# Exact container name only. Created by compose.yml:237
# (container_name: ${CONPORT_CONTAINER_NAME:-mcp-conport}); per-instance names
# come from src/dopemux/mcp/instance_overlay.py:175 via CONPORT_CONTAINER_NAME.
# No substring fallback: never attach to another worktree's/project's container.
expected_name="${CONPORT_CONTAINER_NAME:-mcp-conport}"
if ! container_name="$(find_container "$expected_name")"; then
  echo "❌ conport-wrapper: ConPort container '$expected_name' not found or not running" >&2
  echo "💡 Suggestion: start it with 'dopemux mcp start' (or set CONPORT_CONTAINER_NAME to this project's container)" >&2
  exit 1
fi

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  -e DOPEMUX_INSTANCE_ID="${DOPEMUX_INSTANCE_ID}" \
  "$container_name" \
  uvx --from context-portal-mcp conport-mcp "$@"
