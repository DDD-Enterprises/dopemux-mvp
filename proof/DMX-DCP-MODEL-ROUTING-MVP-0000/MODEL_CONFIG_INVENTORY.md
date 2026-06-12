# DMX-DCP-MODEL-ROUTING-MVP-0000 — MODEL_CONFIG_INVENTORY.md

## Model/Provider Configuration

### litellm.config.yaml (OBSERVED)

| Model Name | Provider | Model ID | Max Tokens | API Key | API Base | Fallbacks |
|------------|----------|----------|------------|---------|----------|-----------|
| gemini-2.5-flash-lite | gemini | gemini-2.5-flash-lite | 131072 | GEMINI_API_KEY | - | grok-4.1-fast, gpt-5-mini |
| gemini-2.5-flash | gemini | gemini-2.5-flash | 131072 | GEMINI_API_KEY | - | grok-4.1-fast, gpt-5-mini |
| gemini-2.5-pro | gemini | gemini-2.5-pro | 131072 | GEMINI_API_KEY | - | gpt-5.2, grok-4.1-fast-reasoning |
| grok-4.1-fast-reasoning | xai | grok-4-1-fast-reasoning | 131072 | XAI_API_KEY | https://api.x.ai/v1 | gpt-5.2, gemini-2.5-pro |
| grok-4.1-fast | xai | grok-4-1-fast-non-reasoning | 131072 | XAI_API_KEY | https://api.x.ai/v1 | gemini-2.5-flash-lite, gpt-5-mini |
| grok-4-fast-reasoning | xai | grok-4-fast-reasoning | 131072 | XAI_API_KEY | https://api.x.ai/v1 | grok-4.1-fast-reasoning, gpt-5.2 |
| grok-4-fast | xai | grok-4-fast-non-reasoning | 131072 | XAI_API_KEY | https://api.x.ai/v1 | grok-4.1-fast, gemini-2.5-flash-lite |
| grok-code-fast-1 | xai | grok-code-fast-1 | 131072 | XAI_API_KEY | https://api.x.ai/v1 | gpt-5.2-codex, grok-4.1-fast |
| gpt-5.2 | openai | gpt-5.2 | 131072 | OPENAI_API_KEY | - | grok-4.1-fast-reasoning, gemini-2.5-pro |
| gpt-5.2-codex | openai | gpt-5.2-codex | 131072 | OPENAI_API_KEY | - | grok-code-fast-1, gpt-5.2 |
| gpt-5-mini | openai | gpt-5-mini | 131072 | OPENAI_API_KEY | - | gemini-2.5-flash-lite, grok-4.1-fast |
| gpt-5-nano | openai | gpt-5-nano | 32768 | OPENAI_API_KEY | - | gemini-2.5-flash-lite, gpt-5-mini |
| openrouter-gpt-5 | openrouter | openai/gpt-5 | 32768 | OPENROUTER_API_KEY | https://openrouter.ai/api/v1 | - |
| openrouter-gpt-5-codex | openrouter | openai/gpt-5-codex | 32768 | OPENROUTER_API_KEY | https://openrouter.ai/api/v1 | - |

**Alias Map** (selected): grok-4 → gemini-2.5-flash-lite, claude-sonnet → grok-4.1-fast-reasoning, claude-opus → gpt-5.2-codex, codex → grok-code-fast-1, default → gemini-2.5-flash-lite

**Fallbacks**: 14 primary models with 2-3 fallbacks each; default_fallbacks: grok-4.1-fast, gemini-2.5-flash-lite, gpt-5-mini

### model_map_v2_tp008.yaml (OBSERVED)

**Lanes**:
- contract_emitter: openai_direct/gpt-5.3-codex (strict) → fallback gpt-5.2
- bulk_docs: xai/grok-4-1-fast (non-strict) → fallback gpt-5.2
- bulk_code: xai/grok-code-fast-1 (non-strict) → fallback gpt-5.2
- aggregator: openai_direct/gpt-5-mini (strict) → fallback gpt-5.2

**Steps**: 40+ phase/step assignments across D/C/A/B/G/H/Q/R/T/Z with lane + sidefill_enabled + repair_mode

**Evidence**: litellm.config.yaml + model_map_v2_tp008.yaml file reads (OBSERVED)
