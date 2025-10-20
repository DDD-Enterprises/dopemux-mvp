#!/bin/bash
# Exa MCP - uvx Startup Script
# Runs Exa in stdio mode for Claude Code

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export EXA_API_KEY if not set (from env or .env file)
if [ -z "$EXA_API_KEY" ]; then
    # Try to load from .env file in project root
    if [ -f "$SCRIPT_DIR/../../../.env" ]; then
        export $(grep "^EXA_API_KEY=" "$SCRIPT_DIR/../../../.env" | xargs)
    fi
fi

# Start Exa MCP in stdio mode
>&2 echo "Starting Exa MCP Server in stdio mode..."
>&2 echo "EXA_API_KEY configured: $([ -n "$EXA_API_KEY" ] && echo 'yes' || echo 'no')"

# Set run mode to stdio and execute
cd "$SCRIPT_DIR"
export MCP_RUN_MODE=stdio
exec uvx --from . exa-mcp
