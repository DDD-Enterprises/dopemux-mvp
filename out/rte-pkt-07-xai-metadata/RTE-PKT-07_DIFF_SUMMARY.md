# RTE-PKT-07 Diff Summary

Changed files and scope rationale:

| File | Scope rationale |
| --- | --- |
| `services/repo-truth-extractor/llm_runtime.py` | Allowed primary runtime path. Adds metadata propagation for requested route identity, returned/effective response fields, structured-output fields, retry/failure flags, and comparison-lane request metadata. Does not change provider selection, model IDs, prompt text, or live dispatch behavior. |
| `services/repo-truth-extractor/run_extraction_v5.py` | Allowed secondary runtime path. Hardens local response-state summary extraction and request_meta enrichment. Does not change route selection, promptsets, model map, pricing, or compose/deployment files. |
| `services/repo-truth-extractor/tests/test_rte_pkt_07_xai_metadata.py` | Allowed tests path. Adds local fake-response coverage for OpenAI-compatible, direct xAI-style, OpenRouter x-ai proxy, refusal, incomplete, Gemini-style, structured-output, and no-provider-client invocation checks. |
| `out/rte-pkt-07-xai-metadata/` | Allowed packet proof output root. Contains evidence artifacts only. |

Forbidden surfaces not touched:

- `services/repo-truth-extractor/promptsets/`
- `services/repo-truth-extractor/prompts/`
- `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
- `services/repo-truth-extractor/lib/structured_output_contracts.py`
- `config/`
- `docs/`
- `compose.yml`
- `docker-compose.yml`

Known validation note:

- One adjacent live-readiness route test failed during expanded validation. The failure is outside the edited metadata surfaces and concerns benchmark-owned route readiness selection.
