---
id: evidence-ledger
title: Evidence Ledger
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Evidence Ledger (explanation) for dopemux documentation and developer workflows.
---
# Evidence Ledger

Access date: 2026-04-28

## Worktree Guard Evidence

- Worktree path verified: `/Users/hue/code/dopemux-mvp-wt-mcp-customization-dr-data`
- Branch verified: `research/dmx-mcp-customization-dr-data`
- Repo marker verified: `.dopetaskroot` present
- Primary checkout was not used for final generated artifacts. An initial generated docs directory was accidentally created in the original thread checkout and then moved into the required dedicated worktree; a follow-up status check showed no `docs/research/mcp-customization` changes remained in the original checkout.

## Repo Authority Evidence

- `PROJECT.md` and `ARCHITECTURE.md` identify Dopemux as a composed multi-system workspace, not a unified platform.
- `PM_PLANE.md` and `src/dopemux/pm/writes.py` preserve split PM authority: Leantime metadata, task-orchestrator workflow, ConPort decisions/progress, dope-memory receipts.
- `docs/03-reference/truth/truth-canonicals.md` records dope-memory, ConPort, task-orchestrator, dopecon-bridge, Serena, and repo-truth-extractor canonicality and drift.
- `services/dopecon-bridge/dopecon_bridge/routes.py` states bridge is adapter/proxy only and must not act as canonical task, workflow, decision, or progress authority.

## Upstream Evidence

- GitHub and package registry checks were run on 2026-04-28 for ConPort, Task Orchestrator candidates, Serena, claude-context, claude-mem candidates, and Mem0 candidates.
- `jpicklyk/task-orchestrator` is recorded as the preferred active Task Orchestrator upstream per operator correction.
- EchoingVesper and iflow task-orchestrator sources are retained as archived/fork/repackage lineage evidence.
- Claude-Mem lineage drift is retained between `customable/claude-mem` and `thedotmack/claude-mem`.
- Mem0 PyPI package repository lineage is marked unresolved because the claimed GitHub repository returned 404 during this pass.

## Validation Evidence

- Task packet schema validation passed against external `/Users/hue/Downloads/dmx_mcp_dr_regen/dopetask-cannonical-spec.json`.
- JSON syntax validation passed for generated JSON files and task packet mirror.
- Required manifest row fields were validated.
- DR upload section coverage was validated.
- Full boundary baseline terms were validated in every DR upload pack.
- Stable JSON row ordering was validated.
- `MANIFEST.sha256` was generated and checked for stable regeneration.
- Secret-pattern scan over generated artifacts returned no matches.
- Allowed write-set check passed.

## Blockers

- Repo-local `dopetask-cannonical-spec.json` is still absent by design; validation used the external schema path.
- PR creation pending until commit/push/PR gates complete.
