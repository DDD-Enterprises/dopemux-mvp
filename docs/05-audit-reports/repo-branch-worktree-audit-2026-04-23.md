---
id: repo-branch-worktree-audit-2026-04-23
title: Repo Branch and Worktree Audit
type: reference
owner: codex
date: 2026-04-23
status: complete
author: '@hu3mann'
last_review: '2026-04-23'
next_review: '2026-07-22'
prelude: Branch, remote, and worktree phase-1 audit for deterministic cleanup planning.
---
# Repo Branch and Worktree Audit

**Audit packet**: `TP-DMX-REPOHYG-001`
**Audit date**: `2026-04-23`
**Execution branch**: `codex/repo-hygiene-audit-phase1`
**Base branch**: `main`
**Scope**: phase-1 evidence collection and non-destructive cleanup planning only

---

## Repo Identity

Observed directly:

- Repo root resolved to `/Users/hue/code/dopemux-mvp`
- `.dopetaskroot` exists at repo root
- `origin` remote is `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- A second remote, `gtm-ssh`, points at `DDD-Enterprises/dopemux-extractor-gtm.git` and was treated as out-of-scope for this audit

Authority used for this audit:

- Runtime repo truth from git surfaces: `git remote -v`, `git branch`, `git branch -vv`, `git worktree list --porcelain`, `git status --short --branch`
- Remote PR evidence from `gh pr list --state open/all`
- Repo operating contract from `AGENTS.md`

Drift observed:

- `AGENTS.md` names `tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_CANONICALS.md` and related truth files as available in this checkout. Those paths were not present during this audit, so they were not used as authority.

---

## Remote Evidence Summary

Observed directly at audit time:

- `gh pr list --state open` returned `[]`
- No open PR heads were present in the current GitHub remote evidence set
- Recent merged heads that still intersect local branches or worktrees include:
  - `codex/pal-sse-wrapper` via PR `#500`
  - `codex/phase0` via PR `#497`
  - `docs/multi-agent-ingress-architecture-revision` via PR `#496`
  - `design/wave7-rte-ui-contract` via PR `#495`
  - `feat/rte-prescan-stage0-live-lane-proving` via PR `#480`
  - `tp/gh-review-thread-agent` via PR `#465`
  - `tp/rte-full-run-hygiene-and-launch-readiness` via PR `#461`
- Recent closed-unmerged heads that still intersect local branches or worktrees include:
  - `codex/ci-unit-shard-experiment` via PR `#499` against `codex/ci-fast-unit-gate`
  - `feat/rte-prescan-first-live-hardening` via PR `#467`
  - `feat/rte-v5-prescan-contract-unification` via PR `#470`
  - `codex/dopecode-ast-navigation-20260417` via PR `#471`
  - `tp/dopecode-ast-navigation` via PR `#469`
  - `tp/serena-tool-surface-audit` via PR `#468`
  - `tp/dopecode-phase2-harden` via PR `#473`
  - `tp/dopecode-phase3-decompose-policy` via PR `#474` and `#477`
  - `tp/dopecode-phase4-language-approval` via PR `#476`

Remote branch naming clusters observed from `refs/remotes/origin`:

- Active-looking prefixes: `codex/`, `tp/`, `feat/`, `docs/`, `design/`
- Legacy or cleanup-sensitive prefixes: `bundle/`, `copilot/`, `dependabot/`, `palette/`, `rescue/`, `prmerge/`
- Branches whose commit subjects explicitly mention supersession or rescue exist on remote and should not be auto-deleted without packeted review

Deterministic rule used in this audit:

- A remote branch was not marked `delete-remote` unless both of these were true:
  - there was explicit merged or closed-unmerged PR evidence, and
  - no active local worktree, dirty state, detached checkout dependency, or unresolved branch-purpose ambiguity blocked deletion

No remote branch met that standard in this phase-1 packet.

---

## Local Worktree Evidence

### Inventory Counts

