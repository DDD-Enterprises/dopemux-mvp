---
id: gpt55-mcp-architecture-prompt-05-operator-ux
title: GPT55 MCP Architecture Prompt 05 Operator UX
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 5 GPT-5.5 prompt for operator UX.
---
# Prompt 05: Operator UX

You are GPT-5.5 Pro performing Phase 5 of a Dopemux MCP/service architecture review.

Use Phase 0-4 outputs and `bundle-05-operator-ux.md`. Design Cockpit/dashboard/CLI UX only after target architecture and roadmap are known.

## Required Output

1. Operator Experience Principles.
2. Cockpit State Model:
   - services
   - MCP
   - F001
   - ADHD advisory
   - Task Orchestrator
   - receipts
3. Dashboard State Model.
4. Status Vocabulary:
   - `LIVE`
   - `DEGRADED`
   - `NOT_PROBED`
   - `UNKNOWN`
   - `BLOCKED`
   - `ADVISORY`
   - `PROXY`
5. Safe Action Gate Specification.
6. Receipt Model.
7. F001 And ADHD Interaction Flow.
8. Progressive Disclosure Rules.
9. UX-Specific Task Packets.
10. Visual Quality Bar.

Do not weaken proof gates for smoother UX. Do not hide unknown or degraded states.
