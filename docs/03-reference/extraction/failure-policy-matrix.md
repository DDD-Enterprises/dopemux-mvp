---
id: EXTRACTION-FAILURE-POLICY-MATRIX
title: Extraction Failure Policy Matrix
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Deterministic actions used by doctor and the reprocessor to rerun only actionable
  failures.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/lib/reprocess_policy.py
  - scripts/reprocess_failed_partitions.py
  - services/repo-truth-extractor/run_extraction_v3.py
last_review: '2026-02-21'
next_review: '2026-05-22'
---
# Extraction Failure Policy Matrix

The matrix is implemented in `services/repo-truth-extractor/lib/reprocess_policy.py` and consumed by:

- `python scripts/reprocess_failed_partitions.py --failure-policy matrix`
- `python services/repo-truth-extractor/run_extraction_v3.py --doctor --run-id <RUN_ID>` (plan output)

## Canonical actions (matrix v1)

- `parse` + `truncated_string|truncated_container`
  - action: `rerun_shrink_on_truncation`
  - behavior: rerun partition; runner applies deterministic file-prefix shrink lane and writes `*.SHRINK_TRACE.json`.
- `parse` + `fence_wrapped|preamble|multi_json|suffix_only_closer_junk`
  - action: `rerun_parse_repair`
  - behavior: rerun once through deterministic parse-repair stack.
- `quota_or_billing|rate_limit`
  - action: `rerun_conservative`
  - behavior: rerun with conservative workers (`1`) plus deterministic 429 backoff.
- `auth*`
  - action: `manual_auth_fix`
  - behavior: do not auto-rerun; run `--doctor-auth` and fix credentials.
- `missing_success_json|io_persist`
  - action: `rerun_regenerate_success`
  - behavior: rerun once to regenerate canonical success artifacts and sidecars.
- `schema|contract_violation`
  - action: `rerun_once_then_manual`
  - behavior: rerun once; if persistent, escalate to prompt/schema intervention.
- other/unknown
  - action: `manual_review`

## Evidence inputs (artifacts)

- `qa/PHASE_FAILURE_ROLLUP.json`
- `qa/PARSE_FAILURE_SHAPES.json`
- `qa/PHASE_REQUEST_META_INDEX.json`
- `qa/RETRY_DECISIONS.json` and `qa/RETRY_STATS.json`
