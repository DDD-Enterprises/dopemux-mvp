---
id: HOWTO-EXTRACTION-REPO-TRUTH-EXTRACTOR-USER-GUIDE
title: Repo Truth Extractor User Guide
type: how-to
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: End-user guide for running, validating, and operating Repo Truth Extractor
  with v4 defaults and cost-first routing.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - src/dopemux/cli.py
  - services/repo-truth-extractor/run_extraction_v3.py
  - services/repo-truth-extractor/run_extraction_v4.py
last_review: '2026-02-21'
next_review: '2026-05-22'
---
# Repo Truth Extractor User Guide

This guide is the operator-facing manual for Repo Truth Extractor in Dopemux.

Canonical CLI entrypoint:

```bash
dopemux extractor ...
```

## 1. Core concepts

- Service identity: `Repo Truth Extractor`
- Engines:
  - `v4`: default, strict contracts and deterministic promotion
  - `v3`: compatibility fallback
- Runtime root:
  - `extraction/repo-truth-extractor/`
- Phase runs:
  - `extraction/repo-truth-extractor/<engine>/runs/<RUN_ID>/`

## 2. Before you run

Required for sync execution:

- Python environment with project dependencies
- Valid provider API keys for the providers you intend to use
- Clean enough disk space for raw and norm outputs

Optional but recommended:

- `dopemux extractor preflight --engine-version v4 --auth-doctor`
- `dopemux extractor promptset audit --engine-version v4`

## 3. First run (safe dry-run)

Phase-only dry-run:

```bash
dopemux extractor run --engine-version v4 --phase A --dry-run --run-id rte_user_a_001
```

Full dry-run:

```bash
dopemux extractor run --engine-version v4 --phase ALL --dry-run --run-id rte_user_all_001
```

## 4. Execute run (provider calls enabled)

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase ALL \
  --execute \
  --resume \
  --run-id rte_exec_all_001
```

Expected behavior:

- `raw/` contains partition-level provider responses
- `norm/` contains deterministic merged artifacts
- `qa/` contains coverage, failure rollups, and promotion ledgers

## 5. Routing policy and model ladder

Default policy is `cost` and uses cheap-first ladder semantics.

Primary controls:

```bash
--routing-policy {cost|balanced|quality}
--disable-escalation
--escalation-max-hops 2
```

Practical examples:

Cost-first with escalation:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase C \
  --execute \
  --routing-policy cost \
  --escalation-max-hops 2
```

Single-rung behavior only:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase C \
  --execute \
  --routing-policy cost \
  --disable-escalation
```

## 6. Batch mode (opt-in)

Batch mode is asynchronous submit-and-wait. Use when phase latency is not interactive.

Controls:

```bash
--batch-mode
--batch-provider {auto|openai|gemini|xai}
--batch-poll-seconds 30
--batch-wait-timeout-seconds 86400
--batch-max-requests-per-job 2000
```

Example:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --execute \
  --routing-policy cost \
  --batch-mode \
  --batch-provider openai \
  --batch-poll-seconds 30 \
  --batch-wait-timeout-seconds 86400 \
  --batch-max-requests-per-job 2000
```

Batch artifacts per phase/step:

- `<PHASE>/batch/<STEP_ID>.requests.jsonl`
- `<PHASE>/batch/<STEP_ID>.job.json`
- `<PHASE>/batch/<STEP_ID>.results.jsonl`
- `<PHASE>/batch/<STEP_ID>.summary.json`

## 7. Monitoring and diagnosis

Status:

```bash
dopemux extractor status --engine-version v4 --run-id rte_exec_all_001
```

JSON status:

```bash
dopemux extractor status --engine-version v4 --run-id rte_exec_all_001 --json
```

Doctor:

```bash
dopemux extractor doctor --engine-version v4 --run-id rte_exec_all_001
```

Doctor with reprocess planning:

```bash
dopemux extractor doctor \
  --engine-version v4 \
  --run-id rte_exec_all_001 \
  --auto-reprocess \
  --reprocess-dry-run
```

## 8. Interpreting stdout quickly

`PHASE_START`:

- phase, run_id, inventory count, partition count, routing policy, tier defaults

`STEP_START`:

- step id, tier (`bulk|extract|qa|synthesis`), selected route (`provider/model`)

`ESCALATE` (only on trigger):

- reason, from route, to route, hop number

`STEP_DONE`:

- ok/failed counts, hop distribution, escalated partitions count
- sync vs batch counts
- final provider/model usage counts

## 9. Output structure

Run root:

```text
extraction/repo-truth-extractor/v4/runs/<RUN_ID>/
```

Per phase:

- `inputs/` deterministic inventory and partition plans
- `raw/` partition provider outputs and trace payloads
- `norm/` merged deterministic artifacts
- `qa/` validation and reliability artifacts
- `batch/` (only when batch mode is enabled)

Top-level run files include routing fingerprint, resume proof, and run manifest.

## 10. Common failure patterns

Auth/provider failure:

- Run preflight with `--auth-doctor`
- Verify provider key env vars are present

Schema gate failures:

- Check phase `qa/PHASE_FAILURE_ROLLUP.json`
- Check `qa/PHASE_REQUEST_META_INDEX.json` for failing step/partition IDs

Excessive escalations:

- Start with `--routing-policy balanced`
- Reduce phase scope to isolate one phase

Unexpected run size growth:

- Limit scope to targeted phase
- Use dry-run first
- Keep `--resume` enabled for retries

## 11. Engine fallback

Use v3 only when needed:

```bash
dopemux extractor run --engine-version v3 --phase ALL --execute --run-id rte_v3_fallback_001
```

## 12. Recommended operator workflow

1. Promptset audit
2. Provider preflight
3. Dry-run targeted phase
4. Execute with `--resume`
5. Check status
6. Run doctor and reprocess plan
7. Archive run artifacts and QA outputs
