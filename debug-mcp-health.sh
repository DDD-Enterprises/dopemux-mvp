#!/bin/bash
# MCP Server Health Check Script for Dopemux

echo "🔍 Dopemux MCP Server Health Check"
echo "=================================="
echo ""

# Check environment variables
echo "📋 Environment Variables:"
[ -n "$OPENAI_API_KEY" ] && echo "✅ OPENAI_API_KEY set" || echo "❌ OPENAI_API_KEY missing"
[ -n "$EXA_API_KEY" ] && echo "✅ EXA_API_KEY set" || echo "❌ EXA_API_KEY missing"
[ -n "$OPENROUTER_API_KEY" ] && echo "✅ OPENROUTER_API_KEY set" || echo "⚠️  OPENROUTER_API_KEY missing (optional)"
[ -n "$GEMINI_API_KEY" ] && echo "✅ GEMINI_API_KEY set" || echo "⚠️  GEMINI_API_KEY missing (optional)"
echo ""

# Check required binaries
echo "📦 Binary Availability:"
which mcp-server-mas-sequential-thinking >/dev/null 2>&1 && echo "✅ sequential-thinking binary found" || echo "❌ sequential-thinking binary missing"
which uvx >/dev/null 2>&1 && echo "✅ uvx available" || echo "❌ uvx missing"
which npx >/dev/null 2>&1 && echo "✅ npx available" || echo "❌ npx missing"
which python >/dev/null 2>&1 && echo "✅ python available" || echo "❌ python missing"
echo ""

# Check Python packages
echo "🐍 Python Package Check:"
python -c "import agno" 2>/dev/null && echo "✅ agno package available" || echo "❌ agno package missing"
python -c "import exa_py" 2>/dev/null && echo "✅ exa_py package available" || echo "❌ exa_py package missing"
python -c "import mcp" 2>/dev/null && echo "✅ mcp package available" || echo "❌ mcp package missing"
python -c "import serena" 2>/dev/null && echo "✅ serena package available" || echo "❌ serena package missing"
echo ""

# Check Docker
echo "🐳 Docker Status:"
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker available: $(docker --version)"
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker daemon running"
    else
        echo "❌ Docker daemon not running"
    fi
else
    echo "❌ Docker not available"
fi
echo ""

# Check Docker Compose
echo "🔧 Docker Compose Status:"
if command -v docker-compose >/dev/null 2>&1; then
    echo "✅ Docker Compose available: $(docker-compose --version)"
    cd /Users/hue/code/dopemux-mvp/docker/mcp-servers 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ MCP servers directory accessible"
        echo "📊 Current container status:"
        docker-compose ps 2>/dev/null || echo "⚠️  No containers currently running"
    else
        echo "❌ MCP servers directory not found"
    fi
else
    echo "❌ Docker Compose not available"
fi
echo ""

# Test sequential thinking server specifically
echo "🧠 Sequential Thinking Server Test:"
if which mcp-server-mas-sequential-thinking >/dev/null 2>&1; then
    echo "Attempting to start sequential thinking server (5s timeout)..."
    timeout 5s mcp-server-mas-sequential-thinking --help >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Sequential thinking server responds to --help"
    elif [ $? -eq 124 ]; then
        echo "⚠️  Sequential thinking server timeout (may indicate startup issues)"
    else
        echo "❌ Sequential thinking server error"
    fi
else
    echo "❌ Sequential thinking server binary not found"
fi
echo ""

echo "🎯 Health Check Complete!"
echo ""
echo "📋 Quick Fix Commands:"
echo "   Install missing packages: pip install agno exa-py mcp serena"
echo "   Install uvx: pip install uv"
echo "   Set API keys: export OPENAI_API_KEY=your_key_here"
echo "   Start Docker: sudo systemctl start docker (Linux) or start Docker Desktop (Mac)"
echo ""