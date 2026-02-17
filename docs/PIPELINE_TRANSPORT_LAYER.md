---
id: PIPELINE_TRANSPORT_LAYER
title: Pipeline Transport Layer
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Pipeline Transport Layer (explanation) for dopemux documentation and developer
  workflows.
---
# Pipeline Transport Layer

This file describes the transport reliability layer in
`/Users/hue/code/dopemux-mvp/UPGRADES/run_extraction_v3.py`.

## Chunking Rules

- Deterministic plan: partitions are chunked in stable order using
  `(path, mtime, size)` with `path` as primary key.
- Chunk budget is character-based (`--max-chars`) with a soft target (~70%).
- Per-file truncation uses `--file-truncate-chars` and includes deterministic
  head + tail snippets.
- Runtime chunk manifest is written to:
  `inputs/CHUNK_MANIFEST_<step>.json`
  with:
  `chunk_id`, `file_entries`, truncation flags, per-file injected bytes,
  `injected_text_sha256`, and `chunk_key`.

## Retry Matrix

- No retry: missing API key, `400`, `401`, `403`.
- Retry with exponential backoff + deterministic jitter:
  `408`, `429`, `500`, `502`, `503`, `504`, network timeout/connection errors.
- Attempt cap: 6.
- Total retry-time cap per chunk: 10 minutes.
- On retry exhaustion or non-retryable error, write:
  `raw/<step>__<chunk>.FAILED.json`.

## Backpressure / Throttle

- Provider-scoped limiter for OpenAI/Gemini/xAI with configurable:
  `RPM`, `TPM`, and `max_inflight`.
- OpenAI header feedback is applied when present:
  `x-ratelimit-remaining-*`, `x-ratelimit-reset-*`.
- On `429`, limiter adaptively increases min delay and reduces inflight floor to 1.

## Resume Semantics

Unit of work:
`(phase, step, partition_id/chunk_id)`.

For each unit:
- Raw output: `raw/<step>__<chunk>.json`
- Meta ledger: `raw/<step>__<chunk>.request_meta.json`
- Payload cache: `inputs/payload_cache/<step>__<chunk>.prompt.txt`

`--resume` skips only when:
1. output JSON exists and parses,
2. meta exists,
3. stored `chunk_key` matches recomputed `chunk_key`.

## Norm Gate Behavior

`normalize_step` now requires full chunk coverage per artifact:
- If `len(chunks_for_artifact) != len(planned_chunks)`, that artifact is marked
  missing and not written to `norm/`.

This prevents partial-merge garbage and preserves strict upstream gating for Phase R.

## Tuning

Chunk and payload geometry:
- `--max-files-docs`
- `--max-files-code`
- `--max-chars`
- `--file-truncate-chars`

Provider quotas:
- `--rpm-openai`, `--tpm-openai`
- `--rpm-gemini`, `--tpm-gemini`
- `--rpm-xai`, `--tpm-xai`
- `--max-inflight`
