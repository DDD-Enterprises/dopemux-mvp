# RTE-PKT-14 Pricing Surface Matrix

| Case | provider_route_kind | upstream_provider | economic_surface | pricing_surface | api_key_env | billing authority | live validation status | direct provider billing inherited |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Direct xAI | direct_provider | xai | xai_direct | xai_direct | XAI_API_KEY | direct_provider_catalog_or_unknown | LIVE_VALIDATION_REQUIRED | null |
| OpenRouter x-ai | openrouter_proxy_xai | xai | openrouter | openrouter | OPENROUTER_API_KEY | openrouter_catalog_or_unknown | LIVE_VALIDATION_REQUIRED | false |
| OpenRouter OpenAI | openrouter_proxy_other | openai | openrouter | openrouter | OPENROUTER_API_KEY | openrouter_catalog_or_unknown | LIVE_VALIDATION_REQUIRED | false |
| OpenRouter unknown/native | openrouter_native_or_unknown | unknown | openrouter | openrouter | OPENROUTER_API_KEY | openrouter_catalog_or_unknown | LIVE_VALIDATION_REQUIRED | false |
| Direct OpenAI | direct_provider | openai | openai_direct | openai_direct | OPENAI_API_KEY | direct_provider_catalog_or_unknown | LIVE_VALIDATION_REQUIRED | null |
| Direct Gemini | direct_provider | gemini | gemini_direct | gemini_direct | GEMINI_API_KEY | direct_provider_catalog_or_unknown | LIVE_VALIDATION_REQUIRED | null |
| Unknown provider | unknown | unknown | unknown | unknown | null | unknown | UNKNOWN | null |

## Authority Notes

- OpenRouter x-ai uses `pricing_surface=openrouter` even when `upstream_provider=xai`.
- Direct provider billing is not inherited through OpenRouter proxy routes.
- No row claims live provider billing equivalence.
