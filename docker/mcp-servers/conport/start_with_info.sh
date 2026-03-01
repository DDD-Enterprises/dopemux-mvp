#!/bin/bash
set -e

echo "Starting ConPort with service discovery support..."

# Start info server in background
python info_server.py &
INFO_PID=$!

# Start REST API server on port 3004 (for Docker service-to-service)
MCP_SERVER_PORT=3004 python enhanced_server.py &
REST_PID=$!

# Start MCP protocol server on port 3005 (for Claude Code)
MCP_SERVER_PORT=3005 python server.py &
PROXY_PID=$!

# Wait for all processes
wait $INFO_PID $REST_PID $PROXY_PID
