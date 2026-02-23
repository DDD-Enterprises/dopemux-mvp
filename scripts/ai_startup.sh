#!/bin/bash
# Comprehensive AI Environment Startup Script
# Setup for Google Jules, Copilot, Codex, and Claude Code Cloud

set -e

echo "🚀 AI Environment Startup"
echo "========================================"
echo "Initializing environment for:"
echo "  • Google Jules (Agent Context)"
echo "  • GitHub Copilot / Grok"
echo "  • OpenAI Codex"
echo "  • Claude Code Cloud"
echo "========================================"
echo

# 1. Check Prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi

# Check for docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose is not found."
    exit 1
fi
echo "✅ Docker & Python found."

# 2. Check Environment Variables
echo "🔍 Checking environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "⚠️  .env file not found. Copying from .env.example..."
        cp .env.example .env
        echo "✅ Created .env"
    else
        echo "❌ .env file not found and .env.example missing."
        exit 1
    fi
fi

# Check for keys (non-blocking warning if missing, as user might set them later)
check_key() {
    if ! grep -q "^$1=" .env && [ -z "${!1}" ]; then
        echo "⚠️  Warning: $1 is not set in .env or environment."
    else
        echo "✅ $1 detected."
    fi
}

check_key "ANTHROPIC_API_KEY"
check_key "OPENAI_API_KEY"
check_key "OPENROUTER_API_KEY"
check_key "GEMINI_API_KEY"
check_key "XAI_API_KEY"

if grep -q "^GOOGLE_API_KEY=" .env || [ -n "${GOOGLE_API_KEY:-}" ]; then
    echo "⚠️  GOOGLE_API_KEY detected. Canonical Dopemux key is GEMINI_API_KEY in repo-root .env."
    echo "   Keep one source of truth: set GEMINI_API_KEY and remove GOOGLE_API_KEY."
fi

# 3. Check Dopemux Installation
if ! command -v dopemux &> /dev/null; then
    echo "⚠️  'dopemux' command not found."
    echo "   Installing in editable mode..."
    pip install -e .
    if ! command -v dopemux &> /dev/null; then
        echo "❌ Failed to install dopemux."
        exit 1
    fi
    echo "✅ Dopemux installed."
fi

# 4. Start MCP Servers
echo
echo "🔌 Starting MCP Servers (Copilot/Tools Integration)..."
if [ -f "./start-mcp-servers.sh" ]; then
    ./start-mcp-servers.sh
elif [ -f "./scripts/start-mcp-servers.sh" ]; then
    ./scripts/start-mcp-servers.sh
else
    echo "❌ start-mcp-servers.sh not found in . or ./scripts/"
    exit 1
fi

# 5. Start Main Environment with Routing
echo
echo "🚀 Starting Dopemux with AI Routing..."
echo "   (This enables LiteLLM proxy for Codex/Grok/Claude)"

# We run this in the background or just exec it?
# The user likely wants to enter the environment.
# dopemux start is interactive (TUI).

echo
echo "✅ Setup Complete!"
echo "   To enter the ADHD-optimized environment:"
echo
echo "   $ dopemux start --alt-routing"
echo
echo "   This will launch:"
echo "   - Claude Code (via LiteLLM proxy)"
echo "   - Copilot integrations (via MCP)"
echo "   - Codex access (via 'dopemux code' or chat)"
echo "   - Jules context (via active session)"
echo
echo "   Or run specific modes:"
echo "   $ dopemux start --grok    (Force Grok)"
echo "   $ dopemux start --codex   (Force Codex)"
echo "   $ dopemux start --altp    (Tier-matched routing)"
echo
