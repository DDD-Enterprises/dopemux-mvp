# RTE-PKT-12 Diff Summary

Changed code and test files:

- `services/repo-truth-extractor/llm_runtime.py`: added static route identity classifier and attached labels to request metadata and ladder attempts.
- `services/repo-truth-extractor/run_extraction_v5.py`: propagated route identity through `enrich_request_meta` and captured `returned_model_id` as response metadata.
- `services/repo-truth-extractor/lib/structured_output_contracts.py`: added `provider_schema_variant` labels while preserving existing response-format behavior variants.
- `services/repo-truth-extractor/lib/prescan/provider_catalog.py`: added route-kind/upstream/economic/live-validation labels to static prescan route rows, readiness matrix rows, and routing-plan rows.
- `services/repo-truth-extractor/tests/test_openrouter_xai_route_identity.py`: added local static tests for direct xAI vs OpenRouter x-ai separation, structured-output labeling, returned-model preservation, and no-provider-call safety.

Forbidden surfaces not changed:

- Prompt files: unchanged.
- Promptset YAML/model map: unchanged.
- Provider route selection/model IDs: unchanged.
- Provider client behavior/live dispatch: unchanged.
- Pricing calculations: unchanged.
- Compose/config/deployment files: unchanged.
