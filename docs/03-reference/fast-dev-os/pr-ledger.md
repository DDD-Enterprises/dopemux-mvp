---
id: fast-dev-os-pr-ledger
title: Fast Dev OS — PR Ledger (Snapshot)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Snapshot of open Pull Requests at the time this ledger was authored. Refresh via `gh pr list --state open` for live truth.
---
# Fast Dev OS — PR Ledger

> **⚠️ SNAPSHOT — NOT LIVE TRUTH.** Run `gh pr list --state open --json number,title,headRefName,mergeStateStatus,statusCheckRollup` for current state.

## Relationship to governance

This snapshot **operationalizes** the governance layer at [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md); it **does not override** that layer. When this snapshot and live `gh pr` state conflict, live `gh pr` state wins.

## Snapshot metadata

```yaml
snapshot:
  taken_at: '2026-05-23T02:33:00Z'
  repo_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  origin_main_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  ledger_class: snapshot
  refresh_policy: manual-per-session
  next_review_trigger: any new PR opened/closed OR merge to main OR session boundary
  refresh_command: 'gh pr list --state open --limit 30 --json number,title,headRefName,baseRefName,mergeStateStatus,statusCheckRollup'
  taken_by: 'TP-DMX-FDOS-004-AUTHORITY-REFRESH (initial authoring)'
```

## Open PRs at snapshot time (13)

| PR | Title | Head ref | mergeStateStatus | CI |
|----|-------|----------|------------------|----|
| #674 | 🎨 Palette: AI Recommendation Copy Micro-interaction | (palette branch) | BLOCKED | 16/19 |
| #673 | 🎨 Palette: Copy to Clipboard Micro-interaction for AI Recommendations | (palette branch) | BLOCKED | 16/19 |
| #672 | 🎨 Palette: Copy-to-Clipboard AI Recommendations | (palette branch) | BLOCKED | 16/19 |
| #671 | TP-DMX-PR-QUEUE-BLOCKERS-001: audit/block PR #659 and #664 | `tp/dmx-pr-queue-blockers-001` | BLOCKED | 16/19 |
| #670 | docs(governance): refresh PR queue blocker proof | `codex/tp-dmx-pr-queue-blockers-001` | BLOCKED | 16/19 |
| #669 | chore(deps): bump the npm_and_yarn group across 2 directories with 2 u | dependabot | CLEAN | 16/19 |
| **#668** | **docs: assemble ChatGPT Project upload set, thread primers, and repo map intake** | `codex/dmx-fdos-003-upload-set-threads-repo-map` | **AUTO-MERGE QUEUED** | 17/19 (after force-push refresh) |
| #664 | 🎨 Palette: Enhance accessibility and visual feedback for task metadata | (palette branch) | BLOCKED | 16/19 |
| #663 | docs: strengthen frontdoor positioning and product docs | `docs/frontdoor-positioning-002` | BEHIND | 16/19 |
| #661 | chore(deps): bump the uv group across 2 directories with 3 updates | dependabot | BEHIND | 16/19 |
| #659 | docs(governance): add governance-principles module and align CLAUDE.md | (governance branch) | BEHIND | 16/19 |
| #657 | docs(rte): orchestrate remaining remediation waves | `codex/rte-macro-pkt-remaining-parallel-001` | BEHIND | 16/19 |
| #656 | RTE-UX-PKT: harden prelive validator error shape | `codex/rte-prelive-validator-error-shape` | BEHIND | 16/19 |

**Legend**:
- `CLEAN` = mergeable, all checks pass, branch up to date
- `BEHIND` = branch behind base; needs rebase
- `BLOCKED` = required reviewer / status check / branch protection rule blocking
- `AUTO-MERGE QUEUED` = `gh pr merge --auto` enabled; will fire on condition resolution

## Cross-reference: chat-context-v2 PR conflicts

The chat-context-v2 reconciled corpus at [`/Users/hue/Downloads/dopemux-chat-context-v2/04_reconciled/PR_PACKET_PROOF_MAP.md`](../../../../Downloads/dopemux-chat-context-v2/04_reconciled/PR_PACKET_PROOF_MAP.md) detected 6 PRs with status conflicts across chat sessions. See [`unknown-conflicting-stale.md §2`](unknown-conflicting-stale.md) for the full conflict register and resolution recommendations.

## Recently merged (top 10, for context)

| PR | Title | Merged at |
|----|-------|-----------|
| #667 | docs(governance): add Codex packet and proof templates | 2026-05-20 |
| #666 | docs(governance): add Codex operator runbook and prompt pack | 2026-05-20 |
| #665 | Docs: install mobile-first tmux Cockpit UX spec | 2026-05-20 |
| #662 | docs(governance): refresh Codex authority matrix | 2026-05-19 |
| #660 | docs: add public AI docs surface and RTE external baseline | 2026-05-19 |

## Truth posture

PR statuses are point-in-time. Run live `gh pr list` before acting. Branch protection rules are at [`gh api repos/DDD-Enterprises/dopemux-mvp/branches/main/protection`](https://api.github.com/repos/DDD-Enterprises/dopemux-mvp/branches/main/protection): 0 required approving reviews, 7 required status checks, linear history enforced.
