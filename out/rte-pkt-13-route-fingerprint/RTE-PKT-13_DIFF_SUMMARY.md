# RTE-PKT-13 Diff Summary

## OBSERVED code changes

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Added static route fingerprint authority constants and required fingerprint input fields.
  - Added deterministic static route fingerprint material/hash helpers.
  - Enriched `RUN_ROUTING_FINGERPRINT.json` phase rows with requested route identity, endpoint/economic authority, transport, provider signature, structured-output mode, provider schema variant, live-validation boundary, static authority, and provider-behavior proof boundary.
  - Enriched representative `effective_model_routing` rows in the run routing fingerprint artifact when a `RunnerConfig` is available.
  - Preserved existing row fields including `provider`, `model_id`, `api_key_env`, `ladder`, `transport`, `endpoint_base_url`, `endpoint_effective`, and `routing_signature`.
- `services/repo-truth-extractor/llm_runtime.py`
  - Aligned `route_identity_authority` with the packet-required static request route metadata authority label.
- `services/repo-truth-extractor/tests/test_route_fingerprint_static_identity.py`
  - Added targeted static tests for direct xAI, OpenRouter x-ai, fingerprint separation, returned-model identity preservation, and no-provider-call artifact generation safety.

## INFERRED compatibility impact

- Existing consumers of older route fingerprint fields should continue to read those fields because no existing `RUN_ROUTING_FINGERPRINT.json` keys were removed.
- Consumers that compare full artifact JSON may observe additive fields in `phases[*]` rows and in `effective_model_routing` rows emitted by `write_run_routing_fingerprint`.

## Non-goals preserved

- No prompt files changed.
- No promptset YAML or model-map route IDs changed.
- No provider dispatch behavior changed.
- No provider client behavior changed.
- No pricing logic changed.
- No live extraction, provider preflight, or batch provider operation was run.
