#!/bin/bash
cd "$(dirname "$0")"

# Load environment variables from project root .env
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
fi

# Source shared workspace detection (exports DOPEMUX_WORKSPACE_ROOT)
PROJECT_ROOT="$(cd ../.. && pwd)"
if [ -f "$PROJECT_ROOT/src/dopemux/export_workspace_env.sh" ]; then
    source "$PROJECT_ROOT/src/dopemux/export_workspace_env.sh"
fi

exec python -m src.mcp.server
