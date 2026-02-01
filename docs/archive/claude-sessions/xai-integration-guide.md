# xAI (Grok) Integration with Dopemux and Claude Pro Max

## Quick Setup

### 1. Set Your xAI API Key

After obtaining your key from https://x.ai/api, update your `.env` file:

```bash
# Replace 'your_xai_api_key_here' with your actual API key
XAI_API_KEY=xai-abc123...your-actual-key
```

### 2. Load Environment Variables

```bash
# Source the .env file to make the key available
source .env

# Or export directly
export XAI_API_KEY="xai-abc123...your-actual-key"
```

### 3. Verify Configuration

Your LiteLLM config at `litellm.config.yaml` already includes:
- **xai-grok-4**: General purpose Grok model
- **Fallback routing**: Claude → GPT-5 → Grok
- **Rate limiting**: 60 RPM, 1M TPM for xAI

## How It Works

### Multi-Model Architecture

```
Claude Pro Max (Primary)
      ↓ (if unavailable/rate-limited)
  OpenAI GPT-5
      ↓ (fallback)
  xAI Grok-4
```

### Integration Points

1. **Claude Code**: Uses your Claude Pro Max subscription directly
2. **LiteLLM Proxy**: Provides unified access to all models
3. **Dopemux**: Orchestrates model selection based on:
   - Availability
   - Rate limits
   - Task requirements
   - Cost optimization

## Using xAI with Claude Code

### Option 1: Direct Claude Pro Max (Recommended)

Claude Code will use your Pro Max subscription by default. xAI serves as backup:

```bash
# Start normally - Claude Pro Max is primary
dopemux start

# Or with dangerous mode (skip all permission checks)
dopemux start --dangerous
```

### Option 2: With LiteLLM Routing

Enable multi-model fallback routing:

```bash
# Start with LiteLLM proxy for intelligent model routing
dopemux start --litellm

# The system will:
# 1. Use Claude Pro Max for complex reasoning
# 2. Fall back to GPT-5 when rate limited
# 3. Use xAI Grok as final fallback
```

### Option 3: Debug Mode

Monitor which models are being used:

```bash
# Start with debug output to see model routing
dopemux start --litellm --debug
```

## Testing the Integration

### Test xAI Connection

```bash
# Test direct xAI API
curl -X POST https://api.x.ai/v1/chat/completions \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-2",
    "messages": [{"role": "user", "content": "Hello Grok!"}]
  }'
```

### Test LiteLLM Routing

```bash
# Start LiteLLM proxy
litellm --config litellm.config.yaml --port 4100

# Test via proxy (in another terminal)
curl -X POST http://localhost:4100/v1/chat/completions \
  -H "Authorization: Bearer YOUR_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "xai-grok-4",
    "messages": [{"role": "user", "content": "Test message"}]
  }'
```

## Troubleshooting

### Common Issues

1. **"XAI_API_KEY not found"**
   - Ensure you've sourced `.env` or exported the variable
   - Check: `echo $XAI_API_KEY`

2. **Rate limiting errors**
   - xAI has 60 RPM limit (lower than Claude/OpenAI)
   - System automatically falls back to other models

3. **Connection errors**
   - Verify API endpoint: `https://api.x.ai/v1`
   - Check network/firewall settings

### Debug Mode

```bash
# Start with verbose logging
dopemux start --debug --litellm

# Check logs
tail -f .dopemux/litellm/A/litellm.log
```

## Advanced Configuration

### Custom Model Preferences

Edit `litellm.config.yaml` to adjust:

```yaml
# Adjust fallback order
fallbacks:
  - claude-sonnet-4.5:
    - xai-grok-4  # Prefer Grok over GPT-5
    - openai-gpt-5
```

### ADHD-Optimized Settings

xAI Grok works well with ADHD accommodations:

```yaml
# Fast responses for maintaining focus
xai-grok-code-fast-1:
  litellm_params:
    temperature: 0.0  # Consistent, predictable
    max_tokens: 4096  # Quick, focused responses
    stream: true       # Immediate feedback
```

## Benefits of xAI Integration

1. **Cost Optimization**: Grok is often cheaper than GPT-5
2. **Speed**: Grok-code-fast-1 optimized for quick responses
3. **Redundancy**: Multiple model fallbacks prevent interruptions
4. **Specialized Models**: Different models for different tasks

## Next Steps

1. Set your XAI_API_KEY in `.env` (✅ Already done!)
2. Source the environment: `source .env`
3. Test with: `dopemux start --litellm`
4. Monitor usage: `tail -f .dopemux/litellm/A/litellm.log`

---

**Note**: Claude Pro Max remains your primary model. xAI provides additional capacity and specialized capabilities when needed.