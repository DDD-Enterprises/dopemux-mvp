# RTE-PKT-13 Route Fingerprint Matrix

| Route | requested_provider | requested_model_id | provider_route_kind | upstream_provider | economic_surface | api_key_env | endpoint/economic authority | structured_output_mode | provider_schema_variant | live_validation_status | direct_provider_guarantees_inherited | live_provider_behavior_proven |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Direct xAI | `xai` | `grok-fixture` | `direct_provider` | `xai` | `xai_direct` | `XAI_API_KEY` | direct xAI endpoint/key/economic surface | `json_schema` | `xai_relaxed_direct` | `LIVE_VALIDATION_REQUIRED` | `null` | `false` |
| OpenRouter x-ai | `openrouter` | `x-ai/grok-fixture` | `openrouter_proxy_xai` | `xai` | `openrouter` | `OPENROUTER_API_KEY` | OpenRouter endpoint/key/economic surface | `json_schema` | `openrouter_proxy_xai_relaxed` | `LIVE_VALIDATION_REQUIRED` | `false` | `false` |
| OpenRouter OpenAI | `openrouter` | `openai/gpt-fixture` | `openrouter_proxy_other` | `openai` | `openrouter` | `OPENROUTER_API_KEY` | OpenRouter endpoint/key/economic surface | `json_schema` | `openrouter_proxy_canonical` | `LIVE_VALIDATION_REQUIRED` | `false` | `false` |
| OpenRouter unknown/native | `openrouter` | `native-fixture` | `openrouter_native_or_unknown` | `unknown` | `openrouter` | `OPENROUTER_API_KEY` | OpenRouter endpoint/key/economic surface | `json_schema` | `openrouter_proxy_canonical` | `LIVE_VALIDATION_REQUIRED` | `false` | `false` |
| Direct OpenAI | `openai` | `gpt-fixture` | `direct_provider` | `openai` | `openai_direct` | `OPENAI_API_KEY` | direct OpenAI endpoint/key/economic surface | `json_schema` | `canonical_direct` | `LIVE_VALIDATION_REQUIRED` | `null` | `false` |
| Direct Gemini | `gemini` | `gemini-fixture` | `direct_provider` | `gemini` | `gemini_direct` | `GEMINI_API_KEY` | direct Gemini endpoint/key/economic surface | `json_schema` | `gemini_relaxed_direct` | `LIVE_VALIDATION_REQUIRED` | `null` | `false` |
| Unknown provider | `unknown` | `unknown-fixture` | `unknown` | `unknown` | `unknown` | `UNKNOWN` | UNKNOWN | `none` | `unknown` | `UNKNOWN` | `null` | `false` |

## OBSERVED fingerprint inputs

The deterministic route fingerprint material is limited to:

`requested_provider`, `requested_model_id`, `provider_route_kind`, `upstream_provider`, `economic_surface`, `api_key_env`, `endpoint_effective`, `transport`, `provider_signature`, `structured_output_mode`, `provider_schema_variant`, `live_validation_status`.

`returned_model_id` is response metadata only and is intentionally excluded from the static fingerprint material.
