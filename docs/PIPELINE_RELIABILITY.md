---
id: PIPELINE_RELIABILITY
title: Pipeline Reliability
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Pipeline Reliability (explanation) for dopemux documentation and developer
  workflows.
---
# Pipeline Reliability (v1)

This document defines reliability controls added to `UPGRADES/run_extraction_v3.py`.

## Chunk Key

Each step/chunk now gets a deterministic `chunk_key`:

- `prompt_version` (prompt file hash)
- `provider` + `model`
- `system_prompt_hash`
- `file_manifest_hash` (stable ordered file manifest)
- execution caps (`max_chars`, `file_truncate_chars`, effective `max_files`)
- `home_scan_mode`
- redaction flags/version

Resume logic (`--resume`) skips a chunk only when:

1. chunk output JSON exists and parses
2. `raw/<step>__<chunk>.request_meta.json` exists
3. stored `chunk_key` matches the current computed `chunk_key`

## Retry Matrix

Retry behavior is status-aware and deterministic:

- `429`, `500`, `502`, `503`, `504`, `408`: retry
- network timeout/connection errors: retry
- `400`, `401`, `403`: fail fast

Delay strategy:

- If `Retry-After` is present: `Retry-After + deterministic_jitter(0..250ms)`
- Else: `min(base * 2^(attempt-1), max_delay) + deterministic_jitter`

Jitter seed is deterministic per run/chunk/attempt (`run_id|phase|step|partition|attempt`).

## Rate Limiter Behavior

Per-provider local limits are configurable via CLI:

- `--rpm-openai`, `--tpm-openai`
- `--rpm-gemini`, `--tpm-gemini`
- `--rpm-xai`, `--tpm-xai`
- `--max-inflight` (currently enforced as sequential mode with default `1`)

For OpenAI, the controller consumes response headers when present:

- `x-ratelimit-remaining-requests`
- `x-ratelimit-reset-requests`
- `x-ratelimit-remaining-tokens`
- `x-ratelimit-reset-tokens`

If remaining counts hit zero, the limiter schedules a pause until reset.
If headers are absent, the runner uses local configured limits.

## How to Tune Caps

Primary payload controls:

- `--max-chars` (overall payload size guard)
- `--file-truncate-chars` (per-file truncation)
- `--max-files-docs`, `--max-files-code` (partition/chunk size)

Step chunk planning uses deterministic split policy:

1. stable path ordering
2. fill to soft target (`~70%` of `max_chars`)
3. split by file count/size thresholds only

This keeps chunks bounded and reproducible across resume runs.

## Artifacts Added

Per step:

- `inputs/CHUNK_MANIFEST_<step>.json`
- `raw/<step>__<chunk>.request_meta.json`
- `qa/<step>__chunk_coverage.json`

Payload cache:

- `inputs/payload_cache/<step>__<chunk>.prompt.txt`

The payload cache avoids rebuilding chunk prompts during retries/restarts.
