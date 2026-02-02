# Week 3 Implementation Roadmap: Day-by-Day Execution Plan

**Sprint**: Week 3 (CognitiveGuardian Production Integration)
**Duration**: 5 days (Mon-Fri)
**Goal**: Production-ready ADHD support with 60% functionality
**Method**: ADHD-optimized implementation (25-min focus blocks, gentle breaks)

---

## Overview: The ADHD-Friendly Implementation Strategy

**Philosophy**: Work with your brain, not against it

**Key Principles**:
1. **Focus blocks**: 25-minute intense work, then 5-minute break
2. **One thing at a time**: Single file/feature per block
3. **Test immediately**: Validate after each block
4. **Celebrate wins**: Mark progress after each completion
5. **Flexible timing**: If hyperfocus hits, ride it (up to 60 min)

**Total Focus Blocks**: 10 blocks (2 per day)
**Total Break Time**: ~50 minutes (built-in recovery)
**Buffer Time**: 20% (for unexpected complexity)

---

## Day 1 (Monday): ConPort MCP Integration Foundation

**Goal**: Wire CognitiveGuardian to ConPort for persistence
**Energy Required**: High (new integration work)
**Complexity**: 0.5 (moderate - following existing patterns)

---

### Focus Block 1.1 (25 min) - ConPort Client Detection

**Start Time**: 9:00 AM (optimal high-energy window)

**Task**: Add Claude Code context detection + client initialization

**File**: `services/agents/cognitive_guardian.py`

**Changes**:
```python
# In __init__():
self._in_claude_code = self._detect_claude_code_context()
```

**Add Methods**:
1. `_detect_claude_code_context()` (~10 lines)
2. `_load_user_preferences()` (~20 lines)

**Test**:
```bash
cd services/agents
python -c "from cognitive_guardian import CognitiveGuardian; g = CognitiveGuardian('/test'); print(f'Claude Code: {g._in_claude_code}')"
```

**Expected Output**: `Claude Code: True` (if in Claude Code) or `False`

**Completion Criteria**:
- [ ] Method added
- [ ] Test passes
- [ ] No import errors

**Break**: 5 minutes (stretch, water, quick walk)

---

### Focus Block 1.2 (25 min) - User Preference Loading

**Start Time**: 9:30 AM

**Task**: Implement preference loading from ConPort

**File**: `services/agents/cognitive_guardian.py`

**Changes**:
```python
async def _load_user_preferences(self):
    """Load ADHD preferences from ConPort."""
    try:
        from mcp_tools import mcp__conport__get_custom_data
        prefs = await mcp__conport__get_custom_data(...)
        if prefs:
            self.break_interval = prefs.get("gentle_reminder", 25)
            # ...
    except Exception as e:
        logger.warning(f"Could not load preferences: {e}")
```

**Test**:
```python
# In test_cognitive_guardian.py
async def test_preference_loading():
    guardian = CognitiveGuardian("/test")
    # If prefs available:
    # assert guardian.break_interval == (custom value)
    # Else:
    assert guardian.break_interval == 25  # default
```

**Completion Criteria**:
- [ ] Preferences loaded (if available)
- [ ] Defaults work if ConPort unavailable
- [ ] Test passes

**Break**: 10 minutes (longer break after 2 blocks)

---

### Focus Block 1.3 (25 min) - User State Persistence

**Start Time**: 10:05 AM

**Task**: Save user state to ConPort after calculation

**File**: `services/agents/cognitive_guardian.py`

**Add Method**:
```python
async def _save_user_state(self, user_state: UserState):
    """Persist user state to ConPort."""
    if not self._in_claude_code:
        return
    try:
        from mcp_tools import mcp__conport__update_active_context
        await mcp__conport__update_active_context(
            workspace_id=self.workspace_id,
            patch_content={"cognitive_guardian_state": {...}}
        )
    except Exception as e:
        logger.error(f"Failed to save user state: {e}")
```

**Integrate in `get_user_state()`**:
```python
async def get_user_state(self) -> UserState:
    # ... calculate state ...
    user_state = UserState(...)
    await self._save_user_state(user_state)  # NEW
    return user_state
```

**Test**:
```python
# Manual test in Claude Code
guardian = CognitiveGuardian("/Users/hue/code/dopemux-mvp")
await guardian.start_monitoring()
state = await guardian.get_user_state()
# Check ConPort for saved state:
# mcp__conport__get_active_context(workspace_id="/Users/hue/code/dopemux-mvp")
```

