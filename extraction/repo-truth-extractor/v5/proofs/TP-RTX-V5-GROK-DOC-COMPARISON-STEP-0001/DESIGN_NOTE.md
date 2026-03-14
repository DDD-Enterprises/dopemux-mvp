---
title: "TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001 \u2014 Design Note"
type: explanation
status: active
prelude: Design rationale for the non-canonical Grok comparison lane added to v5 repo-truth-extractor.
tags:
- comparison-lane
- grok
- v5
- extractor
- non-canonical
id: DESIGN_NOTE
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
---
# Design Note: Grok Comparison Lane (TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001)

## Why Comparison Is Non-Canonical

This implementation adds an **observation lane**, not a routing migration. The canonical
extractor behavior remains authoritative. Comparison outputs exist solely to answer:

> "Would Grok 4.20 Beta produce better results on documentation-heavy steps, and by how much?"

This separation is intentional and enforced at multiple levels:

1. **Metadata**: Every comparison artifact carries `lane: "comparison"` and
   `authoritative: false`. Canonical artifacts have no such markers (they are the default truth).
2. **Artifact path**: Comparison outputs go to `raw/comparison/{provider}__{model}/`, never to `raw/`.
3. **Stats isolation**: `execute_step_for_partitions` returns `step_stats` from the canonical
   path only. Comparison results are computed after `step_stats` is assembled.
4. **Resume isolation**: Canonical and comparison have independent resume state. A comparison
   rerun never triggers a canonical rerun.
5. **Failure isolation**: Comparison lane failures are caught by a try/except wrapper and logged
   as `COMPARE_LANE_ERROR`. They never propagate to the canonical return value.

## Eligible Steps and Rationale

Eligibility is config-driven via `COMPARISON_ELIGIBLE_STEPS` (frozenset). The seed set was
chosen based on two criteria:

1. **Output class**: Documentation synthesis, merge/QA, or semantic summarization — tasks where
   a high-context model may show measurable improvement.
2. **Non-mechanical**: Steps that produce human-meaningful narrative or structured synthesis
   (not checksums, manifests, or purely mechanical extractions).

| Step | Prompt Purpose | Lane Class | Rationale |
|------|---------------|------------|-----------|
| A9 | Implicit behavior hints synthesis | BULK_DOCS_GENERAL | Synthesis from scan results |
| B9 | Boundary enforcement merge/QA | AGG | Doc merge — boundary analysis |
| G9 | Generic merge/QA | AGG | Doc merge pattern |
| H9 | Home/entrypoint truth merge/QA | AGG | High-context doc merge |
| R9 | Leantime integration truth synthesis | BULK_DOCS_GENERAL | Pure synthesis |
| S9 | Dependency graph summary synthesis | BULK_DOCS_GENERAL | Synthesis heavy |
| T9 | Task packet merge/QA | AGG | Doc merge pattern |
| W9 | Generic merge/QA | AGG | Doc merge pattern |
| X9 | Feature index merge/QA | AGG | Doc merge pattern |

Excluded:
- **Z9**: Freeze manifest + checksums — mechanical, non-narrative.
- **C9, E9, Q9**: Mixed code+ops; marked ⚠️ borderline, deferred to a future packet.

## How Fairness/Parity Is Preserved

The comparison run receives:
- **Same partition inputs** as canonical (same partition dict, same source files)
- **Same prompt text** as canonical (`prompt_text` passed directly to `run_comparison_lane`)
- **Same normalization pipeline**: `parse_json_from_response` → `coerce_artifacts_from_response`
  (same functions, same code paths)

Only the **route** differs: `provider=cfg.compare_provider, model_id=cfg.compare_model`
instead of the canonical ladder route.

This means any difference in output quality is attributable to the model, not to different
prompts, different data, or different validation logic.
