---
id: QUICK_START_ALT_ROUTING
title: Quick_Start_Alt_Routing
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Quick_Start_Alt_Routing (explanation) for dopemux documentation and developer
  workflows.
---
# 🚀 Quick Start: Automatic Alternative Routing

Use OpenRouter, XAI (Grok), and Minimax instead of expired Anthropic API credits.

## ✅ One-Command Start

```bash
cd /Users/hue/code/dopemux-mvp
git checkout -b feature/your-work  # Don't work on main branch
dopemux start --alt-routing
```

**Or with tmux:**
```bash
dopemux tmux start --alt-routing
```

That's it! Everything happens automatically.

---

## 🎯 What Happens Automatically

1. **Loads your API keys** from `.env.routing`
2. **Kills stuck LiteLLM** instances (if any)
3. **Starts LiteLLM** proxy on port 4000
4. **Waits for health check** (up to 15 seconds)
5. **Configures Claude** to use LiteLLM
6. **Launches dopemux** normally

---

## 📋 Available Models

### Direct XAI (No middleman fees)
- `grok-4-fast` - Fast general purpose
- `grok-code-fast-1` - Code-specialized

### Via OpenRouter
- `minimax-m2-free` - **FREE** tier ($0.00)
- `gpt-5-pro` - Premium GPT-5
- `gpt-5` - Standard GPT-5
- `gpt-5-mini` - Faster GPT-5
- `gpt-5-codex` - Code GPT-5
- `o3-deep-research` - Deep reasoning
- `o4-mini-deep-research` - Compact research
- `o3-pro` - Pro reasoning
- `o3` - Standard reasoning
- `codex-mini` - Compact code model
- `glm-4.6` - Z-AI's GLM

### Smart Fallbacks
```
grok-4-fast → gpt-5 → minimax-m2-free (always ends at FREE)
grok-code-fast-1 → gpt-5-codex → gpt-5
o3-deep-research → o3-pro → o3
```

---

## 🔍 Verify It's Working

After starting, ask Claude:
```
"What model are you using?"
```

Should respond with one of the configured models (not "Claude").

**Check logs:**
```bash
tail -f .dopemux/litellm/A/litellm.log
```

**List available models:**
```bash
source .env.routing
curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://localhost:4000/v1/models | jq '.data[].id'
```

---

## ⚙️ Configuration Files

### `.env.routing`
Your API keys and routing config (already set up):
```bash
OPENROUTER_API_KEY=REDACTED_OPENROUTER_KEY
XAI_API_KEY=REDACTED_XAI_KEY
LITELLM_MASTER_KEY=REDACTED_LITELLM_KEY
```

### `.dopemux/litellm/A/litellm.config.yaml`
Model routing configuration (already set up with your 12 models).

---

## 🛠️ Troubleshooting

### LiteLLM Won't Start
```bash
# Check logs
tail -f .dopemux/litellm/A/litellm.log

# Manually restart
pkill -f litellm
dopemux start --alt-routing
```

### "401 Unauthorized"
LiteLLM master key mismatch. Check `.env.routing`:
```bash
cat .env.routing | grep LITELLM_MASTER_KEY
```

### "Model not found"
Check available models:
```bash
source .env.routing
curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://localhost:4000/v1/models | jq '.data[].id'
```

---

## 💡 Tips

- **First start:** Takes ~5-10 seconds (LiteLLM startup)
- **After that:** Instant (LiteLLM stays running)
- **Restart LiteLLM:** `pkill -f litellm && dopemux start --alt-routing`
- **Use FREE tier:** Set model to `minimax-m2-free` for $0 cost

---

## 📚 More Info

- Full routing docs: `CLAUDE_CODE_ROUTING_ANALYSIS.md`
- Model config: `.dopemux/litellm/A/litellm.config.yaml`
- Architecture: `DOPEMUX_ARCHITECTURE_OVERVIEW.md`

---

**Created:** 2025-10-29
**Your Setup:** Ready to go! ✅
