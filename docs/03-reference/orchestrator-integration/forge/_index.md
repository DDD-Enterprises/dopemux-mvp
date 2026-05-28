---
id: orchestrator-forge-index
title: Task Packet Forge Reference
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference detailing templates and automated pipelines for scaffolding Task Packets.
related_packets:
  - TP-DMX-ORCH-010
---

# Task Packet Forge Workflow

The task packet forge provides automated template-building pipelines for scaffolding new, spec-compliant Task Packets.

## Forge Steps
1.  **Read Active Schemas**: Reads schema templates.
2.  **Generate JSON spec**: Resolves allowlists, invariants, and Pytest commands based on the prompt profile input.
