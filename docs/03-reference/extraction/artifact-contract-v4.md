---
id: EXTRACTION-ARTIFACT-CONTRACT-V4
title: Extraction Artifact Contract V4
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Artifact registry, canonical writer policy, and deterministic normalization for Repo Truth Extractor v4.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/repo-truth-extractor/promptsets/v4/artifacts.yaml
    - services/repo-truth-extractor/run_extraction_v4.py
---
# Extraction Artifact Contract v4

The v4 artifact registry is defined in `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`.

## Registry fields

Each artifact record contains:

- `phase`
- `artifact_name`
- `canonical_writer_step_id`
- `kind`
- `norm_artifact`
- `allow_timestamp_keys`
- `merge_strategy`
- `required_fields`

Global deterministic controls:

- `forbidden_norm_keys` (applied recursively to norm payloads)

## Output layout

For run `<RUN_ID>`, v4 writes:

- `extraction/repo-truth-extractor/v4/runs/<RUN_ID>/<phase>/norm/by_step/<STEP_ID>/<artifact>`
- `extraction/repo-truth-extractor/v4/runs/<RUN_ID>/<phase>/norm/<artifact>` (canonical promoted)
- `extraction/repo-truth-extractor/v4/runs/<RUN_ID>/<phase>/qa/PHASE_<PHASE>_CANONICAL_INDEX.json`
- `extraction/repo-truth-extractor/v4/runs/<RUN_ID>/<phase>/qa/PHASE_<PHASE>_COLLISIONS.json`

## Canonical writer policy

- All step outputs are preserved under `norm/by_step`.
- Only the canonical writer is promoted to phase root `norm/`.
- Collision ledger reports canonical-policy violations.

## Merge strategy

Default list behavior (`itemlist_by_id`):

- concatenate partition items
- deduplicate by `id`
- merge duplicate IDs deterministically
- normalize evidence entries by (`path`, `line_range`, `excerpt`)
- write merge conflicts to QA sidecar

Service catalog behavior (`itemlist_by_service_id`):

- deduplicate by `service_id`
- enforce required service fields

## Norm vs QA rules

Norm artifacts:

- deterministic
- timestamp-free (unless allowlisted)
- consumed by downstream phases

QA artifacts:

- may include `generated_at`, counters, run metadata
- stored in `qa/` or run-level manifests
