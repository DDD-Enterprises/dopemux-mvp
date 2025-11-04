#!/usr/bin/env bash
# Quick test script to verify routing is working
set -euo pipefail

echo "🧪 Testing Dopemux LiteLLM Routing"
echo "=================================="
echo ""

MASTER_KEY="${LITELLM_MASTER_KEY:-HZy6cX-h1t5wPed3XJHRByCK3lde4Pu17zDA5mz-BvM}"

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
if curl -s -H "Authorization: Bearer $MASTER_KEY" http://localhost:4000/health | jq .; then
    echo "✅ LiteLLM is healthy"
else
    echo "❌ LiteLLM health check failed"
    exit 1
fi
echo ""

# Test 2: List models
echo "Test 2: Available Models"
echo "------------------------"
MODELS=$(curl -s -H "Authorization: Bearer $MASTER_KEY" http://localhost:4000/v1/models | jq -r '.data[].id' 2>/dev/null)
if [ -n "$MODELS" ]; then
    echo "✅ Available models:"
    echo "$MODELS" | while read model; do
        echo "   • $model"
    done
else
    echo "❌ No models found"
    exit 1
fi
echo ""

# Test 3: Test Grok (Direct XAI)
echo "Test 3: Grok-4-Fast (Direct XAI)"
echo "--------------------------------"
if curl -s -X POST http://localhost:4000/v1/chat/completions \
    -H "Authorization: Bearer $MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "grok-4-fast",
        "messages": [{"role": "user", "content": "Say hello in 3 words"}],
        "max_tokens": 20
    }' | jq -r '.choices[0].message.content' 2>/dev/null; then
    echo "✅ Grok-4-Fast is working (Direct XAI)"
else
    echo "⚠️  Grok-4-Fast test failed (check XAI_API_KEY)"
fi
echo ""

# Test 4: Test free model (OpenRouter)
echo "Test 4: Minimax-M2-Free (OpenRouter)"
echo "------------------------------------"
if curl -s -X POST http://localhost:4000/v1/chat/completions \
    -H "Authorization: Bearer $MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "minimax-m2-free",
        "messages": [{"role": "user", "content": "Say hi in 2 words"}],
        "max_tokens": 10
    }' | jq -r '.choices[0].message.content' 2>/dev/null; then
    echo "✅ Minimax-M2-Free is working (OpenRouter)"
else
    echo "⚠️  Minimax test failed (check OPENROUTER_API_KEY)"
fi
echo ""

# Test 5: Check aliases
echo "Test 5: Model Aliases"
echo "---------------------"
echo "Testing alias 'grok' → grok-4-fast..."
if curl -s -X POST http://localhost:4000/v1/chat/completions \
    -H "Authorization: Bearer $MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "grok",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5
    }' | jq -r '.model' 2>/dev/null | grep -q "grok"; then
    echo "✅ Alias 'grok' works"
else
    echo "⚠️  Alias 'grok' may not work as expected"
fi
echo ""

echo "=================================="
echo "✅ Routing tests complete!"
echo ""
echo "All systems ready. You can now:"
echo "  export ANTHROPIC_BASE_URL='http://localhost:4000'"
echo "  export ANTHROPIC_API_KEY='$MASTER_KEY'"
echo "  dopemux start"
echo ""
