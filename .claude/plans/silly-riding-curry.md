# Fix LiteLLM OpenRouter Configuration Issue

## Context
The current LiteLLM configuration routes OpenAI models through OpenRouter, which is causing a `functools.partial()` keyword argument collision error due to `extra_headers` configuration. This prevents Claude Code from working properly with the responses API. The user wants to switch to direct OpenAI routing while maintaining responses API support.

## Problem Analysis
- **Root Cause**: `extra_headers` in OpenRouter model configuration causes parameter collision in LiteLLM's internal `functools.partial()` usage
- **Impact**: Claude Code cannot initialize properly, blocking development workflow
- **Current State**: OpenRouter models (gpt-5, o3, deepseek-r1, etc.) configured with problematic headers
- **Goal**: Direct OpenAI routing that supports responses API for Claude Code router

## Implementation Approach

### Phase 1: Remove Problematic OpenRouter Configurations
**Remove all OpenRouter models** from `litellm.config.yaml` that include `extra_headers`:
- gpt-5 (openrouter/openai/gpt-5)
- gpt-5-mini (openrouter/openai/gpt-5-mini)
- o3 (openrouter/openai/o3)
- o3-mini (openrouter/openai/o3-mini)
- deepseek-r1 (openrouter/deepseek/deepseek-r1)
- grok models (openrouter/xai/grok-*)
- All Claude models (openrouter/anthropic/*)

**Keep**: Models that don't use OpenRouter or don't have header issues (if any).

### Phase 2: Add Direct OpenAI Configurations
**Add direct OpenAI model configurations** to support responses API:

```yaml
- model_name: o3
  litellm_params:
    model: o3
    api_key: os.environ/OPENAI_API_KEY
    api_base: https://api.openai.com/v1
    max_tokens: 100000

- model_name: gpt-5
  litellm_params:
    model: gpt-5
    api_key: os.environ/OPENAI_API_KEY
    api_base: https://api.openai.com/v1
    max_tokens: 32768

- model_name: gpt-5-mini
  litellm_params:
    model: gpt-5-mini
    api_key: os.environ/OPENAI_API_KEY
    api_base: https://api.openai.com/v1
    max_tokens: 32768
```

### Phase 3: Update Fallback Configurations
**Update model_alias_map and fallbacks** to use direct OpenAI models:
- Remove OpenRouter references
- Point aliases to direct OpenAI model names
- Ensure o3 models are properly aliased for Claude Code compatibility

### Phase 4: Verify Claude Code Integration
**Ensure Claude Code router works** with direct OpenAI:
- Verify responses API support for o3 models
- Confirm environment variable setup (OPENAI_API_KEY, OPENAI_API_BASE)
- Test Claude Code initialization without LiteLLM proxy dependency

## Critical Files to Modify

### Primary Configuration
- `litellm.config.yaml` - Remove OpenRouter models, add direct OpenAI models

### Verification Files
- Check `src/dopemux/litellm_proxy.py` for any hardcoded OpenRouter assumptions
- Verify `docker/mcp-servers/litellm/litellm.config.yaml` if it needs similar updates

## Testing Strategy

### Pre-Implementation Tests
1. **Backup current configuration** - Save working copy of litellm.config.yaml
2. **Test current failure** - Confirm the functools.partial error occurs

### Post-Implementation Tests
1. **LiteLLM proxy restart** - Verify new configuration loads without errors
2. **Claude Code integration** - Test that Claude Code can initialize with responses API
3. **Model availability** - Confirm o3, gpt-5, gpt-5-mini are accessible
4. **Fallback behavior** - Test that model aliases work correctly

### Rollback Plan
- Restore original `litellm.config.yaml` from backup if issues occur
- Keep OpenRouter configuration as fallback option

## Risk Assessment

### Low Risk
- Direct OpenAI routing is simpler than OpenRouter proxying
- Removes problematic `extra_headers` configuration entirely
- Claude Code responses API works natively with OpenAI

### Medium Risk
- Cost implications (no OpenRouter markup, but direct OpenAI pricing)
- Rate limits change to OpenAI tier limits instead of pooled limits
- Some OpenRouter-exclusive models may become unavailable

### Mitigation
- Keep OpenRouter configuration documented for easy rollback
- Test thoroughly before committing to direct routing
- Monitor Claude Code initialization and responses API functionality

## Success Criteria

✅ **LiteLLM proxy starts without functools.partial errors**
✅ **Claude Code initializes successfully with responses API**
✅ **o3, gpt-5, gpt-5-mini models are accessible**
✅ **Model aliases work correctly for backward compatibility**
✅ **No regression in existing functionality**