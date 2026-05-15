# RTE-PKT-07 Provider Metadata Matrix

Generated: 2026-05-15T10:34:49Z

| Runtime path | Requested route fields | Returned/effective fields | Refusal/incomplete fields | Structured-output fields | Test coverage | Remaining UNKNOWN |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI-compatible Chat Completions object | `requested_provider`, `requested_model_id`, `api_key_env`, endpoint fields, transport, `provider_signature`, `provider_route_kind` | `response_id`, `returned_model_id`, `effective_model_id`, `finish_reason`, `finish_reasons`, `usage`, token aliases, `response_text_length`, `choice_count`, `created`, `system_fingerprint_if_present` | `refusal`, `refusal_reason`, `incomplete`, `incomplete_reason`, `response_status` when fixture provides them | `structured_output_mode`, `response_format_type`, `json_schema_name_if_present`, `strict_schema_required`, `provider_schema_variant` | `test_openai_compatible_response_summary_captures_returned_model_and_usage`, refusal, incomplete, structured-output tests | Live provider response variants not proven |
| Direct xAI through OpenAI-compatible SDK | `requested_provider=xai`, requested route model, xAI endpoint metadata, `provider_route_kind=direct_provider` | Returned model captured separately from requested route model | Same OpenAI-compatible response-state extraction | Same structured-output propagation if request metadata carries it | `test_direct_xai_request_meta_keeps_requested_and_returned_model_separate` | Live xAI object shape and refusal/incomplete field names remain unknown |
| OpenRouter `x-ai/...` proxy path | `requested_provider=openrouter`, `requested_model_id=x-ai/...`, OpenRouter endpoint metadata, `provider_route_kind=openrouter_proxy_xai` | Returned model captured without changing provider to direct xAI | Same OpenAI-compatible response-state extraction | Same structured-output propagation if request metadata carries it | `test_openrouter_xai_proxy_request_meta_is_not_direct_xai` | OpenRouter upstream/provider-specific passthrough metadata remains unknown |
| Gemini SDK/native-style response | `requested_provider=gemini`, requested route model, Gemini endpoint/auth metadata when present | `finish_reason`, `finish_reasons`, usage/token aliases, `choice_count` from candidates | `safety_reason` captured from candidate/prompt feedback when present | Existing Gemini structured-output metadata is flattened when present in request_meta | `test_gemini_style_response_summary_preserves_finish_safety_and_usage` | Live Gemini refusal/incomplete shape remains unknown |
| Comparison lane | Comparison `request_meta` now copies response summary fields from `llm_meta` plus requested provider/model and `provider_route_kind` | Same copied fields as available from `call_llm` metadata | Same copied fields as available from `call_llm` metadata | Same copied fields as available from `call_llm` metadata | Existing `test_comparison_lane.py` passed in adjacent suite | No live comparison call was run |

Notes:

- Metadata capture improves response provenance only. It does not make extracted content true.
- Provider refusal and provider incomplete state are recorded as provider response metadata and are not converted into local parse/schema failure fields.
- Local parse-repair provenance remains separate under existing `response_parse_provenance` paths.