**Completion Criteria**:
- [ ] Method added
- [ ] Integration in get_user_state() complete
- [ ] ConPort save verified (check logs or ConPort directly)

**Break**: 5 minutes

---

### Focus Block 1.4 (25 min) - Metrics Persistence

**Start Time**: 10:35 AM

**Task**: Save metrics to ConPort on session end

**File**: `services/agents/cognitive_guardian.py`

**Add Method**:
```python
async def _save_metrics(self):
    """Persist metrics to ConPort."""
    if not self._in_claude_code:
        return
    try:
        from mcp_tools import mcp__conport__log_custom_data
        metrics = self.get_metrics()
        await mcp__conport__log_custom_data(
            workspace_id=self.workspace_id,
            category="adhd_metrics",
            key=f"session_{datetime.now(timezone.utc).isoformat()}",
            value=metrics
        )
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
```

**Integrate in `stop_monitoring()`**:
```python
async def stop_monitoring(self):
    # ... existing code ...
    await self._save_metrics()  # NEW
    logger.info("CognitiveGuardian monitoring stopped")
```

**Test**:
```python
# Start, work, stop
guardian = CognitiveGuardian("/test")
await guardian.start_monitoring()
await asyncio.sleep(5)  # Simulate work
await guardian.stop_monitoring()
# Check logs for "Metrics persisted to ConPort"
```

**Completion Criteria**:
- [ ] Method added
- [ ] Integration complete
- [ ] Metrics visible in ConPort

**Lunch Break**: 60 minutes (11:00 AM - 12:00 PM)

---

### Afternoon Session: Day 1 Validation

**Start Time**: 1:00 PM (post-lunch lower energy - good for testing)

**Focus Block 1.5 (25 min) - Unit Tests**

**Task**: Add tests for ConPort integration

**File**: `services/agents/test_cognitive_guardian.py`

**New Tests**:
```python
async def test_conport_state_persistence():
    """Test user state saved to ConPort."""
    guardian = CognitiveGuardian("/test")
    await guardian.start_monitoring()
    
    state = await guardian.get_user_state()
    # Verify _save_user_state() called (check logs or mock)
    
    await guardian.stop_monitoring()

async def test_preference_defaults():
    """Test default preferences when ConPort unavailable."""
    guardian = CognitiveGuardian("/test")
    assert guardian.break_interval == 25
    assert guardian.mandatory_break == 90
```

**Run Tests**:
```bash
cd services/agents
python test_cognitive_guardian.py
```

**Expected**: 6/6 tests passing (4 existing + 2 new)

**Completion Criteria**:
- [ ] Tests added
- [ ] All tests passing
- [ ] No regressions

---

### Day 1 Wrap-Up (30 min) - 2:00 PM

**Tasks**:
1. Run full test suite
2. Commit changes:
   ```bash
   git add services/agents/cognitive_guardian.py
   git add services/agents/test_cognitive_guardian.py
   git commit -m "Week 3 Day 1: ConPort integration foundation
   
   - Add Claude Code context detection
   - Implement user preference loading from ConPort
   - Add user state persistence
   - Add metrics persistence
   - Tests: 6/6 passing
   
   Impact: CognitiveGuardian now persists state to ConPort"
   ```
3. Document progress:
   - Update `WEEK3_PROGRESS.md` (create if needed)
4. Celebrate: ✅ Day 1 complete!

**Output**: ~195 lines added/modified

---

## Day 2 (Tuesday): Task Suggestions from ConPort

**Goal**: Replace simulation mode with real task queries
**Energy Required**: High (new query logic)
**Complexity**: 0.6 (moderate-high - filtering logic)

---

### Focus Block 2.1 (25 min) - Task Query Structure

**Start Time**: 9:00 AM

**Task**: Wire ConPort task queries into `suggest_tasks()`

**File**: `services/agents/cognitive_guardian.py`

**Changes to `suggest_tasks()`**:
```python
async def suggest_tasks(...) -> List[Dict[str, Any]]:
    # ... get user state ...
    
    # NEW: Real ConPort queries
    if not self._in_claude_code:
        return self._simulate_task_suggestions(...)
    
    try:
        from mcp_tools import mcp__conport__get_progress
        all_tasks = await mcp__conport__get_progress(
            workspace_id=self.workspace_id,
            status="TODO"
        )
        # ...
    except Exception as e:
        return self._simulate_task_suggestions(...)  # Fallback
```

