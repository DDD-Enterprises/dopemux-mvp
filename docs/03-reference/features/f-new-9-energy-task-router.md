---
id: F-NEW-9_ENERGY_TASK_ROUTER
title: F New 9_Energy_Task_Router
type: reference
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: F New 9_Energy_Task_Router (reference) for dopemux documentation and developer
  workflows.
---
# F-NEW-9: Energy-Aware Intelligent Task Router

**Date**: 2025-10-25
**Status**: Design Phase
**Impact**: CRITICAL - Matches tasks to cognitive capacity automatically
**Prerequisites**: F-NEW-6 (Session Intelligence), Task-Orchestrator

## Problem Statement

### Current Pain Point
ADHD developers face **task-state mismatch**: picking high-complexity tasks during low energy leads to frustration, context switching, and abandonment. Current system provides task lists but doesn't guide **which task to do now** based on cognitive state.

### Real-World Scenario
```
10:00am: High energy, focused attention
User manually picks: "Fix typo in README" (complexity 0.1)
❌ Wasted high-energy state on trivial task

2:00pm: Post-lunch dip, scattered attention
User manually picks: "Refactor authentication system" (complexity 0.8)
❌ Frustration, abandonment, context switch

With F-NEW-9:
10:00am: System suggests "Refactor auth" (matches high energy)
2:00pm: System suggests "Fix typo" (matches low energy)
✅ Optimal task-energy matching, higher completion rate
```

## Architecture

### Data Flow
```
F-NEW-6 Session Intelligence
  ├─ Energy: high/medium/low
  ├─ Attention: focused/transitioning/scattered
  └─ Cognitive Load: 0.0-1.0
         ↓
F-NEW-9 Energy-Aware Router
  ├─ Query ConPort for TODO tasks
  ├─ Enrich with F-NEW-3 complexity scores
  ├─ Match to current cognitive state
  └─ Rank by energy-complexity alignment
         ↓
Suggested Tasks (top 3, ADHD-safe)
  - Best match task
  - Alternative 1
  - Alternative 2
```

### Matching Algorithm

**Energy-Complexity Matrix**:
```
Energy Level    | Optimal Complexity Range | Task Types
----------------|--------------------------|------------------
High            | 0.6 - 1.0                | Refactoring, architecture
Medium          | 0.3 - 0.6                | Feature implementation
Low             | 0.0 - 0.3                | Documentation, fixes
```

**Attention-Task Type Matrix**:
```
Attention State | Optimal Task Characteristics
----------------|-----------------------------
Focused         | Deep work, complex logic, requires sustained concentration
Transitioning   | Moderate tasks, clear boundaries, interruptible
Scattered       | Atomic tasks, checklist items, no dependencies
```

**Matching Score Calculation**:
```python
def calculate_task_match(task, cognitive_state):
    # Energy-complexity alignment (50% weight)
    energy_score = match_energy_to_complexity(
        energy=cognitive_state.energy,
        complexity=task.complexity
    )

    # Attention-task type alignment (30% weight)
    attention_score = match_attention_to_task_type(
        attention=cognitive_state.attention,
        task_type=task.characteristics
    )

    # Time available (20% weight)
    time_score = match_time_to_duration(
        time_available=cognitive_state.time_until_break,
        estimated_duration=task.estimated_minutes
    )

    # Weighted combination
    match_score = (
        energy_score * 0.50 +
        attention_score * 0.30 +
        time_score * 0.20
    )

    return match_score  # 0.0-1.0
```

## Key Features

### 1. Smart Task Suggestions
```python
async def get_suggested_tasks(user_id: str, count: int = 3) -> List[TaskSuggestion]:
    """
    Get top N tasks matching current cognitive state.

    Returns:
        - Task details
        - Match score (why this task now)
        - Estimated duration
        - Energy requirement
        - Complexity score
    """
```

### 2. Energy-Task Mismatch Detection
```python
async def detect_task_mismatch(user_id: str, current_task_id: str) -> Optional[MismatchWarning]:
    """
    Detect if current task doesn't match cognitive state.

    Returns warning if:
    - High complexity task + low energy
    - Deep focus task + scattered attention
    - Long task + little time before scheduled break
    """
```

### 3. Task Queue Reordering
```python
async def reorder_task_queue(user_id: str) -> List[str]:
    """
    Automatically reorder TODO queue based on:
    - Current time of day
    - Predicted energy curve (from F-NEW-6 patterns)
    - Task complexity distribution
    - Urgency/priority
    """
```

### 4. Context-Preserved Task Switching
```python
async def suggest_alternative_task(
    user_id: str,
    current_task_id: str,
    reason: str  # "low_energy", "scattered_attention", "time_constraint"
) -> TaskSuggestion:
    """
    When stuck, suggest better-matched alternative task.
    Preserves context of current task for later resume.
    """
```

## Integration Points

### With Existing Features
- **F-NEW-6**: Real-time cognitive state input
- **F-NEW-3**: Task complexity scoring
- **F-NEW-8**: Coordinates break timing with task selection
- **Task-Orchestrator**: Task queue management
- **ConPort**: Task storage and retrieval

