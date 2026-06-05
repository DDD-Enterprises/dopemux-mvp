---
id: dcp-mcp-readonly-build-series
title: DCP Read-Only MCP Facade — Build Series
type: reference
owner: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Packet roadmap and dependency chain for the read-only MCP evidence facade build series for dopemux documentation and developer workflows.
---

# Build Series — DCP Secure MCP Read-Only Evidence Facade

> Series id: `DCP-MCP-RO`. Linear dependency chain (each packet `BLOCKS` the next). Series branch: `dcp/chatgpt-mcp-readonly-facade-series`; packet branch pattern: `dcp/chatgpt-mcp-ro-<n>-<short-slug>`.

| Packet | Title | Risk | Objective (one line) | Depends on |
| --- | --- | --- | --- | --- |
| TP-DCP-MCP-RO-0001 | Read-Only Surface Inventory (discovery) | — | Inventory 15 backend surfaces; classify read-only / mutating / side-effect. **Done** — produced [`READ_ONLY_SURFACE_INVENTORY.json`](READ_ONLY_SURFACE_INVENTORY.json). | — |
| TP-DCP-MCP-RO-0002 | Architecture Doc And Multi Project Contract | MEDIUM | Author architecture, registry, tool, envelope, security, decisions, build-series docs (**this packet**). | 0001 |
| TP-DCP-MCP-RO-0003 | Inspect Dopemux Init Registry Contract | MEDIUM | Statically inspect `dopemux init` / workspace identity; formalize registry validation contract. | 0002 |
| TP-DCP-MCP-RO-0004 | Facade Scaffold Registry Resolver Repo Proof Tools | HIGH | Scaffold `services/dcp-readonly-facade/`; registry, resolver, envelope, redaction, repo-state + proof tools. | 0003 |
| TP-DCP-MCP-RO-0005 | ConPort And Dope Memory Read Adapters | HIGH | Add ConPort + dope-memory read adapters with route allowlists, denylist tests, redaction. | 0004 |
| TP-DCP-MCP-RO-0006 | Dope Context And Task Orchestrator Read Adapters | HIGH | Add dope-context + task-orchestrator read adapters; deny `search_all`/index/sync/transition/PM/bridge. | 0005 |
| TP-DCP-MCP-RO-0007 | Secure MCP Tunnel Integration Docs And Manual Validation | MEDIUM | Document loopback tunnel setup, redacted configs, manual validation, ChatGPT connector flow. | 0006 |
| TP-DCP-MCP-RO-0008 | Hardening Cross Project Isolation And PR Readiness | HIGH | Cross-project isolation, injection/redaction, stale-proof, denylist regression, PR readiness. | 0007 |

## Sequencing rationale

The series is deliberately **docs-first → identity → local-only scaffold → service adapters → tunnel → hardening**:

1. **0002–0003** establish guardrails (contracts) and resolve the `UNKNOWN` workspace-identity marker before any code.
2. **0004** writes code only against local filesystem/git surfaces (cheapest blast radius) — registry, resolver, proof/git tools.
3. **0005–0006** add service-backed reads one trust-tier at a time (structured memory first, then search + workflow), each with denylist tests.
4. **0007** documents the tunnel without committing secrets.
5. **0008** is the acceptance/hardening slice — no new features, only isolation, injection, redaction, and stale-proof regression tests.

Each packet emits a proof bundle under `proof/TP-DCP-MCP-RO-<n>/` (`PROOF.json`, `COMMAND_LOG.md`, `AUDIT.md`) per AGENTS.md §9.
