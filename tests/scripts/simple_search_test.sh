#!/bin/bash

echo "🔍 Testing VoyageAI rerank-2.5 search with existing indexed data..."

# Create test request
cat <<EOF > /tmp/search_request.json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_code",
    "arguments": {
      "path": "/workspace/dopemux-mvp",
      "query": "ADHD context preservation workflow",
      "limit": 3
    }
  }
}
EOF

echo "📤 Sending search request to claude-context container..."
timeout 10s docker exec -i mcp-claude-context sh -c '
  echo "Starting MCP session..." >&2
  npx @zilliz/claude-context-mcp@latest 2>&1 &
  sleep 3
  cat /tmp/search_request.json
  sleep 5
' < /tmp/search_request.json

echo "✅ Search test completed"