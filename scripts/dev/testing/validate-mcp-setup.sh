#!/bin/bash
# MCP Server Configuration Validation Script
# Validates environment variables and MCP server connectivity

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Validating MCP Server Setup..."
echo "📁 Project root: $PROJECT_ROOT"

# Function to check if environment variable is set
check_env_var() {
    local var_name="$1"
    local description="$2"

    if [ -z "${!var_name}" ]; then
        echo "❌ $var_name not set: $description"
        return 1
    else
        echo "✅ $var_name is set"
        return 0
    fi
}

# Function to check if docker container exists and is running
check_container() {
    local container_name="$1"
    local description="$2"

    if docker ps --filter "name=$container_name" --filter "status=running" --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "✅ $container_name container is running: $description"
        return 0
    else
        echo "❌ $container_name container not running: $description"
        return 1
    fi
}

# Function to test MCP server health
test_mcp_server() {
    local name="$1"
    local url="$2"
    local description="$3"

    echo -n "⏳ Testing $name..."

    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo " ✅ $description"
        return 0
    else
        echo " ❌ $description (not responding)"
        return 1
    fi
}

# Check environment variables
echo ""
echo "🔑 Checking required environment variables..."

env_errors=0

# Core AI APIs
check_env_var "OPENAI_API_KEY" "Required for GPT models and most MCP servers" || ((env_errors++))
check_env_var "ANTHROPIC_API_KEY" "Required for Claude models" || ((env_errors++))
check_env_var "GEMINI_API_KEY" "Required for Google Gemini models" || ((env_errors++))
check_env_var "OPENROUTER_API_KEY" "Required for OpenRouter models" || ((env_errors++))

# Research and search APIs
check_env_var "TAVILY_API_KEY" "Required for web search in research" || ((env_errors++))
check_env_var "EXA_API_KEY" "Required for Exa neural search" || ((env_errors++))
check_env_var "PERPLEXITY_API_KEY" "Required for Perplexity research" || ((env_errors++))

# Specialized APIs
check_env_var "VOYAGEAI_API_KEY" "Required for vector embeddings" || ((env_errors++))

# XAI Grok (optional but recommended)
check_env_var "XAI_API_KEY" "Optional: Required for xAI Grok models" || echo "⚠️  XAI_API_KEY not set (xAI Grok will not be available)"

if [ -n "${GOOGLE_API_KEY:-}" ]; then
    echo "⚠️  GOOGLE_API_KEY is set. Canonical Dopemux Gemini key is GEMINI_API_KEY."
fi

# Check Docker containers
echo ""
echo "🐳 Checking Docker containers..."

container_errors=0

# Infrastructure
check_container "dopemux-postgres-age" "PostgreSQL database for knowledge graph" || ((container_errors++))
check_container "dopemux-redis-primary" "Redis cache for MCP servers" || ((container_errors++))
check_container "mcp-qdrant" "Vector database for semantic search" || ((container_errors++))

# Core MCP servers
check_container "mcp-conport" "Knowledge graph and context management" || ((container_errors++))
check_container "mcp-zen" "Multi-model reasoning and orchestration" || ((container_errors++))
check_container "mcp-pal" "Official documentation and API references" || ((container_errors++))
check_container "mcp-serena" "Code navigation and LSP functionality" || ((container_errors++))
check_container "mcp-dope-context" "Semantic code and document search" || ((container_errors++))

# Additional MCP servers
check_container "mcp-exa" "Neural web search" || echo "⚠️  mcp-exa container not running (optional)"
check_container "mcp-gptr-mcp" "Deep research and report generation" || echo "⚠️  mcp-gptr-mcp container not running (optional)"
check_container "mcp-leantime-bridge" "Project management integration" || echo "⚠️  mcp-leantime-bridge container not running (optional)"
check_container "mcp-desktop-commander" "Desktop automation" || echo "⚠️  mcp-desktop-commander container not running (optional)"
check_container "mcp-task-orchestrator" "Task orchestration and dependencies" || echo "⚠️  mcp-task-orchestrator container not running (optional)"
check_container "mcp-clear-thought" "Structured reasoning frameworks" || echo "⚠️  mcp-clear-thought container not running (optional)"

# Test MCP server endpoints
echo ""
echo "🌐 Testing MCP server endpoints..."

endpoint_errors=0

# Core servers with health endpoints
test_mcp_server "ConPort" "http://localhost:3004/health" "Knowledge graph API" || ((endpoint_errors++))
test_mcp_server "PAL apilookup" "http://localhost:3003/health" "Documentation API" || ((endpoint_errors++))
test_mcp_server "Dope Context" "http://localhost:3010/health" "Semantic search API" || ((endpoint_errors++))

# Servers with SSE endpoints (check if port is open)
if nc -z localhost 3003 2>/dev/null; then
    echo "✅ Zen MCP server responding on port 3003"
else
    echo "❌ Zen MCP server not responding on port 3003"
    ((endpoint_errors++))
fi

if nc -z localhost 3006 2>/dev/null; then
    echo "✅ Serena MCP server responding on port 3006"
else
    echo "❌ Serena MCP server not responding on port 3006"
    ((endpoint_errors++))
fi

# Optional servers
if nc -z localhost 3008 2>/dev/null; then
    echo "✅ Exa MCP server responding on port 3008"
else
    echo "⚠️  Exa MCP server not responding on port 3008 (optional)"
fi

if nc -z localhost 3009 2>/dev/null; then
    echo "✅ GPT Researcher MCP server responding on port 3009"
else
    echo "⚠️  GPT Researcher MCP server not responding on port 3009 (optional)"
fi

if nc -z localhost 3015 2>/dev/null; then
    echo "✅ Leantime Bridge MCP server responding on port 3015"
else
    echo "⚠️  Leantime Bridge MCP server not responding on port 3015 (optional)"
fi

# Summary
echo ""
echo "📊 Validation Summary:"
echo "Environment variables: $((8 - env_errors))/8 required set"
echo "Docker containers: $((5 - container_errors))/5 core containers running"
echo "MCP endpoints: $((5 - endpoint_errors))/5 core endpoints responding"

if [ $env_errors -eq 0 ] && [ $container_errors -eq 0 ] && [ $endpoint_errors -eq 0 ]; then
    echo ""
    echo "🎉 All core MCP servers are properly configured and running!"
    echo "💡 You can now start Claude Code with full MCP server support:"
    echo "   claude"
    exit 0
else
    echo ""
    echo "⚠️  Some MCP servers are not properly configured."
    echo "🔧 To fix issues, run:"
    echo "   ./scripts/start-mcp-servers.sh"
    echo "   # or"
    echo "   docker compose -f compose.yml up -d"
    exit 1
fi
