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

## Preferred Phased Upload Order

1. Start with `phased-runbook.md`.
2. Upload `pre-run-evidence.md` with Phase 0 so GPT-5.5 sees current branch, PR, service, and validation state.
3. Run `prompt-00-evidence-triage.md` with `bundle-00-evidence-triage.md`.
4. Continue through `prompt-01-current-state.md` to `prompt-06-final-synthesis.md`, uploading only the matching bundle and carry-forward output for each phase.
5. Use `gpt55-web-prompt.md` only as a one-shot fallback if the phased run is not possible.
6. Upload source files listed in `source-manifest.md` only when GPT-5.5 asks for deeper code inspection.

## Evidence Rules

- Treat `claudedocs/*` and transcript digests as advisory unless backed by source/config/tests.
- Treat `origin/main` at `8f71ab9af` as the current merged baseline for this packet.
- Treat `claude/mcp-fleet-audit-complete` as later Claude work that is not the current baseline until merged.
- Treat the two recent synthesis attachments listed in `source-manifest.md` as advisory reconciliation inputs. They are useful for PR #1002 and packetization strategy, but they do not outrank live repo/GitHub/runtime evidence.
- Do not paste raw transcript JSONL unless a specific claim must be adjudicated; the digest provides hashes and paths for auditability.

## Desired GPT-5.5 Output

Across the phased run, ask GPT-5.5 Pro for:

- optimal architecture by service/server
- canonical writer and authority boundaries
- generated-config and lifecycle design
- integration model across MCP, Cockpit, CLI, Task Orchestrator, ConPort, dope-memory, dope-context, Serena, ADHD Engine, PAL, gptr, DCP facade, and external tools
- packetized implementation roadmap with tests, rollback, and sequencing
