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

# Activate virtual environment.
# Setup may create either .venv (modern convention) or .zen_venv (legacy PAL
# setup / run_integration_tests.sh); prefer .venv, fall back to .zen_venv,
# matching communication_simulator_test.py. Fail loudly if neither exists.
if [[ -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.venv/bin/activate"
elif [[ -f "$SCRIPT_DIR/.zen_venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.zen_venv/bin/activate"
else
  echo "start-pal.sh: no virtualenv found (.venv or .zen_venv) in $SCRIPT_DIR" >&2
  exit 1
fi

# Start the PAL server
exec python "$SCRIPT_DIR/server.py"
