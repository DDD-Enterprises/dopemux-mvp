---
id: HOWTO-EXTRACTION-BATCH-QUICKSTART
title: Repo Truth Extractor Batch Quickstart
type: how-to
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Quick operational guide for running Repo Truth Extractor in batch mode
  with OpenAI, Gemini, or xAI providers through the canonical dopemux rte v5 CLI.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/run_extraction_v5.py
  - services/repo-truth-extractor/lib/batch_clients.py
last_review: '2026-02-21'
next_review: '2026-05-22'
---
# Repo Truth Extractor Batch Quickstart

Use this when you want lower-cost async execution for high-volume extraction steps.

Batch is opt-in and live by default only when explicit consent is present.
The canonical operator command family is `dopemux rte`; `dopemux upgrades` is only a legacy compatibility alias.
The strongest v5 runtime authority remains `services/repo-truth-extractor/run_extraction_v5.py`.
Batch request/response proof is safer after TP-RTE-BATCH-005, TP-RTE-BATCH-E2E-006, and TP-RTE-STRICT-ATTESTATION-007, but live provider and batch execution remain policy-gated.

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
--batch-submit-only
--batch-watch
--batch-retrieve
--retrieve-provider {openai|gemini|xai}
--batch-ids <JOB_ID,...>
--max-partitions-per-step <N>
```

Consent gate for any live batch network call:

```bash
--execute
DPMX_LIVE_OK=1
```

OpenRouter is not supported for live batch in this workflow.

Tuning flags:

```bash
--batch-poll-seconds 30
--batch-wait-timeout-seconds 86400
--batch-max-requests-per-job 2000
```

## 3. Minimal end-to-end command

```bash
DPMX_LIVE_OK=1 dopemux rte run \
  --pipeline-version v5 \
  --phase D \
  --execute \
  --routing-policy balanced_openrouter \
  --batch-mode \
  --batch-provider openai \
  --batch-submit-only \
  --max-partitions-per-step 3 \
  --run-id rte_batch_d_001 \
  --promptset-root /abs/path/to/generated/promptset
```

## 4. Provider-specific command examples

OpenAI:

```bash
DPMX_LIVE_OK=1 dopemux rte run \
  --pipeline-version v5 \
  --phase D \
  --execute \
  --batch-mode \
  --batch-provider openai \
  --batch-submit-only \
  --run-id rte_batch_openai_001 \
  --promptset-root /abs/path/to/generated/promptset
```

Gemini:

```bash
DPMX_LIVE_OK=1 dopemux rte run \
  --pipeline-version v5 \
  --phase D \
  --execute \
  --batch-mode \
  --batch-provider gemini \
  --batch-submit-only \
  --run-id rte_batch_gemini_001 \
  --promptset-root /abs/path/to/generated/promptset
```

xAI:

```bash
DPMX_LIVE_OK=1 dopemux rte run \
  --pipeline-version v5 \
  --phase D \
  --execute \
  --batch-mode \
  --batch-provider xai \
  --batch-submit-only \
  --run-id rte_batch_xai_001 \
  --promptset-root /abs/path/to/generated/promptset
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
dopemux rte status --pipeline-version v5 --run-id rte_batch_d_001
```

2. Confirm batch artifacts exist:

```bash
find extraction/repo-truth-extractor/v5/runs/rte_batch_d_001 -path "*/batch/*" -type f
```

3. Confirm step summaries show execution mode split:

- `exec_mode={"batch": ...}` should appear when batch was used

## 7. Troubleshooting

Timeout waiting for batch completion:

- Increase `--batch-wait-timeout-seconds`
- Increase `--batch-poll-seconds` for lower poll pressure

Provider mismatch or auth failures:

- Run:
  - `dopemux rte preflight --pipeline-version v5 --auth-doctor`
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
--routing-policy balanced_openrouter
--batch-mode
--batch-provider openai
--batch-submit-only
--max-partitions-per-step 3
--batch-poll-seconds 30
--batch-wait-timeout-seconds 86400
--batch-max-requests-per-job 2000
```

Then tune based on observed queue latency and provider throughput.
