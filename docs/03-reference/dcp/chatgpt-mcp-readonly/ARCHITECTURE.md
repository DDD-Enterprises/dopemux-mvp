---
id: dcp-mcp-readonly-architecture
title: DCP Read-Only MCP Evidence Facade — Architecture
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Architecture of the multi-project read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# DCP Read-Only MCP Evidence Facade — Architecture

> **Authority note.** This document is design guidance for the facade. It is **not** an authority over the systems it projects. Runtime code, schemas, and the committed [`READ_ONLY_SURFACE_INVENTORY.json`](READ_ONLY_SURFACE_INVENTORY.json) (the TP-DCP-MCP-RO-0001 discovery artifact, `head_sha 9667f5e2d`) outrank this prose. Where this document asserts a runtime fact, it is labelled `OBSERVED`; design intent is labelled `PROPOSED`; gaps are `UNKNOWN`.

## 1. Overview and Purpose

The DCP read-only MCP evidence facade is a single, **loopback-only** local MCP server that projects repository truth, execution state, and structured context from a dopemux workspace to ChatGPT (via a Secure MCP Tunnel) for evidence-gathering. It holds **no write authority** and is an **evidence projection layer, not a canonical source**.

The facade exists so that ChatGPT can read proof bundles, decisions, progress, chronicle records, code/doc search results, and workflow status **without** ChatGPT gaining direct access to any backend MCP server, arbitrary filesystem path, URL, port, backend route, SQL, or shell.

## 2. Component Boundaries

| Component | Responsibility |
| --- | --- |
| **Project Registry** | Explicit operator-approved list of exposed projects. Eligibility (a `dopemux init` workspace) ≠ exposure (a registry entry). |
| **Workspace Resolver** | Maps a caller-supplied `project_id` to a canonical, symlink-resolved path inside an approved root. Rejects unknown/disabled projects and path-escape attempts. |
| **Response Envelope** | Normalizes every tool result into a canonical structure carrying provenance, authority labels, freshness, limitations, warnings, redactions, and blocked reasons. See [`RESPONSE_ENVELOPE_SCHEMA.md`](RESPONSE_ENVELOPE_SCHEMA.md). |
| **Redaction Layer** | Strips secrets, tokens, and absolute paths from payloads before they leave the facade. |
| **Read Adapters** | Per-system clients (ConPort, dope-memory, dope-context, task-orchestrator) bound to a strict route/method allowlist. |
| **Tools** | MCP tool surface exposed to the tunnel; strictly bounded to read operations. See [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md). |

## 3. Data Flow

```
ChatGPT (client)
   → Secure MCP Tunnel (loopback only)
      → DCP Read-Only Facade
         → Project Registry (validate project_id, enabled)
         → Workspace Resolver (project_id → canonical path)
         → Read Adapter (route/method allowlist)
            → backend: ConPort | dope-memory | dope-context | task-orchestrator
         → Response Envelope + Redaction
   ← enveloped, redacted, authority-labelled result
```

Every request except `list_projects` carries a `project_id`. No request carries a raw path, URL, port, backend route, SQL fragment, or shell command. `dopecon-bridge` is **not** in the data path (see §14).

## 4. Phase 1 Scope and Limitations

`OBSERVED` from the discovery inventory summary: **15 surfaces** were inventoried across 5 systems — 11 confirmed read-only, 1 read-with-side-effect-risk, 3 mutating. **8 surfaces are recommended for Phase 1; 7 are denied** (see §15 for the reconciliation).

Phase 1 limitations:

- **No live writes.** All mutating surfaces are denied (§15).
- **No `dopecon-bridge`.** The proxy layer is denied in favour of direct reads (§14).
- **No `search_all`.** Its decision-fusion path triggers a network call to `dopecon-bridge` and Redis side effects (`OBSERVED`); denied for Phase 1.
- **No generic search/fetch.** Phase 1 exposes only the Dopemux-specific evidence tools enumerated in [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md).
- **Search/list limits capped at 20** unless a specific tool lowers the cap (e.g. chronicle `top_k=3`).

## 5. Multi-Project Registry Design

The registry is the trust boundary. It is an explicit, operator-maintained mapping of `project_id → { workspace_path, enabled, service_profiles }`. A workspace becoming `dopemux init`-eligible does **not** auto-expose it; a registry entry plus `enabled: true` is required. Full schema and validation rules live in [`MULTI_PROJECT_REGISTRY_CONTRACT.md`](MULTI_PROJECT_REGISTRY_CONTRACT.md). The exact `dopemux init` marker contract is `UNKNOWN` at this packet and is resolved in TP-DCP-MCP-RO-0003.

## 6. Workspace Resolver

