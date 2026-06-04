# PR Queue Drain Plan: Sequential Remediation

## Objective
Scan, remediate, and merge all open pull requests sequentially, prioritizing ready-to-merge PRs over those requiring CI fixes, adhering strictly to the `pr-merge-specialist` policy.

## Key Files & Context
- Open PRs requiring merge: #812, #807, #800, #811, #810
- Open PRs requiring CI fixes/remediation: #813, #792
- Execution Script: `python3 scripts/dopemux_pr_merge_specialist/cli.py` or native `gh` / `git` workflow.

## Implementation Steps

### Phase 1: Drain Ready-to-Merge PRs
1. **Merge #812**: `fix(orchestrator): close DMX-ORCH audit gaps` (Checks passing)
2. **Merge #807**: `refactor(brand): kill status-color hex-drift` (Checks passing)
3. **Merge #800**: `🎨 Palette: Tactile feedback` (Checks passing)
4. **Merge #811**: `chore(deps): bump the uv group` (Checks passing)
5. **Merge #810**: `chore(deps): bump the pip group` (Checks passing)

### Phase 2: Sequential Remediation
6. **Remediate #813**: `docs(dcp): land DCP decision`
   - Isolate into a worktree.
   - Investigate 3/24 CI failures.
   - Address PR comments / resolve conversations.
   - Push fixes, await CI green, then merge.
7. **Remediate #792**: `docs(adhd): ADHD/cognitive remediation plan`
   - Isolate into a worktree.
   - Investigate 3/18 CI failures.
   - Address PR comments / resolve conversations.
   - Push fixes, await CI green, then merge.

## Verification & Testing
- Use `gh pr status` to confirm the PR queue is fully drained.
- Ensure no orphaned worktrees remain after the fixes.

## Migration & Rollback
- If a CI fix fails or becomes blocked by complex architectural issues, the PR will be marked `HIGH_RISK` and skipped to maintain queue velocity.