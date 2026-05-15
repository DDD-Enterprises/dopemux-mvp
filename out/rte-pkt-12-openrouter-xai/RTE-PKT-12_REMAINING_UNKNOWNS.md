# RTE-PKT-12 Remaining Unknowns

Static route identity improved, but the following remain unresolved:

- OpenRouter x-ai live upstream metadata is UNKNOWN.
- OpenRouter x-ai returned model behavior is UNKNOWN without live validation.
- OpenRouter x-ai schema acceptance is LIVE_VALIDATION_REQUIRED.
- OpenRouter x-ai retention, ZDR, billing, rate-limit, and direct xAI guarantee equivalence are UNKNOWN.
- Direct xAI live safety remains LIVE_VALIDATION_REQUIRED.
- RTE-PKT-10 `proof_contract.py` helper is absent from this checkout, so proof-contract consumption could not be implemented or tested here.
- RTE-PKT-11 `risk_dashboard.py` helper is absent from this checkout, so dashboard consumption could not be implemented or tested here.
- The active packet JSON supplied in the user request does not conform to the checked-in `dopetask-canonical-spec.json`; this was treated as a governance conflict, not as runtime evidence.

Downstream recommendation:

- RTE-PKT-13 route fingerprint work can consume `requested_provider`, `requested_model_id`, `provider_route_kind`, `upstream_provider`, `economic_surface`, `api_key_env`, `endpoint_effective`, `transport`, and `provider_signature`.
- RTE-PKT-14 pricing visibility should continue treating OpenRouter x-ai economic surface as `openrouter` unless provider billing artifacts prove otherwise.
