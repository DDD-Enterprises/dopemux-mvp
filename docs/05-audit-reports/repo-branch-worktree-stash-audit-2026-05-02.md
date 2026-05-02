---
id: repo-branch-worktree-stash-audit-2026-05-02
title: Repo Branch, Worktree, and Stash Lost-Work Audit
type: reference
owner: codex
date: 2026-05-02
status: complete
author: '@hu3mann'
last_review: '2026-05-02'
next_review: '2026-08-01'
prelude: Phase-4 repo hygiene audit, preservation pass, and conservative cleanup execution.
---
# Repo Branch, Worktree, and Stash Lost-Work Audit

**Task packet**: `TP-DMX-REPOHYG-004`
**Parent packet**: `TP-DMX-REPOHYG-003`
**Execution branch**: `codex/repo-hygiene-lost-work-audit-20260502`
**Execution worktree**: `/Users/hue/.codex/worktrees/repo-hygiene-20260502/dopemux-mvp`
**Recovery root**: `/Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502`
**Base**: `origin/main` at `af5c462747860ad8382efa72304dd18970374205`

---

## Scope and Policy

This phase extended the prior repo-hygiene packets to include local branches, worktrees, remote PR heads, reflogs, and all stashes. The cleanup posture was conservative:

- preserve dirty worktrees and all stashes before cleanup;
- delete only local worktree metadata, clean worktrees, and local branches with graph proof;
- do not delete remote branches;
- do not open topic recovery PRs without file-level verification of unique work.

No runtime, service, schema, API, or production config behavior changed in this packet.

---

## Authority Refresh

Observed directly during execution:

- `origin/main`, local `main`, and the execution worktree started at `af5c462747860ad8382efa72304dd18970374205`.
- `gh pr list --state open` returned no open PRs during planning; the execution proof sampled `500` PR records.
- `42` worktree entries, `68` local branches, `131` remote refs, `16` stashes, and `1117` reflog entries were captured.
- Raw command output and large recovery artifacts were written outside the repo under `/Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502`.

Classification after preserving the original thread checkout:

- Worktrees: `content-audit`: 10, `delete-safe`: 10, `keep`: 2, `preserve-dirty`: 20
- Branches: `content-audit`: 40, `delete-safe`: 12, `keep`: 2, `preserve-dirty`: 14
- Stashes: `stash-recovery`: 16

---

## Preservation Results

Dirty worktrees, branch deltas, and stash patches were preserved before cleanup. Recovery artifacts include status files, binary patches, untracked-file archives, branch diff bundles where applicable, stash patches, raw Git/GitHub output, and the machine-readable local ledger.

Local recovery files are intentionally not committed because they include large generated archives and potentially operator-local work.

---

## Cleanup Executed

Cleanup commands run: `14`. Failures: `0`.

- Pruned missing worktree metadata entries: `9`
- Removed clean duplicate worktrees: `1`
- Deleted local merged branch refs with `git branch -d`: `12`
- Dropped stashes: `0`
- Deleted remote branches: `0`

Removed worktree:

| Path |
| --- |
| /Users/hue/.codex/worktrees/8972/dopemux-mvp-wt-cockpit-pm-textual |

Deleted local branches:

| Branch |
| --- |
| audit/gemini-rte-deep-pal |
| audit/rte-deep-audit-gemini-007 |
| claude/admiring-jepsen-0715aa |
| claude/flamboyant-ardinghelli-9ad2ba |
| claude/jovial-hellman-c3848d |
| claude/optimistic-torvalds-3158d6 |
| codex/chatgpt-upload-validation |
| codex/cockpit-pm-textual |
| codex/rte-canonical-operator-entrypoint |
| feat/rte-prescan-grok-optimization |
| global-ci-fix-407841f2 |
| prmerge/20260423_170024-514 |

Cleanup command ledger:

