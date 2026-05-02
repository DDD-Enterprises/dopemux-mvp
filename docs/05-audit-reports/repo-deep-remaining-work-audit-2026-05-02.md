---
id: repo-deep-remaining-work-audit-2026-05-02
title: Repo Deep Remaining Work Audit
type: reference
owner: codex
date: 2026-05-02
status: complete
author: '@hu3mann'
last_review: '2026-05-02'
next_review: '2026-08-01'
prelude: Phase-6 repo hygiene deep audit and recovery queue classification.
---
# Repo Deep Remaining Work Audit

**Task packet**: `TP-DMX-REPOHYG-006`
**Parent packet**: `TP-DMX-REPOHYG-005`
**Execution branch**: `codex/repo-hygiene-deep-audit-20260502`
**Execution worktree**: `/Users/hue/.codex/worktrees/repo-hygiene-20260502-tp006/dopemux-mvp`
**Stacked base**: `origin/codex/repo-hygiene-remaining-disposition-20260502`
**Recovery root**: `/Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/deep-audit-20260502`
**Current origin/main**: `4959a089f1ba456faee86649ce88215402f9bc65`
**Local main**: `af5c462747860ad8382efa72304dd18970374205`

## Scope and Policy

TP006 is a docs/proof-only deep audit. It does not delete branches, worktrees, remote refs, or stashes, and it does not recover runtime code. Dirty worktree diffs, branch evidence, and stash patches were written to the local recovery root for later subsystem PRs.

## Base Drift and PR Gate

`origin/main` advanced after TP005. PR #561 is now behind `main`, and PR #563 remains stacked on #561. The known failing gate is the external Gemini `review / review` provider path; local TP005 validation had passed before this packet. TP006 therefore stays stacked and compares every candidate against current `origin/main`.

## Disposition Counts

The worktree total is `28` because the fresh TP006 execution worktree is included and classified as `blocked`; the pre-existing remaining worktree registry count was `27`.

**Worktrees**

| Class | Count |
| --- | --- |
| blocked | 3 |
| cleanup-safe-next | 1 |
| dirty-local | 10 |
| operator-local-artifact | 10 |
| topic-pr-ready-review | 3 |
| unfinished-abandoned | 1 |

**Branches**

| Class | Count |
| --- | --- |
| blocked | 4 |
| cleanup-safe-next | 1 |
| dirty-local | 14 |
| recover-partial | 5 |
| topic-pr-ready-review | 14 |
| unfinished-abandoned | 8 |

**Stashes**

| Class | Count |
| --- | --- |
| cleanup-safe-next | 2 |
| operator-local-artifact | 7 |
| recover-partial | 3 |
| topic-pr-ready-review | 4 |

## Recovery Queue

