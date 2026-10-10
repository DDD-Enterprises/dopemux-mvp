---
id: leantime_runtime_truth_transport_runbook
title: Leantime Runtime Truth Transport and Runbook
type: runbook
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
status: active
prelude: Current transport facts and integration runbook notes for Leantime as evidenced through repository clients and tests.
---
# Leantime - Transport and Runbook

## Primary transport

- Protocol: JSON-RPC 2.0 over HTTP
- Endpoint: `/api/jsonrpc`
- Auth header: `x-api-key`

## Secondary seam

- Plugin support is part of the architecture direction, but this repo's strongest runtime evidence remains JSON-RPC and bridge translation logic.

## Not primary today

- A standalone Leantime MCP surface is not evidenced here as the primary contract.
- Supervisor and PM-plane integrations should continue to treat JSON-RPC as the main operational seam.