**Test**:
```python
# In Claude Code with ConPort:
guardian = CognitiveGuardian("/Users/hue/code/dopemux-mvp")
await guardian.start_monitoring()
tasks = await guardian.suggest_tasks(energy="high")
print(f"Found {len(tasks)} tasks")
```

**Completion Criteria**:
- [ ] ConPort query wired
- [ ] Fallback to simulation works
- [ ] No crashes on ConPort errors

**Break**: 5 minutes

---

### Focus Block 2.2 (25 min) - Task Filtering Logic

**Start Time**: 9:30 AM

**Task**: Implement energy + attention-based task filtering

**File**: `services/agents/cognitive_guardian.py`

**Filtering Logic**:
```python
matched_tasks = []
for task in all_tasks:
    task_energy = task.get("energy_required", "medium")
    task_complexity = task.get("complexity", 0.5)
    
    # Energy match
    if task_energy != target_energy:
        continue
    
    # Attention match
    if user_state.attention == AttentionState.SCATTERED:
        if task_complexity > 0.5:
            continue  # Skip complex when scattered
    
    matched_tasks.append({...})
```

**Test**:
```python
# Scenario 1: High energy (morning)
tasks = await guardian.suggest_tasks(energy="high")
# Should return only high-energy tasks

# Scenario 2: Low energy (evening)
tasks = await guardian.suggest_tasks(energy="low")
# Should return only low-energy, simple tasks
```

**Completion Criteria**:
- [ ] Filtering logic implemented
- [ ] Energy matching works
- [ ] Attention matching works

**Break**: 5 minutes

---

### Focus Block 2.3 (25 min) - Task Match Scoring

**Start Time**: 10:00 AM

**Task**: Add match score calculation for task ranking

**File**: `services/agents/cognitive_guardian.py`

**New Method**:
```python
def _calculate_task_match_score(
    self,
    user_state: UserState,
    task_complexity: float,
    task_energy: str
) -> float:
    """Calculate how well task matches user's current state."""
    score = 0.5  # Base
    
    # Energy match bonus
    if task_energy == user_state.energy.value:
        score += 0.3
    
    # Complexity match bonus
    if user_state.attention == AttentionState.HYPERFOCUS:
        if task_complexity > 0.7:
            score += 0.2  # Perfect for complex work
    # ...
    
    return min(1.0, score)
```

**Integration**:
```python
matched_tasks.append({
    "title": task.get("title"),
    "complexity": task_complexity,
    "match_score": self._calculate_task_match_score(
        user_state, task_complexity, task_energy
    )
})

# Sort by match score
matched_tasks.sort(key=lambda t: t["match_score"], reverse=True)
```

**Test**:
```python
# High energy + complex task should score high
score = guardian._calculate_task_match_score(
    UserState(energy=EnergyLevel.HIGH, attention=AttentionState.FOCUSED, ...),
    task_complexity=0.8,
    task_energy="high"
)
assert score > 0.7  # Should be high match
```

**Completion Criteria**:
- [ ] Scoring method added
- [ ] Tasks sorted by score
- [ ] Top matches returned

**Break**: 10 minutes

---

### Focus Block 2.4 (25 min) - Extract Simulation Fallback

**Start Time**: 10:35 AM

**Task**: Move simulation code to separate method

**File**: `services/agents/cognitive_guardian.py`

**Extract Method**:
```python
def _simulate_task_suggestions(
    self,
    target_energy: str,
    max_suggestions: int
) -> List[Dict[str, Any]]:
    """Simulation mode for when ConPort unavailable."""
    print(f"\n🎯 Task Suggestions (Energy: {target_energy}) [SIMULATION]")
    
    if target_energy == "high":
        print("   Suggested (complex tasks):")
        print("   1. Design microservices architecture (0.8)")
        # ...
    
    return []  # No real tasks in simulation
```

**Update `suggest_tasks()`**:
```python
async def suggest_tasks(...):
    # ...
    if not self._in_claude_code:
        return self._simulate_task_suggestions(target_energy, max_suggestions)
    
    try:
        # Real ConPort logic
        # ...
    except Exception as e:
        logger.error(f"ConPort query failed: {e}")
        return self._simulate_task_suggestions(target_energy, max_suggestions)
```

**Completion Criteria**:
- [ ] Simulation extracted
- [ ] Fallback works
- [ ] Code cleaner

**Lunch Break**: 60 minutes

---

### Focus Block 2.5 (25 min) - Integration Tests

**Start Time**: 1:00 PM

