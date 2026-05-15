# RTE-PKT-12 Risk And Authority Labels

Authority observed in this checkout:

- `services/repo-truth-extractor/llm_runtime.py` now emits static route labels in request metadata.
- `services/repo-truth-extractor/run_extraction_v5.py` now normalizes the same labels through `enrich_request_meta`.
- `services/repo-truth-extractor/lib/structured_output_contracts.py` now emits a provider-specific schema label separate from behavior.
- `services/repo-truth-extractor/lib/prescan/provider_catalog.py` now emits route-kind, upstream, economic-surface, and live-validation-required labels in prescan route rows.

Absent surfaces:

- `services/repo-truth-extractor/lib/proof_contract.py` is not present in this checkout.
- `services/repo-truth-extractor/lib/risk_dashboard.py` is not present in this checkout.
- The matching selectors for `proof_contract or artifact_authority` and `risk and dashboard` selected no tests and exited with pytest code 5.

OpenRouter x-ai authority boundary:

- Static provider route identity: `openrouter_proxy_xai`.
- Upstream provider label: `xai`, derived from the `x-ai/` model prefix only.
- Economic surface: `openrouter`.
- API key env: `OPENROUTER_API_KEY`.
- Direct xAI guarantees inherited: `false`.
- Live validation status: `LIVE_VALIDATION_REQUIRED`.

This packet does not claim OpenRouter x-ai has direct xAI retention, ZDR, billing, rate-limit, schema-acceptance, or returned-model behavior.
