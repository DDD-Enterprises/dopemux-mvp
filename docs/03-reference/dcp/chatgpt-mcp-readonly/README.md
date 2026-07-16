---
id: README
title: DCP Read-Only MCP Evidence Facade
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Authority and local-only documentation for the registry-v2 DCP read-only MCP evidence facade.
---
# DCP Read-Only MCP Evidence Facade

Status: `LOCAL_IMPLEMENTATION_WITH_GAPS`

The public FastMCP entrypoint now uses the registry-v2 opaque `target_id`
contract. It exposes only local target, repository, proof, static capability,
and non-callable runtime-evidence receipts. It does not expose a listener,
tunnel, connector, credential, backend adapter, or runtime lifecycle action.

Primary current references:

- [`REGISTRY_V2_CONTRACT.md`](REGISTRY_V2_CONTRACT.md)
- [`RUNTIME_CATALOG_JOIN_CONTRACT.md`](RUNTIME_CATALOG_JOIN_CONTRACT.md)
- [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md)
- [`RESPONSE_ENVELOPE_SCHEMA.md`](RESPONSE_ENVELOPE_SCHEMA.md)
- [`FACADE_LOCAL_RUN.md`](FACADE_LOCAL_RUN.md)
- [`MANUAL_VALIDATION.md`](MANUAL_VALIDATION.md)

The older v1 `project_id` and direct-backend documents preserve implementation
history but do not define the current public MCP manifest. Runtime and source
truth continue to outrank generated or historical architecture artifacts.