| Surface | Count | Notes |
| --- | --- | --- |
| Local worktrees listed | 26 | Includes main checkout |
| Detached worktrees | 6 | `/private/tmp/dopemux-pr492`, `pr493`, `pr494`, `pr495`, `pr497`, `pr497b` |
| Explicitly prunable worktrees | 2 | `/private/tmp/dopemux-pr467`, `/private/tmp/dopemux-pr480` |
| Worktrees with observed dirty state | 7 | Main checkout plus 6 additional worktrees |
| Worktrees on branches whose upstream is gone | 4 | Includes `codex/prompts-prefix-mirror` and `tp/rte-full-run-hygiene-and-launch-readiness` |

### Dirty or Ambiguous Worktrees

| Worktree | Branch / State | Observed condition | Classification | Reason | Blocking risk |
| --- | --- | --- | --- | --- | --- |
| `/Users/hue/code/dopemux-mvp` | `codex/repo-hygiene-audit-phase1` | Dirty: `AGENTS.md`, untracked `.claude/worktrees/` | `keep` | Active audit workspace for this packet | Current packet in progress |
| `/private/tmp/dopemux-pr467` | `pr/467` | `prunable gitdir file points to non-existent location`; `git status` failed | `unknown` | Broken worktree metadata; branch tied to closed-unmerged PR `#467` | Worktree repair/removal needs explicit follow-up |
| `/private/tmp/dopemux-pr480` | `pr/480` | `prunable gitdir file points to non-existent location`; `git status` failed | `unknown` | Broken worktree metadata; branch tied to merged PR `#480` | Worktree repair/removal needs explicit follow-up |
| `/private/tmp/dopemux-pr497` | detached | Dirty: `M task-packets/TP-DMX-AIG-001.md` | `keep` | Detached worktree has uncommitted changes | Must be reconciled before any deletion |
| `/Users/hue/code/dopemux-mvp-rte-seams` | `codex/rte-seam-extraction-foundation` | Dirty: workflow file modified, test file untracked | `keep` | Active non-audited local changes present | Deletion would discard unresolved work |
| `/Users/hue/code/dopemux-mvp-worktrees/v1-runtime-proof-linkage` | `codex/v1-runtime-proof-linkage` | Untracked `.operator/`; behind `origin/main` by 242 | `archive` | Local worktree is stale and off `main`, but contains local-only material | Archive/review local-only content before cleanup |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/gracious-poitras-850e4f` | `claude/gracious-poitras-850e4f` | Untracked `.claude/brand-voice-guidelines.md`; behind `origin/main` by 19 | `archive` | Stale assistant worktree with local-only file | Local content needs review before deletion |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/rte-decompose` | `refactor/rte-decompose-snapshot` | Large dirty multi-file change set plus untracked `reporting.py` | `keep` | Active unresolved implementation work | Unsafe for cleanup in phase 1 |

### Clean but Review-Relevant Worktrees

