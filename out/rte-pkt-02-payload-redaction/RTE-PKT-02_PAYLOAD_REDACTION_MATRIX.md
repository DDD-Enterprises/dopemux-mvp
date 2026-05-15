# RTE-PKT-02 Payload Redaction Matrix

Status: READY_FOR_REVIEW

| Surface | Observed boundary | Change | Test coverage | Remaining status |
| --- | --- | --- | --- | --- |
| Shared provider sanitizer | `output_safety.py:111` | Added `sanitize_text_for_provider_payload` and `sanitize_payload_for_provider`; preserves hashes and safe metadata while redacting assignment/header/query/private-key/common-token/high-entropy token shapes. | `test_provider_payload_sanitizer_redacts_secret_shapes_but_preserves_context` | CLOSED for covered patterns |
| Grok file preview | `grok_passes.py:200` | `_get_file_preview` sanitizes decoded/truncated text before returning it to any provider-bound payload path. | `test_grok_file_preview_redacts_secret_shaped_file_content` | CLOSED |
| Grok pass payloads | `grok_passes.py:384`, `grok_passes.py:422` | `_execute_pass` now builds provider payloads through `_build_provider_payload`, which recursively sanitizes payload data before cache keying, JSON serialization, token estimation, and `_call_grok_validated`. | `test_grok_pass_payload_builders_sanitize_nested_content_without_provider_call`; `test_grok_execute_pass_sends_only_sanitized_payload_to_provider_boundary` | CLOSED for `dedup`, `discover`, `feasibility`, `optimize` |
| Sync v5 chat payload body | `run_extraction_v5.py:7906` | `build_chat_payload` sanitizes system/user text before constructing provider message bodies. | `test_v5_chat_payload_builder_redacts_before_request_body_construction` | CLOSED for callers using this builder |
| Runtime provider call wrapper | `llm_runtime.py:174`, `llm_runtime.py:455`, `llm_runtime.py:475`, `llm_runtime.py:489` | `call_llm` sanitizes prompts before dependency payload construction and uses the sanitized prompt for native Gemini contents/system instruction and chat SDK message dispatch. | `test_llm_runtime_sanitizes_prompts_before_dependency_payload_build` | CLOSED for `call_llm` callers |
| v5 batch request builder | `run_extraction_v5.py:10924` | `build_v5_batch_request` sanitizes system/user text before creating `BatchRequest`; lower-level batch clients then serialize sanitized request text. | `test_v5_batch_request_builder_redacts_before_batch_body_serialization`; existing batch response-format and strict passthrough tests | CLOSED for observed v5 builder |
| Path-level secret exclusions | `corpus_walker.py` secret exclude defaults and allowlist behavior | No code change; regression coverage verifies `.env`, `.env.local`, key/private-key names stay out of the corpus, while `.env.example` remains include-eligible and preview-sanitized. | `test_path_exclusions_remain_and_env_templates_are_preview_sanitized`; `test_prescan_v5_integration.py -k default_excludes` | CLOSED for covered paths |

Notes:
- No promptsets, model maps, structured-output schemas, provider route policy, compose files, or pricing behavior were changed.
- Direct `lib.batch_clients.BatchRequest` construction outside `build_v5_batch_request` remains outside this packet's allowed write scope.
- Legacy `run_extraction_v3.py` provider paths remain outside this packet's target and allowlist.
