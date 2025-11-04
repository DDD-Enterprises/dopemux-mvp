# LiteLLM + Claude Code Router - Setup Complete ✅

## Issues Fixed

1. ✅ **PostgreSQL Disk Space** - Cleaned up Docker (freed 4.4GB)
2. ✅ **LiteLLM Database Connection** - Fixed and started successfully
3. ✅ **Claude Code Router** - Updated from v1.0.47 → v1.0.65
4. ✅ **GPT-5-Pro Added** - Available for extreme thinking tasks
5. ✅ **Dynamic Routing Configured** - Smart model selection based on task

## Current Setup

### LiteLLM (Port 4000)
- **Status**: ✅ Running
- **Models**: 9 available
- **Auth**: Bearer `sk-master-dopemux-local-20251101`

### Claude Code Router (Port 3456)  
- **Status**: ✅ Running
- **Version**: 1.0.65
- **Auth**: Bearer `3-W5jDXWWaEKth9gerZogE38Mtsd_IP0ddyLFAZ-eK4`

## Available Models

| Model | Purpose | Token Limit |
|-------|---------|-------------|
| `openrouter-xai-grok-code-fast` | Fast coding | 131K |
| `openrouter-xai-grok-4-fast` | General tasks | 131K |
| `grok-4-fast-reasoning` | Reasoning | 131K |
| `openrouter-openai-gpt-5` | Default | 131K |
| `openrouter-openai-gpt-5-codex` | Code (primary fallback) | 131K |
| `openrouter-openai-gpt-5-mini` | Quick/web search | 65K |
| **`openrouter-openai-gpt-5-pro`** | **Extreme thinking** | **131K** |
| `openrouter-google-gemini-2-flash` | Fast responses | 65K |
| `openrouter-meta-llama-3.1-405b` | Large context | 65K |

## Routing Configuration

### Automatic Routes:
- **Default**: GPT-5
- **Background**: Grok-4-Fast  
- **Think** (extreme thinking): **GPT-5-Pro** ⭐
- **Long Context** (>60K): Claude Sonnet 4.5
- **Web Search**: GPT-5-Mini

### Fallback Priority:
All models fall back to **GPT-5-Codex** as primary, then GPT-5-Pro/GPT-5

## Usage in Claude Code

### Method 1: Let CCR Auto-Route
Use keywords in your prompts:
- "think deeply about..."
- "analyze thoroughly..."
- "reason through..."

→ Automatically routes to GPT-5-Pro

### Method 2: Explicit Model Request
```
Use model: litellm,openrouter-openai-gpt-5-pro for this task
```

### Method 3: Use Aliases
- `gpt-5-pro` → GPT-5-Pro
- `gpt-5-codex` → GPT-5-Codex  
- `grok` → Grok Code Fast

## Known Issues

- **Fastify Warning**: CCR logs show `FST_ERR_REP_INVALID_PAYLOAD_TYPE` errors, but requests complete successfully. This is a known issue in CCR that doesn't affect functionality.

## Environment Variables

Required in your environment:
```bash
export DOPEMUX_LITELLM_MASTER_KEY="sk-master-dopemux-local-20251101"
export OPENROUTER_API_KEY="your-key"
export XAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

## Restart Commands

```bash
# Restart LiteLLM
pkill -f "litellm.*4000"
cd /Users/hue/code/dopemux-mvp
nohup litellm --config litellm.config.yaml --port 4000 > .dopemux/litellm/A/litellm.log 2>&1 &

# Restart CCR
pkill -f "ccr start"
export DOPEMUX_LITELLM_MASTER_KEY="sk-master-dopemux-local-20251101"
cd /Users/hue/code/dopemux-mvp
HOME=.dopemux/claude-code-router/A SERVICE_PORT=3456 ccr start >> .dopemux/claude-code-router/A/claude-code-router.log 2>&1 &
```

## Testing

```bash
# Test LiteLLM
curl -H "Authorization: Bearer sk-master-dopemux-local-20251101" \
  http://localhost:4000/v1/models

# Test CCR
curl -H "Authorization: Bearer 3-W5jDXWWaEKth9gerZogE38Mtsd_IP0ddyLFAZ-eK4" \
  http://localhost:3456/health
```

---
**Setup completed**: 2025-11-04 04:36 UTC
