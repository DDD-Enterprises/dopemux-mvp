# RTE-PKT-07 Remaining UNKNOWNs

## LIVE_VALIDATION_REQUIRED

- Direct xAI live response object shape remains unknown. Local fixtures prove extraction behavior only for expected OpenAI-compatible shapes.
- OpenRouter `x-ai/...` live upstream metadata remains unknown. Static metadata now preserves `requested_provider=openrouter` and `provider_route_kind=openrouter_proxy_xai`, but does not prove OpenRouter live passthrough fields.
- Live Gemini refusal and incomplete-state field names remain unknown beyond local SDK-style candidate and usage metadata fixtures.
- Live OpenAI-compatible aliases may return provider-specific status fields not represented by the local fixtures.

## Static Drift / Residual Risk

- Comparison lane now copies available response metadata from `llm_meta`, but no live comparison lane was executed.
- Batch response metadata remains outside this packet. RTE-PKT-08-XAI-BATCH-STATIC should inspect batch result metadata separately.
- The expanded adjacent test command that included `test_run_extraction_v5_live_readiness.py` failed in route-readiness logic on both implementation and clean base. Classification: `BASELINE_FAILURE`. That route-readiness drift remains unresolved by RTE-PKT-07.

## Recommended Next Packets

- RTE-PKT-08-XAI-BATCH-STATIC: inspect static batch result metadata.
- RTE-PKT-12-OPENROUTER-XAI: verify OpenRouter `x-ai/...` proxy route proof and upstream metadata semantics.
- RTE-PKT-13-ROUTE-FINGERPRINT: harden route fingerprint evidence if broader route proof is required.
- RTE-PKT-09-LIVE-VALIDATION-PLAN: plan live validation without performing it in this packet.
