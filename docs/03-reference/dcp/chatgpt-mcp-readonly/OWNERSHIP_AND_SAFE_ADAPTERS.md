---
id: dcp-mcp-readonly-ownership-and-safe-adapters
title: DCP Ownership Verification And Release-One Adapters
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Fail-closed ownership verification and release-one ConPort/dope-memory adapter gates for the DCP read-only facade.
---

# Ownership Verification And Release-One Adapters

Packet: **TP-DCP-MCP-RO-0015**

## Scope

This packet lands:

1. A pure **ownership verifier** that adjudicates candidate evidence without
   trusting ports alone.
2. A **release-one safe adapter gate** for:
   - ConPort: decision list + decision read by explicit ID
   - dope-memory: `memory_search` + `memory_replay_session`

It does **not** enable dope-context, task-orchestrator, bridge passthrough,
progress reads (auto-fork risk), broad ConPort query mode, writes, tunnels, or
live network by default. Tests inject HTTP transports; live backends remain
opt-in and unauthorized in this series step.

## Ownership rules

Module: `dcp_facade.ownership`

| Check | Fail-closed outcome |
| --- | --- |
| Family not in `{conport, dope_memory}` | BLOCKED |
| `candidate_count != 1` | no candidate / ambiguous |
| Stale evidence | BLOCKED |
| Port listening without identity/labels | **port-only BLOCKED** |
| Missing required labels | BLOCKED |
| Project ID / roots / label mismatches | BLOCKED |
| Mounts omit project/worktree root | BLOCKED |
| `protocol_ok` not True | BLOCKED (live probe required) |

`OwnershipVerdict.callable` is always `False`. Verification never grants
callable authority by itself.

Required labels:

- `dopemux.project_id`
- `dopemux.service`
- `dopemux.worktree_root`

## Release-one operations

Module: `dcp_facade.safe_adapters` + `route_manifest.RELEASE_ONE_OPERATIONS`

| Family | Allowed ops | Explicitly blocked |
| --- | --- | --- |
| conport | `list_decisions`, `get_decision` | progress, broad search/query, writes |
| dope_memory | `memory_search`, `memory_replay_session` | store/correct/reflect/mark/link |

Each entrypoint:

1. Checks operation is release-one.
2. Requires `OwnershipVerdict.verified` for the same family.
3. Invokes the low-level adapter with an injected `ReadOnlyHttpClient`.
4. Returns a non-callable public dict (`callable: false`).

## Relationship to earlier packets

| Packet | Role |
| --- | --- |
| 0011 | Runtime/catalog join evidence (non-callable) |
| 0012 | Public target_id tools (local only) |
| 0013 | Connector auth/policy |
| 0014 | Loopback ingress |
| **0015** | Ownership + release-one adapter gates |

Public FastMCP server tools for live decision/memory reads remain a later
wiring decision; this packet provides the fail-closed gate those tools must use.

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_ownership.py services/dcp-readonly-facade/tests/test_safe_adapters.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
```
