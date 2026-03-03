#!/bin/bash
# Desktop Commander MCP - uvx Startup Wrapper
# Ensures HTTP server is running, then starts stdio bridge

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_PORT=3012
SERVER_PID_FILE="/tmp/desktop-commander-uvx.pid"

# Check if server is already running
if [ -f "$SERVER_PID_FILE" ]; then
    PID=$(cat "$SERVER_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        # Server is running
        >&2 echo "Desktop Commander HTTP server already running (PID: $PID)"
    else
        # PID file exists but process is dead, clean up
        rm "$SERVER_PID_FILE"
    fi
fi

# Start server if not running
if [ ! -f "$SERVER_PID_FILE" ]; then
    >&2 echo "Starting Desktop Commander HTTP server with python..."
    cd "$SCRIPT_DIR"
    export DISPLAY=:0
    python3 server.py > /dev/null 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$SERVER_PID_FILE"
    >&2 echo "Desktop Commander HTTP server started (PID: $SERVER_PID)"

    # Wait for server to be ready
    for i in {1..10}; do
        if curl -s http://localhost:$SERVER_PORT/health > /dev/null 2>&1; then
            >&2 echo "Server is ready!"
            break
        fi
        >&2 echo "Waiting for server... ($i/10)"
        sleep 0.5
    done
fi

# Start stdio bridge
>&2 echo "Starting stdio bridge..."
exec python3 "$SCRIPT_DIR/stdio_bridge.py"
