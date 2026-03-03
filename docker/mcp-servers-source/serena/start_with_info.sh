#!/bin/bash
set -e

echo "Starting Serena with service discovery support..."

# Symlink host path to internal mount if variables are set
if [ -n "$HOST_CODE_PARENT_DIR" ]; then
    echo "Creating symlink for host path compatibility..."
    # Create parent directories
    mkdir -p "$(dirname "$HOST_CODE_PARENT_DIR")"
    # Link host path to /workspaces
    ln -sfn /workspaces "$HOST_CODE_PARENT_DIR"
    echo "Linked $HOST_CODE_PARENT_DIR -> /workspaces"
fi

# Start info server in background
python info_server.py &
INFO_PID=$!

# Start main MCP server (wrapper.py)
python wrapper.py &
MCP_PID=$!

# Wait for both processes
wait $INFO_PID $MCP_PID