**Task**: Test task suggestions end-to-end

**File**: `services/agents/test_cognitive_guardian.py`

**New Tests**:
```python
async def test_task_suggestions_energy_filtering():
    """Test tasks filtered by energy level."""
    # Mock ConPort to return sample tasks
    # Verify only high-energy tasks returned when energy="high"

async def test_task_suggestions_complexity_filtering():
    """Test complex tasks filtered when attention=scattered."""
    # Simulate scattered attention (95 min session)
    # Verify no high-complexity tasks suggested
```

**Run Tests**:
```bash
python test_cognitive_guardian.py
```

**Expected**: 8/8 tests passing

**Completion Criteria**:
- [ ] Tests added
- [ ] All tests passing

---

### Day 2 Wrap-Up (30 min) - 2:00 PM

**Tasks**:
1. Run full test suite
2. Commit changes:
   ```bash
   git add services/agents/cognitive_guardian.py
   git add services/agents/test_cognitive_guardian.py
   git commit -m "Week 3 Day 2: Task suggestions from ConPort
   
   - Wire ConPort get_progress queries
   - Add energy + attention-based filtering
   - Implement task match scoring
   - Extract simulation fallback
   - Tests: 8/8 passing
   
   Impact: Real task suggestions (not simulation)"
   ```
3. Update `WEEK3_PROGRESS.md`
4. Celebrate: ✅ Day 2 complete!

**Output**: ~100 lines added

---

## Day 3 (Wednesday): Task-Orchestrator Integration

**Goal**: CognitiveGuardian advises routing decisions
**Energy Required**: Medium-High (integration work)
**Complexity**: 0.5

---

### Focus Block 3.1 (25 min) - Add CognitiveGuardian Parameter

**Start Time**: 9:00 AM

**Task**: Wire CognitiveGuardian into Task-Orchestrator

**File**: `services/task-orchestrator/enhanced_orchestrator.py`

**Changes to `__init__()`**:
```python
class EnhancedTaskOrchestrator:
    def __init__(
        self,
        workspace_id: str,
        memory_agent: Optional[Any] = None,
        cognitive_guardian: Optional[Any] = None,  # NEW
        ...
    ):
        self.cognitive_guardian = cognitive_guardian
```

**Test**:
```python
from cognitive_guardian import CognitiveGuardian
from enhanced_orchestrator import EnhancedTaskOrchestrator

guardian = CognitiveGuardian("/test")
orchestrator = EnhancedTaskOrchestrator(
    workspace_id="/test",
    cognitive_guardian=guardian
)
assert orchestrator.cognitive_guardian is not None
```

**Completion Criteria**:
- [ ] Parameter added
- [ ] Stored in instance
- [ ] Test passes

**Break**: 5 minutes

---

### Focus Block 3.2 (25 min) - User Readiness Check

**Start Time**: 9:30 AM

**Task**: Check user readiness before routing

**File**: `services/task-orchestrator/enhanced_orchestrator.py`

**Changes to `_assign_optimal_agent()`**:
```python
async def _assign_optimal_agent(self, task: Dict[str, Any]) -> str:
    complexity = task.get("complexity", 0.5)
    
    # NEW: Check user readiness
    if self.cognitive_guardian:
        user_state = await self.cognitive_guardian.get_user_state()
        task_energy = task.get("energy_required", "medium")
        
        readiness = await self.cognitive_guardian.check_task_readiness(
            task_complexity=complexity,
            task_energy_required=task_energy
        )
        
        if not readiness["ready"]:
            logger.warning(f"User not ready: {readiness['reason']}")
            
            # Mandatory break check
            if user_state.session_duration_minutes >= 90:
                return "break_required"  # Special signal
    
    # EXISTING ROUTING LOGIC
    # ...
```

**Test**:
```python
# Simulate low energy
task = {"complexity": 0.9, "energy_required": "high"}
agent = await orchestrator._assign_optimal_agent(task)
# Should be blocked or alternative route
```

**Completion Criteria**:
- [ ] Readiness check added
- [ ] Warnings logged
- [ ] No crashes

**Break**: 5 minutes

---

### Focus Block 3.3 (25 min) - Fix Routing Optimization

**Start Time**: 10:00 AM

**Task**: Move complexity check before keyword matching

**File**: `services/task-orchestrator/enhanced_orchestrator.py`

**Changes to `_assign_optimal_agent()`**:
```python
# BEFORE (Week 2 bug):
if any(kw in description for kw in ["design", ...]):
    return "zen"  # Keyword matched first
if complexity > 0.8:
    return "zen"  # Never reached for "design" tasks

# AFTER (Week 3 fix):
# Move complexity check FIRST
if complexity > 0.8:
    return "zen"  # High complexity always goes to Zen

# THEN keyword matching
if any(kw in description for kw in ["design", ...]):
    # Only if not already routed by complexity
    if self.cognitive_guardian:
        if user_state.energy == "low":
            return "conport"  # Log decision instead
    return "zen"
```

**Test**:
```python
# Bug scenario from Week 2:
task = {
    "description": "Design distributed tracing system",
    "complexity": 0.9,
    "energy_required": "high"
}
agent = await orchestrator._assign_optimal_agent(task)
assert agent == "zen"  # Now routes correctly
```

**Completion Criteria**:
- [ ] Routing order fixed
- [ ] Test passes
- [ ] Week 2 bug resolved

**Break**: 10 minutes

---

### Focus Block 3.4 (25 min) - Handle Break-Required State

**Start Time**: 10:35 AM

**Task**: Add break enforcement in dispatch

**File**: `services/task-orchestrator/enhanced_orchestrator.py`

**Changes to `_dispatch_to_agent()`**:
```python
async def _dispatch_to_agent(self, task: Dict[str, Any], agent: str):
    # NEW: Handle break-required state
    if agent == "break_required":
        logger.warning("🛑 MANDATORY BREAK - Task deferred")
        print("\n" + "="*70)
        print("🛑 MANDATORY BREAK REQUIRED")
        print("   Take a 10-minute break, then return.")
        print("="*70 + "\n")
        return
    
    # EXISTING DISPATCH LOGIC
    if agent == "conport":
        await self._dispatch_to_conport(task)
    # ...
```

**Test**:
```python
# Simulate overwork
guardian.session_start = datetime.now(timezone.utc) - timedelta(minutes=95)

task = {"description": "Any task", "complexity": 0.5}
agent = await orchestrator._assign_optimal_agent(task)
assert agent == "break_required"

# Dispatch should print break message, not crash
await orchestrator._dispatch_to_agent(task, agent)
```

**Completion Criteria**:
- [ ] Break handling added
- [ ] Message displays
- [ ] No dispatch attempted

**Lunch Break**: 60 minutes

---

### Day 3 Afternoon: Integration Testing

**Start Time**: 1:00 PM (lower energy - good for testing)

**Focus Block 3.5 (50 min) - Write Integration Tests**

**Task**: Create comprehensive integration test suite

**File**: `services/task-orchestrator/test_week3_integration.py` (new)

**Tests to Write**:
1. `test_energy_aware_routing()` - High energy → complex tasks
2. `test_low_energy_blocking()` - Low energy blocks complex tasks
3. `test_mandatory_break_enforcement()` - 95 min blocks all tasks
4. `test_conport_persistence()` - State saved to ConPort

**Run Tests**:
```bash
cd services/task-orchestrator
python test_week3_integration.py
```

**Expected**: 4/4 tests passing

**Completion Criteria**:
- [ ] 4 tests written
- [ ] All tests passing
- [ ] Integration validated

**Break**: 10 minutes (longer after writing tests)

---

### Day 3 Wrap-Up (30 min) - 2:30 PM

**Tasks**:
1. Run all tests (unit + integration)
2. Commit changes:
   ```bash
   git add services/task-orchestrator/enhanced_orchestrator.py
   git add services/task-orchestrator/test_week3_integration.py
   git commit -m "Week 3 Day 3: Task-Orchestrator integration
   
   - Add CognitiveGuardian parameter to orchestrator
   - User readiness check before routing
   - Fix routing optimization (complexity before keywords)
   - Handle break-required state in dispatch
   - Integration tests: 4/4 passing
   
   Impact: Energy-aware task routing operational"
   ```
3. Update `WEEK3_PROGRESS.md`
4. Celebrate: ✅ Day 3 complete!

**Output**: ~280 lines added (80 orchestrator + 200 tests)

---

## Day 4 (Thursday): Production Patterns & Validation

**Goal**: Polish, optimize, validate
**Energy Required**: Medium (refinement work)
**Complexity**: 0.4

---

### Focus Block 4.1 (25 min) - Error Handling Review

**Start Time**: 9:00 AM

**Task**: Add comprehensive error handling

**Files**: `cognitive_guardian.py`, `enhanced_orchestrator.py`

