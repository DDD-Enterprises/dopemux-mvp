---
id: quick-reference
title: Quick Reference
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Quick Reference (reference) for dopemux documentation and developer workflows.
---
# DDDPG - Quick Reference Card

**Last Updated**: 2025-10-29
**Status**: ✅ Ready to Build Week 4 Day 2

---

## 🚀 Quick Start

### If you're new, read in this order:
1. **README_START_HERE.md** (5 min) - Navigation
1. **EXECUTIVE_SUMMARY.md** (10 min) - Overview
1. **WEEK4_DAY2_IMPLEMENTATION_PLAN.md** (2 min scan) - What to build

### If you want to build today:
1. Open **WEEK4_DAY2_IMPLEMENTATION_PLAN.md**
1. Follow 4 phases (~95 minutes total)
1. Phase 1 → Phase 2 → Phase 3 → Phase 4
1. Run tests, update docs

---

## 📁 Key Files

### Documentation (services/dddpg/)
```
README_START_HERE.md              ← Start here!
EXECUTIVE_SUMMARY.md              ← What/why/status
DEEP_ANALYSIS_CURRENT_STATE.md    ← Full audit
WEEK4_DAY2_IMPLEMENTATION_PLAN.md ← Build guide
WEEK4_PROGRESS.md                 ← Progress tracker
```

### Code (services/dddpg/)
```
core/models.py           ← Decision, Relationship, WorkSession
storage/sqlite_backend.py ← SQLite storage
queries/service.py       ← Query API (extend today)
kg_integration.py        ← KG layer (extend today)
```

### Tests (services/dddpg/)
```
test_kg_integration.py         ← KG tests (extend today)
test_relationship_mapper.py    ← NEW today
```

---

## 🎯 Week 4 Day 2 Phases

### Phase 1: Decision-Task Linking (15 min)
**File**: `kg_integration.py`
**Add**: 3 methods (link, get, unlink)
**Tests**: 4 tests

### Phase 2: Relationship Mapper (25 min)
**File**: `relationship_mapper.py` (NEW)
**Add**: RelationshipMapper class
**Tests**: 3 tests

### Phase 3: Suggestion Engine (35 min)
**File**: `suggestion_engine.py` (NEW)
**Add**: SuggestionEngine class
**Tests**: 5 tests

### Phase 4: QueryService Integration (20 min)
**File**: `queries/service.py`
**Add**: KG integration methods
**Tests**: 4 integration tests

---

## ✅ Current Status

**Complete**:
- ✅ Core models (Decision, Relationship, WorkSession)
- ✅ SQLite storage with FTS5
- ✅ Query patterns (Top-3, progressive)
- ✅ KG integration foundation
- ✅ 100% test coverage (KG layer)

**Today**:
- ⏳ Relationship mapping
- ⏳ Suggestion engine
- ⏳ QueryService KG integration

**Future**:
- [ ] Semantic search (embeddings)
- [ ] EventBus integration
- [ ] Performance optimization

---

## 📊 Key Metrics

**Code**: ~1,400 lines production, ~300 lines tests
**Tests**: 100% coverage (KG layer), 19/19 passing
**Speed**: Day 1 completed in 1 hour (vs 3.5 planned = 3.5x!)
**Day 2 Est**: 95 minutes (~1.5 hours)

---

## 🏗️ Architecture

```
User/Agent
    ↓
QueryService (queries/service.py)
    ↓
├─→ RelationshipMapper → DDDPGKG → AGE
└─→ SuggestionEngine   → DDDPGKG → AGE
```

**Key Concepts**:
- **Multi-instance**: workspace_id + instance_id
- **ADHD-optimized**: Top-3 pattern, progressive disclosure
- **Graph-native**: PostgreSQL AGE, typed relationships
- **Agent-friendly**: Flexible metadata dict

---

## 🧪 Common Commands

### Run Tests
```bash
cd services/dddpg
pytest test_kg_integration.py -v
pytest -v  # All tests
```

### Check Coverage
```bash
pytest --cov=. --cov-report=term-missing
```

### Lint
```bash
pylint kg_integration.py
```

---

## 🎓 Design Patterns

### Top-3 Pattern (ADHD)
```python
async def overview(limit: int = 3):
    """Never show more than 3 items by default"""
```

### Graceful Degradation
```python
if not self.kg:
    return fallback_behavior()
return kg_powered_behavior()
```

### Parameterized Queries (Security)
```python
query = "SELECT * WHERE id = $id"
params = {'id': task_id}  # No string interpolation!
```

### Multi-Instance Isolation
```python
class Decision(BaseModel):
    workspace_id: str  # Main workspace
    instance_id: str   # A, B, feature-auth
    visibility: str    # PRIVATE/SHARED/GLOBAL
```

---

## 🔥 Quick Wins

### Want to understand the codebase?
→ Read **DEEP_ANALYSIS_CURRENT_STATE.md** (20 min)

### Want to build today?
→ Follow **WEEK4_DAY2_IMPLEMENTATION_PLAN.md** (95 min)

### Want high-level overview?
→ Read **EXECUTIVE_SUMMARY.md** (10 min)

### Want to see progress?
→ Check **WEEK4_PROGRESS.md** (2 min)

---

## 💡 Remember

**ADHD Principles**:
- Top-3 pattern (never >3 items)
- Progressive disclosure (Overview → Exploration → Deep)
- Graceful degradation (always works)
- Context preservation (WorkSession)

**Multi-Instance**:
- workspace_id + instance_id everywhere
- Visibility controls (PRIVATE/SHARED/GLOBAL)
- Git worktree compatible

**Security**:
- Parameterized queries always
- Input validation (Pydantic)
- Error handling everywhere

---

## 🚀 Next Action

**Open**: `services/dddpg/WEEK4_DAY2_IMPLEMENTATION_PLAN.md`
**Start**: Phase 1 - Decision-Task Linking
**Time**: 95 minutes total
**Confidence**: 🟢 Very High

**Let's build!** 🎯
