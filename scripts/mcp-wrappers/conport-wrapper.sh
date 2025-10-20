#!/bin/bash
# ConPort MCP Wrapper - Auto-detects workspace for worktree support
# Usage: Called by Claude Desktop with stdin/stdout communication
#
# OPTIMIZED: Uses shared workspace detection module (single source of truth)
# Note: ConPort uses local Python (not Docker) because Docker container runs
# HTTP server, while Claude Code needs stdio mode.

# Source shared workspace detection (eliminates duplicate code!)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/src/dopemux/export_workspace_env.sh"

# DOPEMUX_WORKSPACE_ROOT is now set by shared script
WORKSPACE_PATH="$DOPEMUX_WORKSPACE_ROOT"

# Execute ConPort MCP via local Python (stdio mode)
# Note: Each call spawns new process, but cached workspace detection reduces overhead by ~40%
exec conport-mcp \
    --workspace_id "$WORKSPACE_PATH" \
    --mode stdio \
    "$@"
