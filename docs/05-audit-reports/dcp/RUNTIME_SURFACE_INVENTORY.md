---
id: RUNTIME_SURFACE_INVENTORY
title: Runtime Surface Inventory
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-11'
last_review: '2026-06-11'
next_review: '2026-09-09'
prelude: Runtime Surface Inventory (reference) for dopemux documentation and developer
  workflows.
---
# Runtime Surface Inventory

## Executive Summary

Status: EVIDENCE_READY_WITH_GAPS. This discovery pack was rebuilt from the saved GPT-5.5 recon source file and current repo state at `ac3a26f746e472feb8a31f1b634d8c0432e08db6` on branch `codex/gpt55-recon-chain`.

No tunnel setup, local MCP tool invocation, service start, runtime implementation, or mutating route call was performed. Existing tracked inventory contributed the classified surface set; command evidence is captured in `proof/TP-DCP-MCP-RO-0001/COMMAND_LOG.md`.

## Commands Used

See `proof/TP-DCP-MCP-RO-0001/COMMAND_LOG.md`.

## MCP Surfaces

MCP and stdio/streamable route declarations were discovered with read-only `rg` scans. Treat any local MCP invocation as denied unless a future packet proves a safe wrapper.

## HTTP Surfaces

GET routes can be candidates only after wrapper-level scoping, redaction, and freshness labels. POST routes are denied by default unless the implementation is proven side-effect-free read behavior.

## CLI / Filesystem Proof Surfaces

Proof directories, task packets, extraction outputs, and tracked docs are suitable as filesystem-backed evidence sources when wrapped with explicit allowlists and secret redaction.

## Findings By System

- dopemux: operator control surface; not PM/memory/retrieval truth owner.
- dopetask: external execution runtime through `scripts/dopetask`; not PM authority.
- task-orchestrator: workflow views/transitions; read views may be exposed only as snapshots, transitions denied.
- ConPort: structured decisions/progress/context; read routes need strict scoping, writes denied.
- dope-memory: chronicle/evidence sink; search/replay candidates require redaction and session constraints.
- dope-context: derived code/docs retrieval; expose as derived search, not source truth.
- dopecon-bridge: proxy/event transport; never authority by itself.
- ADHD Engine: operator support/cognitive-state; safe status reads only after route-level review.
- Repo Truth Extractor: audit/extraction outputs are evidence artifacts, not runtime truth.
- proof/governance artifacts: strong phase-1 source when freshness and chain of custody are explicit.

## Read-Only Classification Table

| Surface | System | Method | Route/Tool | Class | Authority | Phase 1 |
|---|---|---|---|---|---|---|
| SRF-CONPORT-GET-DECISIONS | conport | GET | `/api/decisions` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW_AFTER_WRAPPER |
| SRF-CONPORT-POST-DECISIONS | conport | POST | `/api/decisions` | MUTATING | CANONICAL | DENY |
| SRF-CONPORT-GET-PROGRESS | conport | GET | `/api/progress` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW_AFTER_WRAPPER |
| SRF-CONPORT-GET-SEARCH | conport | GET | `/api/search/{workspace_id}` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW |
| SRF-CONPORT-GET-CUSTOMDATA | conport | GET | `/api/custom_data` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW_AFTER_WRAPPER |
| SRF-DOMEM-POST-SEARCH | dope-memory | POST | `/tools/memory_search` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW_AFTER_WRAPPER |
| SRF-DOMEM-POST-REPLAY | dope-memory | POST | `/tools/memory_replay_session` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW_AFTER_WRAPPER |
| SRF-DOMEM-POST-CORRECT | dope-memory | POST | `/tools/memory_correct` | MUTATING | CANONICAL | DENY |
| SRF-CONTEXT-MCP-SEARCHCODE | dope-context | MCP_CALL | `search_code` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW |
| SRF-CONTEXT-MCP-DOCSSEARCH | dope-context | MCP_CALL | `docs_search` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW |
| SRF-CONTEXT-MCP-SEARCHALL | dope-context | MCP_CALL | `search_all` | READ_WITH_SIDE_EFFECT_RISK | DERIVED | DENY |
| SRF-ORCH-GET-QUEUE | task-orchestrator | GET | `/api/projects/{project_id}/workflow/queue` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW_AFTER_WRAPPER |
| SRF-ORCH-GET-BLOCKERS | task-orchestrator | GET | `/api/projects/{project_id}/workflow/blockers` | CONFIRMED_READ_ONLY | CANONICAL | ALLOW |
| SRF-ORCH-POST-TRANSITION | task-orchestrator | POST | `/api/projects/{project_id}/workflow/transition` | MUTATING | CANONICAL | DENY |
| SRF-BRIDGE-GET-DDG-DECISIONS | dopecon-bridge | GET | `/ddg/decisions` | CONFIRMED_READ_ONLY | PROXY | DENY |

## Authority Labels

Authority labels are per-surface and must not be lifted to whole systems. Proxy surfaces remain proxy even when they expose canonical upstream data.

## Drift / Contradictions

- Bridge/proxy routes can look authoritative; they are not canonical owners.
- Task-orchestrator has workflow authority but not universal PM truth.
- dope-memory, ConPort, and dope-context overlap in memory/retrieval language but have distinct authority domains.

## Phase-1 Allowlist

- `SRF-CONPORT-GET-DECISIONS` conport GET `/api/decisions`
- `SRF-CONPORT-GET-PROGRESS` conport GET `/api/progress`
- `SRF-CONPORT-GET-SEARCH` conport GET `/api/search/{workspace_id}`
- `SRF-CONPORT-GET-CUSTOMDATA` conport GET `/api/custom_data`
- `SRF-DOMEM-POST-SEARCH` dope-memory POST `/tools/memory_search`
- `SRF-DOMEM-POST-REPLAY` dope-memory POST `/tools/memory_replay_session`
- `SRF-CONTEXT-MCP-SEARCHCODE` dope-context MCP_CALL `search_code`
- `SRF-CONTEXT-MCP-DOCSSEARCH` dope-context MCP_CALL `docs_search`
- `SRF-ORCH-GET-QUEUE` task-orchestrator GET `/api/projects/{project_id}/workflow/queue`
- `SRF-ORCH-GET-BLOCKERS` task-orchestrator GET `/api/projects/{project_id}/workflow/blockers`

## Explicit Denylist

- `SRF-CONPORT-POST-DECISIONS` conport POST `/api/decisions`: MUTATING
- `SRF-DOMEM-POST-CORRECT` dope-memory POST `/tools/memory_correct`: MUTATING
- `SRF-CONTEXT-MCP-SEARCHALL` dope-context MCP_CALL `search_all`: READ_WITH_SIDE_EFFECT_RISK
- `SRF-ORCH-POST-TRANSITION` task-orchestrator POST `/api/projects/{project_id}/workflow/transition`: MUTATING
- `SRF-BRIDGE-GET-DDG-DECISIONS` dopecon-bridge GET `/ddg/decisions`: CONFIRMED_READ_ONLY

## Remaining Unknowns

- Runtime liveness was not tested.
- Secret/redaction behavior is wrapper design work, not proven here.
- Task Orchestrator MCP transport in this Codex session remained closed outside shell-level process checks.