| Kind | Exit | Command | Output sample |
| --- | --- | --- | --- |
| worktree-prune | 0 | git worktree prune --verbose --expire now | Removing worktrees/dopemux-pr-540-mergefix: gitdir file points to non-existent location<br>Removing worktrees/dopemux-pr-541-mergefix: gitdir file points to non-existent location<br>Removing worktrees/dopemux-mvp-phase1-serena |
| worktree-remove | 0 | git worktree remove /Users/hue/.codex/worktrees/8972/dopemux-mvp-wt-cockpit-pm-textual |  |
| branch-delete | 0 | git branch -d audit/gemini-rte-deep-pal | Deleted branch audit/gemini-rte-deep-pal (was 46ea176de). |
| branch-delete | 0 | git branch -d audit/rte-deep-audit-gemini-007 | Deleted branch audit/rte-deep-audit-gemini-007 (was a080c8975). |
| branch-delete | 0 | git branch -d claude/admiring-jepsen-0715aa | Deleted branch claude/admiring-jepsen-0715aa (was a1ca9131f). |
| branch-delete | 0 | git branch -d claude/flamboyant-ardinghelli-9ad2ba | Deleted branch claude/flamboyant-ardinghelli-9ad2ba (was 8765535a1). |
| branch-delete | 0 | git branch -d claude/jovial-hellman-c3848d | Deleted branch claude/jovial-hellman-c3848d (was a1ca9131f). |
| branch-delete | 0 | git branch -d claude/optimistic-torvalds-3158d6 | Deleted branch claude/optimistic-torvalds-3158d6 (was b33cfc69f). |
| branch-delete | 0 | git branch -d codex/chatgpt-upload-validation | Deleted branch codex/chatgpt-upload-validation (was 9ce682fd0). |
| branch-delete | 0 | git branch -d codex/cockpit-pm-textual | Deleted branch codex/cockpit-pm-textual (was 9ce682fd0). |
| branch-delete | 0 | git branch -d codex/rte-canonical-operator-entrypoint | Deleted branch codex/rte-canonical-operator-entrypoint (was 060c93db8). |
| branch-delete | 0 | git branch -d feat/rte-prescan-grok-optimization | Deleted branch feat/rte-prescan-grok-optimization (was a080c8975). |
| branch-delete | 0 | git branch -d global-ci-fix-407841f2 | Deleted branch global-ci-fix-407841f2 (was 0be3cc82c). |
| branch-delete | 0 | git branch -d prmerge/20260423_170024-514 | Deleted branch prmerge/20260423_170024-514 (was f6a4e8e91). |

---

## Topic Recovery Candidates

No topic recovery PR was opened in this packet because the candidate set still needs file-level review to distinguish lost work from intentional supersession or later rewrites.

| Branch | Class | Unique commits | Patch-unique commits | Diff files | Next action |
| --- | --- | --- | --- | --- | --- |
| agents/dopemux-copilot-agent-specs | preserve-dirty | 1 | 0 | 213 | file-level review before topic recovery PR |
| audit/rte-cost-profiles-ladders-wizard-gemini-001 | content-audit | 9 | 7 | 283 | file-level review before topic recovery PR |
| audit/rte-pre-run-hygiene-gemini-001 | content-audit | 1 | 0 | 305 | file-level review before topic recovery PR |
| audit/runtime-authority-verifier-project-docs-improvement | content-audit | 1 | 1 | 211 | file-level review before topic recovery PR |
| claude/inspiring-nobel-101730 | content-audit | 1 | 0 | 334 | file-level review before topic recovery PR |
| codex/add-audit-authority-files | preserve-dirty | 1 | 0 | 171 | file-level review before topic recovery PR |
| codex/agents-codex-endtoend-default | content-audit | 1 | 0 | 210 | file-level review before topic recovery PR |
| codex/cockpit-design-system | preserve-dirty | 6 | 1 | 243 | file-level review before topic recovery PR |
| codex/dopecode-ast-navigation-20260417 | content-audit | 1 | 1 | 655 | file-level review before topic recovery PR |
| codex/dopemux-cli-audit-remediation | preserve-dirty | 1 | 1 | 180 | file-level review before topic recovery PR |
| codex/freeflow-strict-router | preserve-dirty | 2 | 0 | 163 | file-level review before topic recovery PR |
| codex/infra-compose-uv-db-init | content-audit | 6 | 6 | 2092 | file-level review before topic recovery PR |
| codex/installer-smoke-python-deps | preserve-dirty | 1 | 0 | 165 | file-level review before topic recovery PR |
| codex/ops-mac-system-data-scrubber | content-audit | 1 | 0 | 153 | file-level review before topic recovery PR |
| codex/pm-writes-phase1 | content-audit | 3 | 3 | 327 | file-level review before topic recovery PR |
| codex/pm-writes-phase1-local-pre-remote-sync | content-audit | 2 | 2 | 332 | file-level review before topic recovery PR |
| codex/production-extraction-embeddings-hardening | content-audit | 5 | 0 | 31 | file-level review before topic recovery PR |
| codex/remove-stale-root-next-surface | preserve-dirty | 2 | 0 | 73 | file-level review before topic recovery PR |
| codex/rte-prescan-progress-hud | content-audit | 1 | 0 | 257 | file-level review before topic recovery PR |
| codex/rte-wizard-prescan-telemetry | content-audit | 2 | 2 | 255 | file-level review before topic recovery PR |
| codex/tui-runtime-unknown-hardening | preserve-dirty | 1 | 0 | 337 | file-level review before topic recovery PR |
| extractor/prompt-governance-gtm | content-audit | 6 | 0 | 2076 | file-level review before topic recovery PR |
| feat/rte-cost-stabilization-v2 | content-audit | 2 | 1 | 301 | file-level review before topic recovery PR |
| feat/rte-intelligence-wiring | content-audit | 1 | 1 | 491 | file-level review before topic recovery PR |
| fix/restore-runtime-authority-verifier | content-audit | 1 | 0 | 205 | file-level review before topic recovery PR |
| pr/464 | content-audit | 3 | 3 | 619 | file-level review before topic recovery PR |
| pr/467 | content-audit | 2 | 2 | 658 | file-level review before topic recovery PR |
| pr/480 | content-audit | 2 | 2 | 654 | file-level review before topic recovery PR |
| pr/481 | content-audit | 18 | 18 | 477 | file-level review before topic recovery PR |
| prmerge/539 | content-audit | 2 | 2 | 210 | file-level review before topic recovery PR |
| recover/tp1-547 | content-audit | 4 | 4 | 210 | file-level review before topic recovery PR |
| repo-precommit-debt-cleanup | content-audit | 15 | 6 | 689 | file-level review before topic recovery PR |
| research/dmx-mcp-customization-dr-data | preserve-dirty | 1 | 0 | 242 | file-level review before topic recovery PR |
| test/pm-authority-ports | preserve-dirty | 3 | 1 | 209 | file-level review before topic recovery PR |
| tp/dopecode-ast-navigation | content-audit | 1 | 1 | 655 | file-level review before topic recovery PR |
| tp/dopecode-ast-navigation-phase1 | content-audit | 3 | 3 | 654 | file-level review before topic recovery PR |
| tp/dopecode-phase2-harden | content-audit | 7 | 7 | 640 | file-level review before topic recovery PR |
| tp/dopecode-phase3-decompose-policy | content-audit | 9 | 9 | 637 | file-level review before topic recovery PR |
| tp/dopecode-phase4-language-approval | content-audit | 20 | 20 | 621 | file-level review before topic recovery PR |
| tp/dopecode-phase8-events-replay | content-audit | 23 | 23 | 473 | file-level review before topic recovery PR |
| tp/gh-review-thread-agent | content-audit | 1 | 1 | 656 | file-level review before topic recovery PR |
| tp/serena-tool-surface-audit | content-audit | 3 | 3 | 654 | file-level review before topic recovery PR |
| tp/serena-v2-truth | content-audit | 1 | 1 | 655 | file-level review before topic recovery PR |
| work/pr-549 | content-audit | 3 | 0 | 77 | file-level review before topic recovery PR |
| work/pr-551 | content-audit | 2 | 0 | 171 | file-level review before topic recovery PR |
| work/pr-551-fix | content-audit | 2 | 0 | 80 | file-level review before topic recovery PR |
| work/pr-552 | content-audit | 4 | 0 | 61 | file-level review before topic recovery PR |
| work/pr-553 | content-audit | 2 | 0 | 56 | file-level review before topic recovery PR |
| work/pr-554 | content-audit | 2 | 1 | 180 | file-level review before topic recovery PR |
| work/pr-554-fix | content-audit | 2 | 1 | 89 | file-level review before topic recovery PR |