| Worktree | Branch / State | Remote / PR relation | Classification | Reason | Blocking risk |
| --- | --- | --- | --- | --- | --- |
| `/private/tmp/dopemux-ci-pr` | `codex/ci-unit-shard-experiment` | Closed-unmerged PR `#499`; upstream present | `archive` | Branch has explicit closed-unmerged disposition; preserve until reviewer decides whether to keep experiment history | Closed-unmerged branch still mounted in a worktree |
| `/private/tmp/dopemux-pr496` | `docs/multi-agent-ingress-architecture-revision` | Merged PR `#496`; upstream present | `archive` | Worktree still mounted after merge | Remove only in follow-up packet after confirming no local-only deltas |
| `/private/tmp/dopemux-pr492` | detached at merged PR `#492` head | No branch attached | `archive` | Detached PR checkout with no local changes | Safe candidate for later cleanup, but detached state warrants explicit action |
| `/private/tmp/dopemux-pr493` | detached at merged PR `#493` head | No branch attached | `archive` | Detached PR checkout with no local changes | Same as above |
| `/private/tmp/dopemux-pr494` | detached at merged PR `#494` head | No branch attached | `archive` | Detached PR checkout with no local changes | Same as above |
| `/private/tmp/dopemux-pr495` | detached at merged PR `#495` head | No branch attached | `archive` | Detached PR checkout with no local changes | Same as above |
| `/private/tmp/dopemux-pr497b` | detached near merged PR `#497` lineage | No branch attached | `archive` | Detached temp checkout with no local changes | Detached history should be removed explicitly, not silently |
| `/Users/hue/code/dopemux-extractor-gtm` | `codex/prompts-prefix-mirror` | Upstream gone | `archive` | Out-of-scope GTM worktree still tied into this repo’s git worktree registry | Needs separate owner review |
| `/Users/hue/code/dopemux-mvp-rte-main-integration-audit-staging` | `tp/rte-full-run-hygiene-and-launch-readiness` | Merged PR `#461`; upstream gone | `archive` | Historic merged packet branch still mounted | Follow-up can remove after owner confirmation |
| `/Users/hue/code/dopemux-mvp-rte-seams-v2` | `codex/rte-seam-extraction-foundation-v2` | Upstream gone; branch merged earlier via PR `#444` | `archive` | Mounted historical branch with no observed dirty state | Follow-up can remove after review |
| `/Users/hue/code/dopemux-mvp-wt-dopecode-ast` | `codex/dopecode-ast-navigation-20260417` | Closed-unmerged PR `#471`; behind upstream by 14 | `archive` | Explicit closed-unmerged branch line still mounted | Needs disposition before delete |
| `/Users/hue/code/dopemux-mvp-wt-rte-benchmark-r1` | `codex/rte-benchmark-r1-first-campaign` | No PR evidence in sampled recent set | `unknown` | Branch purpose unresolved in phase-1 evidence | Needs owner review |
| `/Users/hue/code/dopemux-mvp-wt-rte-v5-prescan-contract-unification` | `feat/rte-v5-prescan-contract-unification` | Closed-unmerged PR `#470` | `archive` | Closed-unmerged branch still mounted cleanly | Needs disposition before delete |
| `/Users/hue/code/dopemux-mvp-wt-serena-audit` | `tp/serena-audit-runtime-io-tools` | No recent PR resolution observed | `unknown` | Branch line unresolved by available evidence | Needs owner review |
| `/Users/hue/code/dopemux-mvp-wt-serena-fix` | `tp/serena-runtime-fix` | No recent PR resolution observed | `unknown` | Branch line unresolved by available evidence | Needs owner review |
| `/Users/hue/code/dopemux-mvp-wt-serena-upstream-diff` | `tp/serena-upstream-contract-diff` | No recent PR resolution observed | `unknown` | Branch line unresolved by available evidence | Needs owner review |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/inspiring-nobel-101730` | `claude/inspiring-nobel-101730` | Tracks `origin/main`, behind 19 | `archive` | No local changes; stale assistant worktree | Remove only in follow-up |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/optimistic-mayer-6f6e75` | `claude/optimistic-mayer-6f6e75` | Tracks `origin/main`, behind 19 | `archive` | No local changes; stale assistant worktree | Remove only in follow-up |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/rte-structured-outputs-all-providers` | `feat/rte-structured-outputs-all-providers` | No recent PR evidence in sampled set | `unknown` | Clean but unresolved branch purpose | Needs owner review |
| `/Users/hue/code/dopemux-mvp/.claude/worktrees/serene-swirles-f50ab3` | `claude/serene-swirles-f50ab3` | Tracks `origin/main`, behind 30 | `archive` | No local changes; stale assistant worktree | Remove only in follow-up |
| `/Users/hue/code/dopemux-mvp/.worktrees/tp-gh-review-thread-agent` | `tp/gh-review-thread-agent` | Merged PR `#465` | `archive` | Merged branch still mounted as worktree | Follow-up can remove after review |

