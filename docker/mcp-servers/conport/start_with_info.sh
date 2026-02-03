#!/bin/bash
set -e

echo "Starting ConPort with service discovery support..."

# Start info server in background
python info_server.py &
INFO_PID=$!

# Start main MCP server (enhanced_server.py)
python enhanced_server.py &
MCP_PID=$!

# Wait for both processes
wait $INFO_PID $MCP_PID
