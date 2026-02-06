---
id: F-NEW-10_WORKING_MEMORY_ASSISTANT
title: F New 10_Working_Memory_Assistant
type: reference
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: F New 10_Working_Memory_Assistant (reference) for dopemux documentation and
  developer workflows.
---
# F-NEW-10: Working Memory Assistant

**Date**: 2025-10-25
**Status**: Design Phase
**Impact**: CRITICAL - Addresses ADHD working memory limitations
**Prerequisites**: F-NEW-6 (Session Intelligence), EventBus, Desktop Commander

---

## Problem Statement

### ADHD Working Memory Gap

ADHD working memory capacity is **significantly limited** (3-5 items vs 7-9 neurotypical). Current Dopemux features don't actively support working memory - users must remember:
- What they were doing before interruption
- Why they started current task
- What decision they need to make next
- Which files are related to current work
- What they discovered 5 minutes ago

### Real-World Pain Points

**Scenario 1: Phone Call Interruption**
```
10:30am: Deep in auth refactoring, understanding token flow
10:35am: Phone rings - 15 minute call
10:50am: Return to computer... "What was I doing? Why am I in this file?"
         Spend 10-15 minutes re-discovering context
❌ 10-15 minutes lost, frustration, may abandon task
```

**Scenario 2: Context Switching**
```
Working on Feature A, need info from Feature B code
Switch to Feature B files, spend 5 minutes understanding
Try to return to Feature A... "Wait, what was I looking for?"
❌ Lost train of thought, decision lost, start over
```

**Scenario 3: Multi-File Refactoring**
```
Need to update auth in 8 files
Complete files 1-3, context switch (Slack message)
Return... "Which files did I already update? What pattern am I using?"
❌ Risk of inconsistent changes, duplicate work
```

### Comparison to Existing Features

| Feature | Addresses | F-NEW-10 Gap |
|---------|-----------|--------------|
| F-NEW-6 | Shows current state | Doesn't preserve *what* you were doing |
| F-NEW-8 | Suggests breaks | Doesn't help resume after break |
| F-NEW-9 | Task selection | Doesn't track progress within task |
| ConPort | Decision logging | Manual, doesn't auto-capture work state |

**Gap**: No automatic working memory support during interruptions

---

## Solution: Working Memory Assistant

### Core Concept

**Automatic breadcrumb system** that captures context every 2-3 minutes and provides instant recovery after interruptions.

**Architecture**:
```
Background Monitor (every 2-3 minutes)
  ├─ Capture current context
  │  ├─ Active files (cursor positions)
  │  ├─ Recent edits (last 5 changes)
  │  ├─ Search queries (last 3)
  │  ├─ Decisions made (from ConPort)
  │  └─ Mental model notes (auto-detected goals)
  ↓
Store in Working Memory Stack (last 10 snapshots)
  ↓
On Interruption Detected (Desktop Commander)
  ↓
Recovery Assistant Activated
  └─ Shows: "You were: [context]"
      "Last edited: [files]"
      "Looking for: [search context]"
      "Next step: [inferred from pattern]"
```

---

## Key Features

### 1. Automatic Context Snapshots

**Every 2-3 Minutes** (ADHD-optimized interval):
```python
{
  "timestamp": "2025-10-25T10:32:00",
  "active_files": [
    {"path": "auth/jwt.py", "line": 145, "column": 23}
  ],
  "recent_edits": [
    {"file": "auth/jwt.py", "line": 145, "change": "Updated token expiry"},
    {"file": "auth/jwt.py", "line": 89, "change": "Added refresh logic"}
  ],
  "recent_searches": [
    "JWT refresh token pattern",
    "token expiration best practices"
  ],
  "mental_model": "Implementing JWT refresh tokens",
  "inferred_goal": "Add token refresh functionality to auth system",
  "session_duration_min": 23
}
```

### 2. Interrupt Detection & Recovery

