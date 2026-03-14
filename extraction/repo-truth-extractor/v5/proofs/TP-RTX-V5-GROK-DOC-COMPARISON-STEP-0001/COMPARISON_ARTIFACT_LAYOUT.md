---
title: "TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001 \u2014 Comparison Artifact Layout"
type: reference
status: active
prelude: Document structure for comparison lane outputs relative to canonical artifacts.
tags:
- comparison-lane
- artifacts
- layout
- v5
id: COMPARISON_ARTIFACT_LAYOUT
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
---
# Comparison Artifact Layout

## Overview

Comparison outputs live in a clearly separate subtree under `raw/comparison/` within
each phase directory. Canonical artifacts are never touched.

## Directory Tree

```
runs/{run_id}/
└── {phase_dir}/                     # e.g. A_implicit_behavior/, H_home_entrypoints/
    ├── raw/                         # ← CANONICAL artifacts (untouched)
    │   ├── A9__A_P0001.json
    │   ├── A9__A_P0001.FAILED.txt   # (if canonical failed)
    │   └── ...
    │
    ├── raw/comparison/              # ← COMPARISON artifacts (new)
    │   └── {provider}__{model}/     # e.g. xai__grok-4.20-beta/
    │       ├── A9__A_P0001.json         # comparison output (success)
    │       ├── A9__A_P0001.FAILED.txt   # FAILED sidecar (if comparison failed)
    │       └── ...
    │
    └── COMPARE_SUMMARY_A9.json      # ← Step-level comparison summary (JSON)
    └── COMPARE_SUMMARY_A9.md        # ← Step-level comparison summary (Markdown)
```

## Canonical Artifact Fields (unchanged)

```json
{
  "phase": "A",
  "step_id": "A9",
  "partition_id": "A_P0001",
  "generated_at": "2025-01-01T00:00:00Z",
  "artifacts": [...],
  "request_meta": {
    "provider": "xai",
    "model_id": "grok-4-1-fast",
    "contract_lane": "BULK_DOCS_GENERAL",
    ...
  }
}
```

## Comparison Artifact Fields

```json
{
  "phase": "A",
  "step_id": "A9",
  "partition_id": "A_P0001",
  "artifacts": [...],
  "request_meta": {
    "lane": "comparison",
    "authoritative": false,
    "provider": "xai",
    "model_id": "grok-4.20-beta",
    "comparison_of_step": "A9",
    "elapsed_ms": 1234,
    "final_contract_status": "pass",
    "repair_invocations": 0,
    "repair_successes": 0
  }
}
```

Key distinction from canonical: `lane: "comparison"` and `authoritative: false`.

## FAILED Sidecar (comparison failure)

```
raw/comparison/xai__grok-4.20-beta/A9__A_P0001.FAILED.txt
```

Contains the raw failure reason string (exception message or LLM failure_type).

## Step-Level Comparison Summary

### JSON: `COMPARE_SUMMARY_A9.json`

```json
{
  "step_id": "A9",
  "generated_at": "2025-01-01T00:00:00Z",
  "canonical_route": {
    "provider": "xai",
    "model_id": "grok-4-1-fast"
  },
  "comparison_route": {
    "provider": "xai",
    "model_id": "grok-4.20-beta"
  },
  "partitions_compared": 10,
  "canonical_pass_count": 10,
  "comparison_pass_count": 9,
  "canonical_fail_count": 0,
  "comparison_fail_count": 1,
  "canonical_repair_count": 0,
  "comparison_repair_count": 0,
  "latency_summary": {
    "canonical_avg_ms": 0,
    "comparison_avg_ms": 2100
  },
  "schema_compliance_note": "comparison: 9/10 passed schema validation"
}
```

### Markdown: `COMPARE_SUMMARY_A9.md`

Human-readable summary with the same fields formatted as a report.

## Resume Semantics

- Canonical resume: checks `raw/{step_id}__{partition_id}.json`
- Comparison resume: checks `raw/comparison/{provider}__{model}/{step_id}__{partition_id}.json`

These are **independent**. Pre-existing comparison artifacts do not affect canonical resume
decisions, and vice versa.
