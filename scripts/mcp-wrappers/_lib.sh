#!/usr/bin/env bash
# Shared helpers for MCP wrapper scripts.
# Source this file from each wrapper:
#   source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
#
# Provides:
#   detect_workspace       — Resolve the active workspace path (env > git > cwd)
#   detect_instance_id     — Stable short ID for the workspace (env > basename)
#   find_container <name>  — Locate a running Docker container by exact or partial name match
#   require_docker         — Fail with a clear error if `docker` is not on PATH

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

detect_instance_id() {
  local workspace_id="${1:-${DOPEMUX_WORKSPACE_ID:-$(detect_workspace)}}"
  printf '%s\n' "${DOPEMUX_INSTANCE_ID:-$(basename "${workspace_id}")}"
}

find_container() {
  local container_pattern="$1"

  # Try exact match first (most specific).
  if docker ps --format "table {{.Names}}" | grep -q "^${container_pattern}$"; then
    echo "$container_pattern"
    return 0
  fi

  # Try partial match (resilient to container name drift).
  if docker ps --format "table {{.Names}}" | grep -q "$container_pattern"; then
    docker ps --format "table {{.Names}}" | grep "$container_pattern" | head -1
    return 0
  fi

  return 1
}

require_docker() {
  local script_label="${1:-mcp-wrapper}"
  if ! command -v docker >/dev/null 2>&1; then
    echo "❌ ${script_label}: docker is required but not found in PATH" >&2
    exit 1
  fi
}
