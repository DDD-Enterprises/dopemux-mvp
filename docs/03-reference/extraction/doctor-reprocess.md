---
id: EXTRACTION-DOCTOR-REPROCESS
title: Extraction Doctor + Reprocess
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Deterministic diagnosis and policy-driven reprocessing for extraction v4 runs.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/repo-truth-extractor/run_extraction_v4.py
    - services/repo-truth-extractor/run_extraction_v3.py
    - scripts/reprocess_failed_partitions.py
---
# Extraction Doctor + Reprocess

## What doctor does

CLI-first command:

```bash
dopemux extractor doctor --engine-version v4 --run-id <RUN_ID>
```

Runner equivalent:

```bash
python services/repo-truth-extractor/run_extraction_v4.py --doctor --run-id <RUN_ID>
```

Doctor flow:

- runs provider/auth diagnostics
- reads per-phase QA artifacts
- builds a deterministic reprocess plan
- mirrors doctor artifacts into `extraction/repo-truth-extractor/v4/doctor/`

Default mode is non-mutating (plan only).

## Opt-in execution (runner)

Dry-run preview:

```bash
python services/repo-truth-extractor/run_extraction_v4.py \
  --doctor \
  --run-id <RUN_ID> \
  --doctor-auto-reprocess \
  --doctor-reprocess-dry-run
```

Execute doctor-selected reruns:

```bash
python services/repo-truth-extractor/run_extraction_v4.py \
  --doctor \
  --run-id <RUN_ID> \
  --doctor-auto-reprocess
```

Phase override:

```bash
python services/repo-truth-extractor/run_extraction_v4.py \
  --doctor \
  --run-id <RUN_ID> \
  --doctor-auto-reprocess \
  --doctor-reprocess-phases A,H,D
```

## Manual reprocessor integration

Consume the doctor plan:

```bash
python scripts/reprocess_failed_partitions.py --run-id <RUN_ID> --from-doctor
```

Inspect policy output without executing:

```bash
python scripts/reprocess_failed_partitions.py --run-id <RUN_ID> --failure-policy matrix --emit-plan-only
```

## Evidence artifacts

Doctor and the policy matrix read per-phase QA artifacts from the run tree:

- `PHASE_FAILURE_ROLLUP.json`
- `PARSE_FAILURE_SHAPES.json`
- `PHASE_REQUEST_META_INDEX.json`
- `RETRY_DECISIONS.json` and `RETRY_STATS.json`
