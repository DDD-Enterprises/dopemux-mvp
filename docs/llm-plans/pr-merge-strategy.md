# PR Consolidation & Main Merge Plan

## Context
The repo has 27 open PRs, many conflicting, duplicated, or chained off non-main branches. There are 26 worktrees (many stale/detached). The goal is to get all valuable work merged to main as fast as possible, then close the rest.

## Current State Analysis

### PR Categories

#### Category A: CLOSE IMMEDIATELY (subsumed, stale, or duplicated)
| PR | Reason |
|---|---|
| #285 | Duplicate of #298 (same event taxonomy work, #298 is superset with tests) |
| #295 | Duplicate of #299 (same bridge authority work, #299 is superset) |
| #281 | Conflicting, stale (Mar 24), PM write boundary work superseded by pm-continue chain |
| #209 | Conflicting, stale palette PR (content already in main via #249) |
| #212 | Conflicting, 0 files in diff — empty/broken |
| #213 | Conflicting, subsumed by later extraction work |
| #214 | Subsumed by #292 (dev backlog promotion) |
| #236 | Targets non-main branch (#235), conflicting, theme work — close both together |
| #205 | Conflicting, stale pr-merge specialist (superseded by #223) |
| #240 | Conflicting, stale testing PR |

#### Category B: MERGE IN ORDER (the actual valuable work)

**Wave 1 — Independent, mergeable to main NOW:**
| Order | PR | Status | Notes |
|---|---|---|---|
| 1 | #286 | MERGEABLE | Dependabot uv bump (2 files, trivial) |
| 2 | #287 | MERGEABLE | Dependabot npm bump (4 files, trivial) |
| 3 | #294 | MERGEABLE | Execution plane lease store (6 files, clean) |
| 4 | #298 | MERGEABLE | PM event taxonomy (10 files, supersedes #285) |

**Wave 2 — Needs rebase after Wave 1:**
| Order | PR | Status | Notes |
|---|---|---|---|
| 5 | #299 | CONFLICTING | PM bridge authority — rebase onto main after #298 merges, retarget base to main |
| 6 | #300 | MERGEABLE (onto #299) | PM truth rebaseline — retarget to main after #299 merges |

**Wave 3 — Larger independent PRs (merge after Waves 1-2 stabilize):**
| Order | PR | Status | Notes |
|---|---|---|---|
| 7 | #284 | MERGEABLE | PM readiness/observability (11 files) |
| 8 | #210 | MERGEABLE | v5 phase recovery hardening (32 files) |
| 9 | #223 | MERGEABLE | PR Merge Specialist refactor (63 files) |
| 10 | #293 | MERGEABLE | PR-merge cockpit recovery (100 files) |

**Wave 4 — Big merges (careful review needed):**
| Order | PR | Status | Notes |
|---|---|---|---|
| 11 | #224 | MERGEABLE | v5 extraction engine (1368 files, 679K additions — review carefully) |
| 12 | #292 | MERGEABLE | Dev backlog promotion (2761 files, 933K additions — THE BIG ONE) |

#### Category C: CLOSE AS STALE (conflicting, old, superseded by Waves 1-4)
| PR | Reason |
|---|---|
| #225 | Conflicting installer overhaul — reopen fresh PR if still needed after #292 |
| #227 | Conflicting CLI updates — reopen fresh if needed after #292 |
| #235 | Conflicting pr-merge remediation — superseded by #223 + #293 |
| #296 | CONFLICTING, 1.47M additions, 9510 files — this is broken, close it |
| #301 | Targets #296 (which we're closing) — cherry-pick content to new branch if needed |

## Current Branch (codex/main-first-pm-execution-integration)
This branch contains commits equivalent to PRs #294 + #298 + #299 + #300 squashed together. Do NOT create a PR from this branch — it duplicates work already in the PR chain. It served as a local integration test.

## Execution Plan (for Gemini CLI)

### Step 0: Rescue Unique Work from PRs Being Closed

Before closing any PRs, cherry-pick unique work to rescue branches so nothing is lost.