| Priority | Kind | Name | Class | Subsystem | Size | Candidate branch |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | branch | work/pr-554 | topic-pr-ready-review | cli/system | 1 | codex/recover-cli-system-20260502-work-pr-554 |
| 2 | branch | work/pr-554-fix | topic-pr-ready-review | cli/system | 1 | codex/recover-cli-system-20260502-work-pr-554-fix |
| 3 | branch | recover/tp1-547 | topic-pr-ready-review | cli/system | 4 | codex/recover-cli-system-20260502-recover-tp1-547 |
| 4 | branch | tp/gh-review-thread-agent | topic-pr-ready-review | cli/system | 1 | codex/recover-cli-system-20260502-tp-gh-review-thread-agent |
| 5 | branch | feat/rte-cost-stabilization-v2 | topic-pr-ready-review | rte/dopecode | 1 | codex/recover-rte-dopecode-20260502-feat-rte-cost-stabilization-v2 |
| 6 | branch | pr/480 | topic-pr-ready-review | rte/dopecode | 2 | codex/recover-rte-dopecode-20260502-pr-480 |
| 7 | branch | codex/rte-wizard-prescan-telemetry | topic-pr-ready-review | rte/dopecode | 2 | codex/recover-rte-dopecode-20260502-codex-rte-wizard-prescan-telemetry |
| 8 | branch | pr/464 | topic-pr-ready-review | rte/dopecode | 3 | codex/recover-rte-dopecode-20260502-pr-464 |
| 9 | branch | pr/481 | topic-pr-ready-review | rte/dopecode | 18 | codex/recover-rte-dopecode-20260502-pr-481 |
| 10 | branch | tp/dopecode-phase8-events-replay | topic-pr-ready-review | rte/dopecode | 23 | codex/recover-rte-dopecode-20260502-tp-dopecode-phase8-events-replay |
| 11 | branch | feat/rte-intelligence-wiring | topic-pr-ready-review | rte/dopecode | 1 | codex/recover-rte-dopecode-20260502-feat-rte-intelligence-wiring |
| 12 | stash | stash@{1} | topic-pr-ready-review | rte/dopecode | 11 | codex/recover-rte-dopecode-20260502-stash1 |
| 13 | stash | stash@{13} | topic-pr-ready-review | cli/system | 6 | codex/recover-cli-system-20260502-stash13 |
| 14 | stash | stash@{14} | topic-pr-ready-review | rte/dopecode | 17 | codex/recover-rte-dopecode-20260502-stash14 |
| 15 | stash | stash@{15} | topic-pr-ready-review | rte/dopecode | 62 | codex/recover-rte-dopecode-20260502-stash15 |
| 16 | worktree | /Users/hue/.codex/worktrees/558a/dopemux-mvp-wt-cockpit-pm-textual | dirty-local | mixed/unknown | 4 | - |
| 17 | worktree | /Users/hue/.codex/worktrees/7f48/dopemux-mvp-wt-cockpit-pm-textual | dirty-local | mixed/unknown | 3 | - |
| 18 | worktree | /Users/hue/.codex/worktrees/e252/dopemux-mvp-wt-cockpit-pm-textual | dirty-local | cli/system | 9 | - |
| 19 | worktree | /Users/hue/code/dopemux-mvp-wt-agents-copilot-specs | dirty-local | docs/audit | 2 | - |
| 20 | worktree | /Users/hue/code/dopemux-mvp-wt-cockpit-design-system | dirty-local | cli/system | 24 | - |
| 21 | worktree | /Users/hue/code/dopemux-mvp-wt-cockpit-pm-textual | dirty-local | cli/system | 48 | - |
| 22 | worktree | /Users/hue/code/dopemux-mvp-wt-mcp-audit-hardening | dirty-local | infra/services | 17 | - |
| 23 | worktree | /Users/hue/code/dopemux-mvp-wt-mcp-customization-dr-data | dirty-local | docs/audit | 7 | - |
| 24 | worktree | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-201805 | dirty-local | cli/system | 5 | - |
| 25 | worktree | /Users/hue/code/dopemux-mvp-wt-tui-hardening | dirty-local | ui/cockpit | 3 | - |
| 26 | branch | audit/rte-cost-profiles-ladders-wizard-gemini-001 | topic-pr-ready-review | rte/dopecode | 7 | codex/recover-rte-dopecode-20260502-audit-rte-cost-profiles-ladders-wiza |
| 27 | branch | audit/runtime-authority-verifier-project-docs-improvement | topic-pr-ready-review | cli/system | 1 | codex/recover-cli-system-20260502-audit-runtime-authority-verifier-pro |
| 28 | branch | codex/pm-writes-phase1 | topic-pr-ready-review | mixed/unknown | 3 | codex/recover-mixed-20260502-codex-pm-writes-phase1 |
| 29 | branch | codex/pm-writes-phase1-local-pre-remote-sync | recover-partial | mixed/unknown | 2 | codex/recover-mixed-20260502-codex-pm-writes-phase1-local-pre-rem |
| 30 | branch | prmerge/539 | recover-partial | cli/system | 2 | codex/recover-cli-system-20260502-prmerge-539 |
| 31 | branch | repo-precommit-debt-cleanup | recover-partial | rte/dopecode | 6 | codex/recover-rte-dopecode-20260502-repo-precommit-debt-cleanup |
| 32 | branch | tp/dopecode-ast-navigation-phase1 | recover-partial | rte/dopecode | 3 | codex/recover-rte-dopecode-20260502-tp-dopecode-ast-navigation-phase1 |
| 33 | branch | tp/serena-v2-truth | recover-partial | rte/dopecode | 1 | codex/recover-rte-dopecode-20260502-tp-serena-v2-truth |

