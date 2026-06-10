#!/usr/bin/env bash
#
# start-pal.sh
# Robust launcher for PAL MCP server inside OpenCode
# Handles .env loading + venv activation reliably
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# Load environment variables from repo .env
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.venv/bin/activate"

# Start the PAL server
exec python "$SCRIPT_DIR/server.py"
