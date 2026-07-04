# TP-DMX-MCP-FLEET-ROADMAP-005-SERVER-PERSONALITIES

## Scope

Lane 5 converges MCP server personalities through static catalog contract data.
It does not delete services, change runtime startup, run Docker, or claim live
MCP health.

## Changes

- Added schema-backed metadata for MCP plane, authority role, lifecycle,
  management model, identity scope, and follow-on decision.
- Declared metadata in both `mcp_catalog.yaml` and the packaged
  `src/dopemux/mcp/default_catalog.yaml`.
- Added a static personality drift gate for high-risk surfaces:
  ConPort, task-orchestrator, dope-memory, dope-context, PAL, PAL stdio, Exa,
  and desktop-commander.
- Rendered personality metadata into health probe JSON and the generated
  doctrine table.
- Documented that Exa and desktop-commander remain decision-gated until future
  wire-or-retire and delete-or-host-run scans prove a safe action.

## Review Fixes

- Removed lane-specific wording from the reusable personality validator error
  message.
- Changed the generic `decision-required` regression test to use a temporary
  non-pinned server so it specifically covers the generic rule.

## Authority

- `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, and `PM_PLANE.md`.
- Runtime/config surfaces: `mcp_catalog.yaml`, `compose.yml`,
  `src/dopemux/mcp/default_catalog.yaml`, `src/dopemux/mcp/fleet_catalog.py`,
  and existing fleet catalog tests.

## Validation

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-005-SERVER-PERSONALITIES.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/unit/test_mcp_fleet_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py -q`
- `python - <<'PY' ... jsonschema.validate(yaml.safe_load(...), schema) ... PY` for `mcp_catalog.yaml` and `src/dopemux/mcp/default_catalog.yaml`
- `python -m py_compile src/dopemux/mcp/fleet_catalog.py`
- `git diff --check`
- `pre-commit run --files mcp_catalog.yaml src/dopemux/mcp/default_catalog.yaml schemas/mcp/fleet-catalog.schema.json src/dopemux/mcp/fleet_catalog.py tests/unit/test_mcp_fleet_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py docs/03-reference/mcp/fleet-generated-outputs.md task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-005-SERVER-PERSONALITIES.json proof/dmx-mcp-fleet-roadmap/TP-DMX-MCP-FLEET-ROADMAP-005-SERVER-PERSONALITIES/implementation-notes.md`

FAIL:

- `python -m jsonschema -i mcp_catalog.yaml schemas/mcp/fleet-catalog.schema.json` failed because the `jsonschema` CLI parses JSON input, not YAML input. This was replaced by the YAML-aware validation command above.

## Not Run

- Docker compose startup.
- Live MCP initialize or tools-list probes.
- Provider-backed Exa, PAL, or GPT Researcher calls.

Those checks require runtime services and credentials and belong to a bounded
runtime validation lane.