### With F-NEW-7 Phase 3 (Cross-Agent Intelligence)
F-NEW-9 provides input for:
- Pattern Type 2: Cognitive-Code Correlation
- "Low energy + high complexity" warnings
- Automatic task routing based on patterns

## Implementation Plan

### Week 1: Core Matching Engine
```
- Energy-complexity matching algorithm
- Attention-task type matching
- Time-duration matching
- Weighted scoring system
- Unit tests (90% target)
```

### Week 2: Integration & API
```
- ConPort query integration
- F-NEW-6 session intelligence integration
- HTTP endpoints for suggestions
- Redis caching for performance
- Integration tests
```

### Week 3: Intelligence & Learning
```
- Pattern learning (which matches led to completion)
- Personalized energy curves
- Task type preference learning
- A/B testing framework for match quality
```

## Success Criteria

### Performance
- Suggestion generation: <100ms
- Cache hit rate: >80%
- Background queue reordering: <200ms

### ADHD Impact
- Task completion rate increase: +20%
- Context switch reduction: -30%
- Frustration incidents: -50%
- User satisfaction: Measured via completion rate

### Quality
- Match accuracy: >75% (task completed vs abandoned)
- Mismatch detection: <5% false positives
- Queue relevance: Top 3 contain best match >90% of time

## ADHD Benefits

### Reduces Decision Fatigue
Before: "Which of these 20 tasks should I do now?" (paralyzing)
After: "Here are 3 tasks that match your current state" (actionable)

### Prevents Frustration
Before: Start high-complexity task at low energy → give up → feel bad
After: System guides to appropriate task → complete → feel accomplished

### Maximizes Productivity Windows
Before: Waste high-energy state on trivial tasks
After: Automatic routing to high-value work during peak performance

### Supports Time Blindness
Before: "I have 15 minutes, start 2-hour task" → incomplete, frustration
After: "You have 15 min, here's a 10-min task" → completion, success

## API Design

### Endpoint 1: Get Suggestions
```http
GET /api/tasks/suggest?user_id=alice&count=3

Response:
{
  "cognitive_state": {
    "energy": "high",
    "attention": "focused",
    "time_available_min": 35
  },
  "suggestions": [
    {
      "task_id": "T-123",
      "title": "Refactor authentication middleware",
      "match_score": 0.92,
      "complexity": 0.75,
      "estimated_minutes": 30,
      "match_reason": "High energy + focused attention matches complex refactoring",
      "rank": 1
    },
    {...},
    {...}
  ],
  "response_time_ms": 47
}
```

### Endpoint 2: Check Current Task Match
```http
POST /api/tasks/check-match
Body: {"user_id": "alice", "task_id": "T-123"}

Response:
{
  "is_good_match": false,
  "mismatch_reason": "Task complexity (0.8) too high for current low energy",
  "suggested_action": "switch_to_easier_task",
  "alternatives": [
    {"task_id": "T-45", "title": "Update documentation", "match_score": 0.88}
  ]
}
```

### Endpoint 3: Reorder Queue
```http
POST /api/tasks/reorder-queue
Body: {"user_id": "alice"}

Response:
{
  "original_order": ["T-1", "T-2", "T-3", "T-4", "T-5"],
  "optimized_order": ["T-3", "T-1", "T-5", "T-2", "T-4"],
  "reorder_reason": "Matched to predicted energy curve for today",
  "estimated_completion_improvement": "+35%"
}
```

## Comparison to Existing Features

| Feature | Focus | F-NEW-9 Enhancement |
|---------|-------|---------------------|
| F-NEW-6 | Shows current state | Uses state for routing |
| F-NEW-3 | Complexity score | Matches complexity to energy |
| F-NEW-8 | Suggests breaks | Prevents bad task choices |
| Task-Orchestrator | Task management | Adds intelligent selection |

**Synergy**: F-NEW-9 acts as the "intelligence layer" that connects cognitive state (F-NEW-6) to task selection, using complexity (F-NEW-3) and coordinating with breaks (F-NEW-8).

## Risk Assessment

### Low Risk
- ✅ Builds on proven features (F-NEW-3, F-NEW-6)
- ✅ Optional feature (doesn't break existing workflow)
- ✅ Graceful degradation (falls back to manual selection)

### Medium Risk
- ⚠️ Learning accuracy (needs user feedback loop)
- ⚠️ Personalization data (requires usage history)

### Mitigations
- Start with simple rule-based matching
- Add ML personalization in Phase 2
- Provide manual override always
- Track accuracy metrics for continuous improvement

## Next Steps

1. **This session**: Create design document (this file) ✅
2. **Next session**: Implement Week 1 (matching engine)
3. **Week 2**: Integration with F-NEW-6 + Task-Orchestrator
4. **Week 3**: Pattern learning and personalization

## Decision

**Recommendation**: F-NEW-9 should be **Energy-Aware Intelligent Task Router**

**Rationale**:
- Addresses major ADHD pain point (decision fatigue + task-state mismatch)
- High synergy with existing features
- Clear success metrics (completion rate, frustration reduction)
- Feasible implementation (3 weeks)
- Aligns with Dopemux cognitive support mission
