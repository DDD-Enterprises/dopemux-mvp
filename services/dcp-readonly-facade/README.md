# DCP read-only MCP evidence facade (Phase 1 scaffold)

Loopback-only, **read-only** MCP server that projects repository evidence from a
registered dopemux workspace to ChatGPT. It holds no write authority and is an
evidence projection layer, not a canonical source.

This is the **TP-DCP-MCP-RO-0004 scaffold**: registry + resolver + envelope +
redaction + five local/git/proof tools. Backend adapters (ConPort, dope-memory,
dope-context, task-orchestrator) are added in 0005/0006.

## Layout

- `src/dcp_facade/` — pure logic (no MCP dependency): `envelope`, `redaction`,
  `registry`, `resolver`, `gitstate`, `proofs`, `tools`.
- `src/mcp/server.py` — thin FastMCP wiring (delegates to `dcp_facade.tools`).
- `tests/` — pytest suite (registry/resolver/proofs/gitstate/envelope/redaction/tools).
- `registry.example.yaml` — example registry (no secrets).

## Phase-1 tools

`list_projects`, `get_project_capabilities`, `get_repo_state_snapshot`,
`list_proof_bundles`, `fetch_proof_bundle`. Every project-scoped tool requires
`project_id`; results are wrapped in the canonical envelope and redacted.

## Run / test

See [FACADE_LOCAL_RUN.md](../../docs/03-reference/dcp/chatgpt-mcp-readonly/FACADE_LOCAL_RUN.md)
for setup. Quick start:

```bash
export DCP_FACADE_REGISTRY=~/.dopemux/dcp-facade-registry.yaml   # outside the repo
python -m pytest -q services/dcp-readonly-facade/tests
python -m src.mcp.server          # from services/dcp-readonly-facade/ (stdio transport)
```

Contracts: `docs/03-reference/dcp/chatgpt-mcp-readonly/` (ARCHITECTURE,
TOOL_CONTRACT, RESPONSE_ENVELOPE_SCHEMA, SECURITY_MODEL, MULTI_PROJECT_REGISTRY_CONTRACT).
