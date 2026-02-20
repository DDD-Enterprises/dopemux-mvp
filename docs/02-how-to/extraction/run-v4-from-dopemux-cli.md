---
id: HOWTO-EXTRACTION-RUN-V4-FROM-CLI
title: Run V4 Extraction from Dopemux CLI
type: how-to
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Execute, validate, and troubleshoot Repo Truth Extractor v4 from dopemux extractor commands.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - src/dopemux/cli.py
    - services/repo-truth-extractor/run_extraction_v4.py
---
# Run v4 extraction from Dopemux CLI

This guide uses `dopemux extractor` as the canonical entrypoint for extraction v4.

## 1) Promptset audit

```bash
dopemux extractor promptset audit --engine-version v4
```

## 2) Provider preflight

```bash
dopemux extractor preflight --engine-version v4 --auth-doctor
```

## 3) Run a phase

```bash
dopemux extractor run --engine-version v4 --phase A --run-id rte_v4_local_001 --dry-run
```

## 4) Run full pipeline

```bash
dopemux extractor run --engine-version v4 --phase ALL --run-id rte_v4_full_001 --execute --resume
```

Cost-first routing with escalation controls:

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase C \
  --routing-policy cost \
  --escalation-max-hops 2 \
  --execute
```

Batch mode (submit + wait):

```bash
dopemux extractor run \
  --engine-version v4 \
  --phase A \
  --routing-policy cost \
  --batch-mode \
  --batch-provider openai \
  --batch-poll-seconds 30 \
  --batch-wait-timeout-seconds 86400 \
  --batch-max-requests-per-job 2000 \
  --execute
```

## 5) Check status

```bash
dopemux extractor status --engine-version v4 --run-id rte_v4_full_001
```

JSON status:

```bash
dopemux extractor status --engine-version v4 --run-id rte_v4_full_001 --json
```

## 6) Doctor and reprocess plan

```bash
dopemux extractor doctor --engine-version v4 --run-id rte_v4_full_001
```

With auto-reprocess:

```bash
dopemux extractor doctor \
  --engine-version v4 \
  --run-id rte_v4_full_001 \
  --auto-reprocess \
  --reprocess-dry-run
```

## 7) Output locations

- v4 runs: `extraction/repo-truth-extractor/v4/runs/<RUN_ID>/`
- v4 doctor artifacts: `extraction/repo-truth-extractor/v4/doctor/`
- latest v4 run pointer: `extraction/repo-truth-extractor/v4/latest_run_id.txt`

## 8) Legacy fallback

Use v3 fallback when needed:

```bash
dopemux extractor run --engine-version v3 --phase ALL --run-id rte_v3_legacy_001 --execute
```
