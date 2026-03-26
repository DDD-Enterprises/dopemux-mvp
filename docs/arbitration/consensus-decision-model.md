---
id: CONSENSUS_DECISION_MODEL
title: Consensus Decision Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Consensus Decision Model (explanation) for dopemux documentation and developer
  workflows.
---
# Consensus Decision Model

## Overview
The Consensus Decision unifies model-role outputs into a single, policy-bound adjudication. It enforces the distinction between a technical recommendation and the permission to execute.

## Decision Levels
1. **Preferred Candidate Exists**: A clear path forward is identified.
2. **Human Review Required**: A candidate is preferred but exceeds risk/uncertainty thresholds.
3. **No Safe Candidate**: Conflicting requirements or high risks block all proposed paths.
4. **Insufficient Evidence**: Essential context is missing for a confident decision.
5. **Human Defer**: The system explicitly yields authority to a human integrator.

## Consensus Schema
- `preferred_candidate`: ID of the selected end-state.
- `merge_strategy`: One of `OURS_ONLY`, `THEIRS_ONLY`, `SYNTHESIZE_BOTH`, `STAGED_MERGE_THEN_PATCH`, `HUMAN_DEFER`.
- `rationale`: Evidence-backed reasoning for the selection.
- `confidence`: Normalized level (HIGH, MEDIUM, LOW).
- `remaining_blockers`: List of unresolved risks or policy violations.
- `defer_to_human`: Boolean flag triggering escalation.