## Topic PR Ready Branches

| Branch | Subsystem | Unique commits | Unique paths | PR proof | Candidate recovery branch |
| --- | --- | --- | --- | --- | --- |
| audit/rte-cost-profiles-ladders-wizard-gemini-001 | rte/dopecode | 7 | 50 | #520 MERGED | codex/recover-rte-dopecode-20260502-audit-rte-cost-profiles-ladders-wiza |
| audit/runtime-authority-verifier-project-docs-improvement | cli/system | 1 | 4 | #547 MERGED | codex/recover-cli-system-20260502-audit-runtime-authority-verifier-pro |
| codex/pm-writes-phase1 | mixed/unknown | 3 | 13 | #512 MERGED | codex/recover-mixed-20260502-codex-pm-writes-phase1 |
| codex/rte-wizard-prescan-telemetry | rte/dopecode | 2 | 10 | #523 MERGED | codex/recover-rte-dopecode-20260502-codex-rte-wizard-prescan-telemetry |
| feat/rte-cost-stabilization-v2 | rte/dopecode | 1 | 5 | #516 MERGED | codex/recover-rte-dopecode-20260502-feat-rte-cost-stabilization-v2 |
| feat/rte-intelligence-wiring | rte/dopecode | 1 | 194 | #514 MERGED | codex/recover-rte-dopecode-20260502-feat-rte-intelligence-wiring |
| pr/464 | rte/dopecode | 3 | 12 | #464 MERGED | codex/recover-rte-dopecode-20260502-pr-464 |
| pr/480 | rte/dopecode | 2 | 8 | #480 MERGED | codex/recover-rte-dopecode-20260502-pr-480 |
| pr/481 | rte/dopecode | 18 | 163 | #481 MERGED | codex/recover-rte-dopecode-20260502-pr-481 |
| recover/tp1-547 | cli/system | 4 | 4 | #547 MERGED | codex/recover-cli-system-20260502-recover-tp1-547 |
| tp/dopecode-phase8-events-replay | rte/dopecode | 23 | 166 | #481 MERGED | codex/recover-rte-dopecode-20260502-tp-dopecode-phase8-events-replay |
| tp/gh-review-thread-agent | cli/system | 1 | 5 | #465 MERGED | codex/recover-cli-system-20260502-tp-gh-review-thread-agent |
| work/pr-554 | cli/system | 1 | 19 | #554 MERGED | codex/recover-cli-system-20260502-work-pr-554 |
| work/pr-554-fix | cli/system | 1 | 19 | #554 MERGED | codex/recover-cli-system-20260502-work-pr-554-fix |

## Recover Partial Branches

| Branch | Subsystem | Unique commits | Unique paths | PR proof | Reason |
| --- | --- | --- | --- | --- | --- |
| codex/pm-writes-phase1-local-pre-remote-sync | mixed/unknown | 2 | 12 | - | patch-unique commits exist without merged PR proof; needs manual partial recovery decision |
| prmerge/539 | cli/system | 2 | 8 | - | patch-unique commits exist without merged PR proof; needs manual partial recovery decision |
| repo-precommit-debt-cleanup | rte/dopecode | 6 | 29 | - | patch-unique commits exist without merged PR proof; needs manual partial recovery decision |
| tp/dopecode-ast-navigation-phase1 | rte/dopecode | 3 | 16 | - | patch-unique commits exist without merged PR proof; needs manual partial recovery decision |
| tp/serena-v2-truth | rte/dopecode | 1 | 10 | - | patch-unique commits exist without merged PR proof; needs manual partial recovery decision |

## Unfinished or Abandoned Branches

