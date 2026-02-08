#!/usr/bin/env bash
# ONE COMMAND TO START EVERYTHING
# Run this after setting OPENROUTER_API_KEY

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Dopemux Alternative Provider Routing - One-Step Start    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check OpenRouter key
if [ -z "${OPENROUTER_API_KEY:-}" ] || [ "$OPENROUTER_API_KEY" = "your_openrouter_api_key_here" ]; then
    echo "⚠️  OPENROUTER_API_KEY not set!"
    echo ""
    echo "Get your key: https://openrouter.ai/keys"
    echo ""
    echo "Then run ONE of these:"
    echo "  export OPENROUTER_API_KEY='sk-or-v1-YOUR_KEY' && ./scripts/routing/start_here_routing.sh"
    echo "  OR"
    echo "  echo 'OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY' >> .env && source .env && ./scripts/routing/start_here_routing.sh"
    echo ""
    exit 1
fi

echo "✅ API Keys configured"
echo ""

# Start LiteLLM
echo "🚀 Starting LiteLLM proxy..."
./scripts/fix_routing.sh

# Give instructions
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ READY TO GO!                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Now run Claude Code with:"
echo ""
echo "  export ANTHROPIC_BASE_URL='http://localhost:4000'"
echo "  export ANTHROPIC_API_KEY='HZy6cX-h1t5wPed3XJHRByCK3lde4Pu17zDA5mz-BvM'"
echo "  dopemux start"
echo ""
echo "Or test it first:"
echo "  ./TEST_ROUTING.sh"
echo ""
echo "Available models:"
echo "  • grok-4-fast (XAI Direct)"
echo "  • grok-code-fast-1 (XAI Direct)"
echo "  • minimax-m2-free (FREE!)"
echo "  • gpt-5-pro, gpt-5, gpt-5-mini"
echo "  • o3-deep-research, o3-pro, o3"
echo "  • gpt-5-codex, codex-mini"
echo "  • glm-4.6"
echo ""
echo "Logs: tail -f .dopemux/litellm/A/litellm.log"
echo ""
