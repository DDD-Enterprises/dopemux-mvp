#!/bin/bash

# Setup Task Orchestrator Always-On
# Run from project root: /Users/hue/code/dopemux-mvp

set -e  # Exit on error

echo "🚀 Setting up always-on Task Orchestrator..."

# 1. Update Dockerfile in services/task-orchestrator
cat > services/task-orchestrator/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Java for Kotlin backend
RUN apt-get update && apt-get install -y --no-install-recommends \
   gcc \
   openjdk-17-jdk \
   && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose MCP port
EXPOSE 3014

# Health check for MCP SSE endpoint
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3014/sse')" || exit 1

# Run the Python MCP wrapper persistently
CMD ["python", "server.py"]
EOF

echo "✅ Dockerfile updated"

# 2. Update docker-compose.yml - Remove manual profile, update command and healthcheck
sed -i.bak 's/profiles: \["manual"\]//g' docker-compose.yml
sed -i.bak 's/restart: "on-failure:3"/restart: unless-stopped/g' docker-compose.yml
sed -i.bak 's/command: \[.*sleep infinity.*\]/command: ["python", "\/app\/server.py"]/g' docker-compose.yml
sed -i.bak 's/test: \["CMD-SHELL", "exit 0"\]/test: ["CMD-SHELL", "curl -f http:\/\/localhost:3014\/sse --head || nc -z localhost 3014 || exit 1"]/' docker-compose.yml
sed -i.bak 's/timeout: 5s/timeout: 10s/g' docker-compose.yml
sed -i.bak 's/start_period: 30s/start_period: 45s/g' docker-compose.yml
sed -i.bak '/labels:/a\      - "mcp.transport=sse"' docker-compose.yml

echo "✅ docker-compose.yml updated"

# 3. Rebuild the image
docker-compose build --no-cache task-orchestrator

echo "✅ Image rebuilt"

# 4. Restart the container
docker-compose up -d task-orchestrator

echo "✅ Container restarted"

# 5. Verify
sleep 10

echo "🔍 Checking status..."
docker ps | grep task-orchestrator

echo "🔍 Checking logs..."
docker logs mcp-task-orchestrator --tail 20

echo "🔍 Testing MCP handshake..."
curl -s -N -X POST http://localhost:3014/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'

echo "🚀 Setup complete! Check the output above for status."
