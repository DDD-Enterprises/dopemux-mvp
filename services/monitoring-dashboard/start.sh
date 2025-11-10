#!/bin/bash
"""
Start Dopemux Monitoring Dashboard Service

Usage:
    ./start.sh [options]

Options:
    --port PORT     Port to run on (default: 8098)
    --host HOST     Host to bind to (default: 0.0.0.0)
    --debug         Run with debug logging
"""

set -e

# Default configuration
PORT=${PORT:-8098}
HOST=${HOST:-0.0.0.0}
DEBUG=${DEBUG:-false}

# Log directory
LOG_DIR="/var/log/dopemux/monitoring-dashboard"
mkdir -p "$LOG_DIR"

# Environment setup
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "🚀 Starting Dopemux Monitoring Dashboard"
echo "Port: $PORT | Host: $HOST | Debug: $DEBUG"

# Start service
cd services/monitoring-dashboard
python server.py --host $HOST --port $PORT