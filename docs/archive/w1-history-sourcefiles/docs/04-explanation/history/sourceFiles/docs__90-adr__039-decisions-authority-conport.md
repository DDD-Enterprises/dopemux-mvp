# ADR-039: Decisions & Rationale Authority = ConPort

**Status:** Proposed
**Date:** 2025-09-25
**Context:** Zero-Touch Sync across Leantime, Task-Master, and ConPort

## Context

Decision tracking and rationale capture happens across our systems:
- ConPort specializes in project memory and decision context
- Leantime has comments but no structured decision tracking
- Task-Master focuses on execution, not decision rationale

We need durable storage for why decisions were made and implementation patterns.

## Decision

Make **ConPort** the authoritative source for decisions, rationale, patterns, and follow-up context.

## Rationale

- ConPort is purpose-built for project memory and decision tracking
- Structured decision logging provides better searchability than comments
- Rationale and patterns need to persist beyond individual tasks
- Decision context feeds back into future planning and task generation
- ConPort's semantic search enables decision pattern discovery

## Consequences

### Positive
- Durable knowledge layer for organizational learning
- Structured decision format enables better retrieval and analysis
- Decision patterns can inform future similar situations
- Context preservation supports ADHD-friendly workflows
- Reduces repeated decision-making and research

### Negative
- Adds another system to manage decision information
- Requires discipline to log decisions consistently
- Potential for decision information to become stale

### Neutral
- Sync service batches decision logging to reduce noise
- Decision retrieval feeds into Task-Master planning
- Leantime links to relevant decisions without duplicating content

## Implementation

1. ConPort stores decisions with structured format: context, options, decision, rationale
2. Sync service batches decision updates to reduce notification noise
3. Task-Master queries ConPort for relevant decisions during planning
4. Leantime can link to decisions but doesn't duplicate decision content
5. Decision patterns are surfaced during similar future planning

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [ADR-037: Status Source of Truth](./037-status-source-leantime.md)
- [ADR-038: Subtask Authority](./038-subtask-authority-taskmaster.md)
- [ADR-001: ConPort MCP Project Memory Gateway](./ADR-001-conport-mcp-project-memory-gateway.md)