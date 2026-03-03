# ADR-041: Conflict Resolution = LWW + Precedence

**Status:** Proposed
**Date:** 2025-09-25
**Context:** Zero-Touch Sync across Leantime, Task-Master, and ConPort

## Context

When synchronizing data across multiple systems, conflicts are inevitable:
- Same field updated in multiple systems
- Different systems having different "truth" about the same entity
- Race conditions during sync operations
- Schema or enum mapping differences

We need predictable, simple conflict resolution that minimizes manual intervention.

## Decision

Use **Last-Write-Wins (LWW) with explicit precedence rules** for different field types, plus manual review queue for complex conflicts.

## Conflict Resolution Strategy

### Precedence Rules (Override LWW)
- **Status fields** → Leantime wins (authoritative for team visibility)
- **Subtasks/hierarchy** → Task-Master wins (authoritative for task decomposition)
- **Decisions/rationale** → ConPort wins (authoritative for project memory)

### LWW for General Fields
- **Title, description, notes** → Most recent timestamp wins
- **Assignments, due dates** → Most recent timestamp wins
- **Metadata fields** → Most recent timestamp wins

### Manual Review Queue
- Status conflicts when TM is significantly newer than stale LT record
- Field changes that happen simultaneously (within threshold)
- Enum/schema mapping failures

## Rationale

- **Simplicity**: Easy to implement and reason about
- **Predictability**: Deterministic outcomes reduce surprises
- **Authority respect**: Leverages each system's core strength
- **Escape hatch**: Manual review handles edge cases
- **Fast rollout**: No complex CRDT or multi-master logic needed

## Consequences

### Positive
- Simple to implement and test
- Predictable conflict outcomes
- Respects system authorities
- Handles most conflicts automatically
- Clear escalation path for complex cases

### Negative
- May lose some updates in race conditions
- Manual review queue requires operational attention
- LWW doesn't preserve all edit history

### Neutral
- Conflicts requiring review are logged with full context
- Audit trail maintained for all sync operations
- Can evolve to more sophisticated resolution later

## Implementation Details

### Timestamp Handling
```
conflict_threshold = 60 seconds  # simultaneous edit detection
stale_threshold = 30 minutes     # when to prefer newer over authoritative
```

### Review Queue Structure
```
{
  "conflict_id": "uuid",
  "entity_type": "task|ticket|decision",
  "conflict_type": "precedence_override|simultaneous_edit|mapping_failure",
  "systems": ["leantime", "taskmaster"],
  "field": "status",
  "values": {"leantime": "in_progress", "taskmaster": "completed"},
  "timestamps": {"leantime": "2025-09-25T10:30:00Z", "taskmaster": "2025-09-25T10:32:00Z"},
  "auto_resolution": "precedence_leantime|lww_taskmaster|manual_required",
  "created_at": "2025-09-25T10:35:00Z"
}
```

### Monitoring & Alerting
- Alert when review queue > 10 items
- Daily digest of resolved conflicts
- Weekly pattern analysis to identify systemic issues

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [ADR-037: Status Source of Truth](./037-status-source-leantime.md)
- [ADR-038: Subtask Authority](./038-subtask-authority-taskmaster.md)
- [ADR-039: Decisions Authority](./039-decisions-authority-conport.md)