# ADR-038: Subtask Authority = Task-Master

**Status:** Proposed
**Date:** 2025-09-25
**Context:** Zero-Touch Sync across Leantime, Task-Master, and ConPort

## Context

Task decomposition and hierarchical task management occurs across multiple systems:
- Task-Master excels at PRD → hierarchical task trees and next-action logic
- Leantime has limited subtask capabilities
- ConPort tracks decisions but not task hierarchy

We need clear ownership of subtask/hierarchy management to avoid conflicts.

## Decision

Make **Task-Master** the authoritative source for subtasks, task hierarchy, and next-action determination.

## Rationale

- Task-Master specializes in AI-driven task decomposition from PRDs
- Task-Master has sophisticated next-action and dependency logic
- Leantime's subtask features are basic compared to Task-Master's capabilities
- Task hierarchy is complex data that benefits from specialized tooling
- AI-generated task trees require algorithmic management

## Consequences

### Positive
- Leverages Task-Master's core competency in task decomposition
- Maintains sophisticated task hierarchy and dependency tracking
- AI-driven next-action suggestions remain intelligent
- Reduces duplication of complex task management logic

### Negative
- Leantime loses direct subtask editing capabilities for synced tasks
- Task hierarchy lives outside the main project management UI
- Requires sync mechanism to reflect task structure in Leantime

### Neutral
- Leantime receives link-backs and summaries of task hierarchy
- Task structure remains fully managed in Task-Master
- Sync provides visibility without transferring ownership

## Implementation

1. Task-Master maintains authoritative task hierarchy and subtasks
2. Leantime receives link-backs to Task-Master tasks when hierarchy is created
3. Summary information flows to Leantime for visibility
4. Next-action logic remains in Task-Master
5. ConPort logs task-related decisions but doesn't manage task structure

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [ADR-037: Status Source of Truth](./037-status-source-leantime.md)
- [ADR-039: Decisions Authority](./039-decisions-authority-conport.md)