`PROPOSED`. The resolver takes a `project_id`, looks it up in the registry, and resolves the registered `workspace_path` to a canonical absolute path (following symlinks). It then verifies the canonical path is contained within an approved root. Requests for unknown projects, disabled projects, or paths that escape the approved root (including via symlink) fail closed with a `BLOCKED` envelope.

## 7. Response Envelope Structure

Every payload — success, partial, or blocked — is wrapped in the canonical envelope (`project_id`, `branch`, `head_sha`, dirty state, `source_system`, `authority_label`, `freshness`, `limitations`, `warnings`, `redactions`, `blocked_reasons`, `data`). A missing backend capability returns `PARTIAL` or `BLOCKED`, **never guessed data**. See [`RESPONSE_ENVELOPE_SCHEMA.md`](RESPONSE_ENVELOPE_SCHEMA.md).

## 8. Redaction Baseline

`PROPOSED`. Before any payload leaves the facade: absolute filesystem paths are redacted by default; secret/token patterns (API keys, bearer tokens, passwords) are stripped; ConPort `custom_data` and similar unstructured stores are treated as redaction-sensitive (`OBSERVED` security note: "Custom data may contain unstructured metadata; ensure sensitive items are redacted").

## 9. Tool Taxonomy

Phase-1 tools fall into two classes (full contract in [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md)):

- **Local / git tools** (no backend service call): `list_projects`, `get_project_capabilities`, `get_repo_state_snapshot`, `list_proof_bundles`, `fetch_proof_bundle`.
- **Service-backed read tools**: `search_decisions`, `search_progress`, `search_chronicle`, `replay_chronicle_session` (ConPort + dope-memory); `search_code_docs`, `get_index_status`, `get_workflow_status_snapshot` (dope-context + task-orchestrator).

## 10. ConPort Adapter Design

`OBSERVED` surfaces (system `conport`, HTTP, port 3004, `docker/mcp-servers-source/conport/enhanced_server.py`):

| Route | Method | Classification | Phase-1 |
| --- | --- | --- | --- |
| `/api/decisions` | GET | CONFIRMED_READ_ONLY | allow (wrap: max-20 pagination, workspace scope) |
| `/api/decisions` | POST | MUTATING | **deny** |
| `/api/progress` | GET | CONFIRMED_READ_ONLY | allow (wrap: workspace filter, max page) |
| `/api/search/{workspace_id}` | GET | CONFIRMED_READ_ONLY | allow / deferred (see §15) |
| `/api/custom_data` | GET | CONFIRMED_READ_ONLY | deferred (redaction-sensitive) |

ConPort authority label: `CANONICAL`. The adapter binds a project to a ConPort `workspace_id`; the caller cannot select the `workspace_id`.

## 11. dope-memory Adapter Design

`OBSERVED` surfaces (system `dope-memory`, HTTP, port 3020, `services/working-memory-assistant/dope_memory_main.py`):

| Route | Method | Classification | Phase-1 |
| --- | --- | --- | --- |
| `/tools/memory_search` | POST | CONFIRMED_READ_ONLY | allow (POST, but side-effect-free DB lookup; wrap `top_k=3`) |
| `/tools/memory_replay_session` | POST | CONFIRMED_READ_ONLY | allow (prefer `replay_current` mode) |
| `/tools/memory_correct` | POST | MUTATING | **deny** |

`OBSERVED` nuance: `memory_search`/`memory_replay_session` use **POST** but are read-only; the adapter allows POST **only** for these explicitly classified read routes. `memory_correct` inserts corrections/retractions and is denied.

## 12. dope-context Adapter Design

`OBSERVED` surfaces (system `dope-context`, MCP transport, port 3010, `services/dope-context/src/mcp/server.py`):

| Tool | Classification | Authority | Phase-1 |
| --- | --- | --- | --- |
| `search_code` | CONFIRMED_READ_ONLY | CANONICAL | allow (direct) |
| `docs_search` | CONFIRMED_READ_ONLY | CANONICAL | allow (direct) |
| `search_all` | READ_WITH_SIDE_EFFECT_RISK | DERIVED | **deny** |

`OBSERVED`: `search_all` fuses code + docs + decisions and "calls an external HTTP client that sends a network request to dopecon-bridge, which triggers Redis operations" — hence its side-effect risk and Phase-1 denial. Phase-1 dope-context hits are labelled `DERIVED` unless an exact-source fetch is implemented later.

## 13. task-orchestrator Adapter Design

`OBSERVED` surfaces (system `task-orchestrator`, HTTP, port 8000, `services/task-orchestrator/app/api/project_workflow.py`):

| Route | Method | Classification | Phase-1 |
| --- | --- | --- | --- |
| `/api/projects/{project_id}/workflow/queue` | GET | CONFIRMED_READ_ONLY | allow (validate `project_id`, strip identities) |
| `/api/projects/{project_id}/workflow/blockers` | GET | CONFIRMED_READ_ONLY | allow (direct) |
| `/api/projects/{project_id}/workflow/transition` | POST | MUTATING | **deny** |