---

## Worktree Ledger

| Class | Worktree | Branch/state | Head | Dirty | Reason |
| --- | --- | --- | --- | --- | --- |
| preserve-dirty | /Users/hue/code/dopemux-mvp | refs/heads/main | af5c46274 | yes | dirty worktree content preserved locally before any cleanup |
| delete-safe | /private/tmp/dopemux-mvp-phase1-serena-audit | DETACHED | b6147b853 | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-537 | DETACHED | e20673cf0 | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-537b | DETACHED | 4149bf2b7 | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-538 | DETACHED | e8b0e483e | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-539 | DETACHED | c5ec2f48c | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-540-mergefix | DETACHED | 735ce5e18 | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-541-mergefix | DETACHED | b33262d71 | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-542-fix | DETACHED | 4db7f16b5 | no | missing path with prunable git metadata |
| delete-safe | /private/tmp/dopemux-pr-545 | DETACHED | e75fe023c | no | missing path with prunable git metadata |
| preserve-dirty | /Users/hue/.codex/worktrees/11a0/dopemux-mvp | DETACHED | 1fdf61b45 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/22c5/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | 1fdf61b45 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/38c4/dopemux-mvp | refs/heads/codex/remove-stale-root-next-surface | d661b6e1c | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/558a/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | 3bb5464db | yes | dirty worktree content preserved locally before any cleanup |
| keep | /Users/hue/.codex/worktrees/7f12/dopemux-mvp | DETACHED | af5c46274 | no | original thread checkout intentionally preserved during cleanup despite clean ancestor state |
| preserve-dirty | /Users/hue/.codex/worktrees/7f48/dopemux-mvp-wt-cockpit-pm-textual | refs/heads/codex/add-audit-authority-files | 5ad4be889 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/8444/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | 420d40ff3 | yes | dirty worktree content preserved locally before any cleanup |
| delete-safe | /Users/hue/.codex/worktrees/8972/dopemux-mvp-wt-cockpit-pm-textual | DETACHED | af5c46274 | no | clean worktree head is ancestor of origin/main |
| preserve-dirty | /Users/hue/.codex/worktrees/b840/dopemux-mvp-wt-cockpit-pm-textual | refs/heads/codex/restore-system-data-command | 042a60bdd | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/b8c4/dopemux-mvp | refs/heads/codex/installer-smoke-python-deps | 75454e5d3 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/e252/dopemux-mvp-wt-cockpit-pm-textual | refs/heads/codex/dopemux-cli-audit-remediation | d18ddab40 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/.codex/worktrees/e270/dopemux-mvp-wt-cockpit-pm-textual | refs/heads/codex/freeflow-strict-router | 5eccaee6e | yes | dirty worktree content preserved locally before any cleanup |
| content-audit | /Users/hue/.codex/worktrees/eb8e/dopemux-mvp-wt-cockpit-pm-textual | refs/heads/work/pr-549 | 0a02ce9dc | no | clean but head is not ancestor of origin/main; requires file-level review |
| content-audit | /Users/hue/.codex/worktrees/eb8e/dopemux-pr-551-fix | refs/heads/work/pr-551-fix | 6449ea15c | no | clean but head is not ancestor of origin/main; requires file-level review |
| content-audit | /Users/hue/.codex/worktrees/eb8e/dopemux-pr-552 | refs/heads/work/pr-552 | d87160dd0 | no | clean but head is not ancestor of origin/main; requires file-level review |
| content-audit | /Users/hue/.codex/worktrees/eb8e/dopemux-pr-553 | refs/heads/work/pr-553 | 1c99c79f8 | no | clean but head is not ancestor of origin/main; requires file-level review |
| content-audit | /Users/hue/.codex/worktrees/eb8e/dopemux-pr-554-fix | refs/heads/work/pr-554-fix | 98da7f552 | no | clean but head is not ancestor of origin/main; requires file-level review |
| keep | /Users/hue/.codex/worktrees/repo-hygiene-20260502/dopemux-mvp | refs/heads/codex/repo-hygiene-lost-work-audit-20260502 | af5c46274 | no | active execution worktree |
| preserve-dirty | /Users/hue/code/ARCH-5.5-PRO | DETACHED | 5f216582c | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-agents-copilot-specs | refs/heads/agents/dopemux-copilot-agent-specs | 225477ce1 | yes | dirty worktree content preserved locally before any cleanup |
| content-audit | /Users/hue/code/dopemux-mvp-wt-agents-copilot-specs-fresh | DETACHED | 552ce36c8 | no | clean but head is not ancestor of origin/main; requires file-level review |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-cockpit-design-system | refs/heads/codex/cockpit-design-system | c836e3410 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-cockpit-pm-textual | refs/heads/test/pm-authority-ports | c90ed07c0 | yes | dirty worktree content preserved locally before any cleanup |
| content-audit | /Users/hue/code/dopemux-mvp-wt-dopecode-ast | refs/heads/codex/dopecode-ast-navigation-20260417 | 40edc271c | no | clean but head is not ancestor of origin/main; requires file-level review |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-mcp-audit-hardening | refs/heads/codex/mcp-audit-hardening | 087f99329 | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-mcp-customization-dr-data | refs/heads/research/dmx-mcp-customization-dr-data | cba686305 | yes | dirty worktree content preserved locally before any cleanup |
| content-audit | /Users/hue/code/dopemux-mvp-wt-pm-writes-phase1 | refs/heads/codex/pm-writes-phase1 | 94c508605 | no | clean but head is not ancestor of origin/main; requires file-level review |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-195535 | refs/heads/audit/runtime-authority-verifier-20260430-195535 | 5f216582c | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-runtime-authority-20260430-201805 | refs/heads/audit/runtime-authority-verifier-20260430-201805 | 5f216582c | yes | dirty worktree content preserved locally before any cleanup |
| preserve-dirty | /Users/hue/code/dopemux-mvp-wt-tui-hardening | refs/heads/codex/tui-runtime-unknown-hardening | f23c3294c | yes | dirty worktree content preserved locally before any cleanup |
| content-audit | /Users/hue/code/project-docs-improvement | refs/heads/audit/runtime-authority-verifier-project-docs-improvement | 00cb80dd9 | no | clean but head is not ancestor of origin/main; requires file-level review |
| content-audit | /Users/hue/code/restore-runtime-authority-verifier | refs/heads/fix/restore-runtime-authority-verifier | 14b60d2db | no | clean but head is not ancestor of origin/main; requires file-level review |

---

## Branch Ledger

| Class | Branch | Unique commits | Patch-unique | Patch-equivalent | Diff files | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| preserve-dirty | agents/dopemux-copilot-agent-specs | 1 | 0 | 1 | 213 | attached worktree has dirty state |
| delete-safe | audit/gemini-rte-deep-pal | 0 | 0 | 0 | 322 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | audit/rte-cost-profiles-ladders-wizard-gemini-001 | 9 | 7 | 1 | 283 | branch has commits or tree differences requiring review |
| delete-safe | audit/rte-deep-audit-gemini-007 | 0 | 0 | 0 | 310 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | audit/rte-pre-run-hygiene-gemini-001 | 1 | 0 | 1 | 305 | branch has commits or tree differences requiring review |
| preserve-dirty | audit/runtime-authority-verifier-20260430-195535 | 0 | 0 | 0 | 211 | attached worktree has dirty state |
| preserve-dirty | audit/runtime-authority-verifier-20260430-201805 | 0 | 0 | 0 | 211 | attached worktree has dirty state |
| content-audit | audit/runtime-authority-verifier-project-docs-improvement | 1 | 1 | 0 | 211 | branch has commits or tree differences requiring review |
| delete-safe | claude/admiring-jepsen-0715aa | 0 | 0 | 0 | 273 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| delete-safe | claude/flamboyant-ardinghelli-9ad2ba | 0 | 0 | 0 | 25 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | claude/inspiring-nobel-101730 | 1 | 0 | 1 | 334 | branch has commits or tree differences requiring review |
| delete-safe | claude/jovial-hellman-c3848d | 0 | 0 | 0 | 273 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| delete-safe | claude/optimistic-torvalds-3158d6 | 0 | 0 | 0 | 257 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| preserve-dirty | codex/add-audit-authority-files | 1 | 0 | 1 | 171 | attached worktree has dirty state |
| content-audit | codex/agents-codex-endtoend-default | 1 | 0 | 1 | 210 | branch has commits or tree differences requiring review |
| delete-safe | codex/chatgpt-upload-validation | 0 | 0 | 0 | 211 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| preserve-dirty | codex/cockpit-design-system | 6 | 1 | 5 | 243 | attached worktree has dirty state |
| delete-safe | codex/cockpit-pm-textual | 0 | 0 | 0 | 211 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | codex/dopecode-ast-navigation-20260417 | 1 | 1 | 0 | 655 | branch has commits or tree differences requiring review |
| preserve-dirty | codex/dopemux-cli-audit-remediation | 1 | 1 | 0 | 180 | attached worktree has dirty state |
| preserve-dirty | codex/freeflow-strict-router | 2 | 0 | 2 | 163 | attached worktree has dirty state |
| content-audit | codex/infra-compose-uv-db-init | 6 | 6 | 0 | 2092 | branch has commits or tree differences requiring review |
| preserve-dirty | codex/installer-smoke-python-deps | 1 | 0 | 1 | 165 | attached worktree has dirty state |
| preserve-dirty | codex/mcp-audit-hardening | 0 | 0 | 0 | 324 | attached worktree has dirty state |
| content-audit | codex/ops-mac-system-data-scrubber | 1 | 0 | 1 | 153 | branch has commits or tree differences requiring review |
| content-audit | codex/pm-writes-phase1 | 3 | 3 | 0 | 327 | branch has commits or tree differences requiring review |
| content-audit | codex/pm-writes-phase1-local-pre-remote-sync | 2 | 2 | 0 | 332 | branch has commits or tree differences requiring review |
| content-audit | codex/production-extraction-embeddings-hardening | 5 | 0 | 3 | 31 | branch has commits or tree differences requiring review |
| preserve-dirty | codex/remove-stale-root-next-surface | 2 | 0 | 2 | 73 | attached worktree has dirty state |
| keep | codex/repo-hygiene-lost-work-audit-20260502 | 0 | 0 | 0 | 0 | base or active execution branch |
| preserve-dirty | codex/restore-system-data-command | 0 | 0 | 0 | 0 | attached worktree has dirty state |
| delete-safe | codex/rte-canonical-operator-entrypoint | 0 | 0 | 0 | 301 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | codex/rte-prescan-progress-hud | 1 | 0 | 1 | 257 | branch has commits or tree differences requiring review |
| content-audit | codex/rte-wizard-prescan-telemetry | 2 | 2 | 0 | 255 | branch has commits or tree differences requiring review |
| preserve-dirty | codex/tui-runtime-unknown-hardening | 1 | 0 | 1 | 337 | attached worktree has dirty state |
| content-audit | extractor/prompt-governance-gtm | 6 | 0 | 6 | 2076 | branch has commits or tree differences requiring review |
| content-audit | feat/rte-cost-stabilization-v2 | 2 | 1 | 0 | 301 | branch has commits or tree differences requiring review |
| content-audit | feat/rte-intelligence-wiring | 1 | 1 | 0 | 491 | branch has commits or tree differences requiring review |
| delete-safe | feat/rte-prescan-grok-optimization | 0 | 0 | 0 | 310 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | fix/restore-runtime-authority-verifier | 1 | 0 | 1 | 205 | branch has commits or tree differences requiring review |
| delete-safe | global-ci-fix-407841f2 | 0 | 0 | 0 | 306 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| keep | main | 0 | 0 | 0 | 0 | base or active execution branch |
| content-audit | pr/464 | 3 | 3 | 0 | 619 | branch has commits or tree differences requiring review |
| content-audit | pr/467 | 2 | 2 | 0 | 658 | branch has commits or tree differences requiring review |
| content-audit | pr/480 | 2 | 2 | 0 | 654 | branch has commits or tree differences requiring review |
| content-audit | pr/481 | 18 | 18 | 0 | 477 | branch has commits or tree differences requiring review |
| delete-safe | prmerge/20260423_170024-514 | 0 | 0 | 0 | 307 | branch tip is ancestor of origin/main and no dirty attached worktree was observed |
| content-audit | prmerge/539 | 2 | 2 | 0 | 210 | branch has commits or tree differences requiring review |
| content-audit | recover/tp1-547 | 4 | 4 | 0 | 210 | branch has commits or tree differences requiring review |
| content-audit | repo-precommit-debt-cleanup | 15 | 6 | 9 | 689 | branch has commits or tree differences requiring review |
| preserve-dirty | research/dmx-mcp-customization-dr-data | 1 | 0 | 1 | 242 | attached worktree has dirty state |
| preserve-dirty | test/pm-authority-ports | 3 | 1 | 2 | 209 | attached worktree has dirty state |
| content-audit | tp/dopecode-ast-navigation | 1 | 1 | 0 | 655 | branch has commits or tree differences requiring review |
| content-audit | tp/dopecode-ast-navigation-phase1 | 3 | 3 | 0 | 654 | branch has commits or tree differences requiring review |
| content-audit | tp/dopecode-phase2-harden | 7 | 7 | 0 | 640 | branch has commits or tree differences requiring review |
| content-audit | tp/dopecode-phase3-decompose-policy | 9 | 9 | 0 | 637 | branch has commits or tree differences requiring review |
| content-audit | tp/dopecode-phase4-language-approval | 20 | 20 | 0 | 621 | branch has commits or tree differences requiring review |
| content-audit | tp/dopecode-phase8-events-replay | 23 | 23 | 0 | 473 | branch has commits or tree differences requiring review |
| content-audit | tp/gh-review-thread-agent | 1 | 1 | 0 | 656 | branch has commits or tree differences requiring review |
| content-audit | tp/serena-tool-surface-audit | 3 | 3 | 0 | 654 | branch has commits or tree differences requiring review |
| content-audit | tp/serena-v2-truth | 1 | 1 | 0 | 655 | branch has commits or tree differences requiring review |
| content-audit | work/pr-549 | 3 | 0 | 2 | 77 | branch has commits or tree differences requiring review |
| content-audit | work/pr-551 | 2 | 0 | 2 | 171 | branch has commits or tree differences requiring review |
| content-audit | work/pr-551-fix | 2 | 0 | 2 | 80 | branch has commits or tree differences requiring review |
| content-audit | work/pr-552 | 4 | 0 | 4 | 61 | branch has commits or tree differences requiring review |
| content-audit | work/pr-553 | 2 | 0 | 2 | 56 | branch has commits or tree differences requiring review |
| content-audit | work/pr-554 | 2 | 1 | 1 | 180 | branch has commits or tree differences requiring review |
| content-audit | work/pr-554-fix | 2 | 1 | 1 | 89 | branch has commits or tree differences requiring review |

