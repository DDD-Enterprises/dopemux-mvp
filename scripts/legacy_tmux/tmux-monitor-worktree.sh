#!/bin/bash
# Rich Continuous: Full git diff + status for worktree monitor
echo "=== Git Status ==="
git diff --shortstat 2>/dev/null || echo "No changes"
echo ""
echo "=== Changed Files ==="
git status --porcelain 2>/dev/null | head -10 || echo "No files tracked"