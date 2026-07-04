---
id: gpt55-mcp-architecture-investigation-readme
title: GPT55 MCP Architecture Investigation Readme
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Upload guide for the GPT-5.5 MCP architecture investigation packet.
---
# GPT-5.5 MCP Architecture Investigation Packet

Use this directory as the upload/paste package for GPT-5.5 Pro web when asking it to design the optimal Dopemux MCP/service architecture and implementation roadmap.

## Upload Order

1. `gpt55-web-prompt.md`
2. `research.md`
3. `branch-work-audit.md`
4. `transcript-digest.md`
5. `source-manifest.md`
6. The prior all-services audit package, especially `docs/06-research/2026-07-04-dopemux-service-investigation/research.md` and `service-gap-matrix.md`
7. Source files listed in `source-manifest.md` only when GPT-5.5 asks for deeper code inspection

## Evidence Rules

- Treat `claudedocs/*` and transcript digests as advisory unless backed by source/config/tests.
- Treat `origin/main` at `8f71ab9af` as the current merged baseline for this packet.
- Treat `claude/mcp-fleet-audit-complete` as later Claude work that is not the current baseline until merged.
- Do not paste raw transcript JSONL unless a specific claim must be adjudicated; the digest provides hashes and paths for auditability.

## Desired GPT-5.5 Output

Ask GPT-5.5 Pro for:

- optimal architecture by service/server
- canonical writer and authority boundaries
- generated-config and lifecycle design
- integration model across MCP, Cockpit, CLI, Task Orchestrator, ConPort, dope-memory, dope-context, Serena, ADHD Engine, PAL, gptr, DCP facade, and external tools
- packetized implementation roadmap with tests, rollback, and sequencing
