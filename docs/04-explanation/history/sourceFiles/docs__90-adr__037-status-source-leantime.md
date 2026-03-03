# ADR-037: Status Source of Truth = Leantime

**Status:** Proposed
**Date:** 2025-09-25
**Context:** Zero-Touch Sync across Leantime, Task-Master, and ConPort

## Context

In our multi-system workflow, we have status information in multiple places:
- Leantime tickets with team-visible status dashboards
- Task-Master with AI-managed task states
- ConPort with decision context but no formal status

Status is visible to the team and drives reporting, so we need a clear authoritative source.

## Decision

Make **Leantime** the authoritative source for status information across all systems.

## Rationale

- Leantime has established dashboards and reporting infrastructure
- Team members expect status updates to be visible in Leantime
- Leantime status drives milestone and roadmap visibility
- Task-Master specializes in task decomposition, not status management
- ConPort focuses on decisions and context, not operational status

## Consequences

### Positive
- Clear single source of truth for status
- Team visibility maintained through existing Leantime UI
- Status reporting and dashboards remain functional
- Reduces confusion about where to check status

### Negative
- Task-Master status becomes secondary/derived
- Requires sync mechanism to keep systems aligned
- Conflicts between TM and LT status need resolution strategy

### Neutral
- Task-Master status mirrors Leantime unless Leantime is stale/empty
- Status conflicts go to manual review queue
- Automated sync respects Leantime precedence

## Implementation

1. Sync service reads authoritative status from Leantime
2. Task-Master status updates are reflected to Leantime if LT record is stale
3. ConPort logs status-related decisions but doesn't manage status itself
4. Conflict resolution prefers Leantime with manual review for complex cases

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [ADR-038: Subtask Authority](./038-subtask-authority-taskmaster.md)
- [ADR-041: Conflict Resolution](./041-conflict-resolution-lww-precedence.md)