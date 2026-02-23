#!/usr/bin/env bash
set -eo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.cloudflare.dopemux-webhooks.plist"

echo "Stopping daemon..."
launchctl stop com.cloudflare.dopemux-webhooks 2>/dev/null || true
launchctl unload -w "$PLIST_DST" 2>/dev/null || true

echo "Removing plist..."
rm -f "$PLIST_DST"

echo "Uninstalled."