#### 0a. PR #235 — Remediation specialist (13 unique files not in #223)
```bash
git checkout main && git pull origin main
git checkout -b rescue/pr235-remediation-unique
git checkout origin/codex/pr-merge-queue-remediation -- \
  src/dopemux_pr_merge_specialist/action_model.py \
  templates/skills/ci-remediation-specialist/SKILL.md \
  tests/unit/test_pr_merge_specialist_dashboard_and_train.py \
  tests/unit/test_pr_merge_specialist_queue_states.py \
  docs/02-how-to/pr-merge-flight-dashboard.md \
  docs/03-reference/ci-remediation-specialist.md \
  docs/04-explanation/pr-merge-queue-orchestration.md
git add -A && git commit -m "rescue(pr-merge): save unique remediation work from PR #235"
git push -u origin rescue/pr235-remediation-unique
```

#### 0b. PR #301 — Extractor validation toolchain (7 new files + 11 modified)
```bash
git checkout main
git checkout -b rescue/pr301-extractor-validation
git cherry-pick origin/codex/extractor-validation-toolchain-snapshot --no-commit
git add -A && git commit -m "rescue(extractor): save validation toolchain from PR #301"
git push -u origin rescue/pr301-extractor-validation
```

#### 0c. PR #236 — Theme system (2 unique theme commits)
```bash
git checkout main
git checkout -b rescue/pr236-theme-pastel-neon
git cherry-pick 14b604f1f --no-commit  # style: lock in Pastel Neon Dreams theme
git cherry-pick 3a32abf6a --no-commit  # feat(theme): add pastel neon theme refresh
git add -A && git commit -m "rescue(theme): save pastel neon theme work from PR #236"
git push -u origin rescue/pr236-theme-pastel-neon
```

#### 0d. PR #205 — PR-merge skill templates (~15 unique files not on dev)
```bash
git checkout main
git checkout -b rescue/pr205-skill-templates
git checkout origin/feat-pr-merge-specialist-v2 -- \
  templates/skills/pr-merge-specialist/ \
  config/pr_merge_specialist/policy.yaml \
  tests/pr_merge_specialist/
git add -A && git commit -m "rescue(pr-merge): save skill templates from PR #205"
git push -u origin rescue/pr205-skill-templates
```

#### 0e. PR #281 — PM api.py and test (2 unique files, write-boundaries doc covered by #298)
```bash
git checkout main
git checkout -b rescue/pr281-pm-api
git checkout origin/pm-plane-write-boundary-12303391861830324390 -- \
  src/dopemux/pm/api.py \
  tests/test_pm_api.py
git add -A && git commit -m "rescue(pm): save PM api and test from PR #281"
git push -u origin rescue/pr281-pm-api
```

#### 0f. PR #240 — Dashboard API client test (1 unique test file)
```bash
git checkout main
git checkout -b rescue/pr240-api-client-test
git checkout origin/testing-improvement-api-client-14019492419481284990 -- \
  tests/unit/test_dashboard_api_client.py
git add -A && git commit -m "rescue(tests): save API client test from PR #240"
git push -u origin rescue/pr240-api-client-test
```

> **NOTE:** After all waves merge, create PRs from these rescue branches targeting main. The rescue branches preserve work; they are NOT ready to merge as-is (may need updates to work with the post-consolidation codebase).

### Step 0.5: Remove Worktrees That Block Rebase Operations

These worktrees have branches checked out that we need to rebase in later steps. Remove them BEFORE starting merges.

