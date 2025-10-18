#!/bin/bash
# Serena MCP Wrapper - Auto-detects workspace for worktree support
# Usage: Called by Claude Desktop with stdin/stdout communication
#
# OPTIMIZED: Uses Docker container + cached detection for consistency

# Detect the current workspace (worktree-aware with caching)
detect_workspace() {
    # Check if CLAUDE_WORKSPACE is set (passed from Claude Desktop)
    if [ -n "$CLAUDE_WORKSPACE" ]; then
        echo "$CLAUDE_WORKSPACE"
        return
    fi

    # Use dopemux CLI with caching (30s TTL)
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

# Get workspace path (cached via dopemux CLI)
WORKSPACE_PATH=$(detect_workspace)

# Log for debugging (optional - comment out for production)
echo "[Serena Wrapper] Detected workspace: $WORKSPACE_PATH" >&2

# Execute Serena MCP via Docker (reuses running container)
exec docker exec \
    -e WORKSPACE_PATH="$WORKSPACE_PATH" \
    -i mcp-serena \
    python /app/wrapper.py \
    "$@"
