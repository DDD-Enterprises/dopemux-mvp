#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SERVICE_TEMPLATE="$PROJECT_ROOT/installers/systemd/dopemux-mcp.service.template"
SERVICE_DEST="/etc/systemd/system/dopemux-mcp.service"

echo "[dopemux] Installing systemd service to $SERVICE_DEST (sudo required)"
TMP_FILE="$(mktemp)"
sed "s#__PROJECT_ROOT__#$PROJECT_ROOT#g" "$SERVICE_TEMPLATE" > "$TMP_FILE"

sudo mv "$TMP_FILE" "$SERVICE_DEST"
sudo chmod 644 "$SERVICE_DEST"

echo "[dopemux] Reloading systemd, enabling and starting service"
sudo systemctl daemon-reload
sudo systemctl enable dopemux-mcp
sudo systemctl start dopemux-mcp

echo "[dopemux] Service status:"
systemctl --no-pager status dopemux-mcp || true

echo "[dopemux] Manage with: sudo systemctl [start|stop|restart|status] dopemux-mcp"