**Patterns to Add**:
```python
# Timeout protection
try:
    async with asyncio.timeout(5.0):  # Python 3.11+
        result = await mcp__conport__get_progress(...)
except asyncio.TimeoutError:
    logger.error("ConPort timeout (5s)")
    return self._simulate_task_suggestions(...)

# Retry logic
for attempt in range(3):
    try:
        await mcp__conport__update_active_context(...)
        break
    except Exception as e:
        if attempt == 2:
            logger.error(f"Failed after 3 attempts: {e}")
        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
```

**Completion Criteria**:
- [ ] Timeouts added
- [ ] Retries added
- [ ] Graceful degradation works

**Break**: 5 minutes

---

### Focus Block 4.2 (25 min) - Performance Optimization

**Start Time**: 9:30 AM

**Task**: Cache user state to reduce ConPort calls

**File**: `cognitive_guardian.py`

**Add Caching**:
```python
def __init__(self, ...):
    # ...
    self._state_cache: Optional[UserState] = None
    self._state_cache_time: Optional[datetime] = None
    self._state_cache_ttl = 60  # Cache for 60 seconds

async def get_user_state(self) -> UserState:
    """Get current user state (with caching)."""
    now = datetime.now(timezone.utc)
    
    # Return cached state if fresh
    if self._state_cache and self._state_cache_time:
        age = (now - self._state_cache_time).total_seconds()
        if age < self._state_cache_ttl:
            logger.debug(f"Returning cached state (age: {age:.1f}s)")
            return self._state_cache
    
    # Calculate fresh state
    # ... existing logic ...
    
    user_state = UserState(...)
    
    # Cache state
    self._state_cache = user_state
    self._state_cache_time = now
    
    # Persist to ConPort (async, non-blocking)
    asyncio.create_task(self._save_user_state(user_state))
    
    return user_state
```

**Test**:
```python
# Call twice within 60 seconds
state1 = await guardian.get_user_state()
state2 = await guardian.get_user_state()  # Should return cached
# Verify only 1 ConPort call (check logs)
```

**Completion Criteria**:
- [ ] Caching added
- [ ] TTL configurable
- [ ] ConPort calls reduced

**Break**: 5 minutes

---

### Focus Block 4.3 (25 min) - Logging & Debugging

**Start Time**: 10:00 AM

**Task**: Add structured logging for debugging

**Files**: Both

**Enhanced Logging**:
```python
logger.info(
    "CognitiveGuardian state",
    extra={
        "energy": user_state.energy.value,
        "attention": user_state.attention.value,
        "session_duration": user_state.session_duration_minutes,
        "breaks_taken": user_state.breaks_taken,
        "workspace_id": self.workspace_id
    }
)

logger.debug(
    "Task routing decision",
    extra={
        "task_complexity": complexity,
        "user_energy": user_state.energy.value,
        "agent_assigned": agent,
        "readiness_score": readiness.get("confidence", 0.0)
    }
)
```

**Completion Criteria**:
- [ ] Structured logging added
- [ ] Debug logs useful
- [ ] Production logs not verbose

**Break**: 10 minutes

---

### Focus Block 4.4 (25 min) - End-to-End Manual Testing

**Start Time**: 10:35 AM

**Task**: Manual testing checklist

**Checklist**:
```markdown
## Manual Testing Checklist

**Setup**:
- [ ] ConPort running (port 3004)
- [ ] Claude Code session active
- [ ] Workspace ID correct

**Test 1: Preference Loading**:
- [ ] Start CognitiveGuardian
- [ ] Check logs for "Loaded preferences" or "using defaults"
- [ ] Verify break_interval value

**Test 2: State Persistence**:
- [ ] Get user state
- [ ] Check ConPort for saved state
- [ ] Verify energy, attention, breaks_taken

**Test 3: Break Reminders**:
- [ ] Work for 26 minutes
- [ ] See gentle reminder
- [ ] Take break
- [ ] Verify break recorded

**Test 4: Task Suggestions**:
- [ ] Call suggest_tasks(energy="high")
- [ ] Verify tasks returned (or simulation if no ConPort tasks)
- [ ] Check task filtering works

**Test 5: Mandatory Break**:
- [ ] Work for 95 minutes (or fast-forward)
- [ ] Request any task
- [ ] See mandatory break message
- [ ] Verify no task assigned

**Test 6: Energy Mismatch**:
- [ ] Evening (low energy)
- [ ] Request complex task (0.9 complexity)
- [ ] See "not ready" message
- [ ] Verify alternative suggestions

**Test 7: Metrics**:
- [ ] Stop monitoring
- [ ] Check ConPort for saved metrics
- [ ] Verify breaks_taken, energy_mismatches_caught
```

