---
id: repo-remaining-work-disposition-2026-05-02
title: Repo Remaining Work Disposition Audit
type: reference
owner: codex
date: 2026-05-02
status: complete
author: '@hu3mann'
last_review: '2026-05-02'
next_review: '2026-08-01'
prelude: Phase-5 repo hygiene disposition, cleanup-safe local deletion, and recovery queue classification.
---
# Repo Remaining Work Disposition Audit

**Task packet**: `TP-DMX-REPOHYG-005`
**Parent packet**: `TP-DMX-REPOHYG-004`
**Execution branch**: `codex/repo-hygiene-remaining-disposition-20260502`
**Execution worktree**: `/Users/hue/.codex/worktrees/repo-hygiene-20260502-tp005/dopemux-mvp`
**Stacked base**: `codex/repo-hygiene-lost-work-audit-20260502`
**Recovery root**: `/Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/remaining-disposition-20260502`
**Origin main**: `af5c462747860ad8382efa72304dd18970374205`

## Gate Status

PR #561 could not be merged through the normal GitHub path. `gh pr merge 561 --squash --delete-branch` returned exit code `1` because the base branch policy prohibits the merge. The observed failing check is `review / review`, and its log reports Gemini provider `403 PERMISSION_DENIED`. No admin bypass was used. TP005 is therefore stacked on the TP004 branch.

## Cleanup Executed

Clean duplicate work was removed only after branch refs were preserved into a local bundle. No dirty worktree, stash, or remote branch was removed.

- Worktrees removed: `7`
- Local branch refs deleted: `13`
- Cleanup failures: `0`
- Preserved branch bundle: `/Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/remaining-disposition-20260502/cleanup-execution/merged-cleanup-safe-branches.bundle`

| Removed worktree |
| --- |
| /Users/hue/.codex/worktrees/4292/dopemux-mvp |
| /Users/hue/.codex/worktrees/eb8e/dopemux-mvp-wt-cockpit-pm-textual |
| /Users/hue/.codex/worktrees/eb8e/dopemux-pr-551-fix |
| /Users/hue/.codex/worktrees/eb8e/dopemux-pr-552 |
| /Users/hue/.codex/worktrees/eb8e/dopemux-pr-553 |
| /Users/hue/code/dopemux-mvp-wt-agents-copilot-specs-fresh |
| /Users/hue/code/restore-runtime-authority-verifier |


| Deleted local branch |
| --- |
| audit/rte-pre-run-hygiene-gemini-001 |
| claude/inspiring-nobel-101730 |
| codex/agents-codex-endtoend-default |
| codex/ops-mac-system-data-scrubber |
| codex/production-extraction-embeddings-hardening |
| codex/rte-prescan-progress-hud |
| extractor/prompt-governance-gtm |
| fix/restore-runtime-authority-verifier |
| work/pr-549 |
| work/pr-551 |
| work/pr-551-fix |
| work/pr-552 |
| work/pr-553 |

## Post-Cleanup Disposition Counts

**Worktrees**

| Class | Count |
| --- | --- |
| blocked | 2 |
| preserve-dirty | 20 |
| topic-pr | 3 |
| unfinished | 2 |

**Branches**

| Class | Count |
| --- | --- |
| blocked | 2 |
| preserve-dirty | 15 |
| topic-pr | 14 |
| unfinished | 14 |

**Stashes**

| Class | Count |
| --- | --- |
| merged-cleanup-safe | 2 |
| preserve-dirty | 7 |
| topic-pr | 3 |
| unfinished | 4 |

## Topic PR Candidates

These branches or stashes contain patch-unique or source/test/operator changes after a merged PR or stash capture. They are inputs for separate recovery PRs, not changes landed by this packet.

| Branch | Group | Unique commits | Unique paths | PR proof |
| --- | --- | --- | --- | --- |
| audit/rte-cost-profiles-ladders-wizard-gemini-001 | rte/dopecode | 7 | 50 | #520 MERGED |
| audit/runtime-authority-verifier-project-docs-improvement | cli/system | 1 | 4 | #547 MERGED |
| codex/pm-writes-phase1 | mixed/unknown | 3 | 13 | #512 MERGED |
| codex/rte-wizard-prescan-telemetry | rte/dopecode | 2 | 10 | #523 MERGED |
| feat/rte-cost-stabilization-v2 | rte/dopecode | 1 | 5 | #516 MERGED |
| feat/rte-intelligence-wiring | rte/dopecode | 1 | 194 | #514 MERGED |
| pr/464 | rte/dopecode | 3 | 12 | #464 MERGED |
| pr/480 | rte/dopecode | 2 | 8 | #480 MERGED |
| pr/481 | rte/dopecode | 18 | 163 | #481 MERGED |
| recover/tp1-547 | cli/system | 4 | 4 | #547 MERGED |
| tp/dopecode-phase8-events-replay | rte/dopecode | 23 | 166 | #481 MERGED |
| tp/gh-review-thread-agent | cli/system | 1 | 5 | #465 MERGED |
| work/pr-554 | cli/system | 1 | 19 | #554 MERGED |
| work/pr-554-fix | cli/system | 1 | 19 | #554 MERGED |


| Stash | Group | Files | Message |
| --- | --- | --- | --- |
| stash@{1} | rte/dopecode | 11 | stash@{2026-04-27 19:40:41 -0700}: WIP on codex/rte-wizard-prescan-telemetry: a442ed141 Changes from Codex |
| stash@{14} | rte/dopecode | 17 | stash@{2026-04-21 18:20:49 -0700}: WIP on tp/dopecode-phase8-events-replay: 4320ef814 fix(dopecode): fail-close receipt loading on unsupported event_type and empty workspace_id |
| stash@{15} | rte/dopecode | 62 | stash@{2026-04-17 18:28:47 -0700}: On tp/serena-v2-truth: prescan-hardening-work |

## Unfinished / Superseded Work

| Branch | Group | Unique commits | Unique paths | PR state | Reason |
| --- | --- | --- | --- | --- | --- |
| codex/dopecode-ast-navigation-20260417 | rte/dopecode | 1 | 7 | #471 CLOSED | closed/unmerged PR has patch-unique commits |
| codex/infra-compose-uv-db-init | rte/dopecode | 6 | 41 | #436 CLOSED | closed/unmerged PR has patch-unique commits |
| codex/pm-writes-phase1-local-pre-remote-sync | mixed/unknown | 2 | 12 | - | no merged PR proof for patch-unique commits |
| codex/restore-canonical-compose | cli/system | 1 | 10 | - | no merged PR proof for patch-unique commits |
| pr/467 | rte/dopecode | 2 | 11 | #467 CLOSED | closed/unmerged PR has patch-unique commits |
| prmerge/539 | cli/system | 2 | 8 | - | no merged PR proof for patch-unique commits |
| repo-precommit-debt-cleanup | rte/dopecode | 6 | 29 | - | no merged PR proof for patch-unique commits |
| tp/dopecode-ast-navigation | rte/dopecode | 1 | 7 | #469 CLOSED | closed/unmerged PR has patch-unique commits |
| tp/dopecode-ast-navigation-phase1 | rte/dopecode | 3 | 16 | - | no merged PR proof for patch-unique commits |
| tp/dopecode-phase2-harden | rte/dopecode | 7 | 34 | #473 CLOSED | closed/unmerged PR has patch-unique commits |
| tp/dopecode-phase3-decompose-policy | rte/dopecode | 9 | 41 | #474 CLOSED | closed/unmerged PR has patch-unique commits |
| tp/dopecode-phase4-language-approval | rte/dopecode | 20 | 50 | #476 CLOSED | closed/unmerged PR has patch-unique commits |
| tp/serena-tool-surface-audit | rte/dopecode | 3 | 16 | #468 CLOSED | closed/unmerged PR has patch-unique commits |
| tp/serena-v2-truth | rte/dopecode | 1 | 10 | - | no merged PR proof for patch-unique commits |

## Dirty Or Blocked Survivors

Dirty worktrees remain in place. Several dirty branches have zero patch-unique commits and are probably cleanup candidates after their dirty deltas are reviewed, but this packet deliberately did not remove them.

