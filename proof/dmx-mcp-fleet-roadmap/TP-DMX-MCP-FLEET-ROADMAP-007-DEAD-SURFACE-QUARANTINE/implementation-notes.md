# TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE Proof

## Scope

Lane 7 quarantines unresolved MCP fleet surfaces from startable generated config outputs.
It does not delete service code or compose/registry entries because reverse-dependency
evidence still shows active references.

## Reverse Dependency Scan

Command:

```bash
rg -n "desktop-commander|exa|mcp-exa|mcp__exa|mcp__desktop|MCP_DesktopCommander" \
  mcp_catalog.yaml services/registry.yaml src/dopemux/mcp src/dopemux/commands/mcp_commands.py \
  docker/mcp-servers-source/services/mcp-client docker/mcp-servers-source/start-profile.sh \
  docker/mcp-servers-source/start-all-mcp-servers.sh .claude/commands/docs/find.md \
  .claude/commands/web/triage.md docs/03-reference/mcp/fleet-generated-outputs.md
```

Observed classification:

- Catalog and bundled catalog still declare `desktop-commander` and `exa` as
  `decision-required`; these remain source-of-truth audit metadata.
- `services/registry.yaml`, `src/dopemux/mcp/registry.yaml`, start scripts, and
  legacy MCP client code still reference the surfaces, so deletion is not proven safe.
- `.claude/commands/docs/find.md` and `.claude/commands/web/triage.md` mention Exa as a
  human-facing research tool name, but no `mcp__exa__...` generated tool-surface
  reference was observed in the command-surface drift gate.
- `docs/03-reference/mcp/fleet-generated-outputs.md` already states that
  `desktop-commander` is decision-gated.

## Quarantine Evidence

Generated startable output inspection after implementation:

```text
decision_required= ['desktop-commander', 'exa']
local= ['conport', 'dope-memory', 'task-orchestrator']
claude= ['MCP_DOCKER', 'dope-context', 'gpt-researcher', 'pal', 'pal-stdio', 'serena']
codex= ['MCP_DOCKER', 'dope-context', 'gpt-researcher', 'pal', 'pal-stdio', 'serena']
quarantine_errors= []
```

The static gate `validate_decision_required_generated_config_quarantine` fails if a
`decision-required` surface appears in:

- `defaults.per_worktree`
- `local/.mcp.json`
- `claude/mcpServers.json`
- `codex/config.toml`

## Validation

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/arch/test_mcp_fleet_catalog_contract.py -q`
- `python -m pytest tests/unit/test_mcp_fleet_catalog.py -q`
- `python -m py_compile src/dopemux/mcp/fleet_catalog.py`
- `git diff --check`
- `pre-commit run --files src/dopemux/mcp/fleet_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py tests/unit/test_mcp_fleet_catalog.py task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE.json proof/dmx-mcp-fleet-roadmap/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE/implementation-notes.md`

NOT_RUN:

- Docker/provider/live MCP checks; this lane is a static generated-config quarantine.
- `scripts/orchestrator/perpacket_codereview.py`; the helper exits before review because
  this generated Lane 7 packet is not present in `config/orchestrator/perpacket_test_map.yaml`.
  Manual bounded diff review was performed instead.
