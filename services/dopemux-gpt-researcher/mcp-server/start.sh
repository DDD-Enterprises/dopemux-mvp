#!/bin/bash

# Start script for GPT-Researcher MCP Server
# Sets up environment and launches the server

echo "🚀 Starting GPT-Researcher MCP Server..."

# Set workspace path
export WORKSPACE_PATH="${WORKSPACE_PATH:-/Users/hue/code/dopemux-mvp}"

# Load API keys from .env if it exists
if [ -f ../.env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check for API keys
echo "🔑 Checking API keys..."
[ -n "$EXA_API_KEY" ] && echo "  ✅ Exa API key found" || echo "  ⚠️  Exa API key missing"
[ -n "$TAVILY_API_KEY" ] && echo "  ✅ Tavily API key found" || echo "  ⚠️  Tavily API key missing"
[ -n "$PERPLEXITY_API_KEY" ] && echo "  ✅ Perplexity API key found" || echo "  ⚠️  Perplexity API key missing"
[ -n "$CONTEXT7_API_KEY" ] && echo "  ✅ Context7 API key found" || echo "  ⚠️  Context7 API key missing"

# Enable debug mode if requested
if [ "$1" = "--debug" ]; then
    export DEBUG=true
    echo "🐛 Debug mode enabled"
fi

# Start the server
echo ""
echo "📡 Server starting on stdio protocol..."
echo "   Press Ctrl+C to stop"
echo "-----------------------------------------"

python server.py