# Conflict Analysis for PR #544

## Classification
- conflict_type: semantic_or_unknown
- strict_conflicts: True

## PR Context
- title: docs(cockpit): preserve local design package work
- base_ref: main
- head_ref: codex/main-clean-local-work-pr
- merge_state_status: BEHIND
- ci_status: FAILURE

## Rebase Failure Signal
```text
GraphQL: head sha didn't match the current head ref. (updatePullRequestBranch)
```

## Deep Inspection Protocol
1. Inspect conflict hunks (base/ours/theirs) and surrounding commit intent.
2. Compare behavior impact, not text-only resolution convenience.
3. Reject blanket `-X ours/-X theirs` strategies.
4. Require scoped tests plus full validation when conflict touches shared primitives.
5. Escalate if confidence is below release safety threshold.

## Conflicting Files
- none detected


## Recommended Strategy
**Ours then Port Selective** (`OURS_THEN_PORT_SELECTIVE`)
- Rationale: Standard conflict resolution (default)
- Risk: MEDIUM
- Verification: STANDARD
- When to use: Refactor on ours, bugfix on theirs.

## Resolution Decision
- status: escalated
- reason: strict conflict mode requires explicit semantic resolution evidence.
