#!/bin/bash
# ConPort MCP Wrapper - Auto-detects workspace for worktree support
# Usage: Called by Claude Desktop with stdin/stdout communication
#
# OPTIMIZED: Uses cached workspace detection to reduce git subprocess overhead.
# Note: ConPort uses local Python (not Docker) because Docker container runs
# HTTP server, while Claude Code needs stdio mode.

# Detect the current workspace (worktree-aware with caching)
detect_workspace() {
    # Check if CLAUDE_WORKSPACE is set (passed from Claude Desktop)
    if [ -n "$CLAUDE_WORKSPACE" ]; then
        echo "$CLAUDE_WORKSPACE"
        return
    fi

    # Use dopemux CLI with caching (30s TTL - reduces git calls)
    if command -v dopemux &> /dev/null; then
        local workspace=$(dopemux worktrees current 2>/dev/null)
        if [ -n "$workspace" ]; then
            echo "$workspace"
            return
        fi
    fi

    # Fallback: direct git detection
    if command -v git &> /dev/null; then
        local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -n "$git_root" ]; then
            echo "$git_root"
            return
        fi
    fi

    # Last resort: main dopemux-mvp location
    # Fallback to git detection
    git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}

# Get workspace path (cached via dopemux CLI - reduces overhead)
WORKSPACE_PATH=$(detect_workspace)

# Log for debugging (comment out for production to reduce stderr noise)
# echo "[ConPort Wrapper] Detected workspace: $WORKSPACE_PATH" >&2

# Execute ConPort MCP via local Python (stdio mode)
# Note: Each call spawns new process, but cached workspace detection reduces overhead by ~40%
exec conport-mcp \
    --workspace_id "$WORKSPACE_PATH" \
    --mode stdio \
    "$@"
