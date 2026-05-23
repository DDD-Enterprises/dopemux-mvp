---
id: fast-dev-os-thread00-current-operating-ledger
title: Fast Dev OS — Thread 00 Current Operating Ledger (Snapshot)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Snapshot of the current Dopemux operating state at the time this ledger was authored. Manual-per-session refresh.
---
# Fast Dev OS — Thread 00 Current Operating Ledger

> **⚠️ SNAPSHOT — NOT LIVE TRUTH.** This ledger captures point-in-time state. Always check live `git status`, `gh pr list`, and `task-packets/INDEX.md` before acting on these values.

## Relationship to governance

This snapshot **operationalizes** the governance layer at [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md); it **does not override** that layer. When this snapshot and the governance layer conflict, the governance layer wins.

## Snapshot metadata

```yaml
snapshot:
  taken_at: '2026-05-23T02:35:00Z'
  repo_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  origin_main_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  ledger_class: snapshot
  refresh_policy: manual-per-session
  next_review_trigger: any new merge to main OR session boundary
  taken_by: 'TP-DMX-FDOS-004-AUTHORITY-REFRESH (initial authoring)'
```

## Active branches and worktrees (at snapshot time)

- **Primary checkout**: `/Users/hue/code/dopemux-mvp` on `main` at `ab22df5a2` (1 commit behind `origin/main`, needs `git pull`).
- **Active worktree for this packet**: `/Users/hue/code/dopemux-mvp-fdos-004-authority-refresh` on `codex/dmx-fdos-004-authority-refresh` at `8e7a2283f` (= `origin/main`).
- **In-flight refresh worktree**: `/Users/hue/code/dopemux-mvp-dmx-fdos-003-upload-set-threads-repo-map` on `codex/dmx-fdos-003-upload-set-threads-repo-map` at `cd13e071e` (PR #668, OPEN, auto-merge queued).
- **Other open RTE worktrees**: see `git worktree list` for live state.

## PR queue summary (at snapshot time)

13 open PRs across the repo. See [`pr-ledger.md`](pr-ledger.md) for per-PR detail.

| PR | Title | Status |
|----|-------|--------|
| #674 | 🎨 Palette: AI Recommendation Copy Micro-interaction | BLOCKED |
| #673 | 🎨 Palette: Copy to Clipboard Micro-interaction for AI Recommendations | BLOCKED |
| #672 | 🎨 Palette: Copy-to-Clipboard AI Recommendations | BLOCKED |
| #671 | TP-DMX-PR-QUEUE-BLOCKERS-001: audit/block PR #659 and #664 | BLOCKED |
| #670 | docs(governance): refresh PR queue blocker proof | BLOCKED |
| #669 | chore(deps): bump the npm_and_yarn group across 2 directories with 2 u | CLEAN |
| **#668** | **docs: assemble ChatGPT Project upload set, thread primers, and repo map intake** | **AUTO-MERGE QUEUED** (this packet's pre-step) |
| #664 | 🎨 Palette: Enhance accessibility and visual feedback for task metadata | BLOCKED |
| #663 | docs: strengthen frontdoor positioning and product docs | BEHIND |
| #661 | chore(deps): bump the uv group across 2 directories with 3 updates | BEHIND |
| #659 | docs(governance): add governance-principles module and align CLAUDE.md | BEHIND |
| #657 | docs(rte): orchestrate remaining remediation waves | BEHIND |
| #656 | RTE-UX-PKT: harden prelive validator error shape | BEHIND |

## Recent merges to main (last 7)

| SHA | Title |
|-----|-------|
| `8e7a2283f` | docs(governance): add Codex packet and proof templates |
| `ab22df5a2` | docs(governance): add Codex operator runbook and prompt pack (#666) |
| `f94b07d4e` | Docs: install mobile-first tmux Cockpit UX spec (#665) |
| `0f537c572` | docs: address mobile tui review comments |
| `a26ac2a8e` | Merge branch 'main' into codex/tp-dmx-mobile-tui-spec-001 |
| `ce12e1b5b` | docs: update mobile tui proof head |
| `5c4977f26` | docs: install mobile tmux cockpit UX spec |

## Active Task Packets (subsystem snapshot)

See [`packet-ledger.md`](packet-ledger.md) for full inventory. Highlights:

- **Fast Dev OS series** (`DMX-FDOS`): `TP-DMX-FDOS-003` (in PR #668, queued), `TP-DMX-FDOS-004` (this packet, in worktree), `TP-DMX-FDOS-005` and `TP-DMX-FDOS-006` (planned, not yet authored).
- **Codex Refresh series** (`DMX-CODEX-REFRESH`): `001` and `002` MERGED (PRs #662, #666). `003` (templates) merged as PR #667 at `8e7a2283f`.
- **RTE series**: many active TPs (`TP-RTE-V3-CONSENT-004`, `TP-RTE-WALKER-006`, `TP-RTE-DOCS-CANON-008` active; `TP-RTE-BATCH-005/006`, `TP-RTE-STRICT-ATTESTATION-007` MERGED). See `task-packets/INDEX.md`.
- **Cockpit series**: multiple active TPs (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`, `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001`, etc.). See `task-packets/INDEX.md`.

## Open blockers (BLOCKING)

1. **PR #668 awaiting auto-merge** — branch protection BLOCKED state pending; auto-merge SQUASH is queued. Once it fires, TP-DMX-FDOS-004 (this packet) will rebase + push.
2. **PR-queue blockers** — TP-DMX-PR-QUEUE-BLOCKERS-001 (PR #671, PR #670) flagging PRs #659 and #664 as high-risk. See those PR bodies.
3. **Multiple PRs in BLOCKED state** (#664, #670, #671, #672, #673, #674) — investigation deferred to TP-DMX-PR-QUEUE-BLOCKERS-001.
4. **Several PRs BEHIND main** (#656, #657, #659, #661, #663) — require rebase before merge consideration.

## Open blockers (NON-BLOCKING but visible)

1. **AGENTS.md §10 known dangers** — bridge surfaces look authoritative but aren't; task-orchestrator runtime split across multiple paths; memory surfaces overlap; agent authority UNKNOWN; dopetask/TaskX naming drift; MCP/proxy config drift. See [`unknown-conflicting-stale.md`](unknown-conflicting-stale.md) for the full register.
2. **GitHub Dependabot warnings** — 31 vulnerabilities reported on main (2 critical, 12 high, 17 moderate). Out of scope for the doctrine layer; handled in dependency-update PRs (#661, #669).

## Next action queue (this session)

1. **PR #668 merges** (auto-merge fires when GitHub re-evaluates branch protection)
2. **TP-DMX-FDOS-004 lands** (this packet)
3. **TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK** opens next worktree from updated origin/main
4. **TP-DMX-FDOS-006-PACKET-PROOF-TEMPLATES** opens after 005 lands

## Truth posture

All values in this ledger are **chat-derived** at snapshot time. They are NEEDS_LIVE_VALIDATION until checked against live `gh pr list`, `git status`, `git log`, and `task-packets/INDEX.md`.
