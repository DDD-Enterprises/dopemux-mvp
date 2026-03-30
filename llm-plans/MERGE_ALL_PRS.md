# Plan: Merge All Open PRs

## Objective
Add all remaining open PRs (17 in total) to the auto-merge queue.

## Scope & Impact
- Target PRs: All currently open PRs.
- Impact: CI will process them in the merge queue and merge them into `main`.

## Implementation Steps
1. Fetch all open PR numbers using `gh pr list`.
2. Iterate through each PR and run `gh pr merge <PR_ID> --auto --merge`.
3. This queues them for merging without requiring manual approval, assuming they pass CI.

## Verification
- Run `gh pr list` to confirm they are added to the merge queue.