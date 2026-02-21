#!/usr/bin/env bash
set -euo pipefail

# Dope-Context MCP Wrapper - Docker-based semantic search launcher
# This script wraps the docker-based Dope-Context MCP server

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

  # Try partial match (for resilience)
  if docker ps --format "table {{.Names}}" | grep -q "$container_pattern"; then
    docker ps --format "table {{.Names}}" | grep "$container_pattern" | head -1
    return 0
  fi

  return 1
}

workspace_id="$(detect_workspace)"

# Fail closed: require docker
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ dope-context-wrapper: docker is required but not found in PATH" >&2
  exit 1
fi

# Find the Dope-Context container (try new name first, then old)
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

# Verify container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
  echo "❌ dope-context-wrapper: Container '$container_name' is not running" >&2
  exit 1
fi

export DOPEMUX_WORKSPACE_ID="$workspace_id"

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  "$container_name" \
  python /app/server.py "$@"