task-orchestrator status is **workflow-view only**, not PM-metadata truth. `OBSERVED` red-lane finding: unregistered PM routes in `app/api/pm_tools.py` (e.g. `/api/pm/work-items/{task_id}/update`) are defined but never included in `app/main.py` — code drift; mutating endpoints are not active in the running service. The facade must still deny these by route, not rely on them being unregistered.

## 14. dopecon-bridge Denylist

`OBSERVED` surface (system `dopecon-bridge`, HTTP, port 3016, `services/dopecon-bridge/dopecon_bridge/routes.py`): `GET /ddg/decisions` is `CONFIRMED_READ_ONLY` but authority label `PROXY`. It is **denied** for Phase 1: it is a proxy to ConPort `GET /api/decisions`, and "introducing proxy layers in the tunnel increases transport confusion risks." The facade reads ConPort directly to preserve authority boundaries.

## 15. Phase-1 Denylist (reconciliation)

The inventory summary states **8 recommended / 7 denied** (= 15). The denied 7 are:

**Hard denies (5):**
1. ConPort `POST /api/decisions` — MUTATING.
2. dope-memory `POST /tools/memory_correct` — MUTATING.
3. task-orchestrator `POST .../workflow/transition` — MUTATING.
4. dopecon-bridge `GET /ddg/decisions` — PROXY, transport-confusion risk.
5. dope-context `search_all` — READ_WITH_SIDE_EFFECT_RISK (bridge + Redis).

**Deferred reads (2):** two `CONFIRMED_READ_ONLY` ConPort surfaces — `GET /api/custom_data` (redaction-sensitive) and one of `GET /api/search/{workspace_id}` / `GET /api/decisions` — are **not exposed as distinct Phase-1 tools** and are therefore counted among the 7.

> `CONFLICTING`/`PROPOSED`: the discovery inventory carries a per-surface `chatgpt_tunnel_suitability` field (`ALLOW` / `ALLOW_AFTER_WRAPPER` / `DENY`) but **no explicit per-surface `phase_1_recommended` flag**. The exact identity of the 2 deferred reads above is therefore an inference required to reconcile to the summary's `deny_for_phase_1: 7`; it is not directly asserted by the inventory. The 8 recommended surfaces are: ConPort GET decisions + GET progress; dope-memory search + replay; dope-context search_code + docs_search; task-orchestrator queue + blockers.

## 16. Security Controls Summary

Loopback-only binding; explicit registry approval; `project_id` required on every project-scoped tool; no arbitrary path/URL/port/route/SQL/shell; fixed git command allowlist; symlink-escape prevention; default redaction of absolute paths and secrets; fail-closed on unavailable backends; all retrieved content treated as untrusted and wrapped against prompt injection. Full model in [`SECURITY_MODEL.md`](SECURITY_MODEL.md).

## 17. Authority and Source Labels

Every envelope carries `source_system` and `authority_label`. `OBSERVED` labels from the inventory: ConPort, dope-memory, dope-context (`search_code`/`docs_search`), task-orchestrator = `CANONICAL`; `search_all` = `DERIVED`; dopecon-bridge = `PROXY`. Facade-computed or fused results are labelled `DERIVED`. The facade itself is never labelled an authority.

## 18. Phase 2 Deferral Scope

`PROPOSED`. Deferred beyond Phase 1: generic search/fetch tools; `search_all` (pending side-effect isolation and source-label integrity); exact-source fetch for dope-context hits (to upgrade `DERIVED` → `CANONICAL`); `dopecon-bridge` routing; `/api/custom_data` exposure with category/key restriction.

## 19. Deployment Topology

`PROPOSED`. One facade process per exposed workspace set, bound to loopback, fronted by a Secure MCP Tunnel client that points **only** at the facade endpoint — never at a backend service. Implementation lives under `services/dcp-readonly-facade/` (decided; see [`DECISIONS.md`](DECISIONS.md)). Tunnel integration is documented in TP-DCP-MCP-RO-0007.

## 20. Unknowns and Open Questions

- `UNKNOWN`: the `dopemux init` marker / workspace-identity contract (resolved in TP-DCP-MCP-RO-0003).
- `UNKNOWN` (`unresolved_questions` in the inventory): "Should dope-memory be queried directly, or should all chronicle reads be multiplexed through a facade wrapper to normalize output for ChatGPT?"
- `CONFLICTING`/`PROPOSED`: the precise 8/7 surface split (see §15).
- `UNKNOWN`: whether `/api/search/{workspace_id}` or `/api/decisions` backs `search_decisions` (deferred to scaffold packet 0004/0005).
