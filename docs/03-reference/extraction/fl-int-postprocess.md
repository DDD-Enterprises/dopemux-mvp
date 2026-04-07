---
id: EXTRACTION-FL-INT-POSTPROCESS
title: FL INT Post-Processing
type: reference
owner: '@hu3mann'
date: '2026-03-31'
author: '@codex'
prelude: Standalone bounded v1 design-synthesis and feature-ledger post-pass for
  Repo Truth Extractor completed runs.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/run_fl_int.py
  - services/repo-truth-extractor/fl_int/run_fl_int.py
  - services/repo-truth-extractor/fl_int/collect_input.py
  - services/repo-truth-extractor/prompts/phase_fl_int/registry.json
  - services/repo-truth-extractor/promptsets/v4/artifacts.yaml
last_review: '2026-03-31'
next_review: '2026-06-30'
---
# FL INT Post-Processing

`FL_INT` is a standalone post-processing flow that runs over an already completed extraction run.
It is bounded to the v1 slice and does not change the default extraction pipeline.

## Authority

Runtime authority:

- `services/repo-truth-extractor/run_fl_int.py`
- `services/repo-truth-extractor/fl_int/run_fl_int.py`
- `services/repo-truth-extractor/fl_int/collect_input.py`
- `services/repo-truth-extractor/fl_int/models.py`

Prompt and schema authority:

- `services/repo-truth-extractor/prompts/phase_fl_int/registry.json`
- `services/repo-truth-extractor/prompts/phase_fl_int/schemas/`

Artifact registration boundary:

- `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Scope

Included v1 steps:

- `F0`
- `F1`
- `F2`
- `F4`
- `L0`
- `L1`
- `L3`
- `L4`

Deferred from this flow:

- `F3`
- `F5`
- `V0`, `V1`, `V9`
- `F9`, `L9`
- `S/T` integration
- default promptset insertion

## Execution model

`FL_INT` is not inserted into `promptsets/v4/promptset.yaml`.
Operators run it explicitly against an existing completed run root.

Canonical step order:

1. `F0`
2. `F1`
3. `F2`
4. `F4`
5. `L0`
6. `L1`
7. `L3`
8. `L4`

`L3` is the explicit v1 filtering and routing step.
It performs the minimum routing needed to separate:

- canonical ledger items
- historical appendix items
- uncertain appendix items
- excluded non-features

## CLI

```bash
python services/repo-truth-extractor/run_fl_int.py \
  --run-root /abs/path/to/completed/run \
  [--out-root /abs/path/to/output] \
  [--dry-run] \
  [--routing-policy cost] \
  [--fl-int-provider-timeout-seconds 180] \
  [--fl-int-f0-batch-timeout-seconds 210] \
  [--pretty]
```

Notes:

- `--run-root` is required.
- `--out-root` defaults to `<RUN_ROOT>/postprocess/fl_int_v1/`.
- `--dry-run` collects inputs and writes the machine summary without calling providers.
- `--fl-int-provider-timeout-seconds` bounds standalone provider calls used by `FL_INT`.
- `--fl-int-f0-batch-timeout-seconds` bounds one `F0` batch and forces fail-closed diagnostics if the batch never reaches a write boundary.
- The flow does not use implicit latest-run discovery.

## Upstream inputs

Required upstream norm directories:

- `D_docs_pipeline/norm`
- `C_code_surfaces/norm`
- `R_arbitration/norm`

Optional upstream norm directory:

- `X_feature_index/norm`

The collector loads `.json` and `.md` norm artifacts only.
If `X` is absent, `L0` degrades gracefully and the run continues.
If any required phase norm directory is absent, collection fails closed.

## Outputs

Default output root:

```text
<RUN_ROOT>/postprocess/fl_int_v1/
```

Primary deliverables:

- `CANONICAL_DESIGN.md`
- `CANONICAL_DESIGN_META.json`
- `MASTER_FEATURE_LEDGER.json`

Intermediate artifacts:

- `DESIGN_CLAIMS_RAW.json`
- `DESIGN_CLAIMS_CLASSIFIED.json`
- `DESIGN_CONTRADICTIONS.json`
- `FEATURE_CANDIDATES_RAW.json`
- `FEATURE_CANDIDATES_NORMALIZED.json`
- `FEATURE_MERGE_LOG.json`
- `FEATURE_LEDGER_ROUTING.json`

Operational artifacts:

- `FL_INT_INPUT.json`
- `STEP_<STEP_ID>_RESULT.json`
- `FL_INT_MACHINE_SUMMARY.json`
- `FL_INT_SUMMARY.md`
- `FL_INT_CHECKLIST.md`
- `FL_INT_FAIL_CLOSED.md`
- `raw/F0_BATCH_<NNN>_TRACE.json`
- `raw/F0_BATCH_<NNN>_FAILURE.json` on fail-closed `F0` batch aborts
- `raw/F0_BATCH_<NNN>_RESPONSE.txt` when provider output is returned but rejected during normalization or schema validation

## F0 runtime remediation

`F0` is the only step with per-batch runtime diagnostics in the standalone flow.

Current runtime behavior:

- `F0` writes a per-batch trace artifact before the provider call starts and updates it at each execution checkpoint.
- `F0` persists batch result artifacts immediately after schema validation succeeds.
- `F0` fails closed with a machine-readable failure artifact if the provider call, normalization, schema validation, or write path fails.
- `F0` normalization is shape-defensive for common provider drift. It can unwrap top-level `DESIGN_CLAIMS_RAW` envelopes and coerce common row-level aliases such as `claim`, `name`, or `title` into `claim_text`, `source` into `source_artifact`, and string/list evidence into evidence objects without inventing semantic meaning.

Required trace progression for a successful `F0` batch:

- `provider_call_return`
- `normalize_return`
- `schema_validate_return`
- `artifact_write_success`

## Artifact registration boundary

The current v4 artifact registry can represent only `json_item_list` and `markdown`.

Registered in `artifacts.yaml`:

- `DESIGN_CLAIMS_RAW.json`
- `DESIGN_CLAIMS_CLASSIFIED.json`
- `DESIGN_CONTRADICTIONS.json`
- `FEATURE_CANDIDATES_RAW.json`
- `FEATURE_CANDIDATES_NORMALIZED.json`
- `FEATURE_MERGE_LOG.json`
- `FEATURE_LEDGER_ROUTING.json`
- `CANONICAL_DESIGN.md`

Not registered in `artifacts.yaml`:

- `CANONICAL_DESIGN_META.json`
- `MASTER_FEATURE_LEDGER.json`

These two final object-shaped JSON outputs are governed by the standalone `phase_fl_int` schemas instead of the v4 artifact registry.

## Operator invariants

- Upstream extraction outputs are read-only inputs to this flow.
- `FL_INT` must not alter prompt behavior for the default extraction pipeline.
- `CANONICAL_DESIGN.md` and `MASTER_FEATURE_LEDGER.json` are derived outputs, not canonical inputs to upstream phases.
- PM-plane features must survive routing and remain visible in ledger statistics when present upstream.