---

## Local Branch Ledger

This ledger is intentionally bounded to branches materially intersecting worktrees, recent PR evidence, or upstream-gone state.

| Branch | Remote / PR evidence | Recommendation | Reason | Blocking risk |
| --- | --- | --- | --- | --- |
| `codex/repo-hygiene-audit-phase1` | Local audit branch only | `keep` | Active packet branch for this phase-1 work | Current packet not complete until reviewed |
| `main` | Tracks `origin/main` | `keep` | Canonical base branch | None |
| `codex/ci-unit-shard-experiment` | Closed-unmerged PR `#499`; mounted clean worktree | `archive` | Explicit closed-unmerged experimental branch; not safe for silent deletion | Local worktree exists |
| `docs/multi-agent-ingress-architecture-revision` | Merged PR `#496`; mounted clean worktree | `archive` | Merged branch still has attached worktree | Follow-up must remove worktree first |
| `design/wave7-rte-ui-contract` | Merged PR `#495`; local branch ahead 1 / behind 14 | `merge-first` | Diverged local branch shares merged PR lineage but local/remote drift remains | Local divergence unresolved |
| `codex/pal-sse-wrapper` | Merged PR `#500` | `archive` | Recently merged branch; no destruction in phase 1 | Fresh merge; follow-up can delete after review |
| `codex/phase0` | Merged PR `#497`; local branch ahead 1 / behind 4 | `merge-first` | Local branch diverged after merged PR line | Needs explicit review of extra local commit |
| `feat/rte-prescan-first-live-hardening` | Closed-unmerged PR `#467`; duplicate local `pr/467` broken worktree | `archive` | Closed-unmerged plus duplicate branch line | Broken temp worktree blocks safe cleanup |
| `feat/rte-prescan-stage0-live-lane-proving` | Merged PR `#480`; duplicate local `pr/480` broken worktree | `archive` | Merged but temp worktree metadata is broken | Broken temp worktree blocks safe cleanup |
| `feat/rte-v5-prescan-contract-unification` | Closed-unmerged PR `#470`; mounted clean worktree | `archive` | Closed-unmerged branch still mounted | Needs explicit disposition |
| `codex/dopecode-ast-navigation-20260417` | Closed-unmerged PR `#471`; mounted clean worktree | `archive` | Closed-unmerged branch with attached worktree | Needs disposition |
| `tp/dopecode-ast-navigation` | Closed-unmerged PR `#469` | `archive` | Closed-unmerged packet branch | No safe deletion proof in phase 1 |
| `tp/dopecode-phase2-harden` | Closed-unmerged PR `#473` | `archive` | Closed-unmerged packet branch | No safe deletion proof in phase 1 |
| `tp/dopecode-phase3-decompose-policy` | Closed-unmerged PRs `#474`, `#477` | `archive` | Duplicate closed-unmerged PR line; explicit disposition required | Duplicate PR history |
| `tp/dopecode-phase4-language-approval` | Closed-unmerged PR `#476` | `archive` | Closed-unmerged packet branch | No safe deletion proof in phase 1 |
| `tp/dopecode-phase8-events-replay` | Merged PR `#481` | `archive` | Merged branch remains local | Follow-up can delete after review |
| `tp/gh-review-thread-agent` | Merged PR `#465`; mounted clean worktree | `archive` | Merged branch still mounted | Follow-up must remove worktree first |
| `tp/rte-full-run-hygiene-and-launch-readiness` | Merged PR `#461`; upstream gone; mounted clean worktree | `archive` | Historic merged branch with mounted worktree and gone upstream | Worktree cleanup needed first |
| `codex/rte-seam-extraction-foundation` | Dirty mounted worktree; no current remote evidence in recent PR slice | `keep` | Local unresolved modifications exist | Unsafe for cleanup |
| `codex/rte-seam-extraction-foundation-v2` | Upstream gone; historical merged lineage | `archive` | Historic clean worktree remains | Follow-up review required |
| `codex/v1-runtime-proof-linkage` | Tracks `origin/main`; behind 242; dirty untracked state | `archive` | Highly stale and carries local-only content | Local content must be reviewed |
| `claude/gracious-poitras-850e4f` | Tracks `origin/main`; dirty untracked file | `archive` | Assistant branch with local-only artifact | Local file review required |
| `refactor/rte-decompose-snapshot` | Dirty mounted worktree | `keep` | Large unresolved change set | Unsafe for cleanup |
| `tp/serena-audit-runtime-io-tools` | No definitive PR evidence in current slice | `unknown` | Authority unresolved | Owner review required |
| `tp/serena-runtime-fix` | No definitive PR evidence in current slice | `unknown` | Authority unresolved | Owner review required |
| `tp/serena-upstream-contract-diff` | No definitive PR evidence in current slice | `unknown` | Authority unresolved | Owner review required |

