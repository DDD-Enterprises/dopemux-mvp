# DMX-CONPORT-OPTIMAL-104 MCP Custom Data Proof

## Scope

TP: `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-104-mcp-surface-custom-data.json`

Worktree: `/Users/hue/.codex/worktrees/conport-optimal-104-mcp-surface-custom-data`

Branch: `codex/conport-optimal-104-mcp-surface-custom-data`

## Authority

- `AGENTS.md`
- Packet 104 task packet
- Existing REST handlers in `docker/mcp-servers-source/conport/enhanced_server.py`

## Contract Observed

Existing REST routes:

- `POST /api/custom_data`
  - JSON body: `workspace_id`, `category`, `key`, `value`
- `GET /api/custom_data`
  - Query params: `workspace_id` required; `category` and `key` optional
- `DELETE /api/custom_data`
  - Query params: `workspace_id`, `category`, `key`

The packet PR text listed `category` as required for get, but the runtime REST
handler only requires `workspace_id`. The implementation follows runtime truth:
`category` and `key` are optional filters for `get_custom_data`.

## Changes

- Added FastMCP tools to `docker/mcp-servers-source/conport/server.py`:
  - `get_custom_data`
  - `save_custom_data`
  - `delete_custom_data`
- Added the same FastMCP tools to
  `docker/mcp-servers-source/conport/conport_mcp_stdio.py`.
- Added JSON-RPC dispatch entries and schemas to
  `docker/mcp-servers-source/conport/enhanced_server.py`:
  - `conport_get_custom_data`
  - `conport_save_custom_data`
  - `conport_delete_custom_data`
- Added focused TDD regression tests in
  `docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py`.

## TDD Evidence

RED:

- `python3 -m pytest docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py -q`
  - First run failed during collection because host Python lacked `mcp`; test
    harness was corrected with a FastMCP stub.
  - Second RED run failed for missing custom_data schemas, dispatch entries,
    and FastMCP functions.

GREEN:

- `python3 -m pytest docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py -q`
  - Result: `3 passed`

## Validation

PASS:

- `python3 -m pytest docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py -q`
  - Result: `3 passed`
- `python3 -m py_compile docker/mcp-servers-source/conport/server.py docker/mcp-servers-source/conport/conport_mcp_stdio.py docker/mcp-servers-source/conport/enhanced_server.py`
  - Result: exit 0
- `python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-104-mcp-surface-custom-data.json >/dev/null`
  - Result: exit 0
- `python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-104-mcp-surface-custom-data.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Result: exit 0; `jsonschema` CLI deprecation warning only
- `rg -n "get_custom_data|save_custom_data|delete_custom_data|conport_get_custom_data|conport_save_custom_data|conport_delete_custom_data" docker/mcp-servers-source/conport/server.py docker/mcp-servers-source/conport/conport_mcp_stdio.py docker/mcp-servers-source/conport/enhanced_server.py`
  - Result: all expected tool names present
- `git diff --check`
  - Result: exit 0
- `docker compose --env-file /Users/hue/code/dopemux-mvp/.env -f compose.yml build conport`
  - Result: exit 0; image copied updated `server.py`, `enhanced_server.py`, and
    `conport_mcp_stdio.py`
- `docker compose --env-file /Users/hue/code/dopemux-mvp/.env -f compose.yml up -d --no-deps conport`
  - Result: exit 0; `mcp-conport` recreated
- `curl http://localhost:3004/health`
  - Result: HTTP 200 after startup
- `tools/list` via `POST http://localhost:3004/mcp`
  - Result: advertised `conport_get_custom_data`,
    `conport_save_custom_data`, and `conport_delete_custom_data`
- JSON-RPC custom_data round trip via `POST http://localhost:3004/mcp`
  - Result: save/get/delete pass for workspace `packet-104-live`, category
    `codex`, key prefix `roundtrip-`

NOT_RUN:

- GitHub push or PR creation.
- PAL codereview/precommit; no callable PAL tool was available in this session.

## Residual Risk

- Live validation exercised the local-dev ConPort database and removed the
  round-trip row through the new delete tool. It did not test every possible
  `get_custom_data` list/category-only shape against seeded data.
- The live `mcp-conport` container currently runs the locally built packet 104
  image from this worktree.
