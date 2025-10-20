#!/bin/bash
# Serena MCP Wrapper - Auto-detects workspace for worktree support
# Usage: Called by Claude Desktop with stdin/stdout communication
#
# OPTIMIZED: Uses shared workspace detection module (single source of truth)

# Source shared workspace detection (eliminates duplicate code!)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/src/dopemux/export_workspace_env.sh"

# DOPEMUX_WORKSPACE_ROOT is now set by shared script
WORKSPACE_PATH="$DOPEMUX_WORKSPACE_ROOT"

# Log for debugging (optional - can disable with DOPEMUX_DEBUG=0)
if [ "${DOPEMUX_DEBUG:-1}" = "1" ]; then
    echo "[Serena Wrapper] Detected workspace: $WORKSPACE_PATH" >&2
fi

# Execute Serena MCP via Docker (reuses running container)
exec docker exec \
    -e WORKSPACE_PATH="$WORKSPACE_PATH" \
    -i mcp-serena \
    python /app/wrapper.py \
    "$@"
