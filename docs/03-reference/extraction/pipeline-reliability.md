---
id: EXTRACTION-PIPELINE-RELIABILITY
title: Extraction Pipeline Reliability
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Deterministic partitioning, canonical promotion, and coverage gates in extraction v4.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/repo-truth-extractor/run_extraction_v4.py
    - services/repo-truth-extractor/run_extraction_v3.py
    - services/repo-truth-extractor/lib/chunking.py
---
# Extraction Pipeline Reliability

This document describes reliability and determinism controls in `services/repo-truth-extractor/run_extraction_v4.py`.

v4 executes via v3-compatible provider flows, then enforces v4 contracts during sync.

## Deterministic partition planning

Each phase writes deterministic planning inputs:

- `inputs/INVENTORY.json` (file metadata used for stable planning)
- `inputs/PARTITIONS.json` (partition IDs and stable file lists, plus size limits)

Partition planning uses stable ordering (path primary) and bounded context controls:

- `--max-files-docs`, `--max-files-code`
- `--max-chars`, `--file-truncate-chars`
- `--max-request-bytes` (fail-closed before sending)

## Resume semantics

v4 preserves v3 resume behavior for provider execution:

1. `raw/<STEP>__<PARTITION>.json` exists
2. it is a valid success output for that step (parseable JSON, expected artifact structure)

If `raw/<STEP>__<PARTITION>.FAILED.*` exists and is older than the success output, the runner prunes stale FAILED sidecars on skip.

## Canonical artifact reliability

v4 enforces strict artifact reliability:

- Step outputs are preserved in `norm/by_step/<STEP_ID>/`.
- Canonical artifact promotion writes only canonical-writer outputs to `norm/`.
- Canonical index is emitted per phase: `qa/PHASE_<PHASE>_CANONICAL_INDEX.json`.
- Collision ledger is emitted per phase: `qa/PHASE_<PHASE>_COLLISIONS.json`.

## Deterministic normalization

Norm payloads are recursively stripped of forbidden keys:

- `generated_at`
- `timestamp`
- `created_at`
- `updated_at`
- `run_id`

Forbidden keys are defined in `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`.

## Phase QA artifacts

Every phase emits:

- `qa/PHASE_FAILURE_ROLLUP.json` (counts + top offenders)
- `qa/PARSE_FAILURE_SHAPES.json` (parse failure taxonomy)
- `qa/PHASE_REQUEST_META_INDEX.json` (request-meta aggregation for failures)
- `qa/PHASE_<PHASE>_CANONICAL_INDEX.json` (canonical promotion ledger)
- `qa/PHASE_<PHASE>_COLLISIONS.json` (canonical policy violations)

v4 service coverage gate:

- `Q_quality_assurance/qa/QA_SERVICE_COVERAGE.json`

## Cost-first routing and escalation

Repo Truth Extractor now uses a deterministic step-tier classifier and a policy ladder:

- tiers:
  - `bulk`: step IDs ending in `0`
  - `extract`: default tier for non-specialized steps
  - `qa`: `Q` phase and `*9`/`*99` steps
  - `synthesis`: `R/X/T` phases and `Z1/Z2`
- default policy: `cost`
- default ladder behavior: cheap-first with escalation only on hard gates

Escalation triggers:

- provider/auth hard failures
- parse failure after parse-retry loop is exhausted
- schema gate failures (missing expected artifacts, or missing required item keys)

Escalation controls:

- `--disable-escalation`
- `--escalation-max-hops` (default `2`)

Batch controls (opt-in):

- `--batch-mode`
- `--batch-provider {auto,openai,gemini,xai}`
- `--batch-poll-seconds`
- `--batch-wait-timeout-seconds`
- `--batch-max-requests-per-job`

Batch artifacts per step:

- `<PHASE>/batch/<STEP_ID>.requests.jsonl`
- `<PHASE>/batch/<STEP_ID>.job.json`
- `<PHASE>/batch/<STEP_ID>.results.jsonl`
- `<PHASE>/batch/<STEP_ID>.summary.json`
