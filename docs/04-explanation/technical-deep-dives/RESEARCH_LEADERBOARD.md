---
id: RESEARCH_LEADERBOARD
title: Research Leaderboard
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Research Leaderboard (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux Deep Research Leaderboard

This document tracks the audit and research progress for all core components of the Dopemux system, following the protocol in `.claude/PRIMER.md`.

## Research Status Overview

| Component         | Status   | Phase   | Health    | Last Audit |
| :---------------- | :------- | :------ | :-------- | :--------- |
| **Dope-Memory**   | [/] 80%  | Phase 4 | Critical  | 2026-02-09 |
| Serena v2         | [/] 30%  | Phase 1 | Stable    | 2026-02-09 |
| ConPort           | [x] 100% | Phase 4 | Critical  | 2026-02-09 |
| dope-context      | [ ] 0%   | Phase 0 | -         | -          |
| ADHD Engine       | [x] 100% | Phase 1 | Unhealthy | 2026-02-09 |
| DopeconBridge     | [ ] 0%   | Phase 0 | -         | -          |
| Task Orchestrator | [ ] 0%   | Phase 0 | -         | -          |
| Desktop Commander | [ ] 0%   | Phase 0 | -         | -          |
| Leantime Bridge   | [ ] 0%   | Phase 0 | -         | -          |
| Plane Coordinator | [ ] 0%   | Phase 0 | -         | -          |
| Workspace Watcher | [ ] 0%   | Phase 0 | -         | -          |
| Activity Capture  | [ ] 0%   | Phase 0 | -         | -          |
| Voice Commands    | [ ] 0%   | Phase 0 | -         | -          |
| ADHD Notifier     | [ ] 0%   | Phase 0 | -         | -          |
| ADHD Dashboard    | [ ] 0%   | Phase 0 | -         | -          |
| LiteLLM           | [ ] 0%   | Phase 0 | -         | -          |
| Exa               | [ ] 0%   | Phase 0 | -         | -          |
| Genetic Agent     | [ ] 0%   | Phase 0 | -         | -          |
| MCP Client        | [ ] 0%   | Phase 0 | -         | -          |
| PAL               | [ ] 0%   | Phase 0 | -         | -          |
| GPT Researcher    | [ ] 0%   | Phase 0 | -         | -          |

## Active Audits Summary

### Dope-Memory
- **Audit Date**: 2026-02-09
- **Finding**: Implementation exists in `working-memory-assistant` but is missing from runtime orchestration.
- **Next Step**: Port 3020 verification and orchestration logic.

### ADHD Engine
- **Audit Date**: 2026-02-09
- **Finding**: Documentation consolidated in `03-reference`. Runtime CRITICAL: Container unresponsive/zombie. Port 8095 not exposed. Code implementation matches design.
- **Status**: Runtime Unhealthy.

### Serena v2
- **Audit Date**: 2026-02-09
- **Finding**: Source code is external (`github.com/oraios/serena`), installed via pip in Docker. Only integration adapter exists in local repo.
- **Status**: Runtime healthy (21h+ uptime). Internal auditing limited to container inspection.

### ConPort
- **Audit Date**: 2026-02-09
- **Finding**: Critical Drift detected. Active code is in `docker/mcp-servers/conport` (AIOHTTP). `services/conport` (FastAPI) is dead/shadow code.
- **Status**: Runtime Healthy. Architecture matches V2 spec.
