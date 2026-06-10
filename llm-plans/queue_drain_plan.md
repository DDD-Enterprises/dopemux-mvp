# PR Queue Drain Plan

## Background & Motivation
The PR queue currently contains four open pull requests that need to be processed to unblock the pipeline. These PRs require a mix of direct merging, CI remediation, reviewer feedback implementation, and conflict resolution across duplicate efforts.

## Scope & Impact
This plan covers the resolution and merging of PRs 849, 834, 833, and the closure of 817.

## Implementation Steps

### Phase 1: Direct Merge
- **PR 849**: `fix(cli): restore dangerous-mode guards, add post-launch crash protection`
  - Status: CI is green, ready to merge.
  - Action: Merge directly via GitHub CLI or PR Merge Specialist tools.

### Phase 2: Remediate and Merge PR 834
- **PR 834**: `Add dope-context and task-orchestrator read adapters to readonly facade`
  - Issue: Failing CI checks (Docs, Linting) and outstanding reviewer feedback.
  - Action 1: Check out the branch for PR 834.
  - Action 2: Fix the failing CI checks locally (linting and docs issues).
  - Action 3: Add an explicit warning log when `task_orchestrator_project_id` falls back to the default `project_id`, addressing the reviewer's feedback.
  - Action 4: Push fixes, verify CI passes, and merge.

### Phase 3: Consolidate and Resolve PR 833 & 817
- **PR 833** & **PR 817**: Duplicate features for the Palette PredictionPanel. PR 817 contains a necessary `role="group"` accessibility fix, while PR 833 includes extra GitHub workflow and documentation updates. Both have merge conflicts.
  - Action 1: Check out the branch for PR 833 and resolve any merge conflicts with `main`.
  - Action 2: Port the `role="group"` accessibility attribute and specific border adjustments from PR 817 into PR 833's `PredictionPanel.tsx`.
  - Action 3: Validate the build locally (e.g., `pnpm install && pnpm build` in `ui-dashboard`).
  - Action 4: Push the resolved and consolidated code to PR 833.
  - Action 5: Merge PR 833.
  - Action 6: Close PR 817 as a consolidated duplicate.

## Verification & Testing
- Ensure CI is fully green for all modified PR branches before merging.
- Verify `ui-dashboard` builds successfully without TypeScript or Vite errors after consolidating PR 833.