---

## Stash Ledger

No stash was dropped. Every stash has a preserved patch directory under the recovery root.

| Class | Ref | Object | Files | Subject | Recovery dir |
| --- | --- | --- | --- | --- | --- |
| stash-recovery | stash@{2026-04-30 23:10:14 -0700} | 15de39d76 | 1 | On main: volatile AGENTS before syncing main | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-30_23_10_14_-0700-828587618301 |
| stash-recovery | stash@{2026-04-27 19:40:41 -0700} | 8dce51ff1 | 11 | WIP on codex/rte-wizard-prescan-telemetry: a442ed141 Changes from Codex | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-27_19_40_41_-0700-6b1abd355c0e |
| stash-recovery | stash@{2026-04-23 21:27:23 -0700} | 9eefe8bfc | 1 | On codex/rte-prescan-progress-hud: codex temp switch to main for pull | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_21_27_23_-0700-0f8f8414f0bc |
| stash-recovery | stash@{2026-04-23 21:07:37 -0700} | d02a81793 | 1 | On audit/rte-cost-profiles-ladders-wizard-gemini-001: codex temp switch to main | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_21_07_37_-0700-34ad237aa19e |
| stash-recovery | stash@{2026-04-23 20:12:00 -0700} | 6c9ad669d | 1 | On audit/rte-cost-profiles-ladders-wizard-gemini-001: codex-preserve-agents-before-prescan-rebase | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_20_12_00_-0700-a9c7c29ec568 |
| stash-recovery | stash@{2026-04-23 18:12:26 -0700} | fc2a3b4c8 | 18 | On audit/rte-pre-run-hygiene-gemini-001: rte-pre-run-hygiene-isolate-agents-md-pre-commit | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_18_12_26_-0700-c8df1bc617e6 |
| stash-recovery | stash@{2026-04-23 18:08:40 -0700} | 21e7fce76 | 1 | On audit/rte-pre-run-hygiene-gemini-001: rte-pre-run-hygiene-isolate-agents-md-final | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_18_08_40_-0700-7623acdf1ab3 |
| stash-recovery | stash@{2026-04-23 18:05:09 -0700} | f1527ae23 | 1 | On audit/rte-pre-run-hygiene-gemini-001: rte-pre-run-hygiene-isolate-agents-md | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_18_05_09_-0700-c3761701f861 |
| stash-recovery | stash@{2026-04-23 16:59:15 -0700} | d1c2b3e08 | 1 | WIP on feat/rte-cost-stabilization-v2: 326b03271 feat(rte): enforce tiktoken tokenization and authoritative pricing | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_16_59_15_-0700-97ef6871b730 |
| stash-recovery | stash@{2026-04-23 08:14:50 -0700} | 957cec606 | 6 | WIP on main: f23c3294c docs(agents): remove stray memory context and align authority refs | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_08_14_50_-0700-0fbf5409b05b |
| stash-recovery | stash@{2026-04-23 05:21:12 -0700} | 4a63bece5 | 0 | On claude/gracious-poitras-850e4f: cleanup-2026-04-23-gracious-poitras-brand-voice | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_05_21_12_-0700-ac6cb7864212 |
| stash-recovery | stash@{2026-04-23 05:21:11 -0700} | 3ef0715d6 | 0 | On codex/v1-runtime-proof-linkage: cleanup-2026-04-23-v1-operator-build-pack | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_05_21_11_-0700-fd24fd93ec73 |
| stash-recovery | stash@{2026-04-23 05:21:11 -0700} | 879592566 | 0 | On codex/truth-doc-placement: cleanup-2026-04-23-primary-worktree | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_05_21_11_-0700-0f7b0a2360a2 |
| stash-recovery | stash@{2026-04-23 00:18:34 -0700} | 2ab1207b7 | 6 | On main: codex-main-pull-2026-04-23 | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-23_00_18_34_-0700-01cfeeed566e |
| stash-recovery | stash@{2026-04-21 18:20:49 -0700} | e59bb13f2 | 17 | WIP on tp/dopecode-phase8-events-replay: 4320ef814 fix(dopecode): fail-close receipt loading on unsupported event_type and empty workspace_id | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-21_18_20_49_-0700-b75ddd325bac |
| stash-recovery | stash@{2026-04-17 18:28:47 -0700} | e5c5cdbd7 | 62 | On tp/serena-v2-truth: prescan-hardening-work | /Users/hue/.codex/recovery/dopemux-mvp/repo-hygiene-20260502/stashes/stash_2026-04-17_18_28_47_-0700-39ef954fb877 |

---

## Post-Cleanup State

Post-cleanup observed directly:

- Worktree entries after cleanup: `32`
- Stashes after cleanup: `16`
- Execution worktree status: `## codex/repo-hygiene-lost-work-audit-20260502...origin/main`

---

## Residual Risk

- `content-audit` branches may contain real lost work, superseded experiments, or intentional rewrites; they require subsystem review before topic PRs.
- Dirty worktrees and stashes are preserved but unresolved.
- Remote branch cleanup is deferred.
- The local recovery root must be retained until follow-up review resolves the preserved items.
