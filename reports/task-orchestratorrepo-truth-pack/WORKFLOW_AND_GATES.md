# Workflow and Gates

> All state machines, transition rules, and gating logic in this document are extracted directly
> from code (`RoleTransitionHandler.kt`, `AdvanceItemTool.kt`, `NoteSchemaService.kt`,
> `CascadeDetector.kt`). No documentation claims are used without code verification.

## 1. Role State Machine

```
     ┌──── cancel ─────────────────┐
     │                              │
  QUEUE ──start──▶ WORK ──start──▶ REVIEW ──start──▶ TERMINAL
     │              │                │                   ▲
     │              └──── start (no review) ─────────────┘
     │              │                │
     └──block/hold─▶ BLOCKED ◀──block/hold──┘
                      │
                   resume → previousRole
```

### Roles (from `Role.kt`)
| Role       | Purpose                                 | Progression Index |
| ---------- | --------------------------------------- | ----------------- |
| `QUEUE`    | Item created, awaiting start            | 0                 |
| `WORK`     | Active implementation                   | 1                 |
| `REVIEW`   | Under review / validation               | 2                 |
| `TERMINAL` | Done (completed or cancelled)           | 3                 |
| `BLOCKED`  | Paused (orthogonal, not in progression) | —                 |

### Progression Order
`QUEUE < WORK < REVIEW < TERMINAL` (from `Role.PROGRESSION`)

`BLOCKED` is orthogonal — never satisfies a sequential threshold.

## 2. Transition Table (from `RoleTransitionHandler.resolveTransition`)

| Current Role | Trigger        | Target Role  | Condition                         | Status Label  |
| ------------ | -------------- | ------------ | --------------------------------- | ------------- |
| QUEUE        | `start`        | WORK         | dependency gate                   | —             |
| WORK         | `start`        | REVIEW       | `hasReviewPhase=true` + dep gate  | —             |
| WORK         | `start`        | TERMINAL     | `hasReviewPhase=false` + dep gate | —             |
| REVIEW       | `start`        | TERMINAL     | dependency gate                   | —             |
| TERMINAL     | `start`        | **rejected** | "already terminal"                | —             |
| BLOCKED      | `start`        | **rejected** | "must resume first"               | —             |
| QUEUE        | `complete`     | TERMINAL     | none                              | —             |
| WORK         | `complete`     | TERMINAL     | none                              | —             |
| REVIEW       | `complete`     | TERMINAL     | none                              | —             |
| TERMINAL     | `complete`     | **rejected** | "already terminal"                | —             |
| BLOCKED      | `complete`     | **rejected** | "must resume first"               | —             |
| QUEUE        | `block`/`hold` | BLOCKED      | none                              | —             |
| WORK         | `block`/`hold` | BLOCKED      | none                              | —             |
| REVIEW       | `block`/`hold` | BLOCKED      | none                              | —             |
| TERMINAL     | `block`/`hold` | **rejected** | "already terminal"                | —             |
| BLOCKED      | `block`/`hold` | **rejected** | "already blocked"                 | —             |
| BLOCKED      | `resume`       | previousRole | previousRole must exist           | —             |
| non-BLOCKED  | `resume`       | **rejected** | "not blocked"                     | —             |
| QUEUE        | `cancel`       | TERMINAL     | none                              | `"cancelled"` |
| WORK         | `cancel`       | TERMINAL     | none                              | `"cancelled"` |
| REVIEW       | `cancel`       | TERMINAL     | none                              | `"cancelled"` |
| BLOCKED      | `cancel`       | TERMINAL     | none                              | `"cancelled"` |
| TERMINAL     | `cancel`       | **rejected** | "already terminal"                | —             |

**Note**: `hold` is an alias for `block` (code: `"block", "hold" -> resolveBlock()`)

## 3. Three-Phase Transition Process (from `RoleTransitionHandler`)

### Phase 1: Resolve (pure logic, no I/O)
Maps `(currentRole, trigger)` → `targetRole`. Uses `hasReviewPhase` to determine WORK→REVIEW vs WORK→TERMINAL.

### Phase 2: Validate (dependency check)
For forward progressions only:
- Fetches all incoming BLOCKS/IS_BLOCKED_BY dependencies
- For each blocker: checks if `Role.isAtOrBeyond(blockerRole, thresholdRole)`
- Effective threshold = `dependency.unblockAt ?? "terminal"`
- RELATES_TO dependencies have no blocking semantics
- Transitions to BLOCKED always pass (no gate)

### Phase 3: Apply (persist + audit)
- Updates `WorkItem.role`, `previousRole`, `statusLabel`, `roleChangedAt`
- When entering BLOCKED: saves current role as `previousRole`
- When leaving BLOCKED: clears `previousRole`
- Records `RoleTransition` audit entry

## 4. Note Schema Gates (from `AdvanceItemTool` + `NoteSchemaService`)

### Gate Enforcement
- `trigger="start"`: checks required notes for **current phase only**
- `trigger="complete"`: checks required notes for **ALL phases**
- Missing required notes → transition rejected with `missingNotes` array and `guidancePointer`

### Schema Resolution
1. Get item's tags (comma-separated)
2. `NoteSchemaService.getSchemaForTags(tagList)` → first matching schema
3. Filter entries by current role → required entries → check existence
4. No config file → `NoOpNoteSchemaService` → all gates pass (schema-free mode)

### hasReviewPhase
- `NoteSchemaService.hasReviewPhase(tags)` → true if matched schema has any `role="review"` entry
- When false: WORK → `start` → TERMINAL (skips REVIEW)
- When no schema matches: false → REVIEW skipped

## 5. Cascade Logic (from `CascadeDetector`)

### Completion Cascade
When a `WorkItem` reaches TERMINAL and has a `parentId`:
1. Check if ALL sibling items (same `parentId`) are TERMINAL
2. If yes, parent auto-advances to TERMINAL
3. Recursive up ancestor chain (max depth bounded by hierarchy)

### Start Cascade
When a `WorkItem` enters WORK and has a parent in QUEUE:
- Parent auto-advances to WORK

### Unblock Detection
After any transition on item X:
1. Find all outgoing BLOCKS dependencies from X
2. For each target item: check if ALL its incoming blocking deps are now satisfied
3. Report newly-unblocked items as `unblockedItems` in the response

## 6. Config Format (from `YamlNoteSchemaService`)

```yaml
# .taskorchestrator/config.yaml
note_schemas:
  <tag-name>:
    - key: <note-key>
      role: queue | work | review
      required: true | false
      description: "..."
      guidance: "..."    # optional
```

Loaded from: `$AGENT_CONFIG_DIR/.taskorchestrator/config.yaml`
Fallback: `$user.dir/.taskorchestrator/config.yaml`