| Branch | Subsystem | Unique commits | Unique paths | PR proof | Reason |
| --- | --- | --- | --- | --- | --- |
| codex/dopecode-ast-navigation-20260417 | rte/dopecode | 1 | 7 | #471 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| codex/infra-compose-uv-db-init | rte/dopecode | 6 | 41 | #436 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| pr/467 | rte/dopecode | 2 | 11 | #467 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| tp/dopecode-ast-navigation | rte/dopecode | 1 | 7 | #469 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| tp/dopecode-phase2-harden | rte/dopecode | 7 | 34 | #473 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| tp/dopecode-phase3-decompose-policy | rte/dopecode | 9 | 41 | #474 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| tp/dopecode-phase4-language-approval | rte/dopecode | 20 | 50 | #476 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |
| tp/serena-tool-surface-audit | rte/dopecode | 3 | 16 | #468 CLOSED | closed/unmerged PR or superseded branch with patch-unique commits |

## Dirty Local Worktrees

| Class | Worktree | Branch/state | Subsystem | Dirty paths | Untracked | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| operator-local-artifact | /Users/hue/code/dopemux-mvp | main | docs/audit | 3 | 2 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| operator-local-artifact | /Users/hue/.codex/worktrees/11a0/dopemux-mvp | DETACHED | docs/audit | 20 | 19 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| operator-local-artifact | /Users/hue/.codex/worktrees/22c5/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | docs/audit | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| operator-local-artifact | /Users/hue/.codex/worktrees/38c4/dopemux-mvp | codex/remove-stale-root-next-surface | docs/audit | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| dirty-local | /Users/hue/.codex/worktrees/558a/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | mixed/unknown | 4 | 0 | dirty tracked or untracked content includes docs/source/test/operator files |
| dirty-local | /Users/hue/.codex/worktrees/7f48/dopemux-mvp-wt-cockpit-pm-textual | codex/add-audit-authority-files | mixed/unknown | 3 | 1 | dirty tracked or untracked content includes docs/source/test/operator files |
| operator-local-artifact | /Users/hue/.codex/worktrees/8444/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | docs/audit | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| operator-local-artifact | /Users/hue/.codex/worktrees/b840/dopemux-mvp-wt-cockpit-pm-textual | codex/restore-system-data-command | cli/system | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| operator-local-artifact | /Users/hue/.codex/worktrees/b8c4/dopemux-mvp | codex/installer-smoke-python-deps | cli/system | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| dirty-local | /Users/hue/.codex/worktrees/e252/dopemux-mvp-wt-cockpit-pm-textual | codex/dopemux-cli-audit-remediation | cli/system | 9 | 4 | dirty tracked or untracked content includes docs/source/test/operator files |
| operator-local-artifact | /Users/hue/.codex/worktrees/e270/dopemux-mvp-wt-cockpit-pm-textual | codex/freeflow-strict-router | cli/system | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| operator-local-artifact | /Users/hue/code/ARCH-5.5-PRO | DETACHED | mixed/unknown | 2 | 1 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-agents-copilot-specs | agents/dopemux-copilot-agent-specs | docs/audit | 2 | 1 | dirty tracked or untracked content includes docs/source/test/operator files |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-cockpit-design-system | codex/cockpit-design-system | cli/system | 24 | 11 | dirty tracked or untracked content includes docs/source/test/operator files |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-cockpit-pm-textual | test/pm-authority-ports | cli/system | 48 | 44 | dirty tracked or untracked content includes docs/source/test/operator files |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-mcp-audit-hardening | codex/mcp-audit-hardening | infra/services | 17 | 10 | dirty tracked or untracked content includes docs/source/test/operator files |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-mcp-customization-dr-data | research/dmx-mcp-customization-dr-data | docs/audit | 7 | 1 | dirty tracked or untracked content includes docs/source/test/operator files |
| operator-local-artifact | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-195535 | audit/runtime-authority-verifier-20260430-195535 | docs/audit | 1 | 0 | dirty state is local instruction/generated artifact only; cleanup requires explicit operator approval |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-201805 | audit/runtime-authority-verifier-20260430-201805 | cli/system | 5 | 0 | dirty tracked or untracked content includes docs/source/test/operator files |
| dirty-local | /Users/hue/code/dopemux-mvp-wt-tui-hardening | codex/tui-runtime-unknown-hardening | ui/cockpit | 3 | 3 | dirty tracked or untracked content includes docs/source/test/operator files |

## Stash Disposition

