---
id: tp-dmx-mcp-repo-scoped-task-orchestrator-001-implementation-notes
title: Repo-Scoped Task Orchestrator Implementation Notes
type: explanation
owner: '@codex'
author: '@hu3mann'
date: '2026-05-18'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Implementation notes for repo-scoped Task Orchestrator MCP launch behavior.
---
# TP-DMX-MCP-REPO-SCOPED-TASK-ORCHESTRATOR-001 Implementation Notes

## Summary

Implemented repo-scoped state identity for the upstream stdio Task Orchestrator MCP path and wired Dopemux MCP config generation to support the same model.

## Changes

- Added `src/dopemux/mcp/project_identity.py` to resolve current worktree root and stable local-git-repo project identity from `git rev-parse --git-common-dir`.
- Added bundled `src/dopemux/mcp/default_catalog.yaml` and catalog fallback through `DOPEMUX_MCP_CATALOG`, repo-local `mcp_catalog.yaml`, then bundled defaults.
- Updated `dopemux mcp init/add/doctor` to write `DOPEMUX_PROJECT_ROOT` and `TASK_ORCHESTRATOR_PROJECT_ROOT`, keep ports worktree-scoped, and validate stdio Task Orchestrator with `--print-resolution`.
- Updated root `.mcp.json`, `mcp_catalog.yaml`, docs, and tests for the repo-scoped Task Orchestrator MCP runtime.
- Updated `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` to hash project root instead of worktree root and support `--print-resolution` without Docker.

## Validation

- PASS: `python -m jsonschema -i task-packets/TP-DMX-MCP-REPO-SCOPED-TASK-ORCHESTRATOR-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `uv run --extra test pytest tests/unit/test_mcp_commands_catalog.py tests/unit/test_cli_audit_remediations.py`
- PASS: `bash -n /Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`
- PASS: `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution`
- PASS: `TASK_ORCHESTRATOR_PROJECT_ROOT=/tmp /Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution`
- PASS: `git diff --check`

## Remaining Risk

- Existing per-worktree Task Orchestrator DBs were intentionally not merged or deleted.
- Multiple stdio clients can still attach to one repo-scoped DB through separate containers; no daemonization was added in this slice.
- The home-local Codex plugin script is outside the repository and cannot be included in the git commit.
