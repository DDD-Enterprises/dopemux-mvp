# Dopemux v1 Operator Pack

Archive note: recovered on 2026-04-23 from a local cleanup stash/worktree. Preserved as reference material only; not current runtime or process authority.

This bundle contains a corrected, implementation-ready v1 operator pack for the dual-lane Dopemux workflow.

## Files
- `DOPMUX_V1_DUAL_LANE_OPERATOR_SPEC_V2.md`
- `DOPMUX_V1_REVISED_IMPLEMENTATION_PLAN.md`
- `DOPMUX_V1_PACKET_BASELINE.md`
- `DOPMUX_V1_PROOF_BASELINE.md`

## Intent
This pack assumes:
- task-orchestrator is the task manager
- task packets remain the execution contract
- dopetask remains the execution runtime
- proof bundles remain the evidence/acceptance contract
- ConPort / dope-memory / dope-context / Leantime remain separate authority slices
- tmux `orchestrator` layout is the v1 baseline

## Notes
This pack is written against the resolved probe findings and repo-truth constraints, not against stale docs, unmounted routes, or aspirational integrations.
