# RTE-PKT-13 Remaining Unknowns

## UNKNOWN / LIVE_VALIDATION_REQUIRED

- OpenRouter x-ai live upstream metadata remains UNKNOWN.
- OpenRouter x-ai returned model behavior remains UNKNOWN unless future live evidence exists.
- OpenRouter x-ai schema acceptance remains LIVE_VALIDATION_REQUIRED.
- OpenRouter x-ai retention, ZDR, billing, and rate-limit equivalence remain UNKNOWN.
- Direct xAI live safety remains LIVE_VALIDATION_REQUIRED.

## MISSING / UNKNOWN surfaces

- `proof_contract.py` was not found under `services/repo-truth-extractor`; this surface remains MISSING/UNKNOWN for this packet.
- `risk_dashboard.py` was not found under `services/repo-truth-extractor`; this surface remains MISSING/UNKNOWN for this packet.

## Residual risk

- Additive `RUN_ROUTING_FINGERPRINT.json` fields may affect consumers that compare full JSON objects instead of selecting known keys.
- This static proof does not validate live provider schema acceptance, returned-model metadata, billing authority, or retention behavior.
