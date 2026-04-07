# Consolidate Branches and Worktrees Plan

## Objective
Consolidate all in-progress and completed work from all local branches into a single collection branch named `collect`, delete all non-main worktrees, and clean up the old branches.

## Scope & Impact
- **Target Collection Branch:** `collect`
- **Source Branches:** All local branches (over 50+ branches).
- **Worktrees to Delete:**
  - `/Users/hue/.codex/worktrees/5da9/dopemux-mvp`
  - `/Users/hue/.codex/worktrees/extractor-prod/dopemux-mvp`
  - `/Users/hue/code/dopemux-merge-sprint`
  - `/Users/hue/code/dopemux-mvp-runtime-pr`
  - `/Users/hue/code/dopemux-mvp-runtime-salvage`
  - `/Users/hue/code/dopemux-mvp/.worktrees/post-merge-strategy`
  - `/Users/hue/code/dopemux-mvp/worktree-dopetask-probe`
- **Impact:** This is a destructive operation regarding branches and worktrees. All work will be funneled into `collect`. Uncommitted changes in the deleted worktrees will be saved as commits before deletion.

## Implementation Steps

### Phase 1: Preserve Uncommitted Work
1. Iterate through all the secondary worktrees listed above.
2. Check for any uncommitted changes (unstaged or staged).
3. If changes exist, commit them to the currently checked-out branch in that worktree with a message like `chore: preserve worktree state before consolidation`.

### Phase 2: Create the Collection Branch
1. Navigate to the main worktree (`/Users/hue/code/dopemux-mvp`).
2. Checkout `main` and pull the latest changes.
3. Create and checkout the new branch `collect` from `main`.

### Phase 3: Consolidate Branches
*Note: Merging 50+ branches into one will inevitably result in merge conflicts. We will automate this using a script.*
1. Get a list of all local branches (excluding `main` and `collect`).
2. Run a loop to merge each branch into `collect`.
3. **Conflict Resolution Strategy**: If a merge conflict occurs, we will automatically favor the incoming branch (`-X theirs`) or abort and apply as a patch, depending on your preference during execution. *Recommendation: Use `-X theirs` if the goal is to just pile all work together, but this may lead to broken code in `collect`.* 

### Phase 4: Clean Up Worktrees
1. Force remove all secondary worktrees using `git worktree remove --force <path>`.
2. Run `git worktree prune` to clean up any lingering references.

### Phase 5: Clean Up Branches
1. Force delete all local branches that were consolidated into `collect` using `git branch -D <branch_name>`.

## Migration & Rollback
- **Rollback:** Before starting, we will create a lightweight tag on the current `main` and keep a backup list of all branch HEAD SHAs so we can restore any deleted branch using its SHA if the consolidation fails or loses context.

## Verification
- Run `git worktree list` to confirm only the main worktree remains.
- Run `git branch` to confirm only `main` and `collect` (and any explicitly protected branches) remain.