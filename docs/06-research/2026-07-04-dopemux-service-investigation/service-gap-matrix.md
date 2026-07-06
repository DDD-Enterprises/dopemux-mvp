---
id: service-gap-matrix
title: Service Gap Matrix
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Service Gap Matrix (reference) for dopemux documentation and developer workflows.
---
# Dopemux Service Gap Matrix

This matrix classifies every observed top-level `services/*` candidate plus compose-only and registry-only services. It distinguishes active runtime authority from source-only, duplicate, support, adapter, and unknown surfaces.

Legend:

- OBSERVED: directly supported by repo files/config.
- INFERRED: best interpretation from nearby evidence.
- UNKNOWN: not proven by inspected runtime/config/tests.
- PROPOSED: recommended target or follow-up, not current state.

## Directory Candidates

| Candidate | Compose | Registry | Classification | Observed role | Gap / risk | Recommended next action |
|---|---:|---:|---|---|---|---|
| `services/.claude` | no | no | non-service artifact | Claude-local service subtree metadata. | Can inflate service counts if treated as runtime. | Exclude from operational health; keep in raw inventory only. |
| `activity-capture` | no | no | support/unknown | FastAPI service consumes `dopemux:events` and sends content-free activity to ADHD Engine. | Not compose/registry wired in canonical stack. | Promote to support service only after compose/registry wiring and smoke tests. |
| `adhd-dashboard` | no | no | support/unknown | Backend proxies ADHD Engine, activity-capture metrics, Redis state streams, and dashboard WebSocket. | README references stale compose file; not active in canonical compose. | Add explicit registry/compose decision or mark source-only dashboard backend. |
| `adhd-engine` | `adhd-engine` | `adhd-engine` | duplicate naming drift | Hyphenated tree contains only `auth.py` in inspected max-depth inventory. | Can be confused with active `adhd_engine`. | Retire, redirect, or document as duplicate residue. |
| `adhd-notifier` | no | no | support/unknown | Break/hyperfocus notification service with Dockerfile and monitor logic. | Not active in canonical compose/registry. | Wire as optional support service or archive. |
| `adhd_engine` | `adhd-engine` | `adhd-engine` | active canonical support runtime | FastAPI + FastMCP ADHD/operator-support runtime. | Broad routes/event paths; durable store and event listener guarantees remain mixed. | Keep as operator-support authority only; add integration hardening packets. |
| `adhd_notifier` | no | no | duplicate/support | Minimal import package for mobile push. | Duplicates hyphenated notifier family. | Consolidate import package or document its purpose. |
| `agents` | no | no | unknown/experimental | Multiple agent implementations and tests. | Repo-wide agent authority remains UNKNOWN. | Keep out of canonical UX until runtime owner is proven. |
| `claude_brain` | no | no | experimental/unknown | Claude adaptation/proactive intervention service code with Dockerfile. | Not canonical compose/registry. | Archive or define support boundary. |
| `complexity_coordinator` | no | no | support/unknown | Unified complexity helper. | Not wired as service. | Treat as library unless promoted. |
| `conport_kg` | no | no | drift/unknown | AGE/KG integration helpers. | Overlaps ConPort authority but not active canonical ConPort runtime. | Keep distinct from ConPort; document as adjacent tooling. |
| `conport_kg_ui` | no | no | drift/unknown | UI package for KG-adjacent surface. | Not compose/registry canonical. | Mark source-only until deployed. |
| `copilot_transcript_ingester` | no | no | support/unknown | Transcript ingestion package. | No active runtime wiring found. | Keep as tool/support candidate. |
| `dcp-readonly-facade` | no | no | adapter/support | Read-only DCP facade with tests. | Not active compose service. | Preserve as read-only adapter; do not promote to authority. |
| `dddpg` | no | no | experimental/support | Bridge/KG integration helpers and tests. | Not active service. | Archive or document as support library. |
| `dope-context` | `dope-context` | `dope-context` | canonical retrieval runtime | Dockerized code/docs retrieval and indexing surface. | Derived retrieval can be mistaken for source truth. | Keep retrieval-only in UX. |
| `dope-memory` | `dope-memory` | `dope-memory` | adapter/drift | Directory only shows MCP stdio adapter; compose uses working-memory-assistant Dockerfile. | Directory name does not contain full runtime. | Label runtime path explicitly in Cockpit/service inventory. |
| `dope-query` | no | no | legacy | Sparse old retrieval/query surface per catalog. | Could be mistaken for active retrieval. | Archive or add pointer to dope-context/ConPort. |
| `dopecon-bridge` | `dopecon-bridge` | `dopecon-bridge` / `dopecon-bridge-alt` | active proxy/transport | Bridge/proxy/event routing service. | Broad surface looks authoritative, but is not. | UX must show "proxy only" provenance on all bridge-backed data. |
| `dopemux-gpt-researcher` | no (`gptr-mcp` compose) | `gpt-researcher` | active-but-drifted/source-only | Research API implementation and tests. | Compose builds separate Docker MCP source. | Reconcile in-repo implementation vs Docker wrapper. |
| `intelligence` | no | no | support/unknown | Pattern correlation engine. | Not service-wired. | Treat as library unless promoted. |
| `mcp-capture` | no | no | support/unknown | MCP capture server/test surface. | Not registry/compose active. | Decide if capture belongs in operator observability. |
| `mcp-client` | no | no | adapter | Utility MCP client. | Owns no domain truth. | Keep as diagnostic tool only. |
| `mcp-integration-bridge` | no | no | duplicate/adapter drift | KG endpoint/bridge-like code. | Overlaps dopecon-bridge. | Archive or prove active usage. |
| `ml-predictions` | no | no | support/unknown | LSTM cognitive predictor service code. | ADHD Engine has internal ML modules too. | Consolidate ML prediction ownership. |
| `ml-risk-assessment` | no | no | support/unknown | Risk assessment engine. | Not active compose/registry. | Treat as future support until wired. |
| `monitoring` | no | no | support library | Health and Prometheus helper modules. | Not a standalone service. | Use as shared library; exclude from service health rows. |
| `monitoring-dashboard` | no | no | support/unknown | Monitoring dashboard server with Dockerfile. | Not active canonical compose. | Decide whether Cockpit supersedes it. |
| `repo-truth-extractor` | no | no | canonical audit subsystem | v5 extraction/audit runtime. | Not compose service; live/provider gates must stay explicit. | Keep as audit runtime, not source truth. |
| `router` | no | no | package/unknown | Empty/minimal router package. | No service evidence. | Exclude from UX except raw inventory. |
| `serena` | `serena` | `serena` | active-but-drifted support/MCP | Code intelligence and F001 detection implementation. | Compose uses Docker wrapper; enhanced F001 tool is implemented but not registered/callable. | Add F001 Enhanced registration packet and deployment authority reconciliation. |
| `session-intelligence` | no | no | support/unknown | README and bridge adapter. | Duplicate with underscore package. | Consolidate naming and authority. |
| `session-manager` | no | no | support/unknown | Session orchestrator/TUI demo package. | Not canonical service. | Define if it belongs under Cockpit or archive. |
| `session_intelligence` | no | no | support/unknown | Python coordinator package. | Naming drift with hyphenated service. | Consolidate or document import/runtime split. |
| `shared` | no | no | support library | Shared brand voice, exceptions, workspace utilities. | Not service runtime. | Keep library-only. |
| `slack-integration` | no | no | adapter/unknown | Slack notifier. | No active wiring. | Mark optional integration. |
| `task-orchestrator` | `task-orchestrator` | `task-orchestrator` | active canonical workflow surface with drift | Workflow coordination and PM transition service. | Legacy files and multiple paths still confuse runtime authority. | Keep canonical runtime path explicit; avoid local DB authority overclaims. |
| `task-router` | no | no | unknown/legacy | Routing/matching helpers. | Not current canonical stack. | Archive or prove active use. |
| `voice-commands` | no | no | experimental/support | Voice API/task decomposer with Dockerfile. | Not active compose/registry. | Treat as future optional support. |
| `webhook_receiver` | `webhook-receiver`, `webhook-poller` | `webhook-receiver` | active support | Provider webhook ledger and poller. | Registry omits poller row. | Add poller registry row or document as subordinate worker. |
| `working-memory-assistant` | `dope-memory` | `dope-memory` | canonical runtime path plus support service | Hosts dope-memory runtime and separate WMA support surface. | Tree layout blurs dope-memory vs WMA. | Split service labels in UX: dope-memory runtime vs WMA support. |
| `workspace-watcher` | no | no | support/unknown | Active app/workspace event emitter. | Not active canonical compose. | Wire into optional ADHD loop or archive. |

