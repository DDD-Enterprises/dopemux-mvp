---
id: EVALUATION_MODEL
title: Evaluation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Evaluation Model for the pr-prep-specialist skill.
---
# Evaluation Model

The evaluation of the `pr-prep-specialist` is based on assessing six critical domains across the entire pipeline. The objective is to ensure the skill produces truthful, useful, and complete PR packages, without hallucinating evidence or hiding risks.

## Evaluation Domains

### 1. Branch Truth Quality
- **Focus**: Accuracy of base branch detection, merge base, changed files, and worktree posture.
- **Bands**: `TRUSTWORTHY`, `USEFUL_WITH_CAVEATS`, `NOISY`, `UNSAFE`

### 2. Adjacent-Work Audit Quality
- **Focus**: Effectiveness in detecting meaningful sibling branch or stash overlaps without over-blocking on incidental noise.
- **Bands**: `HIGH_SIGNAL`, `CONSERVATIVE_USEFUL`, `OVERBLOCKING`, `UNDERDETECTING`

### 3. Obligation Accuracy
- **Focus**: Correct identification of docs, changelog, migration notes, and linked context requirements.
- **Bands**: `ACCURATE`, `CONSERVATIVE`, `NOISY`, `UNRELIABLE`

### 4. PR Draft Quality
- **Focus**: Quality of titles, body sections, checklist honesty, and reviewer notes based purely on evidence.
- **Bands**: `HIGHLY_USEFUL`, `USEFUL_WITH_CAVEATS`, `LIMITED`, `MISLEADING`

### 5. Validation Correctness
- **Focus**: Strict adherence to deterministic-first ordering, appropriate invocation of consensus, and honest presentation of blocked/not-run checks.
- **Bands**: `CORRECT`, `CONSERVATIVE`, `INCONSISTENT`, `UNSAFE`

### 6. Handoff Quality
- **Focus**: Completeness, truthfulness, and structural cleanliness of the final handoff bundle sent to the merge specialist.
- **Bands**: `READY_FOR_DOWNSTREAM_USE`, `SUFFICIENT_WITH_GAPS`, `INSUFFICIENT`
