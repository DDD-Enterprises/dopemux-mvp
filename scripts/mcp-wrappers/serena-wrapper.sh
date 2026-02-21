#!/usr/bin/env bash
set -euo pipefail

# Serena V2 MCP Wrapper - Direct Python server launcher
# Uses local Python implementation instead of Docker for better reliability

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

workspace_id="$(detect_workspace)"

# Get the root of dopemux-mvp (where this script lives)
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
serena_path="${script_dir}/services/serena/v2/mcp_server.py"

if [[ ! -f "$serena_path" ]]; then
  echo "❌ serena-wrapper: Serena MCP server not found at $serena_path" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ serena-wrapper: python3 is required but not found in PATH" >&2
  exit 1
fi

export DOPEMUX_WORKSPACE_ID="$workspace_id"

# Launch Serena MCP server directly
exec python3 "$serena_path" "$@"