## Compose-Only / Registry-Only Surfaces

| Surface | Source | Classification | Gap / risk | Recommended next action |
|---|---|---|---|---|
| `conport` | compose | canonical externalized runtime | Registry splits into `conport-http` and `conport-mcp`. | UX should group both rows under one ConPort service. |
| `desktop-commander` | compose/registry | adapter/MCP | Docker source outside `services/*`. | Show as MCP tool adapter, not repo-owned domain service. |
| `exa` | compose/registry | adapter/MCP | External search surface. | Mark external/search adapter with credential state unknown. |
| `gptr-mcp` | compose | adapter/MCP | Registry calls it `gpt-researcher`. | Normalize display alias. |
| `leantime` | compose/registry | PM metadata app | External PM app, not repo-owned service code. | Show as PM metadata authority. |
| `leantime-bridge` | compose/registry | adapter | Bridge to Leantime. | Show upstream authority as Leantime. |
| `litellm` | compose/registry | model routing support | External/provider-dependent. | Show as routing support, not model authority. |
| `mcp-qdrant` / `qdrant` | compose/registry alias | infrastructure | Name mismatch. | Normalize alias in service model. |
| `mysql_leantime` | compose | infrastructure | No registry row. | Decide whether infra rows appear in Cockpit. |
| `pal` / `pal-stdio` | compose/registry partial | adapter/MCP | `pal-stdio` compose row lacks registry row. | Document as PAL transport variant. |
| `postgres` | compose/registry | infrastructure | Shared backing store. | Show as infrastructure dependency. |
| `redis-events` | compose/registry | infrastructure/event bus | Event stream dependency. | Show stream name/provenance in event UX. |
| `redis-primary` | compose/registry | infrastructure/cache | Shared cache/state. | Show as infra, not domain authority. |
| `redis-ui` | compose | optional infra UI | No registry row. | Keep hidden or optional. |
| `redis_leantime` | compose | Leantime infra | No registry row. | Group under Leantime. |
| `webhook-poller` | compose | worker/adapter | Not registry-listed. | Add registry row if operator-visible. |

## Integration Quality Summary

- Strongest active spine: `dopemux`, Task Orchestrator, ConPort, dope-memory, dope-context, dopecon-bridge, ADHD Engine, Repo Truth Extractor, Leantime, Serena, and core MCP/infrastructure containers.
- Highest-risk gaps: F001 Enhanced not registered, Cockpit lacks live F001/ADHD data source, source-only service directories overinflate actionable services, and dashboard/fallback surfaces need provenance.
- Best next UX move: build a normalized service model that groups aliases, exposes provenance, and limits actions to safe inspect/receipt flows until each service has proof gates.
