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

Review follow-up:

- `dopemux mcp sync-globals --apply` now uses the same startable singleton
  renderer as generated Claude global config, so it cannot reintroduce
  `decision-required` singletons into `~/.claude.json`.
- The quarantine validator treats caller-provided empty output maps as real
  validation input and recognizes both mapping-shaped and list-shaped
  `mcpServers` payloads.

## Validation

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/arch/test_mcp_fleet_catalog_contract.py -q`
- `python -m pytest tests/unit/test_mcp_fleet_catalog.py -q`
- `python -m py_compile src/dopemux/mcp/fleet_catalog.py src/dopemux/commands/mcp_commands.py`
- `git diff --check`
- `pre-commit run --files src/dopemux/commands/mcp_commands.py src/dopemux/mcp/fleet_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py tests/unit/test_mcp_fleet_catalog.py task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE.json proof/dmx-mcp-fleet-roadmap/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE/implementation-notes.md`

NOT_RUN:

- Docker/provider/live MCP checks; this lane is a static generated-config quarantine.
- `scripts/orchestrator/perpacket_codereview.py`; the helper exits before review because
  this generated Lane 7 packet is not present in `config/orchestrator/perpacket_test_map.yaml`.
  Manual bounded diff review was performed instead.

## Scope clarification / addendum (2026-07-04)

A later audit of this merged TP correctly flagged that the scope above is narrower than
the phrase "dead fleet surfaces" can imply. Stating it plainly, truth over fluency:

TP-007's static gate (`validate_decision_required_generated_config_quarantine`) quarantines
only **decision-required catalog SERVERS** — concretely `desktop-commander` and `exa` — from
the startable generated config outputs (`local/.mcp.json`, `claude/mcpServers.json`,
`codex/config.toml`). That is the entire proven scope of this lane, and the validation
results above are accurate for that scope.

It does **not** quarantine, delete, or otherwise touch the broader audit kill-list of dead
service directories, scripts, and compose variants identified separately. As of this
addendum, the following remain live on disk and were never in scope for TP-007:

- `services/mcp-integration-bridge/` (service directory; superseded by `dopecon-bridge`)
- `services/mcp-client/`
- `services/router/`
- the in-repo `gpt-researcher`/`gptr` server sources under
  `docker/mcp-servers-source/gptr-mcp` and `docker/mcp-servers-source/gpt-researcher`
- `services/dope-memory` stdio shim
- `services/dope-context/src/mcp/simple_server.py`
- dead config writers: `scripts/mcp/wire_claude_mcp.py`,
  `scripts/mcp/manage-mcp-servers.sh`
- `scripts/mcp-wrappers/conport-wrapper.sh` (upstream ConPort wrapper)
- 2 unconsumed PAL compose variants
- `scripts/mcp-wrappers/serena-wrapper.sh`, which `exec`s a nonexistent path
  (`services/serena/v2/mcp_server.py` does not exist on disk — confirmed by direct
  filesystem check) — a phantom wrapper, not merely unconsumed

None of these names or paths appear in `compose.yml` services, and none are referenced by
any of the generated fleet output files (`generate_fleet_output_files`), so they were
already non-startable via the canonical catalog/compose path before this addendum — but
that was incidental (they were simply never wired in), not something TP-007 verified or
enforced. This addendum is followed by non-startability regression tests
(`tests/arch/test_mcp_fleet_catalog_contract.py`) that lock in the absence of the
compose-service names `mcp-integration-bridge`, `mcp-client`, and `router`, and assert the
generated outputs never reference the dead paths/scripts above, so the quarantine boundary
cannot silently regress. Source-file deletion of the remaining kill-list items is held for
an explicit follow-on decision; this change deletes only
`services/mcp-integration-bridge/Dockerfile` (see follow-on TP scope) to make that one
service concretely non-buildable rather than merely absent from compose.

This correction does not change the PASS results recorded above — those validations were
run against the claimed scope (decision-required servers) and are accurate for it. The
overstatement was in the surrounding prose ("dead fleet surfaces"), not in the test
evidence.