| Class | Stash | Object | Subsystem | Files | Branch hint | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| operator-local-artifact | stash@{0} | 15de39d769b2 | docs/audit | 1 | main | AGENTS.md-only stash retained as operator-local instruction surface |
| topic-pr-ready-review | stash@{1} | 8dce51ff197f | rte/dopecode | 11 | codex/rte-wizard-prescan-telemetry | stash contains source/test/operator files requiring recovery branch review |
| operator-local-artifact | stash@{2} | 9eefe8bfcd57 | rte/dopecode | 1 | codex/rte-prescan-progress-hud | AGENTS.md-only stash retained as operator-local instruction surface |
| operator-local-artifact | stash@{3} | d02a81793565 | rte/dopecode | 1 | audit/rte-cost-profiles-ladders-wizard-gemini-001 | AGENTS.md-only stash retained as operator-local instruction surface |
| operator-local-artifact | stash@{4} | 6c9ad669d473 | rte/dopecode | 1 | audit/rte-cost-profiles-ladders-wizard-gemini-001 | AGENTS.md-only stash retained as operator-local instruction surface |
| recover-partial | stash@{5} | fc2a3b4c8a8a | rte/dopecode | 18 | audit/rte-pre-run-hygiene-gemini-001 | stash contains docs/proof/task-packet changes requiring manual recovery decision |
| operator-local-artifact | stash@{6} | 21e7fce76072 | rte/dopecode | 1 | audit/rte-pre-run-hygiene-gemini-001 | AGENTS.md-only stash retained as operator-local instruction surface |
| operator-local-artifact | stash@{7} | f1527ae23c15 | rte/dopecode | 1 | audit/rte-pre-run-hygiene-gemini-001 | AGENTS.md-only stash retained as operator-local instruction surface |
| operator-local-artifact | stash@{8} | d1c2b3e08245 | rte/dopecode | 1 | feat/rte-cost-stabilization-v2 | AGENTS.md-only stash retained as operator-local instruction surface |
| recover-partial | stash@{9} | 957cec606b3e | ui/cockpit | 6 | main | stash contains docs/proof/task-packet changes requiring manual recovery decision |
| cleanup-safe-next | stash@{10} | 4a63bece58ce | mixed/unknown | 0 | claude/gracious-poitras-850e4f | stash has zero visible files; eligible only for explicit stash-drop follow-up after object ID proof |
| cleanup-safe-next | stash@{11} | 3ef0715d6330 | mixed/unknown | 0 | codex/v1-runtime-proof-linkage | stash has zero visible files; eligible only for explicit stash-drop follow-up after object ID proof |
| recover-partial | stash@{12} | 879592566819 | ui/cockpit | 5 | codex/truth-doc-placement | stash contains docs/proof/task-packet changes requiring manual recovery decision |
| topic-pr-ready-review | stash@{13} | 2ab1207b74c8 | cli/system | 6 | main | stash contains source/test/operator files requiring recovery branch review |
| topic-pr-ready-review | stash@{14} | e59bb13f2c17 | rte/dopecode | 17 | tp/dopecode-phase8-events-replay | stash contains source/test/operator files requiring recovery branch review |
| topic-pr-ready-review | stash@{15} | e5c5cdbd7acd | rte/dopecode | 62 | tp/serena-v2-truth | stash contains source/test/operator files requiring recovery branch review |

## Cleanup Follow-Up

- Cleanup-safe branches: `1` (codex/restore-canonical-compose)
- Cleanup-safe worktrees: `1`
- Cleanup-safe stashes: `2`
- Operator-local artifact items: `17`

No cleanup action is authorized by this packet; these are follow-up inputs only.

## Required Follow-Up Order

1. Recover CLI/system small candidates: `work/pr-554`, `work/pr-554-fix`, `recover/tp1-547`, `tp/gh-review-thread-agent`.
2. Recover RTE/dopecode small candidates: `feat/rte-cost-stabilization-v2`, `pr/480`, `codex/rte-wizard-prescan-telemetry`, `pr/464`.
3. Review large RTE/dopecode candidates and source-bearing stashes.
4. Review dirty worktrees with source/test changes before any deletion.
5. Run a cleanup-only packet for `codex/restore-canonical-compose`, AGENTS/out-only artifacts, and zero-visible-file stashes after explicit proof.
