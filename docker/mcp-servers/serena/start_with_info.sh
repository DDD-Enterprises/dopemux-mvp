#!/bin/bash
set -e

echo "Starting Serena with service discovery support..."

# Start info server in background
python info_server.py &
INFO_PID=$!

# Start main MCP server (wrapper.py)
python wrapper.py &
MCP_PID=$!

# Wait for both processes
wait $INFO_PID $MCP_PID