---

## Deterministic Cleanup Plan

Phase 1 issues recommendations only. No deletion or worktree removal is executed here.

### Follow-up Packet Order

1. Reconcile dirty worktrees first:
   - `/private/tmp/dopemux-pr497`
   - `/Users/hue/code/dopemux-mvp-rte-seams`
   - `/Users/hue/code/dopemux-mvp-worktrees/v1-runtime-proof-linkage`
   - `/Users/hue/code/dopemux-mvp/.claude/worktrees/gracious-poitras-850e4f`
   - `/Users/hue/code/dopemux-mvp/.claude/worktrees/rte-decompose`
2. Repair or remove broken prunable temp worktrees explicitly:
   - `/private/tmp/dopemux-pr467`
   - `/private/tmp/dopemux-pr480`
3. Resolve closed-unmerged branch lines by owner decision, not heuristic deletion:
   - `codex/ci-unit-shard-experiment`
   - `feat/rte-prescan-first-live-hardening`
   - `feat/rte-v5-prescan-contract-unification`
   - `codex/dopecode-ast-navigation-20260417`
   - `tp/dopecode-ast-navigation`
   - `tp/dopecode-phase2-harden`
   - `tp/dopecode-phase3-decompose-policy`
   - `tp/dopecode-phase4-language-approval`
4. Remove merged but still-mounted worktrees only after confirming clean state in the follow-up packet:
   - `/private/tmp/dopemux-pr496`
   - `/private/tmp/dopemux-pr492`
   - `/private/tmp/dopemux-pr493`
   - `/private/tmp/dopemux-pr494`
   - `/private/tmp/dopemux-pr495`
   - `/private/tmp/dopemux-pr497b`
   - `/Users/hue/code/dopemux-mvp-rte-main-integration-audit-staging`
   - `/Users/hue/code/dopemux-mvp-rte-seams-v2`
   - `/Users/hue/code/dopemux-mvp/.worktrees/tp-gh-review-thread-agent`
5. Handle `unknown` branches and worktrees with explicit owner review, not silent cleanup:
   - `codex/rte-benchmark-r1-first-campaign`
   - `tp/serena-audit-runtime-io-tools`
   - `tp/serena-runtime-fix`
   - `tp/serena-upstream-contract-diff`
   - `feat/rte-structured-outputs-all-providers`

### Explicit Non-Recommendations

- No branch is marked `delete-remote` in this packet.
- No worktree is marked immediately safe to remove in this packet without a follow-up execution packet.
- No unknown item was downgraded to delete/cleanup based on naming convention alone.

---

## Residual Risk

- The PR evidence set proves there are no open PRs at audit time, but absence of an open PR does not prove branch irrelevance.
- Several local branches have no recent PR evidence in the sampled set and remain `unknown`.
- The repo contains pre-existing dirty state outside this packet, so a later execution packet must re-validate current status before acting.
- `AGENTS.md` truth-doc path drift means some repo-truth documentation references are stale relative to this checkout.
