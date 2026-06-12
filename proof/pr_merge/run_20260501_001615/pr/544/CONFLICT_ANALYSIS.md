# Conflict Analysis for PR #544

## Classification
- conflict_type: semantic_or_unknown
- strict_conflicts: True

## PR Context
- title: docs(cockpit): preserve local design package work
- base_ref: main
- head_ref: codex/main-clean-local-work-pr
- merge_state_status: DIRTY
- ci_status: FAILURE

## Rebase Failure Signal
```text
X Cannot update PR branch due to conflicts

Local conflict reproduction:
error: cannot rebase: You have unstaged changes.
error: Please commit or stash them.
```

## Deep Inspection Protocol
1. Inspect conflict hunks (base/ours/theirs) and surrounding commit intent.
2. Compare behavior impact, not text-only resolution convenience.
3. Reject blanket `-X ours/-X theirs` strategies.
4. Require scoped tests plus full validation when conflict touches shared primitives.
5. Escalate if confidence is below release safety threshold.

## Conflicting Files
- none detected

## Resolution Decision
- status: escalated
- reason: strict conflict mode requires explicit semantic resolution evidence.
