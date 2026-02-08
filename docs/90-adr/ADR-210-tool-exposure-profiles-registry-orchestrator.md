---
id: ADR-210
title: 'ADR-210: Tool Exposure Governance via Profiles, Registry, and ToolOrchestrator'
type: adr
owner: dopemux-core
date: 2026-02-08
status: proposed
tags:
- mcp
- profiles
- governance
- determinism
- adhd
adhd_metadata:
  cognitive_load: low
  attention_state: any
  context_switching_impact: reduces
supersedes:
- 'Archive RFC: rfc-0043-metamcp-orchestration-system.md (legacy concept)'
- Legacy MetaMCP broker doctrine (if referenced)
author: '@hu3mann'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: 'ADR-210: Tool Exposure Governance via Profiles, Registry, and ToolOrchestrator
  (adr) for dopemux documentation and developer workflows.'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-210: Tool Exposure Governance via Profiles, Registry, and ToolOrchestrator

## Context

Dopemux runs many MCP servers. Exposing too many tools at once causes:
- token bloat
- tool overwhelm and decision paralysis
- nondeterministic tool selection
- increased failure probability

The current repo includes:
- a server registry (docker/mcp-servers/SERVER_REGISTRY.md)
- profile-based startup (docker/mcp-servers/start-profile.sh)
- orchestration and health reporting (start-all-mcp-servers.sh and MCP health docs)
- a task orchestrator service (task-orchestrator)

Legacy brokering concepts (MetaMCP) are treated as non-authoritative unless explicitly present as a required runtime adapter.

## Decision

Tool exposure and selection is governed by a layered system:

1. Registry defines what MCP servers exist and their health contracts.
2. Profiles define which servers are eligible for a workflow.
3. Startup scripts realize a profile into running services.
4. Health checks gate usability.
5. ToolOrchestrator selects tools per task using deterministic policies.

## Normative rules

### Registry

- MUST list each MCP server with:
  - name
  - port/protocol
  - health endpoint
  - category/role
- MUST treat registry drift as a defect.

### Profiles

- MUST define small curated profiles for common modes (minimal, dev, research, full).
- MUST keep default profiles small to reduce cognitive load.
- MUST include PAL in any engineering profile.

### Startup + health gating

- MUST start only servers included in the selected profile.
- MUST run health checks and surface failures clearly.
- SHOULD provide a single-command health summary.

### ToolOrchestrator

- MUST apply deterministic selection policies.
- MUST log tool selection decisions for auditability.
- MUST respect memory lane boundaries and injection opt-in.

## Consequences

### Positive

- Lower cognitive load and faster flow
- Reduced tool sprawl and nondeterministic behavior
- More reliable and debuggable multi-tool operations

### Negative

- Requires ongoing discipline to keep profiles/registry accurate
- Some tasks may require switching profiles intentionally

## Follow-ups

- Identify and label legacy MetaMCP references in docs/scripts (if any) as legacy to prevent split-brain behavior.
- Remove/label Context7 references in profiles since PAL is authoritative.