```bash
# Worktrees for branches we need to rebase (Wave 2 + 3)
git worktree remove /private/tmp/dopemux-pm-continue/03-bridge-authority --force
git worktree remove /private/tmp/dopemux-pm-continue/04-truth-rebaseline --force
git worktree remove /Users/hue/code/dopemux-mvp-pm-main-v2 --force
git worktree remove /Users/hue/code/dopemux-mvp-execution-main-v2 --force

# Worktrees for branches we're closing (safe to remove now)
git worktree remove /private/tmp/dopemux-pm-continue/01-write-boundary --force
git worktree remove /private/tmp/dopemux-pm-continue/02-event-taxonomy --force
git worktree remove /private/tmp/dopemux-merge-254-20260322_045627 --force
git worktree remove /private/tmp/dopemux-pr-merge-recovery --force
git worktree remove /private/tmp/dopemux-pr288-repair --force
git worktree remove /private/tmp/dopemux-pr289-repair --force
git worktree remove /Users/hue/code/dopemux-mvp-dev-stabilize --force
git worktree remove /Users/hue/code/dopemux-mvp-docs-status-pr --force
git worktree remove /Users/hue/code/dopemux-mvp-execution-pr --force
git worktree remove /Users/hue/code/dopemux-mvp-main-baseline --force
git worktree remove /Users/hue/code/dopemux-mvp-main-promo --force
git worktree remove /Users/hue/code/dopemux-mvp-pm-cleanup-pr --force
git worktree remove /Users/hue/code/dopemux-mvp-pm-pr --force
git worktree remove /Users/hue/code/dopemux-mvp-runtime-pr --force
git worktree remove /Users/hue/code/dopemux-mvp-theme-pr --force

# Codex detached HEAD worktrees
for wt in /Users/hue/.codex/worktrees/*/dopemux-mvp; do
  git worktree remove "$wt" --force 2>/dev/null
done

git worktree prune
```

### Step 1: Close Stale/Duplicate PRs (Category A + C)
```bash
# Close with comment explaining why
for pr in 205 209 212 213 214 225 227 235 236 240 281 285 295 296 301; do
  gh pr close $pr --comment "Closing: superseded by newer PRs or subsumed by consolidation. See PR consolidation plan."
done
```

### Step 2: Merge Wave 1 (independent, already mergeable)
```bash
# Merge in order, one at a time, wait for each to complete
gh pr merge 286 --merge
gh pr merge 287 --merge
gh pr merge 294 --squash
gh pr merge 298 --squash
```

### Step 3: Fix and Merge Wave 2 (PR chain)
```bash
# After #298 merges, retarget #299 to main and rebase
gh pr edit 299 --base main
# Then in a local checkout:
git fetch origin
git checkout codex/pm-continue-03-bridge-authority
git rebase origin/main
git push --force-with-lease
# Wait for CI (if applicable), then merge
gh pr merge 299 --squash

# Then retarget #300 to main and rebase
gh pr edit 300 --base main
git checkout codex/pm-continue-04-truth-rebaseline
git rebase origin/main
git push --force-with-lease
gh pr merge 300 --squash
```

### Step 4: Merge Wave 3
```bash
# These should be independent — rebase each onto updated main
for pr in 284 210 223 293; do
  # Get branch name, rebase, push, merge
  branch=$(gh pr view $pr --json headRefName --jq '.headRefName')
  git checkout $branch
  git rebase origin/main
  git push --force-with-lease
  gh pr merge $pr --squash
done
```

### Step 5: Merge Wave 4 (big ones — review diffs first!)
```bash
# #224 - v5 extraction engine (large but mergeable)
gh pr merge 224 --merge  # Use merge commit for large PRs to preserve history

# #292 - dev backlog promotion (THE BIG ONE - merge last)
gh pr merge 292 --merge
```

### Step 6: Cleanup
```bash
# Delete merged remote branches
git fetch --prune
```

## Verification
After all merges:
```bash
gh pr list --state open  # Should be 0 (or just rescue branches)
git worktree list        # Should be just main repo
git log --oneline main -20  # Verify all work landed
```

## Risks & Mitigations
- **Wave 4 (#224, #292) are massive:** Review diffs before merging. #292 especially may introduce conflicts with Waves 1-3 — merge it LAST.
- **Rebase conflicts in Wave 2:** If #299 can't cleanly rebase on main after #298 merges, create a new branch from main and cherry-pick the relevant commits.
- **#292 may conflict after Waves 1-3:** If so, create a fresh branch from main, merge #292's branch into it, resolve conflicts, and force-push.

## Summary
- **Rescue:** 6 branches created to preserve unique work
- **Cleanup:** ~20 worktrees removed early
- **Close:** 15 PRs (stale/duplicate/broken)
- **Merge:** 12 PRs in 4 waves
- **Result:** Clean main with all valuable work landed
