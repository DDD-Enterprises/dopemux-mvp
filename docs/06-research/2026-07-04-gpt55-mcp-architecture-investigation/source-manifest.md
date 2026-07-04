---
id: gpt55-mcp-architecture-source-manifest
title: GPT55 MCP Architecture Source Manifest
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Source manifest for GPT-5.5 MCP architecture packet.
---
# Source Manifest

## Required Repo Authority Files

- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`
- `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md`
- `.claude/modules/shared/memory-trinity-routing.md`

## MCP Fleet Design And Branch Docs

- `claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md`
- `claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md` from `claude/mcp-fleet-audit-complete`
- `docs/90-adr/adr-223-retire-exa-mcp-server.md` from `claude/mcp-fleet-audit-complete`
- `proof/dmx-mcp-fleet-roadmap/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE/implementation-notes.md`

## Current Source Surfaces

- `compose.yml`
- `services/registry.yaml`
- `mcp_catalog.yaml`
- `src/dopemux/mcp/default_catalog.yaml`
- `src/dopemux/mcp/fleet_catalog.py`
- `src/dopemux/mcp/registry.py`
- `src/dopemux/mcp/server_manager.py`
- `src/dopemux/mcp/provision.py`
- `src/dopemux/mcp/resolver.py`
- `src/dopemux/commands/mcp_commands.py`
- `scripts/mcp-wrappers/ensure-pal.sh`
- `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh`
- `.mcp.json`

## Service/Server Surfaces For Architecture Review

- `docker/mcp-servers-source/conport/`
- `services/working-memory-assistant/`
- `services/dope-memory/`
- `services/dope-context/`
- `services/serena/`
- `services/task-orchestrator/`
- `services/adhd_engine/`
- `services/dcp-readonly-facade/`
- `services/dopecon-bridge/`
- `docker/mcp-servers-source/pal/`
- `docker/mcp-servers-source/pal-stdio/`
- `docker/mcp-servers-source/gptr-mcp/`
- `docker/mcp-servers-source/desktop-commander/`
- `services/mcp-capture/`
- `services/mcp-integration-bridge/`
- `services/mcp-client/`
- `services/router/`

## Prior Investigation Package

- `docs/06-research/2026-07-04-dopemux-service-investigation/research.md`
- `docs/06-research/2026-07-04-dopemux-service-investigation/service-gap-matrix.md`
- `docs/06-research/2026-07-04-dopemux-service-investigation/adhd-untracked-work-design.md`
- `docs/06-research/2026-07-04-dopemux-service-investigation/implementation-backlog.md`
- `docs/06-research/2026-07-04-dopemux-service-investigation/ux-integration-spec.md`

## Validation Surfaces

- `tests/arch/test_mcp_fleet_catalog_contract.py`
- `tests/unit/test_mcp_fleet_catalog.py`
- `tests/unit/test_mcp_commands_catalog.py`
- `tests/unit/test_memory_capture_client.py`
- `tests/unit/test_pm_source_events.py` from `claude/mcp-fleet-audit-complete`
- `tests/mcp/`
- `tests/unit/dopemux/ui/cockpit/`
- `services/serena/tests/test_mcp_server_local.py`
- `services/serena/test_f001_enhanced.py`
- `services/adhd_engine/tests/`

## External Transcript Paths

- Main transcript: `/Users/hue/.claude/projects/-Users-hue-code-dopemux-mvp--claude-worktrees-trusting-engelbart-d2fbfe/b05cfc29-976f-4323-8bdc-ee9a341fd6bb.jsonl`
- Subagents: `/Users/hue/.claude/projects/-Users-hue-code-dopemux-mvp--claude-worktrees-trusting-engelbart-d2fbfe/b05cfc29-976f-4323-8bdc-ee9a341fd6bb/subagents/*.jsonl`
