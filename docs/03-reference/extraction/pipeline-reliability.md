---
id: EXTRACTION-PIPELINE-RELIABILITY
title: Extraction Pipeline Reliability
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Deterministic partitioning, spend enforcement, artifact truth, and output-safety rules for the active v5 extractor.
last_review: '2026-04-06'
next_review: '2026-07-06'
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/repo-truth-extractor/run_extraction_v5.py
    - services/repo-truth-extractor/validate_pre_live_gate_v25.py
    - config/pricing.yaml
---
# Extraction Pipeline Reliability

This document describes reliability and determinism controls in the active v5
extractor.

Authoritative surfaces:

- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- `config/pricing.yaml`

Canonical CLI: `dopemux upgrades ...` (legacy alias: `dopemux extractor ...`).

## Validated bounded target

- phase: `A`
- step: `A2`
- routing policy: `balanced_grok_openrouter`

This branch has live validation for that bounded lane only. It does not prove
universal readiness across all routes or phases.

## Deterministic partition planning

Each phase writes deterministic planning inputs:

- `inputs/INVENTORY.json` (file metadata used for stable planning)
- `inputs/PARTITIONS.json` (partition IDs and stable file lists, plus size limits)

Partition planning uses stable ordering (path primary) and bounded context controls:

- `--max-files-docs`, `--max-files-code`
- `--max-chars`, `--file-truncate-chars`
- `--max-request-bytes` (fail-closed before sending)

## Resume semantics

v5 preserves deterministic resume behavior for provider execution:

1. `raw/<STEP>__<PARTITION>.json` exists
2. it is a valid success output for that step (parseable JSON, expected artifact structure)

If `raw/<STEP>__<PARTITION>.FAILED.*` exists and is older than the success output, the runner prunes stale FAILED sidecars on skip.

## Validator and route readiness

The pre-live validator is a hard gate, not an advisory surface.

Canonical bounded validator command:

```bash
python services/repo-truth-extractor/validate_pre_live_gate_v25.py \
  --target-policy balanced_grok_openrouter \
  --target-phases A \
  --step A2 \
  --allow-online-preflight
```

Current branch truth:

- the validated bounded lane requires `XAI_API_KEY`
- if the validator is not `GO_NOW`, live execution must not start
- validator scope and live command shape must agree before the run starts

## Canonical writers and derived artifacts

Canonical writer:

- `services/repo-truth-extractor/run_extraction_v5.py`

Derived run-level artifacts:

- `RUN_MANIFEST.json`
- `RESUME_PROOF.json`
- `COVERAGE_ROLLUP.json`
- `RUN_ROUTING_FINGERPRINT.json`

Raw/operator-truth artifacts:

- `raw/*.FAILED.json`
- `telemetry/FAILURE_INDEX.json`
- `telemetry/SPEND_LEDGER.json`

Reliability rules:

- aggregate artifacts must not translate `COST_ABORTED` into unrelated failure
  classes
- repair events must be counted once per logical failure, even when both a base
  raw JSON payload and a `.FAILED.json` sidecar exist
- malformed phase coverage payloads are non-fatal, but no longer silent

## Deterministic normalization and output safety

Norm payloads are recursively stripped of forbidden keys:

- `generated_at`
- `timestamp`
- `created_at`
- `updated_at`
- `run_id`

Forbidden keys are defined in `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`.

JSON emission now passes through an explicit output-safety boundary before the
write sink:

- `sanitize_payload_for_output(...)`
- stable JSON serialization with sorted keys and explicit `default=str`

Operator-facing safety rules:

- auth-missing logs do not echo raw credential-bearing values
- response-repair warnings emit only a non-sensitive summary and keep
  partition-specific repair metadata in artifacts rather than logs
- auth-missing metadata redacts credential-bearing env-name fields in that
  failure path

## Phase QA artifacts

Every phase emits:

- `qa/PHASE_FAILURE_ROLLUP.json` (counts + top offenders)
- `qa/PARSE_FAILURE_SHAPES.json` (parse failure taxonomy)
- `qa/PHASE_REQUEST_META_INDEX.json` (request-meta aggregation for failures)
- `qa/PHASE_<PHASE>_CANONICAL_INDEX.json` (canonical promotion ledger)
- `qa/PHASE_<PHASE>_COLLISIONS.json` (canonical policy violations)

service coverage gate:

- `Q_quality_assurance/qa/QA_SERVICE_COVERAGE.json`

## Spend authority and cost-abort behavior

Cost authority:

- `config/pricing.yaml`

Spend reliability rules:

- bounded runs may abort on the first priced request if the cap is exceeded
- `SPEND_LEDGER.json` must exist once billable execution begins
- no later billable calls should appear after a cap breach
- `COST_ABORTED` is a truthful terminal state, not a schema-mismatch surrogate

## Routing and escalation model

Repo Truth Extractor uses a deterministic step-tier classifier and a policy ladder:

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
