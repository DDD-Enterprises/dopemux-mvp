---
id: OUTCOME_TAXONOMY
title: Outcome Taxonomy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Outcome Taxonomy (explanation) for dopemux documentation and developer workflows.
---
# Operational Outcome Taxonomy

## Core Categories

### Decision Quality
- **ADVANCED_CORRECTLY**: PR was ready and moved to the next stage.
- **BLOCKED_CORRECTLY**: PR had legitimate blockers that were identified.
- **OVER_BLOCKED**: PR was blocked on false positives or overly strict policy.
- **UNDER_BLOCKED**: PR was advanced despite existing blockers.
- **ESCALATED_APPROPRIATELY**: Ambiguity or high risk correctly identified for human review.
- **ESCALATED_UNNECESSARILY**: Straightforward issues were pushed to human review.

### Mutation Impact
- **MUTATION_HELPFUL**: Automated fix was correct and accepted.
- **MUTATION_NO_EFFECT**: Fix applied but did not resolve the blocker.
- **MUTATION_REVERTED**: Operator or reviewer manually undid the automated change.

### Thread & Queue State
- **THREAD_RESOLUTION_HELD**: Guard correctly kept a thread open.
- **THREAD_REOPENED**: Automated resolution was reversed by a reviewer.
- **QUEUE_ADVANCED**: Remediation led to successful merge or position improvement.
- **QUEUE_STALLED**: PR remained in queue without progress.
- **QUEUE_REMOVED**: PR was ejected from queue due to failure or timeout.

### Operator Interaction
- **OPERATOR_OVERRIDE_ACCEPTED**: Human corrected the engine's course.
- **OPERATOR_OVERRIDE_REJECTED**: Human attempted override but was blocked by platform policy.
- **INSUFFICIENT_EVIDENCE**: Outcome cannot be determined from available artifacts.
