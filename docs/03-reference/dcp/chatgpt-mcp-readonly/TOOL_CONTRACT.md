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
| `list_proof_bundles` | yes | filesystem (proof roots) | OBSERVED/fs | packet_id regex; bounded to proof roots. |
| `fetch_proof_bundle` | yes | filesystem (proof roots) | OBSERVED/fs | Cannot cross project root; symlink-escape blocked. |

### 1b. ConPort + dope-memory read tools — packet 0005

| Tool | Backing surface (OBSERVED) | Method | Authority | Wrapper constraints |
| --- | --- | --- | --- | --- |
| `search_decisions` | conport `/api/decisions` (GET) and/or `/api/search/{workspace_id}` (GET) | GET | CANONICAL | max-20 pagination; workspace scope; sanitize workspace param |
| `search_progress` | conport `/api/progress` (GET) | GET | CANONICAL | workspace filter; max page limit |
| `search_chronicle` | dope-memory `/tools/memory_search` (POST) | POST | CANONICAL | POST allowed (side-effect-free read); `top_k=3` |
| `replay_chronicle_session` | dope-memory `/tools/memory_replay_session` (POST) | POST | CANONICAL | session-bounded; prefer `replay_current` mode |

### 1c. dope-context + task-orchestrator read tools — packet 0006

| Tool | Backing surface | Source | Transport | Authority | Notes |
| --- | --- | --- | --- | --- | --- |
| `search_code_docs` | dope-context `search_code` + `docs_search` | `OBSERVED` (inventory) | MCP | DERIVED | direct; hits DERIVED until exact-source fetch exists |
| `get_index_status` | dope-context index status | `PROPOSED` (load-pack 0006 scope; **not** in inventory) | MCP | DERIVED | ⚠️ no inventoried surface — see note below |
| `get_workflow_status_snapshot` | task-orchestrator `/queue` + `/blockers` (GET) | `OBSERVED` (inventory) | HTTP | CANONICAL | workflow-view only, **not** PM truth; strip identities. **Incomplete — see `/state` note below.** |

> ⚠️ **`get_index_status` is not backed by the discovery inventory.** The committed `READ_ONLY_SURFACE_INVENTORY.json` inventories only `search_code`, `docs_search`, and `search_all` for dope-context. `get_index_status` is named in the TP-DCP-MCP-RO-0006 load-pack scope but has **no** read-only classification, side-effect review, or evidence trail. Before 0006 exposes it, it **must** be added to the inventory with `OBSERVED` evidence (route/method/classification/side-effect notes) — or deferred. Until then it is `PROPOSED` only and must not be wired into the allowlist.

> ⚠️ **`/state` is an OBSERVED runtime route missing from the inventory.** task-orchestrator exposes a first-class GET read endpoint `/api/projects/{project_id}/workflow/state` — `OBSERVED` at `services/task-orchestrator/app/api/project_workflow.py:385` (`@router.get("/state", response_model=WorkflowStateResult)`; returns the workflow snapshot, phases/stages, `allowed_transitions`, and linked workflow/PM IDs), and the existing PM adapter already calls it (`src/dopemux/pm/adapters/orchestrator.py:48`). It is **not** in the discovery inventory and is **not** in the `get_workflow_status_snapshot` backing-surface row above, which currently lists only `/queue` + `/blockers`. Consequence: as contracted, `get_workflow_status_snapshot` is **incomplete** — it omits the `state`/`allowed_transitions` data runtime already provides. Before 0006 implements the snapshot, `/state` **must** be inventoried and classified (route/method/read-only/side-effect evidence) and added to this row — or explicitly deferred like `get_index_status`. Until then, `/state` is `OBSERVED`-but-`UNCLASSIFIED` and must not be wired into the allowlist. (The discovery gap belongs to TP-DCP-MCP-RO-0001; this packet flags it rather than re-authoring 0001's inventory.)

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
