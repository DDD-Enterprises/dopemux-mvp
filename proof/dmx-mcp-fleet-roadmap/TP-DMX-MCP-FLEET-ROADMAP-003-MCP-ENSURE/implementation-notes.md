# TP-DMX-MCP-FLEET-ROADMAP-003-MCP-ENSURE Implementation Notes

## Scope

Implemented Lane 3 `dopemux mcp ensure --fast/--full` over the canonical MCP
fleet catalog.

## Changes

- Added `dopemux mcp ensure`.
- `--fast` performs local/static checks only:
  - filesystem/env-only workspace and project-root detection
  - catalog default `.mcp.json` parity
  - generated env file presence
  - required per-worktree env derivability
- `--full` runs fast checks first, then fails closed unless Docker and
  `compose.yml` are available.
- Full mode starts catalog compose services, runs the PAL ensure wrapper, runs
  the Task Orchestrator HTTP singleton wrapper, and performs bounded loopback
  HTTP MCP tools-list probes.
- Added `scripts/mcp-wrappers/ensure-pal.sh`.
- Added unit tests proving fast mode does not invoke subprocesses or live MCP
  probes, full mode fails closed without Docker, and full mode builds the
  bounded remediation sequence.

## Validation

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-003-MCP-ENSURE.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/unit/test_mcp_commands_catalog.py tests/unit/test_mcp_fleet_catalog.py -q`
- `bash -n scripts/mcp-wrappers/ensure-pal.sh`
- `python -m py_compile src/dopemux/commands/mcp_commands.py src/dopemux/mcp/fleet_catalog.py`
- `PYTHONPATH=src python -m dopemux.cli mcp ensure --help`
- `git diff --check`
- `python -m pytest tests/arch/test_mcp_fleet_catalog_contract.py -q`

FAIL:

- Initial TDD red run failed because `mcp_ensure_cmd` and support imports did
  not exist.
- First green attempt exposed brittle test expectations around Rich path
  wrapping and relative wrapper paths; tests and missing-file messages were
  tightened and rerun successfully.
- PR review identified that fast mode still used canonical git identity
  resolution, which could spawn `git rev-parse`; fast mode was split onto a
  filesystem/env-only context path and rerun successfully.

NOT_RUN:

- `dopemux mcp ensure --full` against live Docker services. This implementation
  validates command construction and fail-closed behavior; live runtime proof
  requires Docker/service availability and should be recorded separately.
- Provider-backed MCP probes. Full mode only probes loopback HTTP MCP URLs from
  the catalog.

## Runtime Boundaries

No Docker containers were started during implementation validation. No provider
calls were made. No secrets were printed.
