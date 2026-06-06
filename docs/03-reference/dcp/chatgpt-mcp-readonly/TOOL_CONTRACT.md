---
id: dcp-mcp-readonly-tool-contract
title: DCP Read-Only MCP Facade — Tool Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Phase-1 tool contract, allowed/denied routes, and authority labels for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Tool Contract

> **Status.** Tool names and groupings are `PROPOSED` (from the build series / load pack). Per-route classifications, methods, ports, and authority labels are `OBSERVED` from [`READ_ONLY_SURFACE_INVENTORY.json`](READ_ONLY_SURFACE_INVENTORY.json). Every project-scoped tool requires `project_id`; `list_projects` is the only exemption. Search/list limits are capped at **20** unless a tool lowers the cap.

## 1. Phase-1 Tools

### 1a. Local / git tools (no backend service call) — packet 0004

| Tool | `project_id`? | Backing surface | Authority | Notes |
| --- | --- | --- | --- | --- |
| `list_projects` | no | registry | facade | Returns approved (`enabled`) projects only. |
| `get_project_capabilities` | yes | registry + reachability | facade | Reports which backends are bound/available. |
| `get_repo_state_snapshot` | yes | local git (fixed cmd allowlist) | OBSERVED/git | branch, head_sha, dirty state. No arbitrary git. |
| `list_proof_bundles` | yes | filesystem (proof roots) | OBSERVED/fs | optional `packet_id_filter` = **literal substring** (≤128 chars, **not** a regex — avoids ReDoS); bounded to proof roots; cap 20. |
| `fetch_proof_bundle` | yes | filesystem (proof roots) | OBSERVED/fs | Cannot cross project root; symlink-escape blocked; bounded read (256KB/file). |

> **Note (0004 implementation):** `list_proof_bundles`' filter is a literal substring, not a regex. Accepting an untrusted caller-supplied regex is a ReDoS (catastrophic-backtracking) DoS surface; the scaffold therefore matches a bounded literal substring instead. The 0001 inventory / earlier drafts referred to a "packet_id regex" — superseded here for safety.

### 1b. ConPort + dope-memory read tools — packet 0005

| Tool | Backing surface (OBSERVED) | Method | Authority | Wrapper constraints |
| --- | --- | --- | --- | --- |
| `search_decisions` | conport `/api/decisions` (GET) — list only; `/api/search/{ws}` (GET) **deferred** ⚠️ | GET | CANONICAL | max-20; **`query` mode deferred** (note ‡) |
| `search_progress` | conport `/api/progress` (GET) | GET | CANONICAL | max page; **fail-closed** unless `progress_readonly_safe` (note †) |
| `search_chronicle` | dope-memory `/tools/memory_search` (POST) | POST | CANONICAL | POST allowed (side-effect-free read); `top_k=3` |
| `replay_chronicle_session` | dope-memory `/tools/memory_replay_session` (POST) | POST | CANONICAL | session-bounded; prefer `replay_current` mode |

> † **`search_progress` is fail-closed.** ConPort's default enhanced server auto-forks (writes) progress rows when a workspace has none (`DOPEMUX_AUTO_FORK_PROGRESS=1`), so a read can mutate. `search_progress` is BLOCKED unless the registry conport profile sets `progress_readonly_safe: true` — set only after `DOPEMUX_AUTO_FORK_PROGRESS=0` on the backend.
>
> ‡ **`search_decisions` query mode is deferred.** ConPort `GET /api/search/{ws}` returns HTTP 500 in the default enhanced server (it builds the result without serializing the UUID `id` before `json.dumps`). The facade does not expose a broken read: a `query` returns `PARTIAL` with a deferral note; list mode (`GET /api/decisions`, which serializes ids) is unaffected. The `conport.search` adapter is implemented and ready for when the backend is fixed.

### 1c. dope-context + task-orchestrator read tools — packet 0006

| Tool | Backing surface | Source | Transport | Authority | Notes |
| --- | --- | --- | --- | --- | --- |
| `search_code_docs` | dope-context `search_code` + `docs_search` | `OBSERVED` (inventory) | MCP | DERIVED | **Phase 1: BLOCKED** — MCP JSON-RPC transport not yet bridged in facade (REST-only client). Hits will be DERIVED until transport bridge + exact-source fetch exist. |
| `get_index_status` | dope-context index status | `PROPOSED` (load-pack 0006 scope; **not** in inventory) | MCP | DERIVED | **Phase 1: BLOCKED** — MCP transport gap + not in inventory. ⚠️ requires formal inventory + classification before allowlist wiring (Phase 2). |
| `get_workflow_status_snapshot` | task-orchestrator `/queue` + `/blockers` + `/state` (GET) | `OBSERVED` (inventory + TP-0006 gap resolved) | HTTP | CANONICAL | workflow-view only, **not** PM truth; strip identities. `/state` classified CONFIRMED_READ_ONLY in TP-0006 (see note below). |

