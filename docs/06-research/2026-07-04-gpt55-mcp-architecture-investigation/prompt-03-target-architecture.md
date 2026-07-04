---
id: gpt55-mcp-architecture-prompt-03-target-architecture
title: GPT55 MCP Architecture Prompt 03 Target Architecture
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 3 GPT-5.5 prompt for target architecture.
---
# Prompt 03: Target Architecture

You are GPT-5.5 Pro performing Phase 3 of a Dopemux MCP/service architecture review.

Use Phase 0-2 outputs and `bundle-03-target-architecture.md`. Now design the target architecture. Preserve authority boundaries and fail-closed behavior.

## Required Output

1. Executive Architecture Verdict.
2. Target-State Service Matrix:
   - name
   - canonical role
   - source path
   - runtime shape
   - MCP/HTTP/stdio surface
   - canonical writer or advisory role
   - generated config status
   - lifecycle owner
3. Authority Table:
   - ConPort
   - dope-memory
   - dope-context
   - Task Orchestrator
   - Leantime
   - dopecon-bridge
   - ADHD Engine
   - Serena
   - DCP facade
   - PAL/gptr/external tools
4. Mermaid Architecture Diagram.
5. MCP Catalog And Generated-Config Design.
6. Lifecycle And Health Design.
7. Memory/Event/Context Flow Design.
8. Rejected Alternatives And Rationale.
9. Human Decisions Still Required.

Label claims as `OBSERVED`, `INFERRED`, `PROPOSED`, or `UNKNOWN`.
