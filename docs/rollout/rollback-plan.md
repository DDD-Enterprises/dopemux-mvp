---
id: ROLLBACK_PLAN
title: Rollback Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Rollback Plan (explanation) for dopemux documentation and developer workflows.
---
# Rollback Plan

## Rollback Triggers
Revert to a lower tier or disable the skill if:
- Unauthorized mutations occur.
- PR body content is corrupted during enforcement.
- Meaningful DESIGN or POLICY disagreements are resolved automatically.
- Incident rate exceeds 5% of runs.

## Rollback Actions

### Tier Rollback (Immediate)
1. Edit the repo-local `policy.yaml`.
2. Set `mode: advisory`.
3. Disable all `mutation` flags.

### Agent Disablement
1. Remove the agent profile (e.g., delete `.github/agents/pr-merge-specialist.agent.md`).
2. Update `AGENTS.md` to mark the specialist as `DISABLED`.

### Validation
After rollback, run a dry-run `pr-fix` to confirm no mutations occur and artifacts report the `advisory` mode.
