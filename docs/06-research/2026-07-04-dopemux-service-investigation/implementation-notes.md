---
id: implementation-notes
title: Implementation Notes
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Implementation Notes (reference) for dopemux documentation and developer
  workflows.
---
# Implementation Notes: Dopemux Service Investigation

Status: OBSERVED implementation artifact.
Date: 2026-07-04.
Task Packet: `TP-DMX-SERVICE-INVESTIGATION-20260704`.

## Scope Executed

- Created a dedicated worktree at `/Users/hue/code/dopemux-mvp/.worktrees/dopemux-service-investigation-20260704`.
- Created the repo-bound Task Packet for this audit.
- Wrote the requested read-only investigation package under `docs/06-research/2026-07-04-dopemux-service-investigation/`.
- Runtime systems were not started for this audit.

## Artifact Map

- `research.md`: evidence summary, inventory counts, deep-dive findings, validation ledger.
- `service-gap-matrix.md`: service-by-service matrix across top-level service directories, compose services, registry services, docs, tests, entrypoints, gaps, and recommended next actions.
- `adhd-untracked-work-design.md`: target integration design for ADHD Engine, Serena/F001, Task Orchestrator, MCP, and Cockpit.
- `implementation-backlog.md`: commit-sized follow-on slices ordered by dependency and risk.
- `ux-integration-spec.md`: Cockpit/dashboard UX model, safe actions, receipts, progressive disclosure, and visual quality bar.

## Important Boundaries

- OBSERVED findings are limited to repository source, config, docs, and non-mutating command output.
- INFERRED design is marked as inference and should not be treated as runtime truth.
- PROPOSED follow-on work is backlog material, not an implemented feature claim.
- UNKNOWN items require either service startup, external MCP state, or additional implementation packets.

## Precommit Notes

- `.claude/claude_config.json` may be locally rewritten by worktree-aware tooling and is outside the scoped allowlist for this audit packet.
- Stage and commit only the Task Packet and investigation files listed in the Task Packet allowlist.
