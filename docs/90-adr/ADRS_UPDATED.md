---
id: ADRS_UPDATED
title: Adrs Updated
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Adrs Updated (adr) for dopemux documentation and developer workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
Title: Architectural Decision Records (Aggregate)
Status: Proposed | Owner: You | Date: 2025-08-15 PT

## ADR-0001 — Local-first CLI and single-user scope
Context: Private, on-device analysis. Options: local CLI / daemon / hosted app. Decision: local-first CLI. Consequences: privacy by default; no GUI.

## ADR-0002 — Vector memory: Chroma per contact
Context: Need local, filterable RAG memory. Options: Chroma / FAISS / pgvector. Decision: Chroma per-contact collections. Consequences: simple, fast; revisit for multi-user.

## ADR-0003 — Embeddings: local default, cloud optional
Context: Privacy vs quality. Options: local ST / OpenAI / hybrid. Decision: default local; allow cloud behind Policy Shield. Consequences: quality tradeoff; config switch.

## ADR-0004 — iMessage via chat.db (not PDF)
Context: Structure (replies/reactions/attachments). Decision: copy DB+WAL; read-only joins. Consequences: accurate threading.

## ADR-0005 — Policy Shield redaction before any cloud
Context: Prevent sensitive leakage. Options: none / best-effort / mandatory. Decision: mandatory redaction, pseudonyms, opaque tokens, coverage gate 0.995 (0.999 strict), hard-fail classes. Consequences: engineering overhead, strong privacy.

## ADR-0007 — Cloud enrichment orchestrator
Context: Need consistent enrichment. Decision: schema-locked prompts, minimal redacted context, JSON validation, caching. Consequences: predictability, effort.

## ADR-0008 — Label-aware retrieval keyed to Issues/Episodes
Context: Queries must target themes over time. Decision: metadata pre-filter + boosts. Consequences: precise, more metadata mgmt.

## ADR-0009 — Issue Registry with Temporal Issue Graph
Context: Track themes and relations (non-causal). Decision: Issues + edges (co_occurs, precedes, amplifies, attenuates) with lags/confidence. Consequences: powerful insights; disclaimers.

## ADR-0010 — Sex-work contexts handled safely
Context: Escorting/clients common; must be safe/useful. Decision: coarse facets for cloud; explicit details as fine local-only with opaque tokens. Consequences: analytics without leakage; stricter detectors.

## ADR-0011 — Local-first enrichment cascade
Context
We want on-device tagging and enrichment to minimize cloud exposure while keeping quality high.

Options
- Cloud-only enrichment after redaction.
- Local-only enrichment.
- Hybrid cascade: local first; cloud escalation on low confidence or complex tasks.

Decision
Adopt a **hybrid cascade**. Run a local model first for tagging and CU enrichment. If `confidence_llm < τ` (default 0.7) or the task requires cross-episode synthesis, optionally escalate to cloud **after** Policy Shield preflight. Persist `source` = local|cloud in outputs.

Consequences
- Better privacy and cost; acceptable quality with escalation.
- Determinism requires fixed seeds and pinned model builds.
- Slightly higher engineering complexity (confidence gating/merge path).
