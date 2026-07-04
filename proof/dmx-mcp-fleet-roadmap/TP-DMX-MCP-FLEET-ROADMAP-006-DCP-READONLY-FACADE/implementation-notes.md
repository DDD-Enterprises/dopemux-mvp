# TP-DMX-MCP-FLEET-ROADMAP-006-DCP-READONLY-FACADE Proof Notes

Date: 2026-07-04
Branch: `codex/mcp-fleet-dcp-readonly-facade`
Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/mcp-fleet-dcp-readonly-facade`
Implementation commit: `b7df66d8e5b4b1e90b32022f19a624f6856ec625`
PR: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/1000`

## Scope

Expose already implemented DCP packet 0006 read-only facade functions through
the operator-run stdio MCP server:

- `search_code_docs`
- `get_index_status`
- `get_workflow_status_snapshot`

The implementation does not add a dope-context transport bridge and does not add
write authority. dope-context wrappers remain fail-closed through the pure
facade functions, returning `BLOCKED` envelopes until MCP JSON-RPC bridge and
inventory work is completed.

## Authority Used

- `AGENTS.md`
- `docs/03-reference/dcp/README.md`
- `docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md`
- `docs/03-reference/dcp/chatgpt-mcp-readonly/RUNTIME_SURFACE_INVENTORY.md`
- `services/dcp-readonly-facade/src/dcp_facade/tools.py`
- `services/dcp-readonly-facade/src/mcp/server.py`
- `services/dcp-readonly-facade/tests/test_packet_0006.py`

## Validation

- PASS: `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-006-DCP-READONLY-FACADE.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Exit 0. The jsonschema CLI emitted its standard deprecation warning.
- PASS: `python -m pytest services/dcp-readonly-facade/tests/test_mcp_server.py services/dcp-readonly-facade/tests/test_packet_0006.py -q`
  - Exit 0. Result: `28 passed`.
- PASS: `python -m py_compile services/dcp-readonly-facade/src/mcp/server.py`
  - Exit 0.
- PASS: `python -m pytest services/dcp-readonly-facade/tests/test_route_denylist.py services/dcp-readonly-facade/tests/test_packet_0008.py -q`
  - Exit 0. Result: `26 passed`.

## NOT_RUN

- NOT_RUN: live operator MCP initialize/tools-list probe.
  - Reason: packet scope is static stdio registration and no live MCP client was
    started in this validation slice.
- NOT_RUN: live dope-context MCP JSON-RPC bridge.
  - Reason: the bridge is intentionally not implemented in this packet;
    dope-context facade tools remain fail-closed.
- NOT_RUN: Docker/provider/service health validation.
  - Reason: no Docker or provider service is required to validate the stdio
    wrapper registration and pure-function delegation path.
