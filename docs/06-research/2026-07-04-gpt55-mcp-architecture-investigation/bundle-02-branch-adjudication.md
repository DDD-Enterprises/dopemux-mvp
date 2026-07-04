---
id: gpt55-mcp-architecture-bundle-02-branch-adjudication
title: GPT55 MCP Architecture Bundle 02 Branch Adjudication
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 2 input bundle for branch work adjudication.
---
# Bundle 02: Branch Adjudication

## Purpose

Have GPT-5.5 decide which follow-on Claude work should be accepted, split, modified, rejected, or held for human decision.

## Required Uploads

1. `prompt-02-branch-adjudication.md`
2. Phase 0 and Phase 1 GPT-5.5 outputs
3. `branch-work-audit.md`
4. `claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md`
5. `claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md` from `claude/mcp-fleet-audit-complete`
6. `proof/dmx-mcp-fleet-roadmap/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE/implementation-notes.md`
7. Recent synthesis attachment `252931e6-3387-4b90-a8c0-47fa3f942310/pasted-text.txt`
8. Recent synthesis attachment `ad6a0ce8-671c-4ddc-9dda-a6c7d93ed2f8/pasted-text.txt`

## Branch Diff Chunks

Chunk A, summary:

```bash
git log --oneline origin/main..claude/mcp-fleet-audit-complete
git diff --name-status origin/main..claude/mcp-fleet-audit-complete
gh pr view 1002 --json number,state,isDraft,mergeable,headRefOid,statusCheckRollup,reviewDecision,latestReviews,comments
```

Chunk B, lifecycle and catalog:

```bash
git diff origin/main..claude/mcp-fleet-audit-complete -- \
  mcp_catalog.yaml \
  src/dopemux/mcp/default_catalog.yaml \
  src/dopemux/mcp/fleet_catalog.py \
  src/dopemux/commands/mcp_commands.py \
  scripts/mcp-wrappers/ensure-pal.sh
```

Chunk C, service/registry/exa:

```bash
git diff origin/main..claude/mcp-fleet-audit-complete -- \
  compose.yml \
  services/registry.yaml \
  docker/mcp-servers-source/exa \
  docs/90-adr/adr-223-retire-exa-mcp-server.md \
  services/mcp-integration-bridge/Dockerfile
```

Chunk D, PM source events:

```bash
git diff origin/main..claude/mcp-fleet-audit-complete -- \
  src/dopemux/pm/api.py \
  src/dopemux/pm/writes.py \
  src/dopemux/adhd/rte_adapter.py \
  tests/unit/test_pm_source_events.py \
  tests/unit/test_memory_capture_client.py
```

## Decisions To Force

- Exa: retire, wire, or defer?
- PR #1002: reconcile first, split, merge after fixes, or treat as advisory only?
- PAL: off-compose ensure, compose-canonical, or singleton HTTP?
- Serena: upstream wrapper, local candidate, or phased migration?
- Dead surfaces: delete, archive, quarantine, or keep source-only?
- PM source events: accept branch semantics or redesign event authority?

## Expected GPT-5.5 Phase Output

- per-commit verdict
- per-file verdict
- PR #1002 live-reconciliation gate
- human-decision list
- accepted/split/reject roadmap inputs
- no final architecture yet
