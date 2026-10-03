---
id: REF-DCP-CURRENT-RUNTIME-RECONCILIATION
title: Current-Main Runtime and Toolchain Reconciliation (R6 / 0000R)
type: reference
owner: Control Tower | Current
last_review: 2026-10-03
next_review: 2026-11-03
author: '@hu3mann'
date: '2026-10-03'
prelude: Current-Main Runtime and Toolchain Reconciliation (R6 / 0000R) (reference)
  for dopemux documentation and developer workflows.
---
# Current-Main Runtime and Toolchain Reconciliation

Reconciles DCP routing, PAL, OpenCode, LiteLLM, runner inventory, MCP wiring, and GitHub control-plane state against current `main` (post-#1400 `b2dc31f871bf31dbb6bbea73c5a328b67dfcbb30`). Supersedes PR #1137.

## Current System State (Observed Repo Truth)

1. **Python Toolchain**: Python 3.11/3.12 managed via `uv`, with pyproject.toml declaring dependencies and strict `tool.uv.override-dependencies`.
2. **MCP Fleet**: Managed under `mcp_catalog.yaml`. `mcp>=1.28.1,<2` and `fastmcp>=3.2.0,<4` preserved.
3. **DCP Boundaries**: DCP is an inert, fail-closed policy, classification, and proof validation boundary. All runner invocation permissions remain disabled.
4. **Trusted Input Adapters**: Active in `src/dopemux/dcp/input_adapters.py` and `trusted_adapter_registry.py` on `main`.
5. **Historical Evidence Labeling**: Past July/August artifacts (such as DMX-DCP-MODEL-ROUTING-MVP-0000R) are historical evidence only and do not outrank observed runtime truth.

## Non-claims

- No merge authorized outside governed merge drain
- No live runner/model/connector execution authorized
- No trusted mutation adapter enabled
- No Dopetask / Task Orchestrator / MCP write mutations from DCP