**Triggers**:
- Workspace switch (Desktop Commander)
- Screen lock > 5 minutes
- Application switch from editor
- Manual trigger (`/recover` command)

**Recovery Display**:
```
🔄 Welcome back! You were interrupted 12 minutes ago.

📍 You were working on: Implementing JWT refresh tokens

📝 Last activity:
   - Editing: auth/jwt.py (line 145)
   - Searching for: "token expiration best practices"
   - Modified: auth/jwt.py, auth/middleware.py

💡 You were probably going to:
   - Add refresh token rotation logic
   - Update middleware to handle refresh requests
   - Write tests for token refresh

🎯 Quick actions:
   [1] Resume at auth/jwt.py:145
   [2] See all modified files (2)
   [3] Review last 5 changes
   [4] Start over with fresh context
```

### 3. Working Memory Stack (Visual)

**Progressive Disclosure** (max 5 items):
```
Working Memory Stack (3 items):

1. [Current] JWT refresh tokens (23 min)
   ├─ Files: auth/jwt.py, auth/middleware.py
   ├─ Goal: Add token refresh functionality
   └─ Next: Implement rotation logic

2. [2 min ago] Understanding auth flow
   ├─ Search: "authentication middleware"
   └─ Context: Researching before implementation

3. [8 min ago] Feature planning
   └─ Decision: Use JWT for auth (logged to ConPort)

[View full stack (7 items)]
```

### 4. Mental Model Inference

**Auto-detect goals from patterns**:
- Editing multiple files → "Multi-file refactoring"
- Search + file open → "Researching [topic]"
- Test file + implementation → "TDD implementation"
- Doc file creation → "Documentation sprint"

**Helps with**: "What was I trying to accomplish?"

### 5. Smart Resume Points

**Not just cursor position - intelligent resume**:
```python
{
  "resume_type": "continue_implementation",
  "suggested_action": "You were about to implement refresh token rotation",
  "evidence": [
    "Last search: 'token rotation best practices'",
    "Last edit: Added refresh_token field to schema",
    "Unfinished: refresh() method has TODO comment"
  ],
  "files_to_open": [
    "auth/jwt.py (line 145) - Continue here",
    "auth/middleware.py (line 67) - Will need to update",
    "tests/test_jwt.py (line 0) - Write test next"
  ]
}
```

---

## Implementation Plan

### Week 1: Core Context Capture (2-3 days)

**Components**:
- Background monitor (captures every 2-3 min)
- Context snapshot structure
- Working memory stack (FIFO, max 10)
- File/cursor tracking
- Edit delta tracking

**Integration**:
- Desktop Commander (workspace switches)
- Editor integration (cursor positions)
- ConPort (decision correlation)

### Week 2: Recovery System (2-3 days)

**Components**:
- Interrupt detector
- Recovery UI/TUI
- Resume point calculator
- Mental model inference
- Quick action menu

**Integration**:
- F-NEW-6 (detect breaks/interruptions)
- EventBus (interrupt events)

### Week 3: Intelligence & Learning (2-3 days)

**Components**:
- Goal inference from patterns
- Recovery success tracking
- Personalized snapshot intervals
- Smart resume optimization

**Integration**:
- F-NEW-7 Phase 3 (pattern correlation)
- F-NEW-9 (task context)

---

## ADHD Benefits

### Reduces Recovery Time
**Before**: 10-15 minutes re-discovering context after interruption
**After**: 30 seconds - see "You were doing X, resume here"
**Impact**: **20-30x faster** interrupt recovery

### Prevents Task Abandonment
**Before**: After interruption, forget context → give up → feel bad
**After**: Instant context recovery → continue → complete → feel accomplished
**Impact**: 40% reduction in abandonment (estimate)

### Supports Limited Working Memory
**Before**: Hold 3-5 things in mind while working (cognitive overload)
**After**: System remembers everything, free up working memory for actual work
**Impact**: Reduced cognitive load, increased capacity

