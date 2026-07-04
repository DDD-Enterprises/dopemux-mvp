---
id: gpt55-mcp-architecture-bundle-03-target-architecture
title: GPT55 MCP Architecture Bundle 03 Target Architecture
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 3 input bundle for target architecture design.
---
# Bundle 03: Target Architecture

## Purpose

Design the optimal service/server architecture after evidence triage, current-state inventory, and branch adjudication are complete.

## Required Uploads

1. `prompt-03-target-architecture.md`
2. Phase 0, 1, and 2 GPT-5.5 outputs
3. `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md`
4. `.claude/modules/shared/memory-trinity-routing.md`
5. `docs/06-research/2026-07-04-dopemux-service-investigation/adhd-untracked-work-design.md`
6. `docs/06-research/2026-07-04-dopemux-service-investigation/ux-integration-spec.md`

## Source Chunks

Chunk A, canonical planes:

- ConPort current runtime: `docker/mcp-servers-source/conport/`
- dope-memory runtime: `services/working-memory-assistant/`
- dope-context runtime: `services/dope-context/`

Chunk B, workflow and PM:

- `services/task-orchestrator/`
- Task Orchestrator MCP wrapper/singleton scripts
- `src/dopemux/pm/`

Chunk C, intelligence/advisory:

- `services/serena/`
- `services/adhd_engine/`
- `services/activity-capture/`
- `services/adhd-dashboard/`

Chunk D, adapters/proxies:

- `services/dopecon-bridge/`
- `services/dcp-readonly-facade/`
- `docker/mcp-servers-source/gptr-mcp/`
- `docker/mcp-servers-source/pal/`
- `docker/mcp-servers-source/pal-stdio/`

## Architecture Questions

- What is canonical, support, adapter, infra, duplicate, legacy, dead, unknown?
- What does one canonical catalog own?
- What gets generated from the catalog?
- What does each server expose as MCP, HTTP, stdio, or internal-only?
- What authority envelope should every cross-plane result carry?
- What must be fail-closed?

## Expected GPT-5.5 Phase Output

- target-state service matrix
- Mermaid integration diagram
- authority/writer table
- generated-config design
- lifecycle/health design
- explicit rejected alternatives
