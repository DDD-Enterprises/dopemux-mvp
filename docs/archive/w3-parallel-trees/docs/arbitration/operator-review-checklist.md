---
id: OPERATOR_REVIEW_CHECKLIST
title: Operator Review Checklist
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Review Checklist (explanation) for dopemux documentation and developer
  workflows.
---
# Operator Review Checklist

## Manual Integration Workflow
Follow these steps when handling a high-risk integration deferral:

1. **Confirm End State**: Review the `preferred_candidate` and `candidate_matrix` to ensure the intended behavior is correct.
2. **Review Objections**: Inspect specific `challenger` objections in the `CHALLENGE_REPORT.json`.
3. **Inspect Overlaps**: Manually verify overlapping code hunks identified in the `ARBITRATION_EVIDENCE_BUNDLE.json`.
4. **Resolve Intent**: If `UNRESOLVED_REVIEWER_INTENT` is cited, clarify the implementation with the relevant reviewers.
5. **Confirm Verification**: Validate the `REQUIRED_VERIFICATION_PLAN.json` and add any additional manual tests needed.
6. **Select Strategy**: Finalize the `merge_strategy` (OURS, THEIRS, or SYNTHESIZED).
7. **Approve Patch**: If a patch was proposed, review and apply it manually or via supervised automation.
