---
id: 04-claude-context
title: 04 Claude Context
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-07'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: 04 Claude Context (explanation) for dopemux documentation and developer workflows.
---
# DR Pack 04: Claude Context / claude-context

Access date: 2026-04-28

## Objective

Research current `zilliztech/claude-context` and map it to Dopemux dope-context deterministic code/docs indexing and retrieval.

## Source Seeds

- https://github.com/zilliztech/claude-context
- https://www.npmjs.com/package/@zilliz/claude-context-mcp
- `docs/06-research/mcp-customization/data/upstream-source-manifest.json`
- Dopemux runtime seed: `services/dope-context/src/mcp/server.py`
- Dopemux docs seed: `docs/03-reference/systems/dope-context/system-dopecontext.md`

Observed source status:

- GitHub: archived=false, pushed_at=2026-04-28T03:05:25Z.
- npm `@zilliz/claude-context-mcp`: latest 0.1.10, modified 2026-04-27T11:41:43Z.
- npm package repository points to `zilliztech/claude-context`, directory `packages/mcp`.

## Required Extraction Fields

- MCP tools/resources/prompts
- indexing architecture
- chunking strategy
- embedding providers
- vector DB requirements
- BM25/dense/hybrid ranking
- incremental index behavior
- include/exclude rules
- status and freshness APIs
- provenance model
- auth/security model
- package/release status

## Dopemux Boundary Constraints

- dope-context owns derived code/docs retrieval only.
- dope-context is not source truth for code/docs.
- dope-context is not ConPort decision authority.
- Hidden semantic scoring cannot drive Phase 1 ranking without deterministic controls.
- Cloud vector storage cannot become mandatory unless explicitly approved.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Does upstream assume Milvus/Zilliz Cloud or any hosted vector dependency?
- Are ranking steps deterministic and inspectable?
- Does indexing capture secrets or ignored files?
- Does retrieval expose source paths, commits, chunk IDs, and freshness?
- Does it overlap with Serena symbol lookup or ConPort decision search?

## Output Contract

Return exactly:

- `items`: Top-3 actionable findings.
- `more_count`
- `next_token`
- evidence matrix
- fact vs inference separation
- UNKNOWN list
- blocker list
- responsibility collision matrix
- implementation slices with validation

## UNKNOWN / Blocker Handling

If ranking, storage, or provenance cannot be proven from current upstream code/docs, mark UNKNOWN and require a spike before adoption.

## Adopt / Adapt / Reject / Hide / Defer Table Requirements

Include rows for:

- AST/contextual chunking
- embeddings
- vector DB
- BM25/dense fusion
- incremental indexing
- MCP search tool
- status/freshness API
- cloud-only assumptions
- ConPort decision sync

## Validation Requirements

- Require deterministic replay tests.
- Require no-secret indexing tests.
- Require source provenance and freshness checks.
- Require p50/p99 search performance and token-budget validation.
