#!/usr/bin/env bash
set -eo pipefail

echo "Installing Cloudflare Tunnel daemon for macOS..."

CFG_DIR="$HOME/.cloudflared"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPS_CFG="$REPO_ROOT/ops/cloudflared/config.yml"
TARGET_CFG="$CFG_DIR/config.yml"
PLIST_SRC="$REPO_ROOT/ops/cloudflared/com.cloudflare.dopemux-webhooks.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.cloudflare.dopemux-webhooks.plist"

mkdir -p "$CFG_DIR"

if [ ! -f "$OPS_CFG" ]; then
    echo "Error: config.yml not found at $OPS_CFG"
    exit 1
fi

echo "Copying config.yml to ~/.cloudflared..."
cp "$OPS_CFG" "$TARGET_CFG"

echo "Copying plist to ~/Library/LaunchAgents/..."
mkdir -p "$HOME/Library/LaunchAgents"
sed "s|{{HOME}}|$HOME|g" "$PLIST_SRC" > "$PLIST_DST"

echo "Bootstrapping daemon..."
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load -w "$PLIST_DST"
launchctl start com.cloudflare.dopemux-webhooks

echo "Tail logs with:"
echo "  tail -f ~/.cloudflared/dopemux-webhooks.log"
echo ""
echo "Or check status with:"
echo "  launchctl print gui/$UID/com.cloudflare.dopemux-webhooks"
