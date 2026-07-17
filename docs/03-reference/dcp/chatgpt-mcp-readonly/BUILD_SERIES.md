---
id: dcp-mcp-readonly-build-series
title: DCP Read-Only MCP Facade — Build Series
type: reference
owner: '@hu3mann'
author: '@hu3mann'
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
| TP-DCP-MCP-RO-0009 | ChatGPT MCP Exposure Target Contract ADR | HIGH | Record accepted `target_id`, runtime-resolution, ownership-evidence, and response-redaction contract. **Done** — runtime follow-on work is now enabled by the landed MCP runtime stack. | 0008 |
| TP-DCP-MCP-RO-0010 | Exposure Target Registry V2 And Pure Resolver Core | HIGH | Parse opaque target consent and resolve filesystem/repository identity without live I/O. **Done** — pure registry v2, resolver core, and capability separation landed. | 0009 |
| TP-DCP-MCP-RO-0011 | Read-Only Runtime Registry And Catalog Join | HIGH | Join resolved targets with operational catalog/runtime evidence using exact scope checks; remain non-callable and fail closed. | 0010 |
| TP-DCP-MCP-RO-0011-REMEDIATION-01 | Runtime Catalog Join Generated Identity Remediation | HIGH | Correct the open 0011 PR so lifecycle-generated runtime IDs match without changing target authorization or live behavior. | 0011 |
| TP-DCP-MCP-RO-0012 | Public Facade Target Contract Migration | HIGH | Migrate public FastMCP to registry-v2 opaque target_id local evidence tools. **Done** — merged PR #1057. | 0011-REMEDIATION-01 |
| TP-DCP-MCP-RO-0013 | Connector Policy Schema And Auth Context | HIGH | Strict connector policy schema/loader and provider-neutral sealed auth context with target/tool authorization. **No public ingress.** | 0012 |
| TP-DCP-MCP-RO-0014 | Loopback Streamable HTTP Ingress | HIGH | Auth-before-discovery loopback HTTP ingress, rate limits, redacted audit, start/stop/health. **No public bind/tunnel.** | 0013 |
| TP-DCP-MCP-RO-0015 | Ownership Verification And Release-One Adapters | HIGH | Fail-closed ownership verifier + ConPort decision list/read and dope-memory search/replay gates. **No live default network.** | 0014 |
| TP-DCP-MCP-RO-0016 | Multi-Provider Setup And Rollback Docs | MEDIUM | Provider setup, disable/rollback, command/source-date ledgers, example secret-scan tests. **Placeholders only.** | 0015 |

## Sequencing rationale

The series is deliberately **docs-first → identity → local-only scaffold → service adapters → tunnel → hardening**:

1. **0002–0003** establish guardrails (contracts) and resolve the `UNKNOWN` workspace-identity marker before any code.
2. **0004** writes code only against local filesystem/git surfaces (cheapest blast radius) — registry, resolver, proof/git tools.
3. **0005–0006** add service-backed reads one trust-tier at a time (structured memory first, then search + workflow), each with denylist tests.
4. **0007** documents the tunnel without committing secrets.
5. **0008** is the acceptance/hardening slice — no new features, only isolation, injection, redaction, and stale-proof regression tests.
6. **0009** is the post-hardening contract ADR slice. It supersedes caller-facing `project_id` language for new exposure contracts with opaque `target_id` language.
7. **0010** implements consent parsing and local identity resolution only; it deliberately does not inspect runtime state or make service calls.
8. **0011** consumes runtime/catalog records as operational evidence only. Live protocol verification, ownership adjudication, and backend adapter authorization remain later gates.

Each packet emits a proof bundle under `proof/TP-DCP-MCP-RO-<n>/` (`PROOF.json`, `COMMAND_LOG.md`, `AUDIT.md`) per AGENTS.md §9.
