#!/bin/bash
# Start missing MCP servers (mas-sequential-thinking, exa, desktop-commander)

set -e

echo "🚀 Starting missing MCP servers..."

# Load environment variables
source .env 2>/dev/null || true

# Start mas-sequential-thinking (port 3001)
echo "Starting mas-sequential-thinking on port 3001..."
docker run -d \
  --name mcp-mas-sequential-thinking \
  --network dopemux-network \
  -p 3001:3001 \
  -e MCP_SERVER_PORT=3001 \
  -e LLM_PROVIDER=${LLM_PROVIDER:-openai} \
  -e OPENAI_API_KEY=${OPENAI_API_KEY} \
  -e DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY} \
  -e GROQ_API_KEY=${GROQ_API_KEY} \
  -e EXA_API_KEY=${EXA_API_KEY} \
  --restart unless-stopped \
  -v "$(pwd)/mcp-server-mas-sequential-thinking:/app" \
  -w /app \
  python:3.11-slim \
  bash -c "pip install -q uv && uv pip install -e . && uv run python docker_server.py" \
  2>/dev/null || echo "⚠️  mas-sequential-thinking already running or failed"

# Start exa (port 3008)
echo "Starting exa on port 3008..."
docker run -d \
  --name mcp-exa \
  --network dopemux-network \
  -p 3008:3008 \
  -e MCP_SERVER_PORT=3008 \
  -e EXA_API_KEY=${EXA_API_KEY} \
  --restart unless-stopped \
  -v "$(pwd)/exa:/app" \
  -w /app \
  python:3.11-slim \
  bash -c "pip install -q -r requirements.txt && python exa_server.py" \
  2>/dev/null || echo "⚠️  exa already running or failed"

# Start desktop-commander (port 3012)
echo "Starting desktop-commander on port 3012..."
docker run -d \
  --name mcp-desktop-commander \
  --network dopemux-network \
  -p 3012:3012 \
  -e MCP_SERVER_PORT=3012 \
  -e DISPLAY=${DISPLAY:-:0} \
  --restart unless-stopped \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /tmp:/tmp \
  -v "$(pwd)/desktop-commander:/app" \
  -w /app \
  python:3.11-slim \
  bash -c "apt-get update -qq && apt-get install -qq -y curl x11-apps xdotool wmctrl scrot imagemagick && pip install -q -r requirements.txt && python server.py" \
  2>/dev/null || echo "⚠️  desktop-commander already running or failed"

echo ""
echo "✅ MCP servers started!"
echo ""
echo "Checking status..."
sleep 2

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "mcp-mas|mcp-exa|mcp-desktop"

echo ""
echo "🎯 Now restart Claude Code to load the new configuration:"
echo "   1. Type /exit or press Ctrl+D"
echo "   2. Run: claude"
echo "   3. Check servers with: /mcp"
