# RTE-PKT-12 Route Identity Matrix

Status: OBSERVED static helper behavior after local implementation. No provider calls were made.

| Route | requested_provider | requested_model_id | provider_route_kind | upstream_provider | economic_surface | api_key_env | endpoint/economic authority | live_validation_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Direct xAI | `xai` | `grok-fixture` | `direct_provider` | `xai` | `xai_direct` | `XAI_API_KEY` | direct xAI endpoint/key surface | `LIVE_VALIDATION_REQUIRED` |
| OpenRouter x-ai | `openrouter` | `x-ai/grok-fixture` | `openrouter_proxy_xai` | `xai` | `openrouter` | `OPENROUTER_API_KEY` | OpenRouter endpoint/key/economic surface | `LIVE_VALIDATION_REQUIRED` |
| OpenRouter OpenAI | `openrouter` | `openai/gpt-fixture` | `openrouter_proxy_other` | `openai` | `openrouter` | `OPENROUTER_API_KEY` | OpenRouter endpoint/key/economic surface | `LIVE_VALIDATION_REQUIRED` |
| OpenRouter unknown/native | `openrouter` | `fixture-model` | `openrouter_native_or_unknown` | `unknown` | `openrouter` | `OPENROUTER_API_KEY` | OpenRouter endpoint/key/economic surface | `LIVE_VALIDATION_REQUIRED` |
| Direct OpenAI | `openai` | `gpt-fixture` | `direct_provider` | `openai` | `openai_direct` | `OPENAI_API_KEY` | direct OpenAI endpoint/key surface | `LIVE_VALIDATION_REQUIRED` |
| Direct Gemini | `gemini` | `gemini-fixture` | `direct_provider` | `gemini` | `gemini_direct` | `GEMINI_API_KEY` | direct Gemini endpoint/key surface | `LIVE_VALIDATION_REQUIRED` |
| Unknown | `unknown` | `fixture-model` | `unknown` | `unknown` | `unknown` | `UNKNOWN` | no static provider authority | `UNKNOWN` |

Important boundary: `upstream_provider=xai` on OpenRouter x-ai is a static route-name classification only. It is not evidence that live OpenRouter passthrough, returned model metadata, provider guarantees, retention, ZDR, rate limits, or billing match direct xAI.
