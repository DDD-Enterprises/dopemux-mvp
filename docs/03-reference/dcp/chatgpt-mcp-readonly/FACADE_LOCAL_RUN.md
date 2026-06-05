---
id: dcp-mcp-readonly-facade-local-run
title: DCP Read-Only MCP Facade — Local Run & Test
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Local setup, registry configuration, and tests for the read-only MCP evidence facade scaffold for dopemux documentation and developer workflows.
---

# Facade Local Run & Test

The TP-DCP-MCP-RO-0004 scaffold lives at `services/dcp-readonly-facade/`. It is a
loopback-only, read-only MCP server. This guide covers configuring the registry,
running the server locally, and running the tests. (Tunnel/connector wiring is
TP-DCP-MCP-RO-0007; backend adapters are 0005/0006.)

## 1. Configure the registry (outside the repo, no secrets)

The registry is the trust boundary. **Do not commit a populated registry.**

```bash
mkdir -p ~/.dopemux
cp services/dcp-readonly-facade/registry.example.yaml ~/.dopemux/dcp-facade-registry.yaml
# edit ~/.dopemux/dcp-facade-registry.yaml: set workspace_path, identity.project, enabled
export DCP_FACADE_REGISTRY=~/.dopemux/dcp-facade-registry.yaml
```

Resolution order for the registry path: `$DCP_FACADE_REGISTRY` → default
`~/.dopemux/dcp-facade-registry.yaml`. A missing file loads an **empty** registry
(every lookup returns `BLOCKED`) — fail-closed by design.

A project is only exposed when it has an `enabled: true` entry **and** the
workspace passes resolution: contained in an `approved_root`, has a `.dopemux/`
directory, validates as a workspace, and its `.repo_id` `project` (and `owner`
if declared) match the entry's `identity`.

## 2. Run the server (stdio)

```bash
cd services/dcp-readonly-facade
python -m src.mcp.server          # DCP_FACADE_TRANSPORT defaults to stdio
```

`fastmcp` is an optional dependency (root `pyproject.toml` `[services]` extra).
When it is not installed the server falls back to a no-op stub for import
safety; install `fastmcp` for a live MCP endpoint.

## 3. Run the tests

```bash
python -m pytest -q services/dcp-readonly-facade/tests
```

Tests build real temporary git workspaces (with `.dopemux/`, `.repo_id`, proof
bundles) and exercise the fail-closed paths: unknown/disabled project → `BLOCKED`;
symlink/cross-project/`..` proof access → `BLOCKED`; stale-proof and dirty-worktree
→ `warnings`; absolute paths and secrets → redacted.

## 4. Tools (Phase 1)

| Tool | `project_id` | Returns |
| --- | --- | --- |
| `list_projects` | no | enabled projects + configured capabilities |
| `get_project_capabilities` | yes | which backends are configured |
| `get_repo_state_snapshot` | yes | branch / head_sha / dirty (read-only git) |
| `list_proof_bundles` | yes | proof bundle ids under `<workspace>/proof/` (cap 20) |
| `fetch_proof_bundle` | yes | one bundle's files (containment + symlink safe) |

All return the canonical envelope (see
[RESPONSE_ENVELOPE_SCHEMA.md](RESPONSE_ENVELOPE_SCHEMA.md)); missing/denied reads
yield `PARTIAL`/`BLOCKED`, never guessed data.
