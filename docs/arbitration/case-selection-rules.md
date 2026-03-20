---
id: CASE_SELECTION_RULES
title: Case Selection Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Case Selection Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Case Selection Rules for Shadow Trial

## Overview
These rules define how Pull Requests are selected and bucketed for the Arbitration Shadow Trial.

## Buckets

### Bucket A: SHADOW_READY
PRs that meet all technical requirements for immediate shadow evaluation.
- **Criteria**:
    - High-risk trigger (TP-029) passes.
    - Merge-base SHA is identifiable and accessible.
    - Diffs for 'ours', 'theirs', and 'base' are complete.
    - Review history (threads/comments) is accessible via GraphQL.
    - All required verification/CI artifacts are present.

### Bucket B: NEEDS_EVIDENCE_REPAIR
PRs that are high-risk but lack essential context for a high-quality arbitration.
- **Criteria**:
    - Missing merge-base lineage (e.g. force-push without anchor).
    - Truncated review history.
    - Inaccessible private sub-modules or protected artifacts.
- **Action**: Log gap notes; do not run full arbitration until repaired.

### Bucket C: NOT_ELIGIBLE
PRs that do not require arbitration or exceed current runtime capabilities.
- **Criteria**:
    - Mechanical-only conflicts.
    - Low-risk documentation or whitespace fixes.
    - PRs targeting branches without defined policy.
