---
id: TASK_ORCHESTRATOR_LOAD
title: Task Orchestrator Load
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Task Orchestrator Load (reference) for dopemux documentation and developer
  workflows.
---
# Task Orchestrator Load Sheet — DCP MCP Read-Only Facade

## Epic

**DCP Secure MCP Read-Only Evidence Facade**

## Load Items

### TP-DCP-MCP-RO-0002 — Architecture Doc And Multi Project Contract
- Status: READY
- Priority: HIGH
- Risk: MEDIUM
- Depends on: TP-DCP-MCP-RO-0001
- Objective: Create repo-tracked architecture, registry, tool-contract, response-envelope, security-model, build-series, and decision docs for the multi-project read-only evidence facade.
- Branch: `dcp/chatgpt-mcp-ro-0002-architecture-doc-and-multi-proje`
- Expected output: ARCHITECTURE.md, MULTI_PROJECT_REGISTRY_CONTRACT.md, TOOL_CONTRACT.md, RESPONSE_ENVELOPE_SCHEMA.md, SECURITY_MODEL.md, BUILD_SERIES.md, DECISIONS.md, TASK_ORCHESTRATOR_LOAD.md, Task packet markdown files 0002-0008, Proof bundle for packet 0002
- Stop if: Working tree has unrelated changes.

### TP-DCP-MCP-RO-0003 — Inspect Dopemux Init Registry Contract
- Status: READY
- Priority: HIGH
- Risk: MEDIUM
- Depends on: TP-DCP-MCP-RO-0002
- Objective: Inspect actual dopemux init/workspace identity behavior and formalize the project registry validation contract without implementing the facade.
- Branch: `dcp/chatgpt-mcp-ro-0003-inspect-dopemux-init-registry-co`
- Expected output: Dopemux_INIT_REGISTRY_DISCOVERY.md, Updated MULTI_PROJECT_REGISTRY_CONTRACT.md, Proof bundle for packet 0003
- Stop if: No init/workspace identity code can be found.

### TP-DCP-MCP-RO-0004 — Facade Scaffold Registry Resolver Repo Proof Tools
- Status: READY
- Priority: HIGH
- Risk: HIGH
- Depends on: TP-DCP-MCP-RO-0003
- Objective: Implement the minimal read-only MCP facade scaffold with project registry, workspace resolver, response envelope, redaction baseline, repo-state tool, proof listing, and proof fetch tools.
- Branch: `dcp/chatgpt-mcp-ro-0004-facade-scaffold-registry-resolve`
- Expected output: Working scaffold service, Registry/resolver/envelope/redaction modules, MCP local/proof/git tools, Tests and docs, Proof bundle for packet 0004
- Stop if: Marker contract from 0003 is unresolved.

### TP-DCP-MCP-RO-0005 — ConPort And Dope Memory Read Adapters
- Status: READY
- Priority: HIGH
- Risk: HIGH
- Depends on: TP-DCP-MCP-RO-0004
- Objective: Add project-scoped ConPort and dope-memory read adapters with strict route allowlists, denylist tests, redaction, pagination, and canonical response envelopes.
- Branch: `dcp/chatgpt-mcp-ro-0005-conport-and-dope-memory-read-ada`
- Expected output: ConPort adapter, dope-memory adapter, Four new tools, Route tests, Proof bundle for packet 0005
- Stop if: Backend read behavior cannot be bounded.

### TP-DCP-MCP-RO-0006 — Dope Context And Task Orchestrator Read Adapters
- Status: READY
- Priority: HIGH
- Risk: HIGH
- Depends on: TP-DCP-MCP-RO-0005
- Objective: Add project-scoped dope-context and task-orchestrator read adapters while denying indexing, search_all, sync, transitions, PM write routes, and bridge/proxy access.
- Branch: `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`
- Expected output: dope-context adapter, task-orchestrator adapter, Three new tools, Denied route tests, Proof bundle for packet 0006
- Stop if: dope-context requires search_all to produce useful results.

### TP-DCP-MCP-RO-0007 — Secure MCP Tunnel Integration Docs And Manual Validation
- Status: READY
- Priority: HIGH
- Risk: MEDIUM
- Depends on: TP-DCP-MCP-RO-0006
- Objective: Document local Secure MCP Tunnel integration, redacted sample configs, local-only runtime posture, manual validation, and ChatGPT connector test flow without committing secrets.
- Branch: `dcp/chatgpt-mcp-ro-0007-secure-mcp-tunnel-integration-do`
- Expected output: TUNNEL_INTEGRATION.md, MANUAL_VALIDATION.md, FAILURE_RUNBOOK.md, Proof bundle for packet 0007
- Stop if: Official tunnel behavior contradicts docs.

### TP-DCP-MCP-RO-0008 — Hardening Cross Project Isolation And PR Readiness
- Status: READY
- Priority: HIGH
- Risk: HIGH
- Depends on: TP-DCP-MCP-RO-0007
- Objective: Harden the full facade with cross-project isolation tests, injection/redaction tests, stale-proof checks, denylist regression tests, no-write evidence, embedded audit, and PR readiness artifacts.
- Branch: `dcp/chatgpt-mcp-ro-0008-hardening-cross-project-isolatio`
- Expected output: Hardened facade, Full regression suite, Security proof artifacts, PR readiness material, Proof bundle for packet 0008
- Stop if: Any test requires weakening a denylist.
