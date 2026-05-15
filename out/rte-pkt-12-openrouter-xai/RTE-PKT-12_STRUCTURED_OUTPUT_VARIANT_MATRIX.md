# RTE-PKT-12 Structured Output Variant Matrix

Observed static behavior after implementation:

| Route | response_format behavior variant | provider_schema_variant label | Live schema acceptance claim |
| --- | --- | --- | --- |
| Direct xAI | `xai_relaxed` | `xai_relaxed_direct` | `LIVE_VALIDATION_REQUIRED` |
| OpenRouter x-ai | `xai_relaxed` | `openrouter_proxy_xai_relaxed` | `LIVE_VALIDATION_REQUIRED` |
| Direct Gemini | `gemini_relaxed` | `gemini_relaxed_direct` | `LIVE_VALIDATION_REQUIRED` |
| OpenRouter Gemini/Google | `gemini_relaxed` | `openrouter_proxy_gemini_relaxed` | `LIVE_VALIDATION_REQUIRED` |
| Direct OpenAI | `canonical` | `canonical_direct` | `LIVE_VALIDATION_REQUIRED` |
| OpenRouter other/unknown | `canonical` | `openrouter_proxy_canonical` | `LIVE_VALIDATION_REQUIRED` |

The implementation preserves the existing `schema_variant` behavior used to adapt response formats. It adds `provider_schema_variant` as a proof/readability label so OpenRouter x-ai can be distinguished from direct xAI without changing `response_format` construction.
