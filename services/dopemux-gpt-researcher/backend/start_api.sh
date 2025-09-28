#!/bin/bash

# Start script for GPT-Researcher Phase 2 FastAPI Application
# Provides ADHD-optimized research API with real-time progress tracking

echo "🚀 Starting GPT-Researcher Phase 2 API..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Set default environment variables
export WORKSPACE_PATH="${WORKSPACE_PATH:-/Users/hue/code/dopemux-mvp}"
export API_PORT="${API_PORT:-8000}"
export SESSION_STORAGE_PATH="${SESSION_STORAGE_PATH:-$WORKSPACE_PATH/.sessions}"

# Load environment variables from .env if it exists
if [ -f "../.env" ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check for API keys
echo ""
echo "🔑 API Key Status:"
[ -n "$EXA_API_KEY" ] && echo "  ✅ Exa API key configured" || echo "  ⚠️  Exa API key missing"
[ -n "$TAVILY_API_KEY" ] && echo "  ✅ Tavily API key configured" || echo "  ⚠️  Tavily API key missing"
[ -n "$PERPLEXITY_API_KEY" ] && echo "  ✅ Perplexity API key configured" || echo "  ⚠️  Perplexity API key missing"
[ -n "$CONTEXT7_API_KEY" ] && echo "  ✅ Context7 API key configured" || echo "  ⚠️  Context7 API key missing"

# Create session storage directory
echo ""
echo "📁 Creating session storage at: $SESSION_STORAGE_PATH"
mkdir -p "$SESSION_STORAGE_PATH"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Enable debug mode if requested
if [ "$1" = "--debug" ]; then
    export DEBUG=true
    echo ""
    echo "🐛 Debug mode enabled"
fi

# Display API information
echo ""
echo "📡 API Information:"
echo "  • Base URL: http://localhost:$API_PORT"
echo "  • Health Check: http://localhost:$API_PORT/health"
echo "  • API Docs: http://localhost:$API_PORT/docs"
echo "  • WebSocket: ws://localhost:$API_PORT/ws/{task_id}"
echo ""
echo "🧠 ADHD Features Active:"
echo "  • Session persistence for interruption recovery"
echo "  • Real-time progress tracking via WebSocket"
echo "  • Automatic break reminders (every 25 minutes)"
echo "  • Attention state detection"
echo "  • Hyperfocus protection"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI application
python -m api.main