# API Configuration Guide - dope-context

## Required API Keys

The dope-context service requires two API keys for full functionality:

### 1. Anthropic API Key
**Purpose**: Context generation using Claude Haiku  
**Cost**: $0.25/M input tokens, $1.25/M output tokens  
**Get Key**: https://console.anthropic.com/settings/keys  
**Add Credits**: https://console.anthropic.com/settings/billing  

**Configuration**:
```bash
# In /Users/hue/code/dopemux-mvp/.env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 2. Voyage AI API Key
**Purpose**: Code embeddings (voyage-code-3) and reranking  
**Get Key**: https://dash.voyageai.com/api-keys  

**Configuration**:
```bash
# In /Users/hue/code/dopemux-mvp/.env
VOYAGE_API_KEY=pa-xxxxx
VOYAGEAI_API_KEY=pa-xxxxx  # Both vars for compatibility
```

## Current Status

✅ API keys configured in `.env`  
⚠️  Anthropic account needs credits added  
✅ Voyage key ready  

## Testing Without Credits

To test infrastructure without API costs:
```python
# Disable context generation in config
skip_context_generation: true

# Or use mock embeddings for testing
```

## Performance Validated

- **Search**: 8.2ms average (61x faster than 500ms target)
- **Throughput**: 254 points/sec insertion
- **Qdrant**: Persistent storage configured
- **Tests**: 92/94 passing
