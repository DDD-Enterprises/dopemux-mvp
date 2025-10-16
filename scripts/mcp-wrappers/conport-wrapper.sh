#!/bin/bash
# ConPort MCP Wrapper - Auto-detects workspace for worktree support
# Usage: Called by Claude Desktop with stdin/stdout communication

# Detect the current workspace (worktree-aware)
detect_workspace() {
    # Check if CLAUDE_WORKSPACE is set (passed from Claude Desktop)
    if [ -n "$CLAUDE_WORKSPACE" ]; then
        echo "$CLAUDE_WORKSPACE"
        return
    fi

    # Try to detect from git
    if command -v git &> /dev/null; then
        # Get git root directory (works for both main repo and worktrees)
        local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -n "$git_root" ]; then
            echo "$git_root"
            return
        fi
    fi

    # Fallback to main dopemux-mvp location
    echo "/Users/hue/code/dopemux-mvp"
}

# Get workspace path
WORKSPACE_PATH=$(detect_workspace)

# Log for debugging (optional - comment out for production)
echo "[ConPort Wrapper] Detected workspace: $WORKSPACE_PATH" >&2

# Execute ConPort MCP with detected workspace in stdio mode
exec /Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp \
    --workspace_id "$WORKSPACE_PATH" \
    --mode stdio \
    "$@"
