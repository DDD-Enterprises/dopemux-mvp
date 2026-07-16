---
id: dcp-mcp-readonly-facade-local-run
title: DCP Read-Only MCP Facade - Local V2 Run and Test
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Local-only registry-v2 setup and test procedure for the DCP read-only MCP evidence facade.
---
# Local V2 Run and Test

The public facade is local-only and defaults to stdio. It has no public
listener, tunnel, connector, credential, backend adapter, or lifecycle action.

## Configure the Registry

Do not commit a populated registry. Copy the v2 example outside the repository:

```bash
mkdir -p ~/.dopemux
cp services/dcp-readonly-facade/registry.example.yaml ~/.dopemux/dcp-facade-registry-v2.yaml
export DCP_FACADE_REGISTRY_V2=~/.dopemux/dcp-facade-registry-v2.yaml
```

The registry is the exposure-consent boundary. A target must be explicitly
enabled and must pass approved-root, workspace, and `.repo_id` identity checks.
A missing or malformed registry loads as empty and blocks every lookup.

## Run Locally

```bash
cd services/dcp-readonly-facade
python -m src.mcp.server
```

`DCP_FACADE_TRANSPORT` defaults to `stdio`. `fastmcp` is required for a live
MCP endpoint; the import fallback exists only for constrained test environments.

## Tool Surface

The server registers only:

```text
list_targets
get_target_capabilities
get_target_repo_state_snapshot
list_target_proof_bundles
fetch_target_proof_bundle
get_target_runtime_receipt
```

All target-scoped tools accept `target_id`, not `project_id`. The legacy v1
registry and backend-adapter functions are not loaded by external server mode.

The runtime receipt reads local catalog and runtime-registry evidence only.
An operator may set `DCP_FACADE_MCP_CATALOG` or
`DOPEMUX_MCP_RUNTIME_REGISTRY` to choose local evidence files. Those paths are
server configuration, never tool inputs, and are never returned to callers.

## Run Tests

```bash
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
```

The suite uses temporary local repositories and fixture files. It performs no
live service, provider, credential, container, or tunnel action. See
[`MANUAL_VALIDATION.md`](MANUAL_VALIDATION.md) for the local operator checklist.
