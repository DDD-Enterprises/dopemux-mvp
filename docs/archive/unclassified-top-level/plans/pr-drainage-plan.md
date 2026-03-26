# Advanced PR Queue Drainage Plan

## Background & Motivation
There are currently 39 open PRs. Many of them are marked as `MERGEABLE` but remain `BLOCKED`. This indicates that the GitHub merge queue is stuck, likely because a PR at the head of the queue is failing CI checks or experiencing merge group conflicts. Several other PRs are `CONFLICTING` (`DIRTY`) and require manual rebasing and conflict resolution. A few are `BEHIND` and need to be brought up to date with `main`. 

## Scope & Impact
This plan will systematically unblock the merge queue, resolve merge conflicts, remediate CI failures, and process the entire queue until all 39 PRs are merged. This will involve using advanced Git worktree strategies (via the `pr-merge-specialist`), `gh` CLI queue management, and surgical code repairs.

## Proposed Solution & Implementation Steps

### Phase 1: Unblock the Merge Queue (The "Queue Flush")
1. **Identify the Blocker:** Determine which PR is currently at the head of the merge queue and failing checks, causing the `BLOCKED` status for all subsequent PRs.
2. **Dequeue the Blocker:** Use `gh pr merge --disable-auto <PR_NUMBER>` to remove the blocking PR(s) from the queue, allowing the healthy, `MERGEABLE` PRs to process and merge automatically.
3. **Update "BEHIND" PRs:** Run `gh pr update <PR_NUMBER>` on PRs like #224, #210, and #205 to bring them up to date with `main` so they can enter the merge queue cleanly.

### Phase 2: Resolve CONFLICTING & DIRTY PRs
For each conflicting PR (e.g., #237, #236, #227, #225, #214, #213, #212, #206), perform the following isolated loop:
1. **Isolate:** Check out the PR branch in a dedicated git worktree to avoid polluting the main workspace state.
2. **Rebase:** Rebase the branch against the latest `origin/main`.
3. **Resolve:** Surgically resolve merge conflicts. We will pay special attention to highly contested files like `cli.py`, `conport_adapter.py`, `theme.py`, and `routes.py`.
4. **Verify:** Run the relevant unit tests locally within the worktree (`pytest tests/unit/`) to ensure the resolution didn't introduce regressions.
5. **Push:** Force push the resolved branch (`git push --force`) and re-add it to the merge queue (`gh pr merge --auto --squash`).

### Phase 3: Remediate Failing CI Checks
For PRs that are failing CI (the original queue blockers):
1. **Analyze:** Use `gh run view --log-failed` to identify the specific test or linting failures.
2. **Fix:** Apply surgical fixes in an isolated worktree.
3. **Verify & Push:** Commit the fixes, push to the branch, and monitor the CI checks. Once green, add back to the merge queue.

### Phase 4: Final Sweep & Verification
1. Run a final `gh pr list` to ensure the queue is fully drained.
2. Verify that the `main` branch passes all CI checks (`gh run list --branch main`) after the mass merge.

## Alternatives Considered
- **Direct Merging:** Bypassing the merge queue is impossible due to repository branch protection rules enforcing the squash merge queue strategy. We must operate within the queue's rules.
- **Closing Stale PRs:** We could close old or highly conflicting PRs to save time, but without explicit user direction, it is safer to update, resolve, and merge them to preserve the intended features.

## Verification & Testing
- GitHub Actions CI pipeline (`docs`, `identity-check`, `Code Quality & Linting`, `Security Review`, `Unit Tests`) will act as the ultimate gatekeeper for each PR.
- Local `pytest` runs will be executed in isolated worktrees during conflict resolution and remediation to prevent pushing broken code to CI.
