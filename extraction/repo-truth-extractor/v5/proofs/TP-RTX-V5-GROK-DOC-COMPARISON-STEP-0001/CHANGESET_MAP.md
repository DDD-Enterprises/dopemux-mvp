---
title: "TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001 \u2014 Changeset Map"
type: reference
status: active
prelude: Files changed and purpose for the Grok comparison lane implementation.
tags:
- comparison-lane
- changeset
- v5
id: CHANGESET_MAP
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
---
# Changeset Map

## Core Runner: `services/repo-truth-extractor/run_extraction_v5.py`

### Added Constants

| Symbol | Line (approx) | Purpose |
|--------|--------------|---------|
| `COMPARISON_ELIGIBLE_STEPS` | ~8570 | frozenset of doc-heavy step IDs eligible for comparison |

### Extended: `RunnerConfig` dataclass

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `compare_mode` | `Optional[str]` | `None` | Enables comparison lane (`"additional"`) |
| `compare_model` | `Optional[str]` | `None` | Model ID for comparison (e.g. `"grok-4.20-beta"`) |
| `compare_provider` | `Optional[str]` | `None` | Provider slug (e.g. `"xai"`) |
| `compare_steps` | `Optional[Tuple[str, ...]]` | `None` | Step override; if None, uses `COMPARISON_ELIGIBLE_STEPS` |

### Added Functions (before `execute_step_for_partitions`)

| Function | Purpose |
|----------|---------|
| `is_comparison_enabled(cfg)` | Returns True if `cfg.compare_mode == "additional"` |
| `_effective_compare_steps(cfg)` | Returns the active comparison step set |
| `validate_comparison_steps(cfg)` | Raises ValueError if any requested step is ineligible |
| `compute_comparison_resume_decision(...)` | Lane-isolated resume: checks comparison artifact path |
| `_comparison_artifact_dir(phase_dir, provider, model)` | Returns `raw/comparison/{provider}__{model}/` |
| `run_comparison_lane(...)` | Executes comparison for each partition; non-blocking per-partition |
| `generate_comparison_summary(...)` | Writes `COMPARE_SUMMARY_{step}.json` + `.md` |

### Modified: `execute_step_for_partitions`

Added a comparison lane block after `write_failure_index_snapshot(...)` and before
`return step_stats`. The block:
- Checks `is_comparison_enabled(cfg) and step_id in _effective_compare_steps(cfg)`
- Calls `run_comparison_lane(...)` with the same prompt/partitions
- Calls `generate_comparison_summary(...)`
- Is wrapped in `try/except Exception` with `COMPARE_LANE_ERROR` logging

### Added CLI Args (argparse section)

| Arg | Type | Default | Purpose |
|-----|------|---------|---------|
| `--compare-mode` | str | None | Enable comparison (`"additional"`) |
| `--compare-model` | str | None | Comparison model ID |
| `--compare-provider` | str | None | Comparison provider slug |
| `--compare-steps` | str | None | Comma-separated step IDs |

### Modified: main `RunnerConfig` construction

Wired `args.compare_mode`, `args.compare_model`, `args.compare_provider`,
`args.compare_steps` (parsed as tuple) into `RunnerConfig(...)`.

Added `validate_comparison_steps(cfg)` call after arg normalization.

---

## Model Registry: `templates/routing.yaml`

Added `grok-4.20-beta` model entry under XAI provider section:

```yaml
- id: grok-4.20-beta
  provider: xai
  tier: bulk_docs
  description: "Grok 4.20 Beta — comparison lane only"
  comparison_only: true
```

---

## LiteLLM Config: `docker/mcp-servers-source/litellm/litellm.config.yaml`

Added proxy route for `grok-4.20-beta`:

```yaml
- model_name: grok-4.20-beta
  litellm_params:
    model: xai/grok-4.20-beta
    api_key: os.environ/XAI_API_KEY
    api_base: https://api.x.ai/v1
```

---

## New Test Files

| File | Tests |
|------|-------|
| `services/repo-truth-extractor/tests/test_comparison_lane.py` | T1–T8: lane isolation, routing, non-blocking, resume, eligibility guard |
| `services/repo-truth-extractor/tests/test_comparison_summary.py` | Summary field completeness, count accuracy, route recording |

---

## Proof Documents (this directory)

| File | Contents |
|------|----------|
| `DESIGN_NOTE.md` | Rationale, eligible steps, fairness |
| `CHANGESET_MAP.md` | This file |
| `TEST_EVIDENCE.md` | Commands run and results |
| `COMPARISON_ARTIFACT_LAYOUT.md` | Where comparison outputs live |
| `RUNBOOK.md` | Example operator commands |
| `INITIAL_CANDIDATE_STEPS.md` | Eligible steps with detailed rationale |