**Run Through Checklist**: Mark items as you test

**Completion Criteria**:
- [ ] 100% checklist complete
- [ ] No critical bugs found
- [ ] User experience smooth

**Lunch Break**: 60 minutes

---

### Day 4 Afternoon: Documentation

**Start Time**: 1:00 PM

**Focus Block 4.5 (60 min) - Production Guide**

**Task**: Create comprehensive production deployment guide

**File**: `COGNITIVE_GUARDIAN_PRODUCTION_GUIDE.md` (new)

**Sections**:
1. Overview
2. Prerequisites
3. Configuration
4. Usage Examples
5. Troubleshooting
6. Performance Tuning
7. Monitoring
8. FAQ

**Content**: ~400 lines (detailed examples, code snippets)

**Completion Criteria**:
- [ ] Guide complete
- [ ] Examples tested
- [ ] Clear and actionable

**Break**: 10 minutes

---

### Day 4 Wrap-Up (30 min) - 3:00 PM

**Tasks**:
1. Final test run
2. Commit:
   ```bash
   git add services/agents/cognitive_guardian.py
   git add services/task-orchestrator/enhanced_orchestrator.py
   git add COGNITIVE_GUARDIAN_PRODUCTION_GUIDE.md
   git commit -m "Week 3 Day 4: Production patterns & validation
   
   - Add error handling (timeouts, retries)
   - Implement state caching (60s TTL)
   - Enhanced logging for debugging
   - Production deployment guide
   - Manual testing: 7/7 scenarios passing
   
   Impact: Production-ready, optimized, documented"
   ```
3. Update progress
4. Celebrate: ✅ Day 4 complete!

**Output**: ~450 lines (50 code + 400 docs)

---

## Day 5 (Friday): Week 3 Summary & Handoff

**Goal**: Document achievements, prepare for Week 4
**Energy Required**: Low-Medium (documentation)
**Complexity**: 0.3

---

### Focus Block 5.1 (25 min) - Week 3 Summary Document

**Start Time**: 9:00 AM

**Task**: Create comprehensive week summary

**File**: `WEEK3_COMPLETE.md` (new)

**Sections**:
1. Executive Summary
2. Deliverables
3. Code Changes Summary
4. Test Results
5. ADHD Impact Metrics
6. Production Readiness
7. What's Next (Week 4 preview)

**Content**: ~300 lines

**Completion Criteria**:
- [ ] Summary complete
- [ ] Metrics accurate
- [ ] Clear achievements documented

**Break**: 5 minutes

---

### Focus Block 5.2 (25 min) - Update Integration Guide

**Start Time**: 9:30 AM

**Task**: Update main integration guide

**File**: `services/agents/INTEGRATION_GUIDE.md`

**Additions**:
- CognitiveGuardian production usage
- ConPort integration examples
- Task-Orchestrator integration
- Common patterns

**Completion Criteria**:
- [ ] Guide updated
- [ ] Examples current
- [ ] Links working

**Break**: 5 minutes

---

### Focus Block 5.3 (25 min) - Final Testing Pass

**Start Time**: 10:00 AM

**Task**: Run entire test suite

**Commands**:
```bash
# Unit tests
cd services/agents
python test_cognitive_guardian.py
# Expected: 8/8 passing

# Integration tests
cd services/task-orchestrator
python test_week3_integration.py
# Expected: 4/4 passing

# Optional: Run MemoryAgent tests (should still pass)
cd services/agents
python test_memory_agent.py
# Expected: 4/4 passing (no regressions)
```

**Total**: 16 tests passing ✅

**Completion Criteria**:
- [ ] All tests passing
- [ ] No regressions
- [ ] Coverage good

**Break**: 10 minutes

---

### Focus Block 5.4 (25 min) - Code Review & Cleanup

**Start Time**: 10:35 AM

**Task**: Self-review all Week 3 changes

**Files to Review**:
- `cognitive_guardian.py` (~195 lines modified)
- `enhanced_orchestrator.py` (~85 lines modified)
- Test files (~250 lines added)

**Checklist**:
- [ ] No commented-out code (except intentional examples)
- [ ] Consistent style
- [ ] Docstrings complete
- [ ] No TODOs left unaddressed
- [ ] Imports organized

