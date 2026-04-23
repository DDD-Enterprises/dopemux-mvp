---
id: repo-branch-worktree-cleanup-phase3
title: Repo Branch and Worktree Cleanup Phase 3
type: reference
owner: codex
date: 2026-04-23
status: complete
author: '@hu3mann'
last_review: '2026-04-23'
next_review: '2026-07-22'
prelude: Phase-3 survivor resolution after phase-2 safe archive cleanup.
---
# Repo Branch and Worktree Cleanup Phase 3

**Task packet**: `TP-DMX-REPOHYG-003`  
**Parent packet**: `TP-DMX-REPOHYG-002`  
**Execution branch**: `codex/repo-hygiene-phase3-unresolved-survivors`  
**Execution date**: `2026-04-23`

---

## Scope

Phase 3 revisited only the survivors left after phase 2:

- broken temp worktrees
- blocked local branches
- dirty survivors
- closed-unmerged worktree/branch lines
- owner-ambiguous assistant and GTM worktrees
- unresolved `unknown` lines

Current open PR authority at phase-3 start:

- [#501](https://github.com/DDD-Enterprises/dopemux-mvp/pull/501) on `codex/repo-hygiene-audit-phase1`
- [#502](https://github.com/DDD-Enterprises/dopemux-mvp/pull/502) on `codex/repo-hygiene-phase2-safe-archive-cleanup`

No action in phase 3 touched either open-PR branch.

---

## Refreshed Survivor Classes

### Broken Temp Worktrees

| Item | Current authority | Phase-3 result |
| --- | --- | --- |
| `/private/tmp/dopemux-pr467` + `pr/467` | directory existed but was not a valid git worktree; `git worktree remove --force` failed; `git worktree prune --expire now` removed stale admin entry | orphan temp directory removed from filesystem; local branch preserved |
| `/private/tmp/dopemux-pr480` + `pr/480` | directory existed but was not a valid git worktree; `git worktree remove --force` failed; `git worktree prune --expire now` removed stale admin entry | orphan temp directory removed from filesystem; local branch preserved |

### Blocked Local Branches

These remain blocked because current graph proof still fails:

| Branch | Current proof result | Classification | Action |
| --- | --- | --- | --- |
| `tp/rte-full-run-hygiene-and-launch-readiness` | `git merge-base --is-ancestor ... origin/main` => `NO` | blocked / merge-first-adjacent | preserved |
| `codex/rte-seam-extraction-foundation-v2` | `git merge-base --is-ancestor ... origin/main` => `NO` | blocked / archive-not-delete-safe | preserved |
| `tp/gh-review-thread-agent` | `git merge-base --is-ancestor ... origin/main` => `NO` | blocked / archive-not-delete-safe | preserved |

### Closed-Unmerged Survivors

| Branch / Worktree | Current authority | Action |
| --- | --- | --- |
| `codex/ci-unit-shard-experiment` + `/private/tmp/dopemux-ci-pr` | closed-unmerged PR `#499` | preserved |
| `codex/dopecode-ast-navigation-20260417` + `/Users/hue/code/dopemux-mvp-wt-dopecode-ast` | closed-unmerged PR `#471`; branch still not ancestor of `origin/main` | preserved |
| `feat/rte-v5-prescan-contract-unification` + `/Users/hue/code/dopemux-mvp-wt-rte-v5-prescan-contract-unification` | closed-unmerged PR `#470`; branch still not ancestor of `origin/main` | preserved |

### Dirty Survivors

| Worktree | Observed state | Action |
| --- | --- | --- |
| `/private/tmp/dopemux-pr497` | detached with modified `task-packets/TP-DMX-AIG-001.md` | preserved |
| `/Users/hue/code/dopemux-mvp-rte-seams` | modified workflow file and untracked test file | preserved |
| `/Users/hue/code/dopemux-mvp-worktrees/v1-runtime-proof-linkage` | untracked `.operator/` | preserved |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/gracious-poitras-850e4f` | untracked `.claude/brand-voice-guidelines.md` | preserved |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/rte-decompose` | large dirty implementation set | preserved |

### Owner-Ambiguous Survivors

| Worktree | Why preserved |
| --- | --- |
| `/Users/hue/code/dopemux-extractor-gtm` on `codex/prompts-prefix-mirror` | GTM/out-of-scope owner boundary |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/inspiring-nobel-101730` | assistant-owned worktree; no current delete proof |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/optimistic-mayer-6f6e75` | assistant-owned worktree; no current delete proof |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/serene-swirles-f50ab3` | assistant-owned worktree; no current delete proof |

### Unknown Survivors

| Worktree / Branch | Why still unknown |
| --- | --- |
| `/Users/hue/code/dopemux-mvp-wt-rte-benchmark-r1` on `codex/rte-benchmark-r1-first-campaign` | no explicit PR or supersession proof gathered in this packet |
| `/Users/hue/code/dopemux-mvp-wt-serena-audit` on `tp/serena-audit-runtime-io-tools` | no current authority establishing canonical disposition |
| `/Users/hue/code/dopemux-mvp-wt-serena-fix` on `tp/serena-runtime-fix` | no current authority establishing canonical disposition |
| `/Users/hue/code/dopemux-mvp-wt-serena-upstream-diff` on `tp/serena-upstream-contract-diff` | no current authority establishing canonical disposition |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/rte-structured-outputs-all-providers` on `feat/rte-structured-outputs-all-providers` | no current authority establishing canonical disposition |

---

## Executed Actions

### Attempted but Blocked

```text
git worktree remove --force /private/tmp/dopemux-pr467
git worktree remove --force /private/tmp/dopemux-pr480
```

Both failed with:

```text
fatal: validation failed, cannot remove working tree: '<path>/.git' does not exist
```

### Executed Successfully

```text
git worktree prune --verbose --expire now
rm -rf /private/tmp/dopemux-pr467
rm -rf /private/tmp/dopemux-pr480
```

Observed result:

- `git worktree prune` removed the stale admin entries for `dopemux-pr467` and `dopemux-pr480`
- both `/private/tmp/dopemux-pr467` and `/private/tmp/dopemux-pr480` were absent after filesystem cleanup
- local branches `pr/467` and `pr/480` were preserved

No local branch deletion occurred in phase 3.

---

## Residual Risk

- `tp/rte-full-run-hygiene-and-launch-readiness`, `codex/rte-seam-extraction-foundation-v2`, and `tp/gh-review-thread-agent` remain blocked because current graph proof still does not justify deletion.
- Closed-unmerged branches remain intentionally preserved.
- Dirty and owner-ambiguous survivors remain unresolved by design.
- `unknown` lines are still unknown; phase 3 did not invent deletion proof where none existed.
