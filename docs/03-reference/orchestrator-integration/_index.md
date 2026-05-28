---
id: orchestrator-integration
title: Task Orchestrator Integration Reference
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference index and canonical documentation for Task Orchestrator integration in Dopemux.
related_packets:
  - TP-DMX-ORCH-DOCS-001
---

# Task Orchestrator Integration

This section contains canonical documentation for the Task Orchestrator integration within the Dopemux daily operator workflow.

## Diataxis Reference & Sections

1.  **[CLI Reference](cli.md)**: Daily operator status and planning CLI wrapper commands.
2.  **[MCP Wrapper Surfaces](mcp-wrappers.md)**: Stdio-based and containerized MCP wrappers.
3.  **[Per-Packet Isolated Validation](perpacket.md)**: Targeted testing and validation mapping.
4.  **[GitHub PR Integration](github/_index.md)**: Live `gh`-backed subprocess PR queue and comment adapter.
5.  **[Memory Writers & Mirroring](memory/_index.md)**: Live ConPort writes with dope-memory mirrors.

## Invariants & Posture
All surfaces observe Option A soft-gates posture. In this mode, queue and work notes are advisory, while the final `proof-bundle` review-phase note serves as the strict complete-gate.
