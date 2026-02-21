#!/usr/bin/env bash
set -euo pipefail

# ConPort MCP Wrapper - Resilient Docker-based MCP server launcher
# This script wraps the docker-based ConPort MCP server, handling:
# - Workspace detection
# - Container name resolution (works with renamed containers)
# - Graceful error handling

detect_workspace() {
  if [[ -n "${DOPEMUX_WORKSPACE_ID:-}" ]]; then
    printf '%s\n' "${DOPEMUX_WORKSPACE_ID}"
    return
  fi

  if command -v git >/dev/null 2>&1; then
    local git_root
    git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "${git_root}" ]]; then
      printf '%s\n' "${git_root}"
      return
    fi
  fi

  pwd
}

find_container() {
  local container_pattern="$1"

  # Try exact match first
  if docker ps --format "table {{.Names}}" | grep -q "^${container_pattern}$"; then
    echo "$container_pattern"
    return 0
  fi

  # Try partial match (for resilience to container name changes)
  if docker ps --format "table {{.Names}}" | grep -q "$container_pattern"; then
    docker ps --format "table {{.Names}}" | grep "$container_pattern" | head -1
    return 0
  fi

  return 1
}

workspace_id="$(detect_workspace)"
instance_id="${DOPEMUX_INSTANCE_ID:-$(basename "${workspace_id}")}"

export DOPEMUX_WORKSPACE_ID="${workspace_id}"
export DOPEMUX_INSTANCE_ID="${instance_id}"

# Fail closed: require docker
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ conport-wrapper: docker is required but not found in PATH" >&2
  exit 1
fi

# Find the ConPort container (try new name first, then old)
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

# Verify container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
  echo "❌ conport-wrapper: Container '$container_name' is not running" >&2
  exit 1
fi

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  -e DOPEMUX_INSTANCE_ID="${DOPEMUX_INSTANCE_ID}" \
  "$container_name" \
  uvx --from context-portal-mcp conport-mcp "$@"