> **`get_index_status` (Phase 1 BLOCKED):** dope-context exposes all tools via MCP JSON-RPC at `/mcp` — not REST. The facade's `ReadOnlyHttpClient` speaks REST only; no REST routes exist at `/search/code`, `/search/docs`, or `/index/status`. `get_index_status` is additionally `PROPOSED`-only (not in the discovery inventory). Both gaps must be closed before Phase 2 can expose it: (1) transport bridge from facade to MCP JSON-RPC, (2) formal inventory + classification of `get_index_status` with read-only + side-effect evidence.

> **`/state` gap resolved (TP-0006):** task-orchestrator exposes `/api/projects/{project_id}/workflow/state` as a first-class GET read endpoint (`project_workflow.py:385`, `@router.get("/state", response_model=WorkflowStateResult)`). Evidence: (1) confirmed GET at line 385; (2) existing PM adapter calls it (`src/dopemux/pm/adapters/orchestrator.py:48`); (3) no write path or side effects observed. **Classified CONFIRMED_READ_ONLY.** Added to `get_workflow_status_snapshot` backing-surface row above. The 0001 inventory gap is noted but not retroactively modified (0001 is a committed artifact).

## 2. Denied Routes / Tools (Phase 1)

`OBSERVED` denials from the inventory (`chatgpt_tunnel_suitability: DENY` or load-pack decision):

| Surface | Reason |
| --- | --- |
| conport `POST /api/decisions` | MUTATING — writes decision records, publishes events. |
| dope-memory `POST /tools/memory_correct` | MUTATING — inserts corrections/retractions into the chronicle ledger. |
| task-orchestrator `POST .../workflow/transition` | MUTATING — mutates task status, updates sprint metrics. |
| dopecon-bridge `GET /ddg/decisions` | PROXY — transport-confusion risk; read ConPort directly. |
| dope-context `search_all` | READ_WITH_SIDE_EFFECT_RISK — network call to dopecon-bridge + Redis ops. |

Also denied implicitly: any task-orchestrator transition / `manage_*` / `advance_item` / `claim_item` write tool, any dope-context `index_*` / `sync_*` / `clear_index` / `*_autonomous_*` control, ConPort `POST /api/progress` / `POST /api/custom_data`, and any generic search/fetch. No arbitrary path, URL, port, backend route, SQL, or shell is ever accepted on any tool.

### Deferred reads (counted in the inventory's 7 denied)

| Surface | Classification | Why deferred |
| --- | --- | --- |
| conport `GET /api/custom_data` | CONFIRMED_READ_ONLY | redaction-sensitive; not surfaced as a Phase-1 tool. |
| conport `GET /api/search/{workspace_id}` *or* `GET /api/decisions` | CONFIRMED_READ_ONLY | one of the two backs `search_decisions`; the other is not separately exposed. |

> `PROPOSED`/`CONFLICTING`: the inventory has no per-surface `phase_1_recommended` flag, so the exact identity of the second deferred read is inferred to reconcile to `deny_for_phase_1: 7`. Resolved concretely when `search_decisions` is implemented (0004/0005).

## 3. Authority Labels

Every tool result is enveloped (see [`RESPONSE_ENVELOPE_SCHEMA.md`](RESPONSE_ENVELOPE_SCHEMA.md)) with an `authority_label`:

- `CANONICAL` — ConPort, dope-memory, dope-context `search_code`/`docs_search`, task-orchestrator queue/blockers.
- `DERIVED` — fused/computed results (e.g. `search_all` if ever enabled; dope-context hits pending exact-source fetch).
- `PROXY` — dopecon-bridge (denied in Phase 1).

Retrieved content additionally retains `OBSERVED` / `PROPOSED` / `UNKNOWN` / `CONFLICTING` provenance where the facade can determine it, and is wrapped as untrusted for prompt-injection safety (see [`SECURITY_MODEL.md`](SECURITY_MODEL.md)).
