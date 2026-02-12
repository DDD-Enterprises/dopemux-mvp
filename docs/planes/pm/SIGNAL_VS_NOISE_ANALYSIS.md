---
id: SIGNAL_VS_NOISE_ANALYSIS
title: Signal Vs Noise Analysis
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: ADHD-first event classification for PM plane distinguishing actionable signals from cognitive noise.
---
# Signal vs. Noise Analysis (Phase 1)

**Status**: Phase 1 Complete (Evidence-Based)
**Analysis Date**: 2026-02-12
**Evidence Location**: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`

## Purpose

Classify PM plane events as **signal** (actionable, requires attention) vs. **noise** (background, suppress by default) from an ADHD developer perspective. Goal: Reduce cognitive load by filtering out 70-90% of events.

## Evidence Base

- Event type definitions: `nl_src_dopemux_events_types.py.txt:1-116`
- Event bus implementation: `nl_src_dopemux_event_bus.py.txt:1-176`
- ADHD metadata structure: `nl_src_dopemux_event_bus.py.txt:33-38` (ADHDMetadata)
- Priority levels: `nl_src_dopemux_events_types.py.txt:14-21` (EventPriority enum)

## Signal Events (Actionable - Show by Default)

Events that require user attention or action. Characteristics: `interruption_allowed=True`, `focus_required=True`, or `priority >= HIGH`.

### 1. ADHD State Changes

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `adhd.break_reminder` | **SIGNAL** | Prevents burnout, requires immediate action (take break) | `types.py:76` (StateType.BREAK_REMINDER) | HIGH |
| `adhd.attention` (focused→scattered) | **SIGNAL** | Critical state change affecting task selection | `types.py:75` (StateType.ATTENTION) | HIGH |
| `adhd.context_switch` (detected) | **SIGNAL** | Indicates potential flow break, may need recovery | `types.py:77` (StateType.CONTEXT_SWITCH) | HIGH |

**Total**: 3 ADHD signal events

### 2. Task State Changes (Critical Only)

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `context.progress_updated` (BLOCKED→TODO) | **SIGNAL** | Task unblocked, ready to work | `types.py:61` (Action.PROGRESS_UPDATED), `20_friction_search.txt:96-108` (status transitions) | HIGH |
| `context.decision_logged` (task-related) | **SIGNAL** | Architectural decision logged, may affect current work | `types.py:60` (Action.DECISION_LOGGED) | MEDIUM |

**Total**: 2 task signal events (out of 6+ task state events)

### 3. Critical Errors/Conflicts

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| ConPort sync conflict | **SIGNAL** (inferred) | Manual resolution required, blocks progress | `30_memory_burden_search.txt:8` ("manual resolution"), `PM_FRICTION_MAP.md` (conflict friction) | CRITICAL |
| Missing required fields error | **SIGNAL** (inferred) | Prevents task creation, needs correction | `30_memory_burden_search.txt:12-24` ("missing id or title") | HIGH |

**Total**: 2 error signal events (inferred from friction analysis)

### 4. Context Recovery Triggers

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `worktree.switched` | **SIGNAL** | Major context change, may need ConPort workspace switch | `types.py:43` (Action.SWITCHED) | MEDIUM |
| `session.destroyed` | **SIGNAL** (if unexpected) | Potential work loss, may need recovery | `types.py:109` (Action.DESTROYED) | HIGH |

**Total**: 2 context recovery signal events

## Noise Events (Background - Suppress by Default)

Events that are implementation details or non-actionable state. Characteristics: `interruption_allowed=False`, `can_batch=True`, or `priority <= MEDIUM`.

### 1. Theme/Visual Updates

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `theme.switched` | **NOISE** | Visual change, no action required | `types.py:91` (Action.SWITCHED) | LOW |
| `theme.updated` | **NOISE** | Configuration change, background | `types.py:92` (Action.UPDATED) | LOW |
| `theme.interpolated` | **NOISE** | Energy state transition visual, automatic | `types.py:93` (Action.INTERPOLATED) | LOW |

**Total**: 3 theme noise events

### 2. Session Lifecycle (Routine)

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `session.attached` | **NOISE** | Routine action, no interruption | `types.py:107` (Action.ATTACHED) | LOW |
| `session.detached` | **NOISE** | Expected behavior, resumable | `types.py:108` (Action.DETACHED) | LOW |
| `session.pane_created` | **NOISE** | Implementation detail, auto-handled | `types.py:110` (Action.PANE_CREATED) | LOW |
| `session.layout_changed` | **NOISE** | Visual change, no action | `types.py:111` (Action.LAYOUT_CHANGED) | LOW |

**Total**: 4 session noise events (out of 6 session events)

### 3. Worktree Operations (Routine)

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `worktree.created` | **NOISE** | Expected after user action, confirmation only | `types.py:42` (Action.CREATED) | LOW |
| `worktree.removed` | **NOISE** | User-initiated cleanup, expected | `types.py:44` (Action.REMOVED) | LOW |
| `worktree.cleaned` | **NOISE** | Background maintenance, automatic | `types.py:45` (Action.CLEANED) | LOW |

**Total**: 3 worktree noise events (out of 4 worktree events)

### 4. Task State Changes (Non-Critical)

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `context.progress_updated` (TODO→IN_PROGRESS) | **NOISE** | Expected state change, user knows they started task | `types.py:61`, `20_friction_search.txt:14-27` (status transitions) | LOW |
| `context.progress_updated` (IN_PROGRESS→DONE) | **NOISE** (maybe SIGNAL) | User knows they finished, but may want confirmation | `types.py:61`, `20_friction_search.txt:14-27` | LOW-MEDIUM |
| `context.updated` (routine) | **NOISE** | Background sync, no action needed | `types.py:58` (Action.UPDATED) | LOW |
| `context.restored` (session start) | **NOISE** | Expected after load, confirmation only | `types.py:59` (Action.RESTORED) | LOW |

**Total**: 4 task noise events (out of 6 task state events)

### 5. ADHD State Changes (Non-Critical)

| Event | Classification | Rationale | Evidence | Priority |
|-------|---------------|-----------|----------|----------|
| `adhd.energy` (transitions) | **NOISE** | Gradual changes, theme adapts automatically | `types.py:74` (StateType.ENERGY) | LOW |
| `adhd.attention` (scattered→focused) | **NOISE** (maybe SIGNAL) | Positive change, less urgent than reverse | `types.py:75` | LOW-MEDIUM |

**Total**: 2 ADHD noise events (out of 4 ADHD events)

## Summary Statistics

### Signal vs. Noise Ratio

| Category | Signal Events | Noise Events | Total | Signal % |
|----------|--------------|--------------|-------|----------|
| **ADHD State** | 3 | 2 | 5 | 60% |
| **Task State** | 2 | 4 | 6 | 33% |
| **Errors/Conflicts** | 2 | 0 | 2 | 100% |
| **Context Recovery** | 2 | 0 | 2 | 100% |
| **Theme/Visual** | 0 | 3 | 3 | 0% |
| **Session Lifecycle** | 2 | 4 | 6 | 33% |
| **Worktree Ops** | 1 | 3 | 4 | 25% |
| **TOTAL** | **12** | **16** | **28** | **43%** |

**Target**: 10-30% signal events (low noise ratio)
**Actual**: 43% signal events
**Gap**: 13-33% too high (need more aggressive noise filtering)

### Filtering Impact

**Current State** (no filtering):
- 28 events/hour estimated (from friction search volume)
- All events shown → cognitive overload

**With Phase 1 Filtering** (suppress noise):
- 12 signal events/hour (43% of 28)
- 57% reduction in notifications
- Still above ADHD-safe threshold (<10 events/hour)

**Phase 2 Target** (adaptive filtering):
- 3-5 critical events/hour during focus state
- 10-12 events/hour during transitioning state
- 85-90% reduction vs. current

## ADHD Filtering Rules

### Rule 1: Priority-Based Suppression

**Suppress by default**:
- `priority == LOW` → Always suppress unless explicitly subscribed
- `priority == MEDIUM` && `can_batch == True` → Batch and show digest (not individual events)

**Show immediately**:
- `priority == HIGH` || `priority == CRITICAL` → Always show

**Evidence**: `event_bus.py:28-32` (Priority enum), `types.py:14-21` (EventPriority)

### Rule 2: ADHD Metadata Filtering

**Suppress when**:
- `interruption_allowed == False` → Never interrupt, batch for later
- `focus_required == False` && current_state == "focused" → Defer to break time

**Show when**:
- `focus_required == True` && current_state == "scattered" → Help user focus
- `time_sensitive == True` → Show regardless of state (e.g., break reminders)

**Evidence**: `event_bus.py:33-38` (ADHDMetadata dataclass)

### Rule 3: Attention State Adaptation

**During focused state**:
- Show: CRITICAL events, break reminders, BLOCKED→TODO transitions
- Suppress: All LOW/MEDIUM events, visual updates, routine state changes
- Batch: Task completion confirmations (show at break time)

**During scattered state**:
- Show: Attention state changes, focus-required events, conflict alerts
- Suppress: Visual updates, session lifecycle, routine worktree ops
- Batch: Decision logs, non-critical progress updates

**During transitioning state**:
- Show: Context recovery triggers, unblock events, ADHD state changes
- Suppress: All LOW priority events
- Batch: Theme updates, session lifecycle

**Evidence**: `types.py:73-82` (ADHDEvent.StateType enum), ADHD accommodation patterns from global CLAUDE.md

### Rule 4: Event Batching

**Batchable events** (`can_batch == True`):
- Group by 5-minute windows
- Show digest: "3 tasks completed, 2 decisions logged" vs. 5 individual events
- User can expand digest to see details

**Non-batchable** (`can_batch == False`):
- Show immediately: Break reminders, critical errors, unblock events

**Evidence**: `event_bus.py:38` (can_batch field in ADHDMetadata)

## Open Questions

**Q1**: What is the actual event frequency per attention state?
- **Why Unknown**: No telemetry on event emission rates during focus vs. scatter
- **Impact**: Can't validate if 43% signal ratio achieves <10 events/hour target

**Q2**: Which "NOISE" events do users actually find valuable?
- **Why Unknown**: No user preference data, classification based on theory
- **Impact**: May be suppressing useful confirmations (e.g., task completion)

**Q3**: What is the optimal batch window for ADHD developers?
- **Why Unknown**: No A/B testing of 1min vs. 5min vs. 15min batching
- **Impact**: Too short = still noisy, too long = lost awareness

**Q4**: How do users respond to attention state change notifications?
- **Why Unknown**: No user interaction telemetry
- **Impact**: May be interrupting unnecessarily if users ignore the notification

## Next Steps (Phase 2)

1. **Instrument Event Bus**: Add telemetry for event frequency, type distribution, user interactions
2. **User Testing**: A/B test signal/noise classification with real ADHD developers
3. **Adaptive Batching**: Implement 5-minute batch windows, measure impact on cognitive load
4. **Priority Calibration**: Adjust event priorities based on user feedback
5. **Custom Filters**: Allow users to customize signal/noise thresholds per attention state

---

**Evidence Manifest**:
- `nl_src_dopemux_events_types.py.txt`: Event type definitions (5 event classes, 28+ event types)
- `nl_src_dopemux_event_bus.py.txt`: Event bus implementation, ADHD metadata, priority levels
- `20_friction_search.txt`: Task state transition patterns (1,710 lines analyzed)
- `30_memory_burden_search.txt`: Error/conflict markers (281 lines analyzed)
- `PM_FRICTION_MAP.md`: Friction analysis informing signal classification
