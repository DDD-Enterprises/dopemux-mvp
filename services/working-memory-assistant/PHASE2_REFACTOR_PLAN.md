# Phase 2 Full Refactor - Remaining Work

## Completed ✅
1. Created `reflection/reflection.py` with `ReflectionGenerator` class
2. Created `trajectory/manager.py` with `TrajectoryManager` class
3. Added Phase 2 methods to `chronicle/store.py`:
   - `insert_reflection_card()`
   - `get_reflection_cards()`
   - `upsert_trajectory_state()`
   - `get_trajectory_state()`
   - `get_work_log_window()`

## Remaining Work

### 1. EventBus Consumer with Pulse Emission
**File**: `services/working-memory-assistant/eventbus_consumer.py`

**Responsibilities**:
- Connect to Redis Streams (`activity.events.v1`)
- Consume events and promote to work_log_entries
- Update trajectory on each promoted entry
- Emit `memory.pulse` events (30-60min cadence + session end)
- Emit `reflection.created` events when reflections are generated

**Event Schemas** (per `docs/spec/dope-memory/v1/04_event_taxonomy.md`):

```python
# memory.pulse event
{
  "id": "uuid",
  "ts": "2026-02-03T00:00:00Z",
  "workspace_id": "...",
  "instance_id": "A",
  "session_id": "...",  # optional
  "type": "memory.pulse",
  "source": "dope-memory",
  "data": {
    "trajectory": "Active in implementation",
    "constraints": [  # decisions + blockers
      {"id": "...", "summary": "..."}
    ],
    "suggested_next": ["Resolve blocker X", "..."],
    "source_entry_ids": ["...", "..."]
  }
}

# reflection.created event
{
  "id": "uuid",
  "ts": "2026-02-03T00:00:00Z",
  "workspace_id": "...",
  "instance_id": "A",
  "session_id": "...",
  "type": "reflection.created",
  "source": "dope-memory",
  "data": {
    "reflection_id": "...",
    "window_start": "...",
    "window_end": "...",
    "trajectory": "Active in debugging"
  }
}
```

**Pulse Cadence Logic**:
- Track `last_pulse_at` per (workspace_id, instance_id, session_id)
- Emit pulse every 30-60 minutes
- Force pulse on session end events
- Use trajectory state + recent reflections for pulse payload

### 2. Refactor dope_memory_main.py

**Changes needed**:
1. **Remove inline Phase 2 code** (lines 420-650 approx)
   - Remove `memory_generate_reflection()` method from `DopeMemoryMCPServer`
   - Remove `memory_reflections()` method
   - Remove `memory_trajectory()` method
   - Remove `_update_trajectory_state()` method

2. **Add imports**:
```python
from reflection.reflection import ReflectionGenerator
from trajectory.manager import TrajectoryManager
```

3. **Initialize in `DopeMemoryMCPServer.__init__()`**:
```python
self.reflection_gen = None  # Lazy init per workspace
self.trajectory_mgr = None  # Lazy init per workspace
```

4. **Update endpoints** to use new modules:
```python
@app.post("/tools/memory_generate_reflection")
async def memory_generate_reflection(request: MemoryGenerateReflectionRequest):
    store = mcp_server._get_store(request.workspace_id)
    gen = ReflectionGenerator(store)
    
    # Generate reflection
    card = gen.generate_reflection(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        window_hours=request.window_hours,
    )
    
    if card["reflection_id"]:
        # Persist
        store.insert_reflection_card(card)
        
        # Emit reflection.created event (if eventbus enabled)
        if ENABLE_EVENTBUS:
            await emit_reflection_created(card)
    
    return card
```

Similar refactoring for `/tools/memory_reflections` and `/tools/memory_trajectory`.

### 3. Add Lifecycle Integration

**In `dope_memory_main.py` lifespan**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_server, eventbus_consumer_task
    
    # Initialize MCP server
    mcp_server = DopeMemoryMCPServer(...)
    
    # Start EventBus consumer (if enabled)
    if ENABLE_EVENTBUS and REDIS_URL:
        from eventbus_consumer import EventBusConsumer
        consumer = EventBusConsumer(
            redis_url=REDIS_URL,
            chronicle_stores=mcp_server._stores,
        )
        eventbus_consumer_task = asyncio.create_task(consumer.run())
    
    yield
    
    # Cleanup
    if eventbus_consumer_task:
        eventbus_consumer_task.cancel()
```

### 4. Reorganize Tests

**Rename files**:
- `tests/test_phase2_reflection_trajectory.py` →
  - `tests/test_reflection.py` (reflection tests)
  - `tests/test_trajectory.py` (trajectory tests)

**Add new test file**:
- `tests/test_pulse_emission.py` - Test pulse gating logic
  - Verify pulse not emitted more frequently than 30min
  - Verify session end forces pulse
  - Verify pulse payload structure matches schema

### 5. Update Documentation

**Files to update**:
- `PHASE2_COMPLETE.md` - Rewrite to reflect proper architecture
- `PHASE2_AUDIT.md` - Mark all items as complete
- Add `PHASE2_ARCHITECTURE.md` - Document module structure

## Testing Strategy

After refactoring:
1. Run all existing tests: `pytest tests/ --no-cov`
2. Verify imports: `python3 -c "from reflection.reflection import ReflectionGenerator; from trajectory.manager import TrajectoryManager"`
3. Test reflection generation manually
4. Test trajectory updates manually
5. Test pulse emission (if eventbus enabled)

## Rollback Plan

If refactoring breaks:
1. Keep backup of current `dope_memory_main.py`
2. Verify new modules work standalone first
3. Integrate one endpoint at a time
4. Run tests after each integration step

## Estimated Effort

- EventBus consumer: ~200-300 lines
- Refactor dope_memory_main.py: ~100 line deletions, ~50 line additions
- Test reorganization: ~50 lines moved
- Documentation updates: ~30 minutes

Total: ~2-3 hours careful work

## Questions Before Proceeding

1. **EventBus Option**: Prefer full consumer (Option A) or simple background task (Option B)?
2. **DopeContext indexing**: Include in Phase 2 or defer to Phase 3?
3. **Session end detection**: How to detect session end events? (need event type or timeout heuristic?)

---

**Status**: Modules created, store methods added. Ready to proceed with eventbus + integration.
