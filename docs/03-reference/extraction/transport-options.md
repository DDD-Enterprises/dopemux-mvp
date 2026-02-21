---
id: EXTRACTION-TRANSPORT-OPTIONS
title: Extraction Transport Options
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Transport and routing flags for Repo Truth Extractor runs and targeted reprocessing.
graph_metadata:
  node_type: DocPage
  impact: medium
  relates_to:
    - services/repo-truth-extractor/run_extraction_v3.py
    - scripts/reprocess_failed_partitions.py
---
# Extraction Transport Options

This reference covers:

- runner: `python services/repo-truth-extractor/run_extraction_v3.py ...`
- reprocessor: `python scripts/reprocess_failed_partitions.py ...`

## Model routing flags (runner)

- `--gemini-model-id` (default: `models/gemini-3-flash-preview`)
- `--openai-model-id` (default: `gpt-5.2`)
- `--xai-model-id` (default: `grok-code-fast-1`)
- `--phase-model-map` (override provider/model per phase; see `--print-config`)

Use `--gemini-list-models` to enumerate Gemini models visible to your credentials.

## Transport flags

Runner transports:

- `--gemini-transport`
  - `sdk` (default): Google GenAI SDK transport to `https://generativelanguage.googleapis.com`.
  - `openai_compat_http`: OpenAI-compatible HTTP transport to `https://generativelanguage.googleapis.com/v1beta/openai`.
- `--openai-transport`
  - `openai_sdk` (default): OpenAI Python SDK transport to `https://api.openai.com/v1`.
- `--xai-transport`
  - `openai_sdk` (default): xAI routes via OpenAI-compatible SDK transport to `https://api.x.ai/v1`.

Gemini auth mode (only relevant for `--gemini-transport openai_compat_http`):

- `--gemini-auth-mode auto` (default): tries `query_key`, then `api_key`, then `both`.
- `--gemini-auth-mode query_key`: uses `?key=...` on the endpoint URL.
- `--gemini-auth-mode api_key`: uses `x-goog-api-key: ...` header.
- `--gemini-auth-mode bearer`: uses `Authorization: Bearer ...` header.
- `--gemini-auth-mode both`: uses both `Authorization` and `x-goog-api-key`.

## Deterministic retry/backoff notes

- 429 responses use deterministic backoff `[2, 4, 8, 16]` seconds (bounded retries).
- Backoff decisions and counts are recorded in `qa/PHASE_REQUEST_META_INDEX.json`.

## Examples

Runner (single phase):

```bash
python services/repo-truth-extractor/run_extraction_v3.py \
  --phase D \
  --run-id docs_substrate_20260217_142101_15718 \
  --resume --no-write-latest \
  --gemini-transport sdk \
  --openai-transport openai_sdk \
  --xai-transport openai_sdk \
  --partition-workers 1
```

Reprocessor (policy-driven reruns):

```bash
python scripts/reprocess_failed_partitions.py \
  --run-id docs_substrate_20260217_142101_15718 \
  --failure-policy matrix \
  --gemini-transport sdk \
  --openai-transport openai_sdk \
  --xai-transport openai_sdk \
  --partition-workers 1
```
