---
id: docs__94-architecture__c4-l1-container
title: Docs  94 Architecture  C4 L1 Container
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Docs  94 Architecture  C4 L1 Container (explanation) for dopemux documentation
  and developer workflows.
---
# C4 Level 1 — Container Diagram

## TODO
Produce container diagram showing:
- Dopemux core containers: Terminal UI, MCP Router, Memory Manager, Task Engine
- External systems: Leantime, Claude-flow, Letta, Vector DB
- Inter-container communication protocols
- Data persistence boundaries

## Acceptance Criteria
- All major containers identified and documented
- Technology choices clearly indicated
- Communication protocols specified (gRPC, REST, MCP)
- Deployment boundaries shown
- Responsibility boundaries clear

## Implementation Notes
- Align with ADR decisions on technology stack
- Show ADHD accommodation components
- Include monitoring and health check flows
- Document scaling considerations