---
title: "TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001 \u2014 Initial Candidate Steps"
type: reference
status: active
prelude: Eligible steps for the Grok comparison lane with detailed selection rationale.
tags:
- comparison-lane
- eligible-steps
- v5
- documentation
id: INITIAL_CANDIDATE_STEPS
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
---
# Initial Candidate Steps

## Selection Criteria

A step qualifies for the comparison allowlist if:

1. **Output class = documentation/synthesis**: The step produces human-meaningful narrative,
   structured summaries, or merge/QA artifacts — not mechanical checksums or code extractions.
2. **High-context benefit**: A larger or more capable model plausibly produces better results
   (more complete recall, fewer contradictions, better synthesis).
3. **Non-mechanical**: The step is not purely rule-based or algorithmic.

## Eligible Steps (Initial Allowlist)

### A9 — Implicit Behavior Hints Synthesis

- **Phase**: A (implicit behavior scanning)
- **Lane**: `BULK_DOCS_GENERAL` (non-strict)
- **Purpose**: Synthesizes implicit behavioral hints from scan results across A1–A8
- **Why eligible**: Pure synthesis step; high-context models may produce richer hints
- **Schema strictness**: Non-strict — output is a free-form hints collection

---

### B9 — Boundary Enforcement Merge/QA

- **Phase**: B (boundary enforcement)
- **Lane**: `AGG` (strict)
- **Purpose**: Merges and QA-validates boundary enforcement truths from B1–B8
- **Why eligible**: Doc merge/QA; boundary analysis is documentation-heavy
- **Schema strictness**: Strict — must pass AGG schema gate

---

### G9 — Generic Merge/QA

- **Phase**: G (generic phase)
- **Lane**: `AGG` (strict)
- **Purpose**: Merge/QA of generic phase truths
- **Why eligible**: Doc merge pattern — large context synthesis
- **Schema strictness**: Strict

---

### H9 — Home/Entrypoint Truth Merge/QA

- **Phase**: H (home/entrypoints)
- **Lane**: `AGG` (strict)
- **Purpose**: High-priority merge/QA of home entrypoint truths from H1–H8
- **Why eligible**: Home entrypoints are critical documentation; merge quality matters
- **Schema strictness**: Strict — primary candidate for Grok evaluation

---

### R9 — Leantime Integration Truth Synthesis

- **Phase**: R (Leantime/project management integration)
- **Lane**: `BULK_DOCS_GENERAL` (non-strict)
- **Purpose**: Synthesizes Leantime integration truths
- **Why eligible**: Pure synthesis; benefit from better recall and less omission
- **Schema strictness**: Non-strict

---

### S9 — Dependency Graph Summary Synthesis

- **Phase**: S (service dependency graph)
- **Lane**: `BULK_DOCS_GENERAL` (non-strict)
- **Purpose**: Synthesizes dependency graph summaries from scan results
- **Why eligible**: High-context synthesis; graph-aware models may capture more relationships
- **Schema strictness**: Non-strict

---

### T9 — Task Packet Merge/QA

- **Phase**: T (task packets)
- **Lane**: `AGG` (strict)
- **Purpose**: Merge/QA of task packet truths
- **Why eligible**: Task packets are documentation artifacts; merge quality directly affects
  operator usability
- **Schema strictness**: Strict

---

### W9 — Generic Merge/QA (W phase)

- **Phase**: W (workflow/ops)
- **Lane**: `AGG` (strict)
- **Purpose**: Merge/QA of workflow truths
- **Why eligible**: Doc merge pattern
- **Schema strictness**: Strict

---

### X9 — Feature Index Merge/QA

- **Phase**: X (feature index)
- **Lane**: `AGG` (strict)
- **Purpose**: Merge/QA of feature index truths
- **Why eligible**: Feature index is high-value documentation; synthesis quality matters
- **Schema strictness**: Strict

---

## Excluded Steps

| Step | Reason |
|------|--------|
| **Z9** | Freeze manifest + checksums — purely mechanical, non-narrative. No benefit from a larger model. |
| **C9** | Mixed code+service runtime truths — borderline. More code-oriented than doc-oriented. Deferred. |
| **E9** | Mixed execution facts — code+ops mix. Deferred to future packet. |
| **Q9** | Test/quality artifacts — mixed. Deferred to future packet. |

## Extending the Allowlist

To add a step to the allowlist, update `COMPARISON_ELIGIBLE_STEPS` in
`services/repo-truth-extractor/run_extraction_v5.py`:

```python
COMPARISON_ELIGIBLE_STEPS: frozenset = frozenset({
    "A9", "B9", "G9", "H9", "R9", "S9", "T9", "W9", "X9",
    # Add new steps here after verifying output class
    # "C9",  # deferred
})
```

No other code changes required — the allowlist drives all eligibility checks.
