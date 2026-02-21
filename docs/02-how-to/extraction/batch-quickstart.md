---
id: HOWTO-EXTRACTION-BATCH-QUICKSTART
title: Repo Truth Extractor Batch Quickstart
type: how-to
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Quick operational guide for running Repo Truth Extractor in batch mode with
  OpenAI, Gemini, or xAI providers.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/run_extraction_v3.py
  - services/repo-truth-extractor/lib/batch_clients.py
last_review: '2026-02-21'
next_review: '2026-05-22'
---
# Repo Truth Extractor Batch Quickstart

Use this when you want lower-cost async execution for high-volume extraction steps.

Batch is opt-in and submit+wait.

## 1. When to use batch mode

Use batch mode for:

- high partition count phases
- non-interactive runs
- cost-first bulk extraction

Do not use batch mode for:

- interactive debugging loops
- immediate human-in-the-loop iteration

## 2. Required flags

```bash
--batch-mode
--batch-provider {auto|openai|gemini|xai}
```

Tuning flags:

```bash
--batch-poll-seconds 30
--batch-wait-timeout-seconds 86400
--batch-max-requests-per-job 2000
```

## 3. Minimal end-to-end command

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --execute \
  --routing-policy cost \
  --batch-mode \
  --batch-provider openai \
  --run-id rte_batch_a_001
```

## 4. Provider-specific command examples

OpenAI:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --execute \
  --batch-mode \
  --batch-provider openai \
  --routing-policy cost \
  --run-id rte_batch_openai_001
```

Gemini:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --execute \
  --batch-mode \
  --batch-provider gemini \
  --routing-policy cost \
  --run-id rte_batch_gemini_001
```

xAI:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --execute \
  --batch-mode \
  --batch-provider xai \
  --routing-policy cost \
  --run-id rte_batch_xai_001
```

Auto provider selection:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --execute \
  --batch-mode \
  --batch-provider auto \
  --routing-policy cost \
  --run-id rte_batch_auto_001
```

## 5. What gets written

Batch diagnostics are written under each phase:

```text
<RUN_ROOT>/<PHASE>/batch/<STEP_ID>.requests.jsonl
<RUN_ROOT>/<PHASE>/batch/<STEP_ID>.job.json
<RUN_ROOT>/<PHASE>/batch/<STEP_ID>.results.jsonl
<RUN_ROOT>/<PHASE>/batch/<STEP_ID>.summary.json
```

Canonical outputs remain unchanged:

- `raw/`
- `norm/`
- `qa/`

## 6. Quick validation checklist

After run:

1. Check status:

```bash
dopemux extractor status --engine-version v4 --run-id rte_batch_a_001
```

2. Confirm batch artifacts exist:

```bash
find extraction/repo-truth-extractor/v4/runs/rte_batch_a_001 -path \"*/batch/*\" -type f
```

3. Confirm step summaries show execution mode split:

- `exec_mode={"batch": ...}` should appear when batch was used

## 7. Troubleshooting

Timeout waiting for batch completion:

- Increase `--batch-wait-timeout-seconds`
- Increase `--batch-poll-seconds` for lower poll pressure

Provider mismatch or auth failures:

- Run:
  - `dopemux extractor preflight --engine-version v4 --auth-doctor`
- Verify corresponding key env vars:
  - OpenAI: `OPENAI_API_KEY`
  - Gemini: `GEMINI_API_KEY`
  - xAI: `XAI_API_KEY`

Too-large job payloads:

- Reduce phase scope
- Lower `--batch-max-requests-per-job`
- Run in multiple phase invocations

## 8. Recommended defaults

For first production batch run:

```bash
--routing-policy cost
--batch-mode
--batch-provider auto
--batch-poll-seconds 30
--batch-wait-timeout-seconds 86400
--batch-max-requests-per-job 2000
```

Then tune based on observed queue latency and provider throughput.
