---
id: FINAL_PREP_DECISION_MODEL
title: Final Prep Decision Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Final Prep Decision Model for pr-prep-specialist validation.
---
# Final Prep Decision Model

This model synthesizes the results of all layered validation gates into a single, conclusive decision for the PR Prep Specialist.

## Synthesis Logic
1. **Deterministic Override**: Any deterministic `FAIL` (e.g., pre-commit, missing docs) immediately forces a `BLOCKED_*` state.
2. **Consensus Application**: If consensus is conditionally invoked (due to high ambiguity or risk) and recommends blocking, the state becomes `BLOCKED_ADJACENT_WORK_AMBIGUITY` or `HIGH_RISK_HANDOFF_REQUIRED`.
3. **Draft Recommendation**: If there are non-blocking warnings (e.g., partial context, high risk but clean code), the state is `DRAFT_RECOMMENDED`.
4. **Clean Pass**: If all gates pass and obligations are met, the state is `CREATE_READY`.

## Allowed Decisions
- `CREATE_READY`
- `DRAFT_RECOMMENDED`
- `BLOCKED_MISSING_DOCS`
- `BLOCKED_MISSING_CHANGELOG`
- `BLOCKED_VERIFICATION_GAP`
- `BLOCKED_ADJACENT_WORK_AMBIGUITY`
- `BLOCKED_TEMPLATE_INSUFFICIENCY`
- `BLOCKED_DIRTY_WORKTREE`
- `HIGH_RISK_HANDOFF_REQUIRED`
- `INSUFFICIENT_EVIDENCE_REVIEW_REQUIRED`

## Output
The final decision is written to `FINAL_PREP_DECISION.json` and summarized in human-readable format in `CLEAN_CLOSEOUT_SUMMARY.md`.
