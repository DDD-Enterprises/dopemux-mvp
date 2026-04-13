# ADR-0001: Record Architecture Decisions

_Last updated: 2025-09-02 UTC_
**Status:** Proposed  
**Date:** 2025-08-30

## Context
We need a lightweight, durable way to capture architecture decisions as the system evolves.

## Decision
Use Markdown ADRs stored under `docs/adr/` with sequential IDs. Each ADR covers one decision and links related ADRs.

## Consequences
- Decisions are explicit and reviewable.
- Easy to update and reference from PRs and issues.
- Minimal overhead; encourages continuous documentation.

## Alternatives Considered
- Wiki-only records (harder to version alongside code)
- No formal ADRs (decisions get lost)
