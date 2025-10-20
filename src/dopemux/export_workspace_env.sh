#!/bin/bash
# Shared Workspace Detection and Environment Export
# Used by all MCP wrapper scripts for consistent workspace detection
#
# ADHD Optimization: Single source of truth, reduces cognitive load
# Worktree Support: Uses git rev-parse (works for main repo + worktrees)
#
# Usage in MCP wrappers:
#   source "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")/src/dopemux/export_workspace_env.sh"
#   # Now $DOPEMUX_WORKSPACE_ROOT is set

detect_workspace() {
    # Priority 1: Explicit DOPEMUX_WORKSPACE_ROOT override
    if [ -n "$DOPEMUX_WORKSPACE_ROOT" ]; then
        echo "$DOPEMUX_WORKSPACE_ROOT"
        return
    fi

    # Priority 2: Claude Desktop's CLAUDE_WORKSPACE
    if [ -n "$CLAUDE_WORKSPACE" ]; then
        echo "$CLAUDE_WORKSPACE"
        return
    fi

    # Priority 3: dopemux CLI with caching (30s TTL - reduces git overhead)
    if command -v dopemux &> /dev/null; then
        local workspace=$(dopemux worktrees current 2>/dev/null)
        if [ -n "$workspace" ]; then
            echo "$workspace"
            return
        fi
    fi

    # Priority 4: Direct git detection (works for main repo + worktrees!)
    if command -v git &> /dev/null; then
        local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -n "$git_root" ]; then
            echo "$git_root"
            return
        fi
    fi

    # Priority 5: Python module fallback (most reliable)
    if command -v python3 &> /dev/null; then
        # Try to use the shared Python module
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        local project_root="$(cd "$script_dir/../.." && pwd)"

        local workspace=$(python3 -c "
import sys
sys.path.insert(0, '$project_root')
try:
    from src.dopemux.workspace_detection import get_workspace_root
    print(get_workspace_root())
except Exception:
    import os
    print(os.getcwd())
" 2>/dev/null)

        if [ -n "$workspace" ]; then
            echo "$workspace"
            return
        fi
    fi

    # Last resort: current directory
    pwd
}

# Detect and export workspace environment variables
export DOPEMUX_WORKSPACE_ROOT=$(detect_workspace)
export DOPEMUX_WORKSPACE_ID="$DOPEMUX_WORKSPACE_ROOT"  # Alias for compatibility

# Optional: Log for debugging (can be disabled in production)
if [ "${DOPEMUX_DEBUG:-0}" = "1" ]; then
    echo "[Dopemux] Workspace detected: $DOPEMUX_WORKSPACE_ROOT" >&2
fi
