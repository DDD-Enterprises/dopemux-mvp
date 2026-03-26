---
id: adr-leantime-json-rpc-plus-plugin-integration-strategy
title: "ADR: Leantime JSON-RPC plus plugin integration strategy"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: Use Leantime JSON-RPC as the primary PM-plane operations seam, with plugins reserved for bounded augmentation.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-dopecon-bridge-narrowing-to-adapter-only-role
    - adr-task-orchestrator-as-workflow-authority
    - adr-conport-as-decision-progress-and-context-authority
    - adr-dope-memory-as-chronicle-memory-authority
---

# ADR: Leantime JSON-RPC plus plugin integration strategy

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux PM Plane / Integration Layer / PM Operations
**Decision Type:** Integration Architecture
**Scope:** Leantime integration into the Dopemux PM plane

## Context

Leantime is the strongest candidate for the **operational PM system of record** in the current Dopemux PM-plane architecture.

The extracted truth pack shows that Leantime has:

- broad PM entity coverage
- strategic planning surfaces
- comments, files, wiki/articles, risks, retros, ideas, timesheets, and canvas-style artifacts
- a stable **JSON-RPC** integration surface
- a plugin architecture
- event and extension seams
- weak workflow enforcement
- an installed but not yet mature or trustworthy MCP path

The most important findings are:

1. **JSON-RPC is the practical stable integration seam**
2. **Leantime should remain canonical for PM entities**
3. **Leantime should not be treated as workflow authority**
4. **Leantime’s MCP infrastructure is not mature enough to be the primary integration contract**
5. **HTML-rich content and loosely structured fields require normalization before promotion into memory/context systems**

The PM plane therefore needs an integration strategy that preserves Leantime’s strengths without overcommitting to immature or drifting surfaces.

## Decision

Leantime will be integrated into the Dopemux PM plane through a **hybrid strategy**:

### Primary integration seam

**JSON-RPC** will be the primary machine-to-machine operational integration surface.

### Secondary extension seam

A **Leantime plugin** may be used selectively for:

- hooks/events
- internal extension seams
- UI injection
- menu/actions
- server-side augmentation where JSON-RPC is insufficient

### Explicit non-decision

Leantime’s built-in MCP path will **not** be treated as the primary contract surface at this time.

## Why JSON-RPC is primary

JSON-RPC is the right primary seam because it is:

- the most mature exposed contract surface in the current Leantime runtime
- broad enough to cover core PM operations
- more stable than the dormant or incomplete MCP path
- more appropriate for machine-to-machine operational calls than HTML/controller scraping
- sufficient for adapter-backed PM-plane tools

This means the PM plane should consume Leantime through a normalized adapter that speaks JSON-RPC, rather than binding agents directly to Leantime-specific service names.

## Why plugin support remains part of the strategy

A plugin is still valuable, but as a **secondary seam**, not the primary integration backbone.

A plugin may be used where the PM plane needs:

- event or hook access
- UI affordances
- operator shortcuts
- internal service access not exposed cleanly via JSON-RPC
- augmentation of server-side workflows without pretending Leantime owns workflow authority

This gives Dopemux a way to leverage Leantime internals without making the entire PM-plane contract depend on in-app custom code.

## What Leantime is authoritative for

Leantime remains authoritative for:

- projects
- tickets/tasks
- sprints
- milestones
- PM-facing membership/user assignment
- PM-local files/comments/docs/timesheets as operational records

Leantime is not authoritative for:

- workflow rules
- blocker logic
- next-action computation
- durable decision memory
- chronicle memory
- technical/code context

Those responsibilities belong elsewhere in the PM plane.

## What the adapter layer must do

The Dopemux adapter layer in front of Leantime must:

1. translate normalized PM-plane tool calls into Leantime JSON-RPC operations
2. normalize payloads, naming, and error handling
3. preserve canonical IDs and mappings
4. wrap side-effectful operations with policy
5. sanitize and normalize rich text before promotion into context/memory systems
6. isolate Leantime-specific quirks from upstream agents and orchestration systems

This is important because the PM plane should be **Leantime-backed**, not **Leantime-shaped**.

## What the adapter layer must not do

The adapter must not:

- create a second canonical PM task store
- silently shadow Leantime entities without explicit non-canonical labeling
- let raw HTML-rich Leantime content flow directly into durable memory
- expose raw Leantime internals directly to agents as the long-term PM interface
- promote Leantime’s weak workflow semantics into PM-plane workflow authority

## MCP decision

Leantime’s own MCP path is currently treated as:

- infrastructural
- incomplete
- not reliable enough for PM-plane contract dependence

Until there is active app-level tool/resource implementation and real registration/runtime proof, the PM plane will not rely on Leantime MCP as the primary or authoritative integration surface.

If Leantime MCP matures later, it may become:

- a convenience surface
- a secondary surface
- or a future internal plugin-backed bridge

But not the primary contract today.

## Content normalization rule

Leantime content must be normalized before promotion into ConPort or dope-memory.

This applies especially to:

- HTML-rich ticket descriptions
- comments
- wiki/articles
- canvas content
- strategic planning artifacts
- retrospective and risk content

Promotion rules:

### Safe for direct operational use

- IDs
- statuses
- dates
- assignments
- PM entity references

### Requires normalization before memory/context promotion

- HTML content
- comments
- wiki/article bodies
- canvas rich text
- retrospective notes
- risk descriptions
- idea text

### Usually not promotable without filtering

- noisy comment chatter
- transient notifications
- read-state
- UI/session artifacts
- queue noise

## Relationship to Task Orchestrator

Task Orchestrator remains the workflow authority.

This means:

- Leantime task status is a PM-facing operational record
- Task Orchestrator governs workflow rules, blockers, next-action, and progression semantics
- Leantime integration must not be designed in a way that gives Leantime de facto workflow authority

If a Leantime plugin adds convenience actions, those actions must still defer to the PM plane’s workflow policy where applicable.

## Relationship to ConPort

ConPort remains the authority for:

- decisions
- progress
- structured durable project context

Leantime can be a source of promotable project material, but not the canonical decision/progress authority.

The adapter layer must therefore support:

- extraction of promotable content from Leantime
- normalization before writing to ConPort
- stable linking between Leantime PM entities and ConPort contextual records

## Relationship to dope-memory

dope-memory remains the authority for chronicle memory.

Leantime can emit or provide source material for chronicle-worthy events, but Leantime itself is not the chronicle authority.

The integration must support:

- event or change capture where appropriate
- normalized references into dope-memory
- no direct assumption that Leantime text fields equal chronicle truth

## Rejected alternatives

### 1. Leantime MCP as the primary integration seam

Rejected because it is not mature enough yet.

### 2. Plugin-only integration

Rejected because it would over-couple PM-plane integration to in-app custom extension logic and ignore the more mature JSON-RPC surface.

### 3. Raw controller/HTML scraping

Rejected because it is brittle, low-trust, and below the quality bar for PM-plane integration.

### 4. Direct agent use of Leantime-native service surfaces

Rejected because the PM plane should expose normalized tools, not subsystem-shaped internals.

## Consequences

### Positive

- stable operational integration path
- lower dependence on immature MCP infrastructure
- flexible plugin seam for hooks/UI/internal augmentation
- cleaner boundary between Leantime and the PM plane
- easier normalization and policy wrapping

### Negative

- requires adapter work
- plugin work may still be needed for higher-quality internal integrations
- two seams must be maintained conceptually:
  - JSON-RPC for primary ops
  - plugin for selective augmentation

## Required follow-up work

1. define normalized PM-plane tools backed by Leantime JSON-RPC
2. create a Leantime field/content normalization policy
3. identify which plugin hooks are worth using
4. avoid raw direct agent exposure of subsystem-specific JSON-RPC calls
5. document ID/link mapping between Leantime, ConPort, and dope-memory
6. revisit Leantime MCP only after it is truly runtime-real

## Success criteria

This ADR is successfully implemented when:

- PM-plane operations against Leantime use JSON-RPC as the primary seam
- plugin usage is selective and justified
- Leantime remains the PM entity authority
- Leantime does not become workflow authority
- raw Leantime content is normalized before promotion into memory/context systems
- agents interact with normalized PM-plane tools rather than raw Leantime-native contracts

## Final decision

**Adopt a hybrid Leantime integration strategy with JSON-RPC as the primary operational seam and plugin support as a selective augmentation layer.**
