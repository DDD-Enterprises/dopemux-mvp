# Production Readiness - Day 1 Execution Guide

**Date**: 2025-11-14
**Duration**: 8 hours
**Goal**: Complete 2 services + start serena

---

## 🎯 Today's Targets

- ✅ orchestrator: 90% → 100% (1.5h)
- ✅ activity-capture: 85% → 100% (1.5h)
- 🔄 serena: 70% → 90%+ (4-5h)
- 📊 **15+ new tests passing**

---

## 🚀 Quick Start

```bash
# 1. Check status
./scripts/production_tracker.sh

# 2. View Day 1 guide
./scripts/day1_quick_start.sh

# 3. Run tests
./run_all_multi_workspace_tests.sh
```

---

## 📝 Task 1: Orchestrator (90min)

### Files to Modify
- `services/orchestrator/src/router.py`

### Changes Needed

**Step 1**: Add import (top of file)
```python
from workspace_support import add_workspace_context
```

**Step 2**: Modify `route()` method
```python
async def route(self, request: dict):
    # Add workspace context
    request = add_workspace_context(request)
    
    # Continue existing logic...
```

### Verify
```bash
cd services/orchestrator
pytest tests/test_workspace_support.py -v
```

**Expected**: 8/8 tests passing ✓

---

## 📝 Task 2: Activity-Capture (90min)

### Files to Modify
- `services/activity-capture/activity_tracker.py`

### Changes Needed

**Step 1**: Add import
```python
from workspace_support import enrich_event_with_workspace
```

**Step 2**: Modify event tracking
```python
def track_event(self, event_type: str, data: dict):
    event = self._create_event(event_type, data)
    
    # ADD THIS LINE
    event = enrich_event_with_workspace(event)
    
    self._emit(event)
```

### Verify
```bash
cd services/activity-capture
pytest tests/ -k workspace -v
```

**Expected**: New tests created + passing ✓

---

## 📝 Task 3: Serena MCP Integration (4-5h)

### Files to Modify
- `services/serena/v2/mcp_server.py` (main file, 4800+ lines)

### Strategy
Update 10 MCP tool functions to accept multi-workspace params.

### Pattern (apply to each function)

**Before**:
```python
@mcp.tool()
async def find_symbol_tool(self, query: str, ...) -> str:
    """Find symbols in the workspace."""
    return await self.find_symbol(query, ...)
```

**After**:
```python
@mcp.tool()
async def find_symbol_tool(
    self, 
    query: str,
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    ...
) -> str:
    """Find symbols across workspaces."""
    
    # Multi-workspace mode
    if workspace_paths or workspace_path:
        from multi_workspace_wrapper import SerenaMultiWorkspace
        wrapper = SerenaMultiWorkspace()
        return await wrapper.find_symbol_multi(
            query,
            workspace_path=workspace_path,
            workspace_paths=workspace_paths,
            ...
        )
    
    # Single workspace (backward compatible)
    return await self.find_symbol(query, ...)
```

### Functions to Update

| # | Function | Line | Priority |
|---|----------|------|----------|
| 1 | `find_symbol_tool` | ~1499 | HIGH |
| 2 | `get_context_tool` | ~1814 | HIGH |
| 3 | `find_references_tool` | ~1913 | HIGH |
| 4 | `analyze_complexity_tool` | ~2126 | MED |
| 5 | `get_reading_order_tool` | ~2411 | MED |
| 6 | `find_relationships_tool` | ~2493 | MED |
| 7 | `get_navigation_patterns_tool` | ~2586 | LOW |
| 8 | `find_similar_code_tool` | ~4493 | LOW |
| 9 | `find_test_file_tool` | ~4654 | LOW |
| 10 | `get_unified_complexity_tool` | ~4753 | LOW |

### Incremental Approach
1. **First 3** (HIGH): Core symbol search - 2h
2. **Next 3** (MED): Analysis tools - 1.5h
3. **Last 4** (LOW): Optional tools - 1h

### Verify After Each Batch
```bash
cd services/serena
pytest tests/test_multi_workspace.py -v
```

**Expected**: Wrapper tests continue passing (9/9) ✓

---

## 🧪 End-of-Day Verification

```bash
# 1. Run all multi-workspace tests
./run_all_multi_workspace_tests.sh

# 2. Check status
./scripts/production_tracker.sh 1

# 3. Count completed
echo "Services complete: X/10"
echo "Tests passing: X/150"
```

### Success Criteria
- [ ] orchestrator: 100% complete
- [ ] activity-capture: 100% complete
- [ ] serena: 6-10 tools updated (60-100%)
- [ ] 15+ new tests passing
- [ ] No regressions in existing tests

---

## 🚨 If Things Go Wrong

### Orchestrator Issues
- **Fallback**: Use wrapper as external utility, don't integrate
- **Time**: Skip TUI changes, focus on router only

### Activity-Capture Issues
- **Fallback**: Add workspace field manually (don't use enrichment)
- **Time**: Skip event_subscriber, focus on tracker only

### Serena Issues
- **Blocker**: Wrapper not working
  - **Solution**: Test wrapper independently first
- **Behind schedule**: 
  - **Day 1**: Complete 3 HIGH priority tools only
  - **Day 2**: Finish remaining 7 tools

---

## 📊 Progress Log

### Morning (4h)
- [ ] 09:00-10:30: orchestrator ✓
- [ ] 10:30-12:00: activity-capture ✓
- [ ] 12:00-13:00: Lunch + tests

### Afternoon (4h)
- [ ] 13:00-15:00: serena tools 1-3 (HIGH)
- [ ] 15:00-17:00: serena tools 4-6 (MED)
- [ ] 17:00-17:30: Verify + commit

### Optional Evening
- [ ] serena tools 7-10 (LOW) - if energy remains

---

## 📁 Reference Documents

- `COMPLETION_CHECKLIST.md` - Detailed task breakdown
- `PRODUCTION_READINESS_PLAN.md` - Full 5-day plan
- `PRODUCTION_READINESS_QUICK_REF.md` - Quick reference

---

## ✅ Before You Start

```bash
# 1. Verify environment
cd /Users/dopemux/code/dopemux-mvp
git status

# 2. Create feature branch
git checkout -b production-day1

# 3. Baseline tests
./run_all_multi_workspace_tests.sh > baseline.log

# 4. Check tracker
./scripts/production_tracker.sh
```

---

**Ready to execute Day 1! 🚀**

**Estimated completion**: 8 hours
**Confidence**: 85%
**Next session**: Day 2 plan
