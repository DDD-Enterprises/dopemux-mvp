# PR Merge Strategy & Deep Analysis

## Objective
Systematically process and merge the 23 open pull requests in `dopemux-mvp`, recovering from previous failed merge attempts by applying deep analysis, proper module invocation, and targeted CI/conflict remediation.

## Root Cause Analysis of Previous Failures
1. **Tooling Execution Error:** The `pr-merge-specialist` script was previously failing with `ImportError: attempted relative import with no known parent package` because it was being invoked directly as a script rather than as a module.
2. **CI Failures:** A significant portion of the PRs (e.g., #296, #210, #205) are blocked by failing unit tests (`🧪 Unit Tests`), linting errors (`💅 Code Quality & Linting`), and documentation checks.
3. **Merge Conflicts:** Older PRs (e.g., #214, #213, #212, #209, #205) have accumulated structural drift resulting in `mergeable: CONFLICTING` status. 

## Implementation Plan

### Phase 1: Tooling Correction & Queue Initialization
*   Invoke the PR merge tool correctly using module syntax to avoid import errors:
    ```bash
    PYTHONPATH=/Users/hue/.gemini/skills/pr-merge-specialist/scripts python3 -m dopemux_pr_merge_specialist.cli queue-scan
    ```
*   Rank PRs into buckets: 
    *   **Ready** (Mergeable, CI passing)
    *   **Blocked by CI** (Mergeable, CI failing)
    *   **Blocked by Conflicts** (Conflicting)

### Phase 2: CI Remediation (Deep Analysis)
*   Activate the `ci-remediation-specialist` to address test and lint failures.
*   For each CI-blocked PR (e.g., #296, #210):
    *   Check out the PR into an isolated worktree.
    *   Run `pytest` and `ruff` locally to reproduce failures.
    *   Use `mcp_pal_debug` and `mcp_pal_analyze` to root-cause and fix the issues surgically without expanding scope.
    *   Commit the fixes and push to the PR branch.

### Phase 3: Conflict Resolution
*   For conflicting PRs (e.g., #214, #213):
    *   Check out into an isolated worktree.
    *   Rebase onto `main` (`git pull --rebase origin main`).
    *   Use `mcp_pal_codereview` / `generalist` sub-agent to intelligently resolve merge markers in code.
    *   Verify with the test suite and force-push.

### Phase 4: Final Drainage
*   Continuously monitor `gh pr list` and trigger `gh pr merge --merge` on all PRs that reach a clean state, starting with the highest-priority/least-blocked PRs.

## Verification
*   The PR queue (`gh pr list --state open`) drops to zero.
*   The main branch passes all CI checks.
