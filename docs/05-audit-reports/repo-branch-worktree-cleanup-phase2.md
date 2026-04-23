---
id: repo-branch-worktree-cleanup-phase2
title: Repo Branch and Worktree Cleanup Phase 2
type: reference
owner: codex
date: 2026-04-23
status: complete
author: '@hu3mann'
last_review: '2026-04-23'
next_review: '2026-07-22'
prelude: Phase-2 execution ledger for evidence-backed safe archive cleanup.
---
# Repo Branch and Worktree Cleanup Phase 2

**Task packet**: `TP-DMX-REPOHYG-002`  
**Parent packet**: `TP-DMX-REPOHYG-001`  
**Execution branch**: `codex/repo-hygiene-phase2-safe-archive-cleanup`  
**Execution date**: `2026-04-23`

---

## Change Scope

This packet executed only the low-risk subset of the phase-1 `archive` class.

Preserved by rule:

- anything `unknown`
- anything `merge-first`
- anything dirty
- anything closed-unmerged
- anything owner-ambiguous or out-of-scope

Current-state change from phase 1:

- `codex/repo-hygiene-audit-phase1` now has open PR [#501](https://github.com/DDD-Enterprises/dopemux-mvp/pull/501), so it is explicitly preserved.

---

## Authority Refresh

Observed directly before deletion:

- repo root still resolves to `/Users/hue/code/dopemux-mvp`
- `.dopetaskroot` still exists
- `origin` still matches `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- `gh pr list --state open` returned one open PR: `#501` on `codex/repo-hygiene-audit-phase1`

Implication:

- no cleanup action in phase 2 touched `codex/repo-hygiene-audit-phase1`
- the phase-2 cleanup set was recomputed from current status, not copied blindly from phase 1

---

## Frozen Cleanup Set

### Removed Worktrees

These remained archive-class and rechecked as clean or detached-clean at execution time:

| Worktree | Prior phase-1 classification | Current recheck | Action |
| --- | --- | --- | --- |
| `/private/tmp/dopemux-pr492` | archive | detached, clean | removed |
| `/private/tmp/dopemux-pr493` | archive | detached, clean | removed |
| `/private/tmp/dopemux-pr494` | archive | detached, clean | removed |
| `/private/tmp/dopemux-pr495` | archive | detached, clean | removed |
| `/private/tmp/dopemux-pr497b` | archive | detached, clean | removed |
| `/private/tmp/dopemux-pr496` | archive | merged PR branch, clean | removed |
| `/Users/hue/code/dopemux-mvp-rte-main-integration-audit-staging` | archive | merged branch worktree, clean | removed |
| `/Users/hue/code/dopemux-mvp-rte-seams-v2` | archive | merged branch worktree, clean | removed |
| `/Users/hue/code/dopemux-mvp/.worktrees/tp-gh-review-thread-agent` | archive | merged branch worktree, clean | removed |

### Removed Local Branches

| Branch | Reason it remained eligible | Action |
| --- | --- | --- |
| `docs/multi-agent-ingress-architecture-revision` | merged PR `#496`, worktree removed, `git branch -d` succeeded | deleted |

### Preserved / Blocked Survivors

These were excluded even if phase 1 called them `archive`:

| Item | Why preserved |
| --- | --- |
| `codex/ci-unit-shard-experiment` and `/private/tmp/dopemux-ci-pr` | closed-unmerged PR `#499` |
| `codex/prompts-prefix-mirror` and `/Users/hue/code/dopemux-extractor-gtm` | owner-ambiguous and out-of-scope GTM worktree |
| `codex/dopecode-ast-navigation-20260417` and `/Users/hue/code/dopemux-mvp-wt-dopecode-ast` | closed-unmerged PR `#471` |
| `feat/rte-v5-prescan-contract-unification` and `/Users/hue/code/dopemux-mvp-wt-rte-v5-prescan-contract-unification` | closed-unmerged PR `#470` |
| `claude/inspiring-nobel-101730`, `claude/optimistic-mayer-6f6e75`, `claude/serene-swirles-f50ab3` | owner-ambiguous assistant worktrees |
| `tp/rte-full-run-hygiene-and-launch-readiness` | `git branch -d` failed; current branch graph does not prove merged to `origin/main` |
| `codex/rte-seam-extraction-foundation-v2` | `git branch -d` failed; current branch graph does not prove merged to `origin/main` |
| `tp/gh-review-thread-agent` | `git branch -d` failed; current branch graph does not prove merged to `origin/main` |
| `/private/tmp/dopemux-pr467` and `/private/tmp/dopemux-pr480` | broken prunable worktrees from phase 1 remain `unknown` |
| `/private/tmp/dopemux-pr497` | detached but dirty; preserve |

---

## Exact Cleanup Commands

### Worktree Removal Commands

Executed successfully:

```text
git worktree remove /private/tmp/dopemux-pr492
git worktree remove /private/tmp/dopemux-pr493
git worktree remove /private/tmp/dopemux-pr494
git worktree remove /private/tmp/dopemux-pr495
git worktree remove /private/tmp/dopemux-pr497b
git worktree remove /private/tmp/dopemux-pr496
git worktree remove /Users/hue/code/dopemux-mvp-rte-main-integration-audit-staging
git worktree remove /Users/hue/code/dopemux-mvp-rte-seams-v2
git worktree remove /Users/hue/code/dopemux-mvp/.worktrees/tp-gh-review-thread-agent
```

### Branch Deletion Commands

Succeeded:

```text
git branch -d docs/multi-agent-ingress-architecture-revision
```

Attempted but blocked:

```text
git branch -d tp/rte-full-run-hygiene-and-launch-readiness
git branch -d codex/rte-seam-extraction-foundation-v2
git branch -d tp/gh-review-thread-agent
```

Blocking result:

- all three returned `error: the branch '<name>' is not fully merged`
- follow-up ancestor checks against `origin/main` returned `NO`
- phase 2 therefore did **not** escalate to `git branch -D`

---

## Post-Cleanup State

Observed directly after execution:

- removed worktrees no longer appear in `git worktree list --porcelain`
- `docs/multi-agent-ingress-architecture-revision` no longer appears in `git branch -vv`
- blocked branches still exist locally and are called out explicitly
- pre-existing unrelated local state remains:
  - modified `AGENTS.md`
  - untracked `.claude/worktrees/`

---

## Residual Risk

- Phase 2 did not achieve full repo hygiene closure; unknown, merge-first, dirty, closed-unmerged, and owner-ambiguous survivors remain by design.
- `tp/rte-full-run-hygiene-and-launch-readiness`, `codex/rte-seam-extraction-foundation-v2`, and `tp/gh-review-thread-agent` need a later packet if force-delete is ever proposed.
- Broken `pr/467` and `pr/480` temp worktrees still require explicit repair/removal handling.
