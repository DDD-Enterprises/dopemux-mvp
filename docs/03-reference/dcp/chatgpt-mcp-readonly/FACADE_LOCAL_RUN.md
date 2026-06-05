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

## 5. Service-backed read tools (TP-DCP-MCP-RO-0005)

These call backend services over loopback HTTP. `base_url` + `workspace_id` come
from the project's registry `service_profiles` (ConPort / dope-memory) — the
caller never supplies a URL, host, port, route, or workspace id. Results are
`CANONICAL`, redacted, and capped; a missing profile, denied route, or
unreachable backend fails closed.

| Tool | Backend route (read-only) | Caps |
| --- | --- | --- |
| `search_decisions` | ConPort `GET /api/decisions` (or `GET /api/search/{ws}?type=decisions` when `query` set) | limit ≤ 20 |
| `search_progress` | ConPort `GET /api/progress` | limit ≤ 20 |
| `search_chronicle` | dope-memory `POST /tools/memory_search` (side-effect-free read) | `top_k` ≤ 3 |
| `replay_chronicle_session` | dope-memory `POST /tools/memory_replay_session` | `top_k` ≤ 3; mode defaults `replay_current` |

### Allowed / denied route manifest

The adapters can issue **only** the routes above (see `route_manifest.py`). POST
is permitted **only** for the two side-effect-free dope-memory reads via an
explicit path allowlist; there is no put/patch/delete and no generic request
surface. **Denied** (structurally unreachable, regression-tested): ConPort
`POST /api/decisions` / `POST /api/progress` / `*/custom_data`; dope-memory
`memory_correct` / reflection / store / mark-issue / link-resolution;
dopecon-bridge `/ddg/`; and any `/kg/` / `/route/pm` PM-write route.

### `search_progress` is fail-closed (auto-fork hazard)

ConPort's default enhanced server is **not** read-only for `GET /api/progress`:
with `DOPEMUX_AUTO_FORK_PROGRESS=1` (the default), `_get_progress` *auto-forks
(writes)* progress rows from shared when the requested workspace has none. The
facade cannot suppress that per-request, so `search_progress` is **blocked by
default** and only runs when the operator sets
`service_profiles.conport.progress_readonly_safe: true` — which you should do
**only after** setting `DOPEMUX_AUTO_FORK_PROGRESS=0` on that ConPort backend.
(`search_decisions` / `search_chronicle` / `replay_chronicle_session` have no
such write-on-read behavior.)

### Security controls

- **Loopback-only** `base_url` (validated via `ipaddress.is_loopback`; non-loopback / unspecified hosts rejected — SSRF guard).
- **Response size cap** (`MAX_RESPONSE_BYTES`, streamed); oversized → fail closed.
- **JSON parsed only for 2xx**; non-2xx → `PARTIAL` with no body.
- `workspace_id` is percent-encoded as a single path segment (rejects `/` / `..`).
- Backend payloads pass through the same redaction as local reads (paths + secrets).

### Optional live tests

The test suite mocks all HTTP (no live calls). To additionally run the
opt-in live smoke tests against real local backends:

```bash
export DCP_FACADE_LIVE_TESTS=1
export DCP_FACADE_REGISTRY=~/.dopemux/dcp-facade-registry.yaml   # must point at a real enabled project
python -m pytest -q services/dcp-readonly-facade/tests/test_live_optional.py
```

They are **skipped by default** (no env flag → skipped).
