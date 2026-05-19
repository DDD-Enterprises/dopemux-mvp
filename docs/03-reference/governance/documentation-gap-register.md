---
id: documentation-gap-register
title: Documentation Gap Register
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-18'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Gap register for repo-grounded Dopemux documentation forge work.
---
# Documentation Gap Register

This register captures gaps found during packet
`TP-DMX-DOCS-FORGE-001-SOURCE-MAP-GAPS`. It is documentation-only and does not
claim that any runtime drift is closed. Runtime code, config, tests, and active
entrypoints remain stronger than this register.

## Register

| ID | Gap | Impact | Missing evidence | Recommended fix | Priority | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| DG-001 | Quickstart service health ports are inconsistent with compose and registry defaults. `docs/01-tutorials/quickstart.md` checks bridge on `3316` and ConPort on `3304`, while `compose.yml` and `services/registry.yaml` expose dopecon-bridge default `3016` and ConPort HTTP `3004`. | A new operator may run the documented checks against the wrong ports and misdiagnose a healthy stack as failed. | No inspected `.env`, compose override, or runtime profile proved `3316` or `3304` as the default quickstart ports. | Packet 002 updated `README.md`, `QUICK_START.md`, and `docs/01-tutorials/quickstart.md` to use observed compose/registry defaults. Runtime startup remains `NOT_RUN`. | P0 | Addressed by packet 002 docs; runtime proof still open. |
| DG-002 | Manual compose startup omits the external Docker network prerequisite. `compose.yml` declares `dopemux-network` as external. | `docker compose -f compose.yml up -d --build` can fail before services start if the network does not already exist. | No packet-001 source proved that `docker network create dopemux-network` is automatically handled before manual compose startup. | Packet 002 added explicit `docker network inspect ... || docker network create dopemux-network` preflight to README and quickstarts. Automatic profile behavior remains `NEEDS_REPO_VERIFICATION`. | P0 | Addressed by packet 002 docs; runtime proof still open. |
| DG-003 | README references `SYSTEM_BOUNDARIES.md` as if it exists at the repo root, but the observed boundary reference path is `docs/03-reference/systems/system-boundaries.md`. | Operators can be sent to an absent path when trying to resolve architecture boundaries. | No root `SYSTEM_BOUNDARIES.md` was observed in this worktree. | Packet 002 updated README links to `docs/03-reference/systems/system-boundaries.md`. No root pointer was created. | P1 | Addressed by packet 002 docs. |
| DG-004 | Task-orchestrator runtime and port authority remain conflicted. System docs and truth docs preserve conflict across `services/task-orchestrator/app/main.py`, `services/task-orchestrator/task_orchestrator/app.py`, `services/task-orchestrator/Dockerfile`, `compose.yml`, `services/registry.yaml`, and older `3014` adapter defaults. | Architecture and operations docs can accidentally present task-orchestrator as cleaner than the repo proves. | Runtime container execution was not exercised in packet 001, and no integration validation closed the Dockerfile versus app-path conflict. | Packet 003 should document the conflict explicitly. A later runtime verification packet should build/run the container and record the actual import path and port. | P0 | Packet 003 plus later runtime verification. |
| DG-005 | ConPort access is split across `3004` HTTP API, `3005` MCP/SSE, PM adapter assumptions, and quickstart examples. | Operators can choose the wrong surface for health, PM context, decision reads, or MCP use. | Packet 001 did not run ConPort. It only observed compose, registry, PM docs, and system docs. | Packet 002 updated quickstart health checks to use the observed ConPort HTTP default `3004`. Packet 003 should still include a surface table separating HTTP API, MCP/SSE, bridge proxy, and PM adapter usage. | P1 | Quickstart portion addressed by packet 002; architecture table remains for packet 003. |
| DG-006 | dope-memory transport and identity are easy to confuse with working-memory-assistant. Current system docs identify `3020` and `dope_memory_main.py` as active dope-memory, while stale adapter surfaces still assume `8096`. | Docs can collapse chronicle authority, WMA snapshot/recovery, and stale MCP adapter behavior into one "memory" service. | Packet 001 did not exercise memory endpoints or adapter behavior. | Packet 003 should document dope-memory as chronicle authority only, mark WMA snapshot/recovery separately, and preserve `8096` as drift unless runtime validation proves otherwise. | P1 | In series, packet 003. |
| DG-007 | Developer onboarding is incomplete for a new contributor path. The packet-002 allowlist includes `docs/02-how-to/developer-onboarding.md`, but no current file with that path was observed. | New contributors lack one policy-compliant guide that ties setup, branch/worktree discipline, packet execution, docs validation, and authority rules together. | No existing developer onboarding file was found under the packet-002 target path. | Packet 002 created `docs/02-how-to/developer-onboarding.md` with repo-grounded prerequisites, setup, validation, Task Packet discipline, and authority rules. | P1 | Addressed by packet 002 docs. |
| DG-008 | AI handoff guidance is absent at the packet-003 target path, while agent authority remains `UNKNOWN` across multiple families. | Agent-facing docs could imply one repo-wide agent runtime or PM authority that the repo does not prove. | No `docs/03-reference/instructions/ai-agent-handoff-guide.md` was observed. Runtime authority across `services/agents`, `src/dopemux/agent_orchestrator.py`, and task-orchestrator agents remains unresolved. | Packet 003 should create an AI handoff guide that treats agents as workflow participants, not source-truth owners, and explicitly preserves `UNKNOWN` agent authority. | P1 | In series, packet 003. |
| DG-009 | Product and marketing docs are missing at packet-004 target paths. | Public-facing positioning can drift into a monolithic assistant story, bridge-as-authority story, or unsupported PM/memory claims. | No docs were observed for `docs/04-explanation/product/positioning.md`, `audience-personas.md`, `homepage-copy.md`, `elevator-pitches.md`, `features-and-benefits.md`, or `faq.md`. | Packet 004 should create repo-faithful product docs that describe Dopemux as an operator-control multi-system workspace with split authority and explicit limitations. | P2 | In series, packet 004. |
| DG-010 | Current docs trust sources partly disagree by date. `docs/03-reference/truth/truth-gaps.md` contains a README/dopetask-version concern, but the inspected README no longer mentions a dopetask version while `.dopetask-pin` and `pyproject.toml` align on `0.5.1`. | A later doc writer may carry forward stale gap claims as current truth. | Packet 001 did not run a full truth-doc regeneration or audit all historical references to the older version. | Preserve the contradiction. Packet 002 should avoid reintroducing stale dopetask version prose. A later truth-refresh packet should update or supersede stale truth-gap entries with evidence. | P2 | Later runtime/truth refresh; avoid in packet 002. |
| DG-011 | The documentation index underlinks current governance trust docs. Before packet 001, `docs/INDEX.md` and `docs/00-MASTER-INDEX.md` exposed Authority Map and Conflict Ledger but did not link the source map or gap register because they did not exist. | Packet outputs would be hard to discover after creation. | No source-map or forge-specific gap-register links existed before packet 001. | Packet 001 should add index links for the new docs and existing Doc Trust Map in the governance section. | P1 | Completed by packet 001 index update if validation passes. |
| DG-012 | Runtime drift is not closed by documentation-only work. The series can produce source maps, docs, and indexes, but it cannot prove service startup, health, or runtime integration behavior unless validators or runtime checks are explicitly run. | Readers may mistake documentation completion for runtime correctness. | Packet 001 does not start services or run integration tests. Later packets may run docs validators but are still documentation-only unless they explicitly run runtime validation. | Every packet proof should list runtime validation as `NOT_RUN` unless actually executed, and docs should use `NEEDS_REPO_VERIFICATION` for unsettled runtime behavior. | P0 | Applies to all packets. |

## Series Routing

- Packet 001 owns this register and the source map.
- Packet 002 addresses onboarding, README, quickstart, and developer setup gaps in docs. Runtime proof remains separate where marked.
- Packet 003 should address architecture, governance, operations, and AI handoff gaps.
- Packet 004 should address repo-faithful product and marketing docs, then produce the final index proof.

## Current Unknowns

- `UNKNOWN`: Whether task-orchestrator Docker startup actually resolves to the intended active app path without a runtime build/run check.
- `UNKNOWN`: Whether ConPort `3004` and `3005` are consistently the correct surfaces across all operator profiles.
- `UNKNOWN`: Whether any local environment override intentionally maps quickstart checks to `3316` or `3304`.
- `UNKNOWN`: Whether the broader agent runtime has a single owner.
- `NEEDS_REPO_VERIFICATION`: Whether manual compose startup is expected to create `dopemux-network` outside `docker compose` itself.

## Proof Notes For Packet 001

- Proposed paths are policy-compliant under `docs/03-reference/governance/`.
- No runtime code, service code, compose files, dependency files, tests, generated extraction outputs, or archived docs are modified by this packet.
- This register should remain open. Closing a gap requires proof from the packet that actually verifies or remediates it.

## Proof Notes For Packet 002

- `README.md`, `QUICK_START.md`, and `docs/01-tutorials/quickstart.md` now use observed compose/registry health defaults for the quickstart path.
- `docs/02-how-to/developer-onboarding.md` was created under an allowed docs root.
- No docs hygiene remap was required for packet 002 paths.
- Runtime startup and live service health validation remain `NOT_RUN`; documentation updates do not close runtime drift.
