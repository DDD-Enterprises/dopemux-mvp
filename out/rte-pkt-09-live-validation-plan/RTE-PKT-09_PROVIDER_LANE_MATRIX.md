# RTE-PKT-09 Provider Lane Matrix

Allowed verdicts:
- `NOT_TESTED`
- `STATIC_ONLY`
- `LIVE_PREFLIGHT_ONLY`
- `LIVE_SYNC_METADATA_VALIDATED`
- `LIVE_SCHEMA_VALIDATED`
- `LIVE_BATCH_PILOT_VALIDATED`
- `LIVE_FAILED`
- `LIVE_BLOCKED`
- `LIVE_VALIDATION_INCOMPLETE`

This packet sets every lane to `STATIC_ONLY` or `NOT_TESTED`. No live verdict is granted here.

| Lane | Current Evidence | Future Evidence Required | Stop Conditions | Packet Verdict |
| --- | --- | --- | --- | --- |
| Direct xAI sync | Static routes exist in `run_extraction_v5.py`; xAI client path exists in `llm_runtime.py`. | Auth/model availability, response ID, returned model, usage, finish reason, refusal/incomplete fields, structured-output acceptance, redacted route metadata. | Auth failure, unexpected model, missing response metadata, unredacted output, cap exceeded. | `STATIC_ONLY` |
| OpenRouter `x-ai/...` sync | OpenRouter route support exists, but current observed ladders do not prove an `x-ai/...` route. | Explicit route configuration or one-off future validation route, upstream/provider metadata, requested vs returned model, proxy behavior, refusal/incomplete fields. | Route not explicitly configured, upstream class unclear, OpenRouter response hides required metadata, cap exceeded. | `NOT_TESTED` |
| OpenAI-compatible sync | OpenAI and OpenRouter OpenAI-compatible paths are statically present. | Minimal sync response metadata, response format behavior, local schema validation, no silent downgrade proof. | Missing metadata, schema downgrade, provider error not preserved, unredacted payload. | `STATIC_ONLY` |
| Gemini native sync | Gemini native SDK path exists in `llm_runtime.py`. | Native response text extraction, safety/refusal/incomplete fields where available, usage availability, auth mode evidence. | Safety metadata absent when required, auth pivot ambiguity, unredacted output, cap exceeded. | `STATIC_ONLY` |
| Gemini OpenAI-compatible sync | `llm_runtime.py` has Gemini OpenAI-compatible transport handling. | Endpoint family, auth mode, response format behavior, failure/metadata shape, no silent downgrade proof. | Auth mode ambiguity not recorded, query/header secret exposure risk, missing metadata. | `STATIC_ONLY` |
| xAI/OpenAI-compatible batch submit/poll/cancel | `XAIBatchClient` derives from OpenAI-compatible batch client. | Submit metadata, batch ID, poll states, terminal status, cancel behavior for validation-created jobs, output/error file IDs. | Provider contract mismatch, timeout, row mismatch, unredacted downloaded content, cost cap exceeded. | `STATIC_ONLY` |
| OpenAI batch submit/poll/cancel | `OpenAIBatchClient` implements submit, poll, fetch, cancel. | Same as xAI batch, with downloaded output/error JSONL inventory. | Same as xAI batch. | `STATIC_ONLY` |
| OpenRouter batch | `OpenRouterBatchClient.submit` raises unsupported-provider error. | Future runtime change would be required before any live batch validation. | Any attempt to submit OpenRouter batch under current runtime. | `LIVE_BLOCKED` |
| Batch retrieval for xAI | `batch_retriever.py` supports xAI helpers; `run_extraction_v5.py --retrieve-provider` currently exposes only openai/gemini. | Future packet must choose supported helper path and prove CLI/runtime entrypoint alignment before xAI retrieval. | CLI path cannot address xAI retrieval, remote file IDs absent, output/error JSONL shape unparsed. | `NOT_TESTED` |
| Retention/ZDR | No local live evidence. | Provider docs/account headers/settings or API evidence, redacted and scoped to validation-created artifacts. | Provider evidence unavailable, account ID exposure risk, claims based only on assumptions. | `NOT_TESTED` |
| Billing/spend truth | Runtime cap support is static; provider billing evidence absent. | Provider-side usage or billing evidence, separately authorized and redacted. | Estimate is treated as billing truth, invoice/account evidence would expose secrets. | `NOT_TESTED` |

## Required Preserved Fields

Future lane verdict rows must preserve:
- provider
- route kind
- requested model
- returned/effective model
- auth status
- metadata status
- schema status
- batch status
- retention status
- ZDR status
- spend status
- evidence references

Missing values must be `UNKNOWN`, `NOT_TESTED`, or `MISSING`; they must not be coerced to success.
