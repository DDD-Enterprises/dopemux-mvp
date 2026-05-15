# RTE-PKT-09 Batch Live Pilot Plan

This is a future pilot plan only. No batch submit, poll, retrieve, cancel, file download, or remote deletion is authorized by this packet.

## Static Basis

Observed:
- `OpenAIBatchClient` writes a temporary JSONL request file, uploads it for provider batch, creates a batch job, polls by job ID, fetches output file content, parses JSONL rows, and cancels by job ID.
- `XAIBatchClient` uses the OpenAI-compatible client with xAI base URL.
- `OpenRouterBatchClient` explicitly rejects live batch submit.
- `GeminiBatchClient` uses Gemini batch APIs with inlined requests and returns inline responses rather than OpenAI-compatible output/error JSONL.
- `batch_retriever.py` writes OpenAI-compatible `*_output.jsonl` or `*_error.jsonl` files when provider file IDs exist.

Unknown:
- Whether xAI currently accepts the exact OpenAI-compatible batch payload.
- xAI status values and terminal states.
- xAI output/error JSONL row shape.
- xAI remote file retention and deletion behavior.
- Whether the `run_extraction_v5.py` CLI retrieval surface should expose xAI or whether retrieval must be tested through `batch_retriever.py`.

## Future Pilot Inputs

Use only synthetic, non-sensitive payloads.

Request cap:
- 1 to 3 total requests.

Required request shape:
- stable `custom_id`
- requested provider
- requested model
- route kind
- schema mode if structured output is tested
- expected local validation rule

Forbidden request shape:
- real repo content
- secrets
- user private data
- production promptsets unless separately authorized
- raw credentials

## Required Batch Evidence

Future batch proof must include:
- submit timestamp
- provider
- route kind
- requested model
- batch ID
- input request count
- custom_id map
- polling timestamps
- observed statuses in order
- terminal status
- output file ID if returned
- error file ID if returned
- downloaded output/error file path if authorized
- SHA-256 for downloaded local files
- row count reconciliation
- missing custom IDs
- duplicate custom IDs
- provider error rows
- local parse errors
- cancellation result if cancellation was authorized
- cleanup result if cleanup was authorized

## Downloaded JSONL Handling

Rules:
- Store downloaded files only under the future isolated validation artifact root.
- Hash every downloaded file.
- Preserve full local files only if the future packet explicitly permits it and redaction scan passes.
- Include only redacted excerpts in human-readable proof.
- Parse each line as JSON.
- Record invalid JSON lines as failures.
- Record non-object lines as failures.
- Reconcile every `custom_id`.
- Treat missing rows as failure evidence, not as success.
- Keep downloaded JSONL proof separate from production readiness claims.

## Stop Conditions

Stop before submit if:
- explicit batch approval is missing
- spend cap is missing
- batch cap is missing
- timeout cap is missing
- provider is OpenRouter under current runtime
- request payload includes non-synthetic data
- credentials would be printed

Stop during poll if:
- timeout cap is reached
- terminal failure is observed
- status sequence is not recorded
- cost cap is reached

Stop during retrieve if:
- output/error file ID is missing when expected
- download would write outside the isolated artifact root
- downloaded content contains credential-shaped material
- row count mismatch is not preserved

Stop during cleanup if:
- cleanup/deletion was not separately authorized
- target ID was not created by the validation run
- provider cannot prove target identity

## Future Exit States

Allowed batch verdicts:
- `NOT_TESTED`
- `STATIC_ONLY`
- `LIVE_BATCH_PILOT_VALIDATED`
- `LIVE_FAILED`
- `LIVE_BLOCKED`
- `LIVE_VALIDATION_INCOMPLETE`

This packet leaves batch at `STATIC_ONLY` plus `LIVE_VALIDATION_REQUIRED`.
