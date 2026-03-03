#!/bin/bash
# verify-setup.sh: Verify the mobile development environment.

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO_ROOT"

echo "=== Mobile-First Setup Verification ==="

# 1. tmux check
if command -v tmux >/dev/null 2>&1; then
    TMUX_VER=$(tmux -V | cut -d ' ' -f 2)
    echo "✅ tmux $TMUX_VER found."
else
    echo "❌ tmux not found."
    exit 1
fi

# 2. Config check
CONFIG_FILE="$HOME/.tmux.mobile.conf"
if [ -L "$CONFIG_FILE" ]; then
    echo "✅ ~/.tmux.mobile.conf is a symlink."
elif [ -f "$CONFIG_FILE" ]; then
    echo "⚠️ ~/.tmux.mobile.conf exists but is NOT a symlink."
else
    echo "❌ ~/.tmux.mobile.conf missing. Run symlink command from SETUP.md."
fi

# 3. Scripts check
SCRIPTS=("scripts/mobile/dopemux-mobile.sh" "scripts/mobile/status-dashboard.sh" "scripts/mobile/supervisor-context.sh")
for s in "${SCRIPTS[@]}"; do
    if [ -x "$s" ]; then
        echo "✅ $s is executable."
    else
        echo "❌ $s not found or not executable."
    fi
done

# 4. ConPort (mcp-conport) connectivity check
if curl -s http://localhost:3005/api/progress >/dev/null; then
    echo "✅ ConPort (mcp-conport) reachable on port 3005."
else
    echo "⚠️ ConPort unreachable on port 3005. (Docker check required)"
fi

echo "--- Verification Complete ---"
