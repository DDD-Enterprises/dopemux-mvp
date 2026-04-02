---
id: HOWTO-EXTRACTION-RTE-V5-FIRST-LIVE
title: Repo Truth Extractor v5 First Live Run
type: how-to
owner: '@hu3mann'
date: '2026-04-01'
author: '@codex'
prelude: Safe first-live procedure for the canonical v5 runner using the staged preset,
  validator-first flow, and dry-run budget review.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
  - services/repo-truth-extractor/run_extraction_v5.py
last_review: '2026-04-01'
next_review: '2026-07-01'
---
# Repo Truth Extractor v5 First Live Run

Use this flow when you want the safest operator path into live v5 execution.

## 1. Validate first

Run the pre-live validator before any live call:

```bash
python services/repo-truth-extractor/validate_pre_live_gate_v25.py
```

The `--preset first-live` flow also runs this validator automatically for live
execution unless `--skip-pre-live-validator` is set.

## 2. Start with a staged dry-run

The initial preset stage runs only `A,H,D,C` and then stops for review.

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --preset first-live \
  --dry-run \
  --run-id rte_first_live_probe
```

Observed default behavior for the preset:

- routing policy: `cost`
- max cost cap: `5.0`
- partition workers: `1`
- batch mode: disabled
- batch wait timeout: `1800`

The runner prints the preset plan before execution so the operator can see the
selected phases and applied defaults.

## 2a. Read route readiness from the right surface

For bounded first-live `A/H/D/C`, `--print-config` now exposes
`route_readiness_summary` as the step-derived readiness surface. Treat
`effective_model_routing` as representative phase-default routing only, not as
the authoritative per-step readiness summary.

Current bounded `cost` route categories on this checkout:

- `required_active_route` providers: `gemini`, `openrouter`, `xai`
- `required_active_route` keys:
  - `GEMINI_API_KEY`
  - `OPENROUTER_API_KEY`
  - `XAI_API_KEY`
- `optional_fallback` provider: `xai`
- `optional_fallback` key:
  - `XAI_API_KEY`
- `configured_not_required` provider: `openai`
- `configured_not_required` key:
  - `OPENAI_API_KEY`

Meaning for operators:

- `OPENROUTER_API_KEY` remains required because strict JSON-managed bounded
  steps still route to OpenRouter `openai/gpt-5.3-codex` and `openai/gpt-5.4`.
- `XAI_API_KEY` is required, not merely optional, because some bounded `A/H/C`
  steps use xAI as the active first route under the current `cost` route truth.
- `OPENAI_API_KEY` is configured in the broader policy ladder but is not
  required for bounded first-live `A/H/D/C`.

## 3. Review budget and paths

Dry-run writes:

- `inputs/COST_PREVIEW.json`
- `inputs/DRY_RUN_CHECKLIST.json`

If you want the budget summary in stdout as well:

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --phase A \
  --dry-run \
  --print-cost-preview \
  --run-id rte_cost_probe
```

If you want an isolated artifact tree:

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --preset first-live \
  --dry-run \
  --run-id rte_first_live_probe \
  --output-root /tmp/rte-v5-sandbox
```

Default artifact root is `extraction/repo-truth-extractor/v5/`.

## 4. Review the checkpoint before synthesis

After the initial stage, inspect:

- `A_repo_control_plane/`
- `H_home_control_plane/`
- `D_docs_pipeline/`
- `C_code_surfaces/`

Recommended checkpoint questions:

- Do the phase inputs and partitions look sane?
- Are the cost-preview warnings acceptable?
- Did dry-run flag unsupported or weakly supported inputs?
- Are the output paths and run root where you expect them to be?

## 5. Run the initial live stage

Only after review:

```bash
DPMX_LIVE_OK=1 python services/repo-truth-extractor/run_extraction_v5.py \
  --preset first-live \
  --run-id rte_first_live_001 \
  --execute
```

If you want to prove route readiness before the live run, use:

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --preset first-live \
  --dry-run \
  --print-config \
  --run-id rte_first_live_probe

python services/repo-truth-extractor/validate_pre_live_gate_v25.py \
  --target-policy cost \
  --target-phases A H D C

python services/repo-truth-extractor/validate_pre_live_gate_v25.py \
  --target-policy cost \
  --target-phases A H D C \
  --allow-online-preflight
```

## 6. Continue after review

Once `A/H/D/C` artifacts are reviewed, run the post-review stage:

```bash
DPMX_LIVE_OK=1 python services/repo-truth-extractor/run_extraction_v5.py \
  --preset first-live \
  --preset-stage post-review \
  --run-id rte_first_live_001 \
  --execute
```

This stage runs `R,X,T,Z,S`.

## 7. Prescan guidance

- Prescan is optional.
- It helps most on larger repos where path reordering and context briefs reduce wasted context.
- It is safe to skip on first dry-runs, small repos, or cheap validator probes.
- Treat prescan as extra preflight work with its own cost.

## 8. Known weak inputs

Be cautious when repo inventory is heavy in:

- PDFs, screenshots, and other image-like assets
- DOCX and PPTX files
- Java, Rust, and Go codebases

The runner now records these classes in the dry-run checklist when they are
present in the resolved inventory.