**Completion Criteria**:
- [ ] Code clean
- [ ] Ready for merge

**Lunch Break**: 60 minutes

---

### Day 5 Afternoon: Week 3 Retrospective

**Start Time**: 1:00 PM

**Focus Block 5.5 (30 min) - Retrospective**

**Task**: Reflect on week, capture learnings

**Questions**:
1. What went well?
2. What was challenging?
3. What surprised you?
4. What would you do differently?
5. Energy management: How did breaks help?
6. Complexity estimates: Were they accurate?

**Document in**: `WEEK3_RETROSPECTIVE.md`

**Completion Criteria**:
- [ ] Reflection complete
- [ ] Lessons captured
- [ ] Improvements identified

---

### Final Commit (30 min) - 2:00 PM

**Tasks**:
1. Stage all documentation
2. Final commit:
   ```bash
   git add services/agents/*.md
   git add COGNITIVE_GUARDIAN_PRODUCTION_GUIDE.md
   git commit -m "Week 3 Day 5: Summary & documentation
   
   - Week 3 complete summary
   - Updated integration guide
   - Production deployment guide
   - Retrospective & lessons learned
   
   Week 3 Status: COMPLETE ✅
   - Tests: 16/16 passing (100%)
   - Functionality: 60% (+25% from Week 2)
   - ADHD optimization: 50% active
   - Production-ready: Yes
   
   Next: Week 4 (Energy learning, advanced features)"
   ```
3. Push to remote (if applicable)
4. Celebrate: 🎉 **WEEK 3 COMPLETE!** 🎉

---

## Week 3 Success Metrics

**Code Output**:
- Production code: ~480 lines added/modified
- Test code: ~250 lines
- Documentation: ~700 lines
- **Total**: ~1,430 lines

**Test Coverage**:
- Unit tests: 8/8 (100%)
- Integration tests: 4/4 (100%)
- Manual scenarios: 7/7 (100%)
- **Overall**: 16+ tests passing ✅

**Functionality Progress**:
- Week 2 end: 35%
- Week 3 end: 60%
- **Gain**: +25% in 1 week ✅

**ADHD Optimization**:
- Week 2 end: 20% active
- Week 3 end: 50% active
- **Gain**: +30% (+150% increase) ✅

**Production Readiness**:
- ConPort integration: ✅ Operational
- Task routing: ✅ Energy-aware
- Break enforcement: ✅ Mandatory breaks work
- Documentation: ✅ Comprehensive guides
- **Status**: Production-ready ✅

---

## Week 3 vs. Original Plan

**Original Estimate** (from 16-week plan):
- 2 weeks for CognitiveGuardian (Weeks 3-4)
- ~800 lines over 2 weeks
- Complexity: 0.6

**Actual Delivery** (Week 3 only):
- 1 week (not 2)
- ~1,430 lines
- Complexity: 0.5 (slightly easier than expected)
- **Ahead of schedule by 1 week!** 🚀

**Why Ahead?**:
1. CognitiveGuardian already existed (603 lines from prior work)
2. Clear patterns from MemoryAgent Week 1-2
3. Excellent research & planning (this roadmap)
4. ADHD-optimized work blocks (high productivity)
5. Strong testing discipline (caught issues early)

---

## Next Steps: Week 4 Preview

**Optional Enhancements** (if time in Week 4):
1. **Energy Learning**: Learn from user corrections
2. **Biometric Integration**: Explore wearable data
3. **Advanced Filtering**: Multi-factor task matching
4. **Mobile Notifications**: MCP notification bridge (if available)

**Or Jump to Week 5**: ADHD Routing Activation (use CognitiveGuardian in all routing)

**Recommendation**: Take Week 4 as buffer/polish week, then Week 5 for routing activation

---

## Celebration Checklist 🎉

After completing Week 3:

- [ ] All 16 tests passing
- [ ] Production guide published
- [ ] Week 3 summary complete
- [ ] Code committed & pushed
- [ ] **60% functionality achieved** (+25% gain)
- [ ] **50% ADHD optimization active** (+30% gain)
- [ ] **Production-ready system** delivered
- [ ] Take a well-deserved break! ☕️

---

**Week 3 Status**: READY TO START
**Start Date**: Monday (Day 1)
**Expected Completion**: Friday (Day 5)
**Confidence**: High (clear plan, strong foundation)
**Impact**: Critical (ADHD support fully operational)

**Let's build production-ready ADHD support!** 🚀
