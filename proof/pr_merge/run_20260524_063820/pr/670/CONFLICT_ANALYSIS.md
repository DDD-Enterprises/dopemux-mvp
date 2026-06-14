# Conflict Analysis for PR #670

## Classification
- conflict_type: semantic_or_unknown
- strict_conflicts: True

## PR Context
- title: docs(governance): refresh PR queue blocker proof
- base_ref: main
- head_ref: codex/tp-dmx-pr-queue-blockers-001
- merge_state_status: DIRTY
- ci_status: SUCCESS

## Rebase Failure Signal
```text
Conflict automation declined before rebase because the PR is not opted in for mechanical recovery.
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
