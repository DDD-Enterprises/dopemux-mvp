# TP-DMX-MCP-FLEET-ROADMAP-001 Implementation Notes

## Scope

Implemented Lane 1 of the MCP fleet roadmap: catalog contract, static drift gates, and minimal data corrections required for the gates to pass. No live MCP, Docker, provider, GitHub mutation, memory writes, or runtime launch behavior changes were performed.

## Authority Used

- Latest user instruction: implement the PR 993-derived packetized MCP fleet roadmap.
- Repo authority: `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`.
- Packet authority: `TP-DMX-MCP-FLEET-ROADMAP-001-CATALOG-CONTRACT`.
- Runtime/config evidence: `mcp_catalog.yaml`, `compose.yml`, `services/registry.yaml`, `src/dopemux/mcp/registry.yaml`, `.mcp.json`, `.claude/commands/**`, `src/dopemux/commands/mcp_commands.py`.

## Observed Preflight

- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/mcp-fleet-contract-gates`
- Branch: `codex/mcp-fleet-contract-gates`
- Base: `origin/main`
- Commit SHA: `fa748f585314790e8b18e9ab1f94a9937c29ef2e`
- PR URL: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/995`
- PR 993 state observed before implementation: open, blocked; audit content treated as advisory input.
- Unrelated worktree-generated dirty file observed before scoped edits: `.claude/claude_config.json`.

## Changes

- Added seven MCP fleet roadmap task packets and indexed them in task packet status/index docs.
- Added `schemas/mcp/fleet-catalog.schema.json`.
- Added `src/dopemux/mcp/fleet_catalog.py` for static duplicate-key loading, schema/compose/registry/generated-config/tool-surface drift checks, and renderer parity helpers.
- Added unit and architecture tests for the new contract.
- Fixed current drift detected by the new gates:
  - `mcp_catalog.yaml`: `exa` Docker exec target now matches compose container `mcp-exa`.
  - `mcp_catalog.yaml`: `pal` declares historical tool alias `zen` used by `.claude/commands`.
  - `src/dopemux/mcp/registry.yaml`: duplicate YAML keys removed while preserving current effective last-key behavior.

## Validation

PASS:

- Baseline before new gates: `python -m pytest tests/unit/test_mcp_commands_catalog.py tests/arch/test_registry_compose_alignment.py -q` -> 22 passed.
- Red path: `python -m pytest tests/unit/test_mcp_fleet_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py -q` failed before implementation on missing `dopemux.mcp.fleet_catalog`.
- After implementation: `python -m pytest tests/unit/test_mcp_fleet_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py -q` -> 15 passed.
- Existing focused tests: `python -m pytest tests/unit/test_mcp_commands_catalog.py tests/arch/test_registry_compose_alignment.py -q` -> 22 passed.
- Packet schemas: all `task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-*.json` validated against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
- Fleet schema self-check: `Draft202012Validator.check_schema(...)` passed.
- Syntax/diff: `python -m py_compile src/dopemux/mcp/fleet_catalog.py && git diff --check` passed.

NOT_RUN:

- `dopemux mcp ensure --full`: not in Lane 1 and would require live service behavior.
- Docker health checks: not in Lane 1 and may mutate/start services.
- Live MCP initialize/tools-list probes: not in Lane 1.
- Provider/network validation: not in Lane 1.
- Task Orchestrator/ConPort/dope-memory/dope-context writes: prohibited by Lane 1 invariants.

## Residual Risk

- Static gates prove committed-surface parity only; they do not prove services are running or that live MCP tool lists match implementation.
- `zen` is now an explicit alias for command-surface compatibility, but runtime alias availability still requires later live probe work.
- Task Orchestrator remains split between compose service port `8000` and per-repo singleton catalog port `7890`; Lane 1 records static boundaries and does not resolve runtime personality convergence.

## Review Follow-up

- PR #995 review unblock addressed static review feedback:
  - `docker exec` target parsing now skips options with attached or following values before selecting the container token.
  - `.claude/commands` MCP tool-surface extraction now includes wildcard references such as `mcp__conport__*`.
  - `exa` stdio catalog entry now passes `MCP_RUN_MODE=stdio` to `docker exec`.
  - Proof preflight records commit SHA and PR URL.
- PR #995 merge unblock follow-up addressed additional review feedback:
  - `.claude/commands/dx/implement.md` now references `mcp__pal__*` instead of the unregistered historical `mcp__zen__*` surface.
  - `mcp_catalog.yaml` no longer suppresses that command-surface drift with a `zen` alias.
- PR #995 merge unblock follow-up also synced the bundled fallback catalog:
  - `src/dopemux/mcp/default_catalog.yaml` matches the root `mcp_catalog.yaml`.
  - The architecture gate now validates bundled catalog schema, root parity, and compose alignment.
