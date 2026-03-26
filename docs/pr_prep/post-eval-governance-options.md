---
id: POST_EVAL_GOVERNANCE_OPTIONS
title: Post-Evaluation Governance Options
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Next steps and governance options following the evaluation of pr-prep-specialist.
---
# Post-Evaluation Governance Options

After running the evaluation (TP-PRPS-007) and receiving a final `GO_NO_GO_DECISION`, operators should proceed with one of the following governance paths based on the outcome.

## 1. Favorable Outcomes (`GO_SUPERVISED_FINAL_CREATION`, `GO_DRAFT_FIRST`, `GO_PACKAGE_ONLY`)

### TP-PRPS-008-PREP-SKILL-LIVE-PILOT
If the evaluation demonstrates that the skill is truthful, conservative, and useful, it should be tested in a controlled live environment.
- **Action**: Run the skill against a curated set of real, active branches.
- **Focus**: Measure actual time-saved, reviewer feedback on draft quality, and true-positive rates for missing adjacent work.

## 2. Restrictive Outcomes (`NO_GO_LIMIT_TO_ARTIFACTS_ONLY`, `ROLLBACK_TO_HUMAN_PREP`)

### TP-PRPS-008-PREP-SKILL-HARDENING-AND-RESTRICTION
If the evaluation exposes hallucinated verification, erratic draft quality, or missing critical evidence in the handoff bundle, operational use must be blocked.
- **Action**: Revisit specific pipeline phases (e.g., improve the deterministic gate strictness, fix the adjacent-work heuristic).
- **Focus**: Eliminate `UNSAFE` or `MISLEADING` behaviors before re-evaluating. Trust must be earned sequentially.
