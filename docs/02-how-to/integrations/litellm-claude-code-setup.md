---
id: LITELLM_CLAUDE_CODE_SETUP
title: Litellm_Claude_Code_Setup
type: how-to
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Litellm_Claude_Code_Setup (how-to) for dopemux documentation and developer
  workflows.
---
# LiteLLM + Claude Code Router Setup Guide

**Purpose**: Configure LiteLLM proxy for Claude Code with intelligent routing and fallbacks

## Configuration Overview

### Providers Configured:
1. **xAI Grok** (via OpenRouter) - FREE code generation!
1. **OpenAI GPT-5** (direct) - Logic and reasoning
1. **OpenAI** (via OpenRouter) - Fallback routing
1. **DeepSeek R1** (via OpenRouter) - Thinking mode
1. **Google Gemini 2.5 Pro** - Large context, analysis

### Routing Strategy:
- **Code tasks** → grok-code-fast-1 (FREE!)
- **Logic tasks** → GPT-5 (reasoning)
- **Fast tasks** → Gemini Flash or GPT-5-mini
- **Rate limits** → Automatic fallback to alternate providers

---

## Setup Steps

### 1. Configure API Keys

Create `/Users/hue/code/dopemux-mvp/docker/mcp-servers/litellm/.env`:

```bash
# Master key for LiteLLM proxy access
LITELLM_MASTER_KEY=your-chosen-secret-key

# Provider API keys
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
OPENAI_API_KEY=sk-your-openai-key
GEMINI_API_KEY=your-google-ai-studio-key

# Optional
DEEPSEEK_API_KEY=your-deepseek-key  # If using DeepSeek direct
```

**Get API Keys**:
- OpenRouter: https://openrouter.ai/keys
- OpenAI: https://platform.openai.com/
- Google AI Studio: https://aistudio.google.com/app/apikey
- DeepSeek: https://platform.deepseek.com/api-keys

### 2. Start LiteLLM Proxy

**Option A: Docker** (recommended):
```bash
cd docker/mcp-servers
docker-compose up -d litellm-proxy

# Verify
curl http://localhost:4000/health
```

**Option B: Direct**:
```bash
pip install litellm[proxy]
litellm --config litellm.config.yaml --port 4000
```

### 3. Configure Claude Code

Add to your Claude Code settings (or `~/.claude.json`):

```json
{
  "apiConfiguration": {
    "baseURL": "http://localhost:4000",
    "apiKey": "your-litellm-master-key"
  }
}
```

---

## Model Routing

### Automatic Routing (via aliases):

**For code generation**:
```
User request → Claude Code
  → LiteLLM sees "code" keyword
  → Routes to: grok-code-fast-1
  → If rate limited → Falls back to: gpt-5
```

**For logic/reasoning**:
```
User request → Claude Code
  → LiteLLM sees "logic" or "reasoning"
  → Routes to: gpt-5
  → If rate limited → Falls back to: grok-code-fast-1 → gpt-5-or → gemini-2.5-pro
```

### Manual Model Selection:

In Claude Code, specify model:
```
Use grok-code-fast-1 to implement this feature
Use gpt-5 for complex reasoning
Use gemini-2.5-pro for large context analysis
```

---

## Fallback Behavior

### Rate Limit Cascade:

**Primary**: grok-code-fast-1 (FREE!)
  → **Fallback 1**: gpt-5 (if Grok rate limited)

**Primary**: gpt-5
  → **Fallback 1**: grok-code-fast-1
  → **Fallback 2**: gpt-5-or (via OpenRouter)
  → **Fallback 3**: gemini-2.5-pro

### Cooldown:
- Failed model: 60-second cooldown
- Allowed failures: 3 before cooldown
- Retry on rate limit: 3 times before fallback

---

## Configuration File

**Location**: `litellm.config.yaml`

**Key Sections**:

```yaml
model_list:
  # Define all available models
- model_name: grok-code-fast-1
- model_name: gpt-5
- model_name: gemini-2.5-pro
  # etc.

litellm_settings:
  # Aliases for Claude Code
  model_alias_map:
    code: grok-code-fast-1      # Code tasks
    logic: gpt-5                 # Reasoning tasks
    fast: gemini-flash          # Quick tasks

  # Fallback chains
  fallbacks:
- grok-code-fast-1: [gpt-5]
- gpt-5: [grok-code-fast-1, gpt-5-or, gemini-2.5-pro]

router_settings:
  routing_strategy: usage-based-routing-v2
  retry_policy:
    RateLimitErrorRetries: 3    # Try 3 times before fallback
```

---

## Usage in Claude Code

### Default (auto-routing):
```
"Implement authentication system"
→ Routes to: grok-code-fast-1 (detected as code task)
```

### Explicit model:
```
"Use gpt-5 to analyze this architecture"
→ Routes to: gpt-5 directly
```

### On rate limit:
```
grok-code-fast-1 rate limited
→ Automatically falls back to: gpt-5
→ User sees: Seamless continuation (no error)
```

---

## Testing

### Test LiteLLM is working:
```bash
curl http://localhost:4000/health
# Should return: {"status": "healthy"}
```

### Test model routing:
```bash
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer your-litellm-master-key"
# Should list all configured models
```

### Test with Claude Code:
1. Open Claude Code
1. Type: "Use grok-code-fast-1 to write hello world"
1. Verify it responds (using Grok via LiteLLM)

---

## Troubleshooting

### Claude Code won't boot:
- Check API key is set: `echo $LITELLM_MASTER_KEY`
- Verify LiteLLM running: `curl http://localhost:4000/health`
- Check logs: `docker logs litellm-proxy` or litellm console output

### Rate limit errors:
- Verify fallbacks are configured
- Check retry_policy settings
- Monitor: `curl http://localhost:4000/metrics`

### Wrong model being used:
- Check model_alias_map in config
- Verify model name in request
- Check routing logs

---

## Cost Optimization

### Free Tier:
- **grok-code-fast-1**: FREE on OpenRouter (use for most code!)
- **grok-4-fast**: FREE on OpenRouter

### Paid Tier:
- **GPT-5**: $2.50 / 1M input tokens (use for complex reasoning)
- **Gemini 2.5 Pro**: $1.25 / 1M input (use for large context)
- **DeepSeek R1**: $0.50 / 1M (use for thinking mode)

**Strategy**: Default to FREE Grok for code, use paid GPT-5 only for complex logic

---

## Advanced: Task-Specific Routing

You can enhance Claude Code prompts with routing hints:

**Code generation**:
```
[Use grok-code-fast-1] Implement user authentication with JWT
```

**Complex reasoning**:
```
[Use gpt-5] Analyze this architecture and identify issues
```

**Large context**:
```
[Use gemini-2.5-pro] Review this 500K token codebase
```

---

## Configuration is Ready!

**File**: `litellm.config.yaml` (configured)
**Providers**: 8 models across 4 providers
**Fallbacks**: Intelligent rate limit handling
**Claude Code**: Ready to boot with LiteLLM

**Next**: Start LiteLLM and test with Claude Code!