### Confidence in Multi-Step Work
**Before**: "If I get interrupted, I'll lose everything"
**After**: "System has my back, safe to work on complex tasks"
**Impact**: Willingness to tackle harder problems

---

## Technical Architecture

### Storage
```
Redis: Working memory stack (hot, last 10 snapshots, 1-hour TTL)
ConPort: Long-term context archive (searchable, permanent)
EventBus: Interrupt/resume events
```

### Capture Loop
```python
while True:
    await asyncio.sleep(150)  # 2.5 minutes

    snapshot = {
        'files': get_active_files(),
        'edits': get_recent_edits(minutes=5),
        'searches': get_recent_searches(count=3),
        'mental_model': infer_goal(),
        'timestamp': now()
    }

    await redis.lpush('working_memory:user_id', json.dumps(snapshot))
    await redis.ltrim('working_memory:user_id', 0, 9)  # Keep last 10
```

### Recovery Flow
```python
@app.route('/recover')
async def recover_context(user_id):
    # Get last snapshot before interruption
    snapshots = await redis.lrange(f'working_memory:{user_id}', 0, 2)

    last_snapshot = json.loads(snapshots[0])

    # Infer what user was doing
    goal = last_snapshot['mental_model']

    # Calculate resume point
    resume_point = calculate_smart_resume(last_snapshot)

    # Display recovery UI
    return {
        'context_summary': f"You were: {goal}",
        'last_files': last_snapshot['files'],
        'suggested_resume': resume_point,
        'quick_actions': generate_quick_actions(last_snapshot)
    }
```

---

## API Design

### Endpoint 1: Get Current Context
```http
GET /api/working-memory/current?user_id=alice

Response:
{
  "current_snapshot": {
    "active_files": ["auth/jwt.py:145"],
    "mental_model": "Implementing JWT refresh tokens",
    "session_duration_min": 23,
    "recent_edits": 5,
    "recent_searches": ["token rotation"]
  },
  "stack_depth": 3
}
```

### Endpoint 2: Recover After Interruption
```http
POST /api/working-memory/recover
Body: {"user_id": "alice"}

Response:
{
  "interruption_duration_min": 12,
  "context_before_interruption": {
    "you_were": "Implementing JWT refresh tokens",
    "last_edited": "auth/jwt.py (line 145)",
    "last_search": "token rotation best practices",
    "inferred_next_step": "Add refresh token rotation logic"
  },
  "quick_resume": {
    "file": "auth/jwt.py",
    "line": 145,
    "action": "continue_implementation"
  },
  "recovery_confidence": 0.92
}
```

### Endpoint 3: View Working Memory Stack
```http
GET /api/working-memory/stack?user_id=alice&limit=5

Response:
{
  "stack": [
    {
      "timestamp": "2025-10-25T10:32:00",
      "mental_model": "JWT refresh tokens",
      "duration_min": 23,
      "file_count": 2
    },
    {...}
  ],
  "total_snapshots": 7
}
```

---

## Integration Points

### With Existing Features

**F-NEW-6 (Session Intelligence)**:
- Provides cognitive state for snapshot decisions
- Triggers recovery on energy/attention changes

**F-NEW-8 (Break Suggester)**:
- Coordinates break timing with snapshots
- Ensures context saved before break

**F-NEW-9 (Task Router)**:
- Uses working memory for task context
- Helps resume interrupted tasks

**F-NEW-7 Phase 3 (Intelligence)**:
- Correlates interruptions with work patterns
- Learns optimal snapshot intervals

**Desktop Commander**:
- Detects workspace switches (interruptions)
- Triggers recovery assistant

**ConPort**:
- Archives important snapshots
- Searchable context history

---

## Success Criteria

### Performance
- Snapshot capture: <50ms (non-blocking)
- Recovery display: <100ms
- Background monitoring: <1% CPU overhead

### ADHD Impact
- Recovery time: <1 minute (vs 10-15 min baseline)
- **20-30x faster** context restoration
- Abandonment reduction: 40%
- User satisfaction: "Feel safe working on complex tasks"

