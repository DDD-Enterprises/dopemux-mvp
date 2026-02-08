---
id: ADR-212
title: 'ADR-212: Memory Lanes, Promotion, and Injection Policy'
type: adr
owner: dopemux-core
date: 2026-02-08
status: proposed
tags:
- memory
- dope-memory
- conport
- dope-context
- eventbus
- determinism
- redaction
- adhd
adhd_metadata:
  cognitive_load: low
  attention_state: any
  context_switching_impact: reduces
author: '@hu3mann'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: 'ADR-212: Memory Lanes, Promotion, and Injection Policy (adr) for dopemux
  documentation and developer workflows.'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-212: Memory Lanes, Promotion, and Injection Policy

## Context

Dopemux implements multiple "memory-like" systems:
- Dope-Memory (Working Memory Assistant) stores raw activity events and curated work log entries in a SQLite canonical store.
- ConPort stores decisions and related knowledge artifacts.
- Dope-Context provides semantic retrieval for code and docs and can optionally include decision artifacts via an explicit integration bridge.

Without explicit lane boundaries, the system risks duplication, accidental injection, and hard-to-audit behavior.

## Decision

Define memory as lanes with explicit responsibilities, promotion rules, and opt-in injection policies.

## Lanes (authoritative)

### Lane 1: Raw activity lane (short retention)
- Owner: Dope-Memory
- Storage: raw_activity_events in SQLite
- Retention: short (7 days by default)
- Redaction: applied at ingestion (fail-closed)

### Lane 2: Curated chronicle lane (durable)
- Owner: Dope-Memory
- Storage: work_log_entries in SQLite
- Population method: deterministic promotion allowlist
- Redaction: applied again at promotion (fail-closed)

### Lane 3: Decision lane (durable, structured)
- Owner: ConPort (canonical decisions)
- Access: via MCP server conport and optional bridge connectors
- Note: decisions may also be promoted into Dope-Memory as work log entries for timeline and operator recall. This is not a second canonical source of truth.

### Lane 4: Retrieval lane (ephemeral context)
- Owner: Dope-Context
- Storage: Qdrant collections
- Scope: code and docs retrieval; optional decision inclusion via bridge

## Promotion policy (Dope-Memory)

- Only allowlisted event types are promotable.
- Promotion must remain deterministic.
- Importance scores are deterministic and must not depend on LLM output in Phase 1.
- Promotion redaction must run before writing curated entries.

## Injection policy (opt-in per lane)

- Default: no lane is automatically injected into an agent prompt unless explicitly requested by:
  - a tool call (for example memory_search, memory_recap)
  - an orchestrator policy for a specific workflow phase
  - an operator config switch

- Lane 3 (decisions) injection must be clearly labeled as decision context and must not be merged indistinguishably with code/docs retrieval.

## EventBus loop guard

- memory.derived.v1 events MUST NOT be re-ingested as activity.events.v1 without explicit loop prevention rules.
- Source allowlists must be enforced at ingestion.

## Consequences

### Positive
- Reduced duplication and injection ambiguity
- Better auditability of "why this context appeared"
- ADHD-safe defaults (bounded, progressive disclosure)

### Negative
- Requires explicit configuration where previously implicit behavior might have been assumed

## Follow-ups

- Document search ordering and cursor semantics in Dope-Memory API contracts.
- Add dedupe strategy between Dope-Memory promoted decisions and ConPort decisions.
