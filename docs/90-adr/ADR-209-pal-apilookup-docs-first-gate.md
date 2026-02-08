---
id: ADR-209
title: 'ADR-209: Documentation-First Gate via PAL apilookup'
type: adr
owner: dopemux-core
date: 2026-02-08
status: proposed
tags:
- docs-first
- pal
- determinism
- adhd
adhd_metadata:
  cognitive_load: low
  attention_state: any
  context_switching_impact: reduces
supersedes:
- 'Archive ADR: 002-context7-first-philosophy.md (legacy)'
author: '@hu3mann'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: 'ADR-209: Documentation-First Gate via PAL apilookup (adr) for dopemux documentation
  and developer workflows.'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-209: Documentation-First Gate via PAL apilookup

## Context

Dopemux must avoid speculative or hallucinated API usage, which creates costly debug loops and breaks developer flow. A docs-first gate is an ADHD-first requirement: it reduces context switching and prevents rework.

The current stack includes PAL as an MCP server (docker/mcp-servers/pal). PAL is the authoritative documentation interface.

Legacy references to Context7 may exist in historical docs and scripts. Context7 is not the canonical gate.

## Decision

Adopt PAL apilookup as the required documentation-first gate.

### Normative rules

1. MUST call PAL apilookup before implementing or modifying any non-trivial integration that:
   - touches external libraries/frameworks
   - changes service contracts, CLI flags, schemas, or MCP tool shapes
   - modifies infrastructure services (Docker, Postgres, Redis, Qdrant, MCP servers)

2. MUST use focused queries:
   - include explicit library identifiers when known
   - use topic-scoped requests where possible
   - apply bounded token limits

3. MUST record "docs proof" in the working context:
   - query used
   - key retrieved claim(s)
   - decision taken based on the docs

4. MUST fail closed on ambiguity:
   - if PAL is unavailable or docs do not cover the needed behavior, do not invent APIs.
   - proceed only with minimal-diff changes that do not require new API assumptions, or require explicit operator approval for speculative work.

## Enforcement points

- Agent prompts and runbooks must include the docs-first step.
- Code review must block changes that introduce unverifiable APIs without docs proof.

## Consequences

### Positive

- Reduced hallucinated API usage
- Higher determinism and auditability
- Lower ADHD context switch cost

### Negative

- Slight upfront lookup time
- Requires consistent logging discipline

## Follow-ups

- Remove or label legacy Context7 references in profile scripts and docs.
