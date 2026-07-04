# TP-DMX-MCP-FLEET-ROADMAP-002-GENERATED-OUTPUTS Implementation Notes

## Scope

Implemented Lane 2 generated MCP fleet projections from the canonical
`mcp_catalog.yaml` contract introduced in Lane 1.

## Changes

- Added deterministic catalog renderers for:
  - per-worktree `.mcp.json`
  - Claude singleton `mcpServers` fragment
  - Codex `config.toml` fragment
  - MCP health probe list
  - generated MCP doctrine doc
- Added `dopemux mcp generate` with dry-run default behavior.
- Required `--apply --output-dir <dir>` for writes.
- Added unit coverage proving dry-run does not write and apply is bounded to
  the requested output directory.
- Added reference documentation for generated outputs.
- Addressed PR review feedback by rendering Codex stdio environment forwarding
  with `env_vars`, deduplicating env names, and avoiding literal placeholder
  env values in generated Codex config.

## Validation

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-002-GENERATED-OUTPUTS.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/unit/test_mcp_commands_catalog.py tests/unit/test_mcp_fleet_catalog.py -q`
- `python -m pytest tests/arch/test_mcp_fleet_catalog_contract.py -q`
- `python -m py_compile src/dopemux/mcp/fleet_catalog.py src/dopemux/commands/mcp_commands.py`
- `PYTHONPATH=src python -m dopemux.cli mcp --help`
- `PYTHONPATH=src python -m dopemux.cli mcp generate --output-dir /tmp/dmx-mcp-generated-smoke`
- `PYTHONPATH=src python -m dopemux.cli mcp generate --apply --output-dir /tmp/dmx-mcp-generated-smoke-lane2`
- `find /tmp/dmx-mcp-generated-smoke-lane2 -type f | sort`
- `python -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path("/tmp/dmx-mcp-generated-smoke-lane2/codex/config.toml").read_text())'`
- `python -m pytest tests/unit/test_mcp_fleet_catalog.py tests/unit/test_mcp_commands_catalog.py -q`
- `python -m py_compile src/dopemux/mcp/fleet_catalog.py src/dopemux/commands/mcp_commands.py`
- `PYTHONPATH=src python -m dopemux.cli mcp generate --apply --output-dir /tmp/dmx-mcp-generated-smoke-lane2-review`
- `python -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path("/tmp/dmx-mcp-generated-smoke-lane2-review/codex/config.toml").read_text())'`

FAIL:

- `python -m pytest tests/unit/test_mcp_commands_catalog.py tests/unit/test_mcp_fleet_catalog.py -q`
  failed before implementation because the tested generator functions and CLI
  command did not exist yet.
- `python -m dopemux.cli mcp generate --output-dir /tmp/dmx-mcp-generated-smoke`
  exercised the installed/imported package instead of this worktree source and
  did not include the new command. The branch-local smoke was rerun with
  `PYTHONPATH=src`.
- `python -m tomllib /tmp/dmx-mcp-generated-smoke-lane2/codex/config.toml`
  used an invalid invocation form because `tomllib` has no module entry point.
  The same TOML file parsed successfully with `python -c`.

NOT_RUN:

- Docker health and live MCP initialize/tools-list probes. This lane is static
  generation only and the packet forbids live MCP or Docker mutation.
- Provider-backed checks. No provider credentials or network calls are required
  for this packet.

## Runtime Boundaries

No Docker, live MCP, provider, or user-global config writes were performed.