### Quality
- Goal inference accuracy: >70%
- Resume point accuracy: >80%
- Snapshot relevance: >85% useful on recovery

---

## Comparison to Existing Tools

| Tool | Approach | F-NEW-10 Difference |
|------|----------|---------------------|
| IDE breadcrumbs | File navigation history | Includes mental model + goals |
| Git history | Code changes over time | Real-time (2-3 min), intent-focused |
| Editor sessions | Open files/tabs | Includes search context + inferred goals |
| Browser history | URLs visited | Captures *why* not just *what* |

**Key Difference**: F-NEW-10 captures **cognitive context** (goals, mental models, intent), not just technical state.

---

## Risk Assessment

### Low Risk
- ✅ Non-intrusive (background monitoring)
- ✅ Optional (user can ignore)
- ✅ Privacy-safe (local storage only)

### Medium Risk
- ⚠️ Storage overhead (10 snapshots × user)
- ⚠️ Goal inference accuracy (may be wrong)

### Mitigations
- Redis TTL (auto-cleanup after 1 hour)
- Show confidence scores with inferences
- Manual correction of inferred goals
- Opt-out option

---

## Implementation Effort

**Week 1: Context Capture**
- Background monitor
- Snapshot structure
- Storage (Redis + ConPort)
- Integration with Desktop Commander
- Unit tests

**Week 2: Recovery System**
- Interrupt detection
- Recovery UI/API
- Mental model inference
- Smart resume calculator
- Integration tests

**Week 3: Intelligence**
- Goal inference from patterns
- Recovery success tracking
- Personalized snapshot intervals
- Learning system
- End-to-end tests

**Total**: 3 weeks (similar to F-NEW-9)

---

## Alternative: F-NEW-10 Could Be...

### Option B: Hyperfocus Detector & Redirector
**Problem**: ADHD hyperfocus on wrong tasks (spend 4 hours on CSS tweak while critical bug waiting)
**Solution**: Detect hyperfocus (>90 min same file), check if aligned with priorities, suggest redirect
**Impact**: Prevent wasted hyperfocus windows

### Option C: Visual Progress Indicators
**Problem**: ADHD anxiety from not seeing progress
**Solution**: Real-time progress visualization (progress bars, completion %, time-since-start)
**Impact**: Reduced anxiety, motivation boost

### Option D: Deadline Anxiety Manager
**Problem**: Time blindness + deadline anxiety (forget deadlines OR panic when remembered)
**Solution**: Smart countdown with buffer warnings, break tasks into deadline-aware chunks
**Impact**: Reduced deadline-related stress

---

## Recommendation

**F-NEW-10 should be: Working Memory Assistant**

**Rationale**:
1. **Biggest remaining gap**: Working memory is #1 ADHD challenge not addressed
2. **High synergy**: Works with F-NEW-6, F-NEW-8, F-NEW-9, Desktop Commander
3. **Measurable impact**: 20-30x faster recovery (10-15min → 30sec)
4. **Broad applicability**: Helps with interruptions, context switches, multi-file work
5. **Aligned with Dopemux mission**: Cognitive support for ADHD developers

**Impact Comparison**:
- F-NEW-9: +20% completion, -30% context switches
- **F-NEW-10**: +40% abandonment reduction, 20-30x recovery speed
- Synergy: F-NEW-9 + F-NEW-10 = Comprehensive task + context support

---

## Next Steps

1. **This session**: Design approved ✅ (this document)
2. **Next session**: Implement Week 1 (context capture)
3. **Week 2**: Recovery system
4. **Week 3**: Intelligence + learning

**Total Effort**: 3 weeks (parallel with F-NEW-9 deployment validation)

---

**Status**: Design complete, ready for Week 1 implementation
**Files**: 0 (design only)
**Tests**: 0 (design only)
**Impact**: CRITICAL - Addresses #1 ADHD working memory gap