| Class | Worktree | Branch/state | Dirty | Reason |
| --- | --- | --- | --- | --- |
| preserve-dirty | /Users/hue/code/dopemux-mvp | main | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/11a0/dopemux-mvp | DETACHED | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/22c5/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/38c4/dopemux-mvp | codex/remove-stale-root-next-surface | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/558a/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | True | dirty worktree retained |
| blocked | /Users/hue/.codex/worktrees/7f12/dopemux-mvp | DETACHED | False | operator thread checkout intentionally retained |
| preserve-dirty | /Users/hue/.codex/worktrees/7f48/dopemux-mvp-wt-cockpit-pm-textual | codex/add-audit-authority-files | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/8444/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/b840/dopemux-mvp-wt-cockpit-pm-textual | codex/restore-system-data-command | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/b8c4/dopemux-mvp | codex/installer-smoke-python-deps | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/e252/dopemux-mvp-wt-cockpit-pm-textual | codex/dopemux-cli-audit-remediation | True | dirty worktree retained |
| preserve-dirty | /Users/hue/.codex/worktrees/e270/dopemux-mvp-wt-cockpit-pm-textual | codex/freeflow-strict-router | True | dirty worktree retained |
| blocked | /Users/hue/.codex/worktrees/repo-hygiene-20260502-tp005/dopemux-mvp | codex/repo-hygiene-remaining-disposition-20260502 | False | active TP005 execution worktree |
| preserve-dirty | /Users/hue/code/ARCH-5.5-PRO | DETACHED | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-agents-copilot-specs | agents/dopemux-copilot-agent-specs | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-cockpit-design-system | codex/cockpit-design-system | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-cockpit-pm-textual | test/pm-authority-ports | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-mcp-audit-hardening | codex/mcp-audit-hardening | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-mcp-customization-dr-data | research/dmx-mcp-customization-dr-data | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-195535 | audit/runtime-authority-verifier-20260430-195535 | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-201805 | audit/runtime-authority-verifier-20260430-201805 | True | dirty worktree retained |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-tui-hardening | codex/tui-runtime-unknown-hardening | True | dirty worktree retained |

## Stash Disposition

| Class | Stash | Files | Group | Reason |
| --- | --- | --- | --- | --- |
| preserve-dirty | stash@{0} | 1 | docs/audit | AGENTS.md-only stash retained |
| topic-pr | stash@{1} | 11 | rte/dopecode | source/test/operator stash requires recovery branch review |
| preserve-dirty | stash@{2} | 1 | docs/audit | AGENTS.md-only stash retained |
| preserve-dirty | stash@{3} | 1 | docs/audit | AGENTS.md-only stash retained |
| preserve-dirty | stash@{4} | 1 | docs/audit | AGENTS.md-only stash retained |
| unfinished | stash@{5} | 18 | rte/dopecode | docs/proof or mixed stash requires manual disposition |
| preserve-dirty | stash@{6} | 1 | docs/audit | AGENTS.md-only stash retained |
| preserve-dirty | stash@{7} | 1 | docs/audit | AGENTS.md-only stash retained |
| preserve-dirty | stash@{8} | 1 | docs/audit | AGENTS.md-only stash retained |
| unfinished | stash@{9} | 6 | ui/cockpit | docs/proof or mixed stash requires manual disposition |
| merged-cleanup-safe | stash@{10} | 0 | mixed/unknown | zero visible files; retained until explicit stash-drop approval |
| merged-cleanup-safe | stash@{11} | 0 | mixed/unknown | zero visible files; retained until explicit stash-drop approval |
| unfinished | stash@{12} | 5 | ui/cockpit | docs/proof or mixed stash requires manual disposition |
| unfinished | stash@{13} | 6 | cli/system | docs/proof or mixed stash requires manual disposition |
| topic-pr | stash@{14} | 17 | rte/dopecode | source/test/operator stash requires recovery branch review |
| topic-pr | stash@{15} | 62 | rte/dopecode | source/test/operator stash requires recovery branch review |

## Next Recovery Order

- First: CLI/system candidates with small unique path sets, especially `work/pr-554`, `work/pr-554-fix`, `recover/tp1-547`, and `tp/gh-review-thread-agent`.
- Second: RTE/dopecode candidates with merged PR proof, starting with narrower branches before the large `pr/481` / `tp/dopecode-phase8-events-replay` pair.
- Third: dirty branches whose committed deltas are already patch-equivalent, after their dirty worktree snapshots are reviewed.
- Stashes remain retained until an explicit stash-drop packet records object IDs and either applies or rejects their patches.
