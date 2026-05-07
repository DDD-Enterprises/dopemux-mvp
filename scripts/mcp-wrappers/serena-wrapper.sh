#!/usr/bin/env bash
set -euo pipefail

# Serena V2 MCP Wrapper - Direct Python server launcher
# Uses local Python implementation instead of Docker for better reliability.

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

workspace_id="$(detect_workspace)"

# Get the root of dopemux-mvp (where this script lives).
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

# Launch Serena MCP server directly.
exec python3 "$serena_path" "$@"
