#!/bin/bash
cd "$(dirname "$0")"

# Load environment variables from project root .env
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
fi

exec python -m src.mcp.server
