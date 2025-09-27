#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PLIST_TEMPLATE="$PROJECT_ROOT/installers/macos/com.dopemux.mcp.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/com.dopemux.mcp.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$PROJECT_ROOT/logs"

echo "[dopemux] Installing LaunchAgent to $PLIST_DEST"
sed "s#__PROJECT_ROOT__#$PROJECT_ROOT#g" "$PLIST_TEMPLATE" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load -w "$PLIST_DEST"

echo "[dopemux] LaunchAgent loaded. Logs: $PROJECT_ROOT/logs/launchd-dopemux-mcp.*.log"
echo "[dopemux] Manage with: launchctl list | grep dopemux; launchctl unload -w $PLIST_DEST"

