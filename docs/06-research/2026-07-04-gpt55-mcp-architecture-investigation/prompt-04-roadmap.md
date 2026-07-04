---
id: gpt55-mcp-architecture-prompt-04-roadmap
title: GPT55 MCP Architecture Prompt 04 Roadmap
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 4 GPT-5.5 prompt for implementation roadmap.
---
# Prompt 04: Implementation Roadmap

You are GPT-5.5 Pro performing Phase 4 of a Dopemux MCP/service architecture review.

Use Phase 0-3 outputs and `bundle-04-roadmap.md`. Convert the accepted target architecture into commit-sized implementation slices.

## Required Output

1. Roadmap Dependency Graph in Mermaid.
2. Task-Packet-Ready Slice Table:
   - packet id
   - goal
   - allowed files
   - canonical authority
   - dependencies
   - implementation summary
   - validation commands
   - rollback plan
   - risks
3. Validation Matrix:
   - command
   - expected pass criteria
   - known current failure if any
   - phase where it becomes required
4. Deletion/Archive Safety Plan.
5. Stop Gates And Human Decisions.
6. First Three Packets To Execute.

Do not combine unrelated authority changes in one packet. Do not make runtime-start assumptions.
