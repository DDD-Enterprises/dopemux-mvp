#!/bin/bash
# Demo launcher for ConPort KG UI
# Starts mock server and UI together with proper cleanup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎭 Starting ConPort KG UI Demo Mode"
echo ""

# Start mock server in background
echo "Starting mock API server..."
npm run mock-server &
MOCK_PID=$!

# Give server time to start
sleep 2

# Check if server is running
if ! kill -0 $MOCK_PID 2>/dev/null; then
  echo "❌ Failed to start mock server"
  exit 1
fi

echo "✅ Mock server running (PID: $MOCK_PID)"
echo ""

# Cleanup function
cleanup() {
  echo ""
  echo "🧹 Cleaning up..."
  if kill -0 $MOCK_PID 2>/dev/null; then
    kill $MOCK_PID 2>/dev/null || true
    echo "✅ Mock server stopped"
  fi
}

# Register cleanup on exit
trap cleanup EXIT INT TERM

# Start UI
echo "Starting UI..."
echo ""
npm run dev

# Cleanup happens automatically via trap
