---
id: ADR-211
title: 'ADR-211: Semantic Search v2 via Dope-Context (Qdrant, Bounded Hybrid)'
type: adr
owner: dopemux-core
date: 2026-02-08
status: accepted
tags:
- semantic-search
- dope-context
- qdrant
- determinism
- adhd
adhd_metadata:
  cognitive_load: low
  attention_state: any
  context_switching_impact: reduces
supersedes:
- 'Draft RFC: Semantic Search v2 (proposal)'
- Archive ADRs/RFCs referencing Milvus or claude-context as primary search
author: '@hu3mann'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: 'ADR-211: Semantic Search v2 via Dope-Context (Qdrant, Bounded Hybrid) (adr)
  for dopemux documentation and developer workflows.'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-211: Semantic Search v2 via Dope-Context

## Context

Dopemux requires semantic retrieval that is deterministic, bounded, ADHD-safe, and auditable. The current Dope-Context implementation satisfies these requirements and is the canonical semantic search authority.

Legacy references to alternative systems (for example, Milvus-based claude-context) are not authoritative unless explicitly enabled and documented.

## Decision

Adopt Dope-Context as the production semantic search engine, with the following enforced properties.

## Architecture (implemented)

### Retrieval lanes

- Code search: search_code
- Documentation search: docs_search
- Unified search: search_all (explicit orchestrator)

Lanes are implemented as separate logic paths and must not be collapsed.

### Storage

- Qdrant is the backing vector store.
- Collections are workspace-scoped and logically separated.

### Retrieval flow

1. Dense vector search is the primary retrieval mechanism.
2. Hybrid search MAY invoke reranking only when explicitly enabled.
3. Reranking operates on a bounded candidate set.
4. Final results are capped and token-budgeted before output.

### Progressive disclosure

- Token budgets are enforced centrally.
- Default result counts are bounded.
- Expansion requires explicit request.

### Decision retrieval

- Decision artifacts are retrieved only via an explicit integration bridge.
- Decision retrieval is opt-in per workspace.
- Decision results must be labeled and must not masquerade as code or documentation truth.

### Determinism

- Retrieval ordering is score-based and stable.
- No stochastic blending or uncontrolled merging is permitted.
- Orchestration logic is explicit in search_all.

## Non-goals

- Replacing Dope-Context with alternative vector engines.
- Making reranking mandatory.
- Implicitly injecting decision memory into search results.

## Consequences

### Positive

- Predictable, inspectable retrieval
- ADHD-safe defaults enforced in code
- Clean separation of concerns
- Low-risk extensibility

### Tradeoffs

- Requires discipline to keep legacy systems clearly labeled
- Unified search is intentionally conservative

## Follow-ups

- Mark docker/mcp-servers/claude-context as legacy or experimental in docs.
- Ensure profiles do not treat claude-context as authoritative unless explicitly intended.
