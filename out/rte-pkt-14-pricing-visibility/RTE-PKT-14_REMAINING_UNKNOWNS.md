# RTE-PKT-14 Remaining Unknowns

## UNKNOWN

- OpenRouter x-ai live upstream metadata remains UNKNOWN.
- OpenRouter x-ai returned-model behavior remains UNKNOWN unless live evidence exists.
- OpenRouter x-ai schema acceptance remains LIVE_VALIDATION_REQUIRED.
- OpenRouter x-ai retention, ZDR, billing, and rate-limit equivalence remain UNKNOWN.
- Direct xAI live safety remains LIVE_VALIDATION_REQUIRED.
- OpenRouter x-ai direct-provider billing inheritance remains false in static metadata unless provider billing artifacts prove otherwise.
- Missing provider billing artifacts remain UNKNOWN.

## OBSERVED

- `services/repo-truth-extractor/lib/proof_contract.py` exists in this checkout.
- `services/repo-truth-extractor/lib/risk_dashboard.py` exists in this checkout.
- Static pricing metadata uses `pricing_surface=openrouter` for OpenRouter x-ai and `pricing_surface=xai_direct` for direct xAI.

## Not Claimed

- No live provider billing, retention, ZDR, rate-limit, schema, or returned-model guarantee is claimed from an OpenRouter `x-ai/...` prefix.
