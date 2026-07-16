---
id: TP-DCP-MCP-RO-0012
title: Public Facade Target Contract Migration
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Migrate the public DCP read-only MCP facade to the registry-v2 opaque target contract while retaining fail-closed local evidence behavior.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0012

## Objective

Replace the external FastMCP v1 `project_id` contract with the registry-v2
opaque `target_id` contract. The public surface must resolve only
operator-approved targets and expose local repository, proof, static policy,
and non-callable runtime-evidence receipts.

## Scope

IN:

- Registry-v2-only server wiring and target-scoped public tools.
- Local repository and proof reads behind resolved targets.
- Static capability reports and redacted non-callable runtime receipts.
- V2 public-contract documentation, tests, packet, index, and proof.

OUT:

- Backend adapters, network/protocol probes, tunnels, ingress, credentials,
  container operations, runtime lifecycle changes, and populated registries.

## Invariants

- V1 `registry.py`, `resolver.py`, and direct service profiles are not imported
  by external server mode.
- A target is a bounded opaque identifier, never a path, URL, port, route,
  workspace ID, SQL fragment, or shell command.
- Local runtime catalog evidence is advisory only and always serializes with
  `callable: false`.
- Unavailable or malformed local evidence yields `PARTIAL` or `BLOCKED`;
  it never selects or calls a backend.
- The generated `.claude/claude_config.json` delta remains outside the packet
  allowlist and will not be staged.

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_tools_v2.py services/dcp-readonly-facade/tests/test_mcp_server.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
uv run --frozen python -m jsonschema -i task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0012.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```

## Stop Conditions

- The public tool surface requires direct backend URLs or a caller-selected
  path, port, route, or workspace ID.
- A runtime receipt can become callable or leak operational topology.
- The change requires a file outside the allowlist.
- A live service, provider, or credential is needed to complete local tests.

## Rollback

Revert the single TP-0012 commit. Do not re-enable the v1 public surface
without a separately approved disabled compatibility path and its own review.
