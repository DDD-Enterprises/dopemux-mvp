#!/usr/bin/env bash
# Quick fix script for Claude Code → LiteLLM → OpenRouter/XAI routing
set -euo pipefail

echo "🔧 Dopemux Routing Fix Script"
echo "================================"
echo ""

# Check if OpenRouter key is set
if [ "${OPENROUTER_API_KEY:-}" = "your_openrouter_api_key_here" ] || [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "❌ OPENROUTER_API_KEY not set!"
    echo ""
    echo "Please get your key from: https://openrouter.ai/keys"
    echo "Then either:"
    echo "  1. Add to .env file: OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE"
    echo "  2. Or export it: export OPENROUTER_API_KEY='sk-or-v1-YOUR_KEY_HERE'"
    echo ""
    read -p "Enter your OpenRouter API key (or press Ctrl+C to exit): " key
    if [ -n "$key" ]; then
        export OPENROUTER_API_KEY="$key"
        echo "✅ OpenRouter key set for this session"
        echo ""
        echo "To make permanent, add to .env:"
        echo "  echo 'OPENROUTER_API_KEY=$key' >> .env"
        echo ""
    else
        exit 1
    fi
fi

# Verify XAI key is set
if [ -z "${XAI_API_KEY:-}" ]; then
    echo "❌ XAI_API_KEY not set!"
    echo ""
    echo "XAI key is required for direct Grok access."
    echo "Get your key from: https://console.x.ai/"
    echo ""
    read -p "Enter your XAI API key (or press Ctrl+C to exit): " key
    if [ -n "$key" ]; then
        export XAI_API_KEY="$key"
        echo "✅ XAI key set for this session"
        echo ""
        echo "To make permanent, add to .env:"
        echo "  echo 'XAI_API_KEY=$key' >> .env"
        echo ""
    else
        exit 1
    fi
else
    echo "✅ XAI_API_KEY found: ${XAI_API_KEY:0:15}..."
fi

echo "✅ OpenRouter API key found: ${OPENROUTER_API_KEY:0:15}..."
echo ""

# Set up LiteLLM master key
if [ -f ".dopemux/litellm/A/master.key" ]; then
    export LITELLM_MASTER_KEY=$(cat .dopemux/litellm/A/master.key)
    echo "✅ Using LiteLLM master key from .dopemux/litellm/A/master.key"
else
    export LITELLM_MASTER_KEY="HZy6cX-h1t5wPed3XJHRByCK3lde4Pu17zDA5mz-BvM"
    echo "✅ Using default LiteLLM master key"
fi

# Persist master key so Dopemux CLI reuses the same credential
mkdir -p .dopemux/litellm/A
printf "%s" "$LITELLM_MASTER_KEY" > .dopemux/litellm/A/master.key

# Configure LiteLLM database URL (optional but required for metrics)
DB_STORE=".dopemux/litellm/A/database.url"
if [ -z "${DOPEMUX_LITELLM_DB_URL:-}" ]; then
    if [ -f "$DB_STORE" ]; then
        DOPEMUX_LITELLM_DB_URL=$(cat "$DB_STORE")
        export DOPEMUX_LITELLM_DB_URL
        echo "✅ Using LiteLLM database URL from $DB_STORE"
    else
        echo ""
        read -r -p "Enter LiteLLM Postgres URL for metrics (leave blank to skip): " db_input
        if [ -n "$db_input" ]; then
            DOPEMUX_LITELLM_DB_URL="$db_input"
            export DOPEMUX_LITELLM_DB_URL
            printf "%s" "$DOPEMUX_LITELLM_DB_URL" > "$DB_STORE"
            echo "✅ LiteLLM database URL saved to $DB_STORE"
        else
            echo "⚠️  LiteLLM database URL not provided - metrics disabled"
        fi
    fi
else
    printf "%s" "$DOPEMUX_LITELLM_DB_URL" > "$DB_STORE"
    echo "✅ LiteLLM database URL loaded from environment"
fi

if [ -n "${DOPEMUX_LITELLM_DB_URL:-}" ]; then
    export LITELLM_DATABASE_URL="$DOPEMUX_LITELLM_DB_URL"
    export DATABASE_URL="$DOPEMUX_LITELLM_DB_URL"
    db_scheme="${DOPEMUX_LITELLM_DB_URL%%://*}"
    echo "   Using driver: ${db_scheme:-postgresql}"
fi

# Enable routing mode
export DOPEMUX_CLAUDE_VIA_LITELLM=true
export DOPEMUX_DEFAULT_LITELLM=1

echo "✅ Routing environment configured"
echo ""

# Kill existing processes
echo "🔄 Stopping existing processes..."
pkill -f "litellm.*4000" 2>/dev/null || true
pkill -f "ccr" 2>/dev/null || true
sleep 2

# Test LiteLLM config exists
if [ ! -f ".dopemux/litellm/A/litellm.config.yaml" ] && [ ! -f "litellm.config.yaml" ]; then
    echo "❌ No LiteLLM config found!"
    echo "Expected: .dopemux/litellm/A/litellm.config.yaml or litellm.config.yaml"
    exit 1
fi

CONFIG_FILE=".dopemux/litellm/A/litellm.config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="litellm.config.yaml"
fi

echo "✅ Using config: $CONFIG_FILE"
echo ""
echo "📋 Configured models:"
echo "   Direct XAI Access:"
echo "     - grok-4-fast (XAI)"
echo "     - grok-code-fast-1 (XAI)"
echo ""
echo "   Via OpenRouter:"
echo "     - minimax-m2-free (Minimax)"
echo "     - o3-deep-research (OpenAI)"
echo "     - o4-mini-deep-research (OpenAI)"
echo "     - gpt-5-pro (OpenAI)"
echo "     - glm-4.6 (Z-AI)"
echo "     - gpt-5-codex (OpenAI)"
echo "     - gpt-5 (OpenAI)"
echo "     - gpt-5-mini (OpenAI)"
echo "     - o3-pro (OpenAI)"
echo "     - codex-mini (OpenAI)"
echo "     - o3 (OpenAI)"
echo ""

# Create log directory if needed
mkdir -p .dopemux/litellm/A

# Start LiteLLM
echo "🚀 Starting LiteLLM proxy on port 4000..."
nohup litellm --config "$CONFIG_FILE" --port 4000 --host 0.0.0.0 > .dopemux/litellm/A/litellm.log 2>&1 &
LITELLM_PID=$!
echo "✅ LiteLLM started (PID: $LITELLM_PID)"

# Wait for LiteLLM to be ready
echo "⏳ Waiting for LiteLLM to start..."
for i in {1..20}; do
    if curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://localhost:4000/health >/dev/null 2>&1; then
        echo "✅ LiteLLM is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 20 ]; then
        echo "❌ LiteLLM failed to start. Check logs:"
        echo "   tail -f .dopemux/litellm/A/litellm.log"
        exit 1
    fi
done

# Test the connection
echo ""
echo "🧪 Testing LiteLLM connection..."
MODELS_OUTPUT=$(curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://localhost:4000/v1/models)
if echo "$MODELS_OUTPUT" | grep -q "grok-4-fast"; then
    echo "✅ LiteLLM is serving models!"
    MODEL_COUNT=$(echo "$MODELS_OUTPUT" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "   Found $MODEL_COUNT models configured"
else
    echo "⚠️  LiteLLM started but may not be fully configured"
    echo "   Response: $MODELS_OUTPUT"
fi

echo ""
echo "================================"
echo "✅ Routing setup complete!"
echo ""
echo "Environment variables set:"
echo "  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:20}..."
echo "  XAI_API_KEY: ${XAI_API_KEY:0:20}..."
echo "  LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY:0:20}..."
echo "  DOPEMUX_CLAUDE_VIA_LITELLM: $DOPEMUX_CLAUDE_VIA_LITELLM"
echo ""
echo "Next steps:"
echo "  1. Test models: curl -H 'Authorization: Bearer $LITELLM_MASTER_KEY' http://localhost:4000/v1/models | jq '.data[].id'"
echo "  2. Start Claude Code with routing:"
echo "     export ANTHROPIC_BASE_URL='http://localhost:4000'"
echo "     export ANTHROPIC_API_KEY='$LITELLM_MASTER_KEY'"
echo "     dopemux start"
echo "  3. Monitor logs: tail -f .dopemux/litellm/A/litellm.log"
echo ""
echo "Quick test (make a request):"
echo "  curl -X POST http://localhost:4000/v1/chat/completions \\"
echo "    -H 'Authorization: Bearer $LITELLM_MASTER_KEY' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\":\"grok-4-fast\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"max_tokens\":50}'"
echo ""
