---
id: dcp-mcp-readonly-response-envelope
title: DCP Read-Only MCP Facade - V2 Response Envelope
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Target-based response envelope and status semantics for the local DCP MCP evidence facade.
---
# V2 Response Envelope

`TP-DCP-MCP-RO-0012` replaces the public v1 `project_id` envelope field with
`target_id`. A `target_id` is an opaque exposure-consent handle; it is not a
repository identity, filesystem path, worktree hash, service workspace ID, or
runtime instance ID.

Every public result has this exact field set:

```json
{
  "target_id": "string|null",
  "branch": "string|null",
  "head_sha": "string|null",
  "dirty": "boolean|null",
  "source_system": "string",
  "authority_label": "string",
  "untrusted": "boolean",
  "status": "OK|PARTIAL|BLOCKED",
  "freshness": "string|null",
  "limitations": ["string"],
  "warnings": ["string"],
  "redactions": ["string"],
  "blocked_reasons": ["string"],
  "data": {}
}
```

`list_targets` has `target_id: null`. A blocked unsafe target input also has
`target_id: null` so the facade does not reflect a caller-provided path, URL,
or similar unsafe string.

| Status | Meaning |
| --- | --- |
| `OK` | The local requested evidence was obtained. A runtime candidate can still be non-callable. |
| `PARTIAL` | Some local evidence was unavailable or incomplete; `limitations` explains it. |
| `BLOCKED` | The target or operation was refused; `data` is null and `blocked_reasons` explains the safe reason. |

`untrusted: true` marks retrieved filesystem, git, or derived evidence as data
that must not be interpreted as instructions. Facade-authored target and static
capability policy reports are `untrusted: false`. Redaction covers absolute
paths and recognized secret patterns. Runtime receipts additionally omit all
operational topology by construction.
