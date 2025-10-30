# 🚀 Quick Start: Claude Code with Alternative Providers

## What This Does

Routes Claude Code requests through LiteLLM to use:
- **Direct XAI** (Grok models - no middleman fees)
- **OpenRouter** (access to GPT-5, O3, Minimax, GLM-4.6, etc.)

## Prerequisites

1. **OpenRouter API Key** (get from https://openrouter.ai/keys)
2. **XAI API Key** (already set in your .env)

## 3-Step Setup

### Step 1: Set Your OpenRouter Key

```bash
# Option A: Add to .env file
echo 'OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE' >> .env

# Option B: Export for this session
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
```

### Step 2: Start LiteLLM Proxy

```bash
./scripts/fix_routing.sh
```

This will:
- ✅ Verify your API keys
- ✅ Start LiteLLM on port 4000
- ✅ Configure all 13 models
- ✅ Test the connection

### Step 3: Start Claude Code

```bash
export ANTHROPIC_BASE_URL='http://localhost:4000'
export ANTHROPIC_API_KEY='HZy6cX-h1t5wPed3XJHRByCK3lde4Pu17zDA5mz-BvM'
dopemux start
```

## Verify It's Working

```bash
# Test the routing
./TEST_ROUTING.sh

# Or manually test a model
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer HZy6cX-h1t5wPed3XJHRByCK3lde4Pu17zDA5mz-BvM" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4-fast",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

## Available Models

### Free Tier 💰
- `minimax-m2-free` - Completely free through OpenRouter

### XAI Direct 🚀
- `grok-4-fast` - Fast general purpose
- `grok-code-fast-1` - Code-specialized

### OpenAI Premium 🧠
- `gpt-5-pro` - Premium GPT-5
- `gpt-5` - Standard GPT-5
- `gpt-5-mini` - Faster GPT-5
- `gpt-5-codex` - Code GPT-5
- `o3-deep-research` - Deep reasoning
- `o4-mini-deep-research` - Compact research
- `o3-pro` - Pro reasoning
- `o3` - Standard reasoning
- `codex-mini` - Compact code model

### Other Providers 🌐
- `glm-4.6` - Z-AI's GLM model

## Aliases (Shortcuts)

- `grok` → `grok-4-fast`
- `grok-code` → `grok-code-fast-1`
- `free` → `minimax-m2-free`
- `codex` → `gpt-5-codex`
- `research` → `o3-deep-research`
- `pro` → `gpt-5-pro`
- `fast` → `grok-4-fast`

## Smart Fallbacks

If a model fails, LiteLLM automatically tries alternatives:

```
grok-4-fast fails → gpt-5 → minimax-m2-free
grok-code-fast-1 fails → gpt-5-codex → gpt-5
o3-deep-research fails → o3-pro → o3
```

## Troubleshooting

### "401 Unauthorized"
- Check: `echo $OPENROUTER_API_KEY`
- Should start with: `sk-or-v1-`

### "LiteLLM not responding"
```bash
# Check if running
curl http://localhost:4000/health

# Check logs
tail -f .dopemux/litellm/A/litellm.log

# Restart
pkill -f litellm
./scripts/fix_routing.sh
```

### "Model not found"
```bash
# List available models
curl -H "Authorization: Bearer HZy6cX-h1t5wPed3XJHRByCK3lde4Pu17zDA5mz-BvM" \
  http://localhost:4000/v1/models | jq -r '.data[].id'
```

## Cost Savings 💸

- **XAI Direct**: No OpenRouter markup
- **Free tier**: `minimax-m2-free` costs $0
- **Smart fallbacks**: Automatically use cheaper models if premium ones fail

## Next Steps

Once working:
1. Use Claude Code normally - all requests route through LiteLLM
2. Monitor usage: Check `.dopemux/litellm/A/litellm.log`
3. Switch models: Edit `.dopemux/litellm/A/litellm.config.yaml`

## Full Documentation

See `CLAUDE_CODE_ROUTING_ANALYSIS.md` for complete architecture details.
