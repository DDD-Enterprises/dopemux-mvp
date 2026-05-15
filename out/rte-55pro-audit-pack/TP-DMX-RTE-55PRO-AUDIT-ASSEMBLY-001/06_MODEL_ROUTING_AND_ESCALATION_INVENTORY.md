# Model Routing And Escalation Inventory

## Runtime Surfaces

- OBSERVED routing constants in `services/repo-truth-extractor/run_extraction_v5.py:497-502`: `ROUTING_POLICY_VERSION`, `DEFAULT_ROUTING_POLICY`, and default Gemini model names.
- OBSERVED route resolution functions in v5: `choose_model_for_step` at line 4750 and `resolve_effective_step_route` at line 4765.
- OBSERVED provider/route readiness and preflight functions in v5 around doctor/preflight surfaces.
- OBSERVED structured-output contract builder in `services/repo-truth-extractor/lib/structured_output_contracts.py:543`.
- OBSERVED live LLM ladder surfaces in both `run_extraction_v5.py:9197` and `services/repo-truth-extractor/llm_runtime.py:716`.
- OBSERVED comparison lane helpers in v5 and `llm_runtime.py`.
- OBSERVED batch-client surfaces in `services/repo-truth-extractor/lib/batch_clients.py` and `lib/batch_retriever.py`.
- OBSERVED prescan routing-plan helper in `services/repo-truth-extractor/lib/prescan/provider_catalog.py`, which references runner authority and provider readiness.

## Provider/Auth/Preflight Surfaces

- OBSERVED config names in `services/repo-truth-extractor/rte_config.py` include routing/model environment variables such as `DPMX_ROUTING_ENABLE`, `DPMX_MODEL_*`, explicit step route variables, benchmark route ownership, webhook variables, and `DPMX_LIVE_OK`.
- OBSERVED doctor and provider-preflight code paths exist; this pack did not execute provider-auth probes because that may require API keys or provider calls.

## Fallback, Escalation, Comparison, Repair

- OBSERVED `RunnerConfig` includes `disable_escalation`, `escalation_max_hops`, batch fields, and comparison fields.
- OBSERVED prior proof #616 says strict passthrough attestation is now based on observed runtime/wire evidence instead of route intent.
- OBSERVED prior proof #615 says strict batch `response_format` is wired into v5 batch request construction.
- INFERRED from code names and prior proof: comparison lanes, fallback ladders, and repair paths are central audit surfaces.
- UNKNOWN: current provider support and reliability for every structured-output mode and model name in 2026 without external research or live validation.

## External Facts Requiring Deep Research

- Current OpenAI structured output and batch behavior for GPT-5.x models.
- Current Anthropic and Gemini structured output/tool-use behavior and schema enforcement guarantees.
- Current OpenRouter passthrough behavior for strict JSON schema and provider-specific request fields.
- Current cost/context/latency tradeoffs for large repository audit prompts.
- Current best practice for multi-model audit routing, fallback, escalation, and provenance-preserving repair.

Do not infer provider behavior from model or provider names alone.
