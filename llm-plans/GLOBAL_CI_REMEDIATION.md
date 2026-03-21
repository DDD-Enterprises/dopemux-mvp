# Global CI Remediation & Specialist Skill Plan

## Background & Motivation
When multiple PRs fail CI due to the same underlying issue (e.g., a shared dependency update, a broken test in `main`), remediating them individually is inefficient and leads to massive merge conflicts. The current system uses a "raw YOLO" Gemini invocation. We need a systemic strategy: a dedicated `ci-remediation-specialist` skill with a strict runbook, and a queue orchestrator that intelligently groups identical failures and fixes them at the source (`main`).

## Scope & Impact
1.  **Create `ci-remediation-specialist` Skill**: Use the skill-creator template to build a specialized agent workflow for reproducing, fixing, and verifying CI errors. (COMPLETED)
2.  **Fingerprint Failures**: Update `ValidationReport` to generate a stable hash of the failing step's name and error output. (COMPLETED)
3.  **Group and Orchestrate**: Update `queue_drain.py` to cluster PRs by this fingerprint. Detect if a global fix PR already exists. If not, spawn the specialist to fix `main`.

## Phase 3 Implementation Plan

### Part 1: GitHubClient Extension
- Add `find_global_fix_prs()` to `GitHubClient` in `src/dopemux_pr_merge_specialist/github_api.py`.
- This will query GitHub for open PRs labeled with `global-ci-fix` authored by the bot.
- Create a helper to parse the `<!-- bot:failure_fingerprint:{hash} -->` from their bodies to map fingerprints to existing fix PRs.

### Part 2: Orchestrator Grouping
- In `queue_drain.py`, implement `_analyze_and_group_failures(results: List[PRResult]) -> Tuple[Dict[str, List[PRResult]], List[PRResult]]`.
- This separates PRs into a dictionary of global blockers (fingerprint -> PRs, where len > 1) and a list of individual PRs.

### Part 3: Handling Global Blockers
- Implement `_handle_global_blockers(...)` in `queue_drain.py`.
- For each global failure fingerprint:
  - If a fix PR already exists (found via the new client method), update the blocked PRs' state (e.g., append a finding) so they know they are waiting.
  - If no fix exists, create a new worktree off `main`, invoke `gemini -p "..." --skill ci-remediation-specialist --yolo`, commit, push to a new branch, and open a PR with the `global-ci-fix` label and the fingerprint comment.

### Part 4: Updating the Action Model
- Ensure `action_model.py` recognizes the new `blocked_by_global_ci_fix` state/finding and suppresses `APPLY_FIX` for those PRs, moving them to a `WAIT` or `HOLD` dashboard tactic.