---
id: EXTRACTION-PIPELINE-TRANSPORT-LAYER
title: Extraction Pipeline Transport Layer
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Provider transports, endpoints, and request-meta evidence for extraction runs.
graph_metadata:
  node_type: DocPage
  impact: medium
  relates_to:
    - services/repo-truth-extractor/run_extraction_v3.py
    - services/repo-truth-extractor/lib/request_meta_classification.py
---
# Extraction Pipeline Transport Layer

This document describes transport behavior in `services/repo-truth-extractor/run_extraction_v3.py`:

- provider selection and routing (phase -> provider/model)
- transport protocols and endpoints
- deterministic retry/backoff behavior
- request-meta evidence artifacts

## Providers and endpoints

Default per-phase routing is defined in `MODEL_ROUTING` in `services/repo-truth-extractor/run_extraction_v3.py` and is overrideable via CLI.

Transport endpoints:

- `gemini` (Google)
  - SDK: `https://generativelanguage.googleapis.com`
  - OpenAI-compat: `https://generativelanguage.googleapis.com/v1beta/openai`
- `openai` (OpenAI): `https://api.openai.com/v1`
- `xai` (xAI): `https://api.x.ai/v1`

## Request meta evidence

When a partition attempt fails (or enters a retry lane), the runner emits:

- `raw/<STEP>__<PARTITION>.REQUEST_META.json` (and `...R1.REQUEST_META.json`, etc for retry attempts)

The sidecar includes:

- effective provider/model routing and endpoint (`endpoint_effective` is redacted of query keys)
- request payload sizing (`request_payload_bytes`)
- deterministic retry trace and 429 backoff policy
- `provider_signature` and `routing_signature` (audit identity)
- canonical failure typing (`final_failure_type`) with `classification_version=reqmeta_v1`

Phase-level aggregation:

- `qa/PHASE_REQUEST_META_INDEX.json` (histograms + examples + backoff/cooldown counters)

## Deterministic retry/backoff

Retry is controlled by:

- `--retry-policy none|default`
- `--retry-max-attempts`, `--retry-base-seconds`, `--retry-max-seconds`

Special case:

- HTTP 429 uses deterministic backoff `(2, 4, 8, 16)` seconds (bounded by `--retry-max-attempts`)

Backoff/cooldown decisions are summarized in `qa/PHASE_REQUEST_META_INDEX.json`.

## Payload sizing controls

Primary controls:

- `--max-files-docs`, `--max-files-code`
- `--max-chars`, `--file-truncate-chars`
- `--max-request-bytes` (fail-closed before sending when exceeded)
