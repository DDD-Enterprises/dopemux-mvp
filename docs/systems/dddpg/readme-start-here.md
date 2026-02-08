---
id: readme-start-here
title: Readme Start Here
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme Start Here (reference) for dopemux documentation and developer workflows.
---
# DDDPG Service - START HERE 🚀

**DDDPG**: Decision-Driven Development Planning Graph
**Purpose**: ADHD-optimized decision tracking with knowledge graph intelligence
**Status**: Week 4 Day 2 - Fully Analyzed & Ready to Build
**Analysis Date**: 2025-10-29

---

## 📖 Quick Navigation

### 🎯 **New here? Start with these (in order)**:

1. **MODERNIZATION_ANALYSIS_2025.md** ← Read this FIRST! 🆕
   - Complete modernization analysis (Oct 2025)
   - Current state deep dive
   - Architecture strengths & unique features
   - Production readiness assessment
   - **Most comprehensive document**

2. **WEEK4_BUILD_ROADMAP.md** ← Complete build plan 🆕
   - Day-by-day implementation guide
   - Phase-by-phase breakdown
   - Full code samples
   - Testing strategies
   - Week 4 complete roadmap

3. **WEEK4_DAY2_IMPLEMENTATION_PLAN.md** ← Build this TODAY!
   - Concrete implementation steps
   - Code snippets ready to paste
   - Testing strategy
   - ~95 minutes to complete

4. **DEEP_ANALYSIS_CURRENT_STATE.md** ← Technical deep dive
   - Complete current state audit
   - Architecture overview
   - What's working, what needs work
   - Technology stack and design decisions

### 📚 **Background/Context**:

1. **ARCHITECTURE_ANALYSIS.md**
   - Data model deep dive
   - Multi-instance architecture
   - Storage strategy decisions

2. **WEEK4_DAY1_COMPLETE.md**
   - What we built on Day 1
   - KG integration foundation
   - 19/19 tests passing

3. **WEEK4_PROGRESS.md**
   - Week 4 tracker
   - Efficiency metrics (3.5x faster!)
   - Roadmap overview

### 🔍 **Detailed Specs** (optional reading):

1. **WEEK4_DAY1_DEEP_ANALYSIS.md** - Day 1 decisions
2. **WEEK4_DAY2_DEEP_RESEARCH.md** - Day 2 research
3. **WEEK4_DAY2_SPEC.md** - Day 2 technical spec
4. **WEEK4_DAY2_VALIDATION.md** - Day 2 validation
5. **STORAGE_DESIGN.md** - Storage architecture

---

## ⚡ Quick Start (If you just want to build)

**Goal**: Implement Week 4 Day 2 features

**Time**: ~95 minutes

**Steps**:
1. Read `DEEP_ANALYSIS_CURRENT_STATE.md` (10 min) - understand what we have
2. Open `WEEK4_DAY2_IMPLEMENTATION_PLAN.md` (2 min) - get the plan
3. Follow the 4 phases:
   - Phase 1: Decision-Task Linking (15 min)
   - Phase 2: Relationship Mapper (25 min)
   - Phase 3: Suggestion Engine (35 min)
   - Phase 4: QueryService Integration (20 min)
4. Run tests, update progress docs (10 min)

**Code files you'll create/modify**:
- `kg_integration.py` - extend with 3 new methods
- `relationship_mapper.py` - NEW file
- `suggestion_engine.py` - NEW file
- `queries/service.py` - extend with KG integration
- `test_kg_integration.py` - add 4 tests
- `test_relationship_mapper.py` - NEW file (tests)

---

## 🏗️ Architecture at a Glance

```
services/dddpg/
├── core/
│   ├── models.py          ✅ COMPLETE - Decision, Relationship, WorkSession
│   └── config.py          ✅ COMPLETE
│
├── storage/
│   ├── interface.py       ✅ COMPLETE - Storage abstraction
│   ├── sqlite_backend.py  ✅ COMPLETE - SQLite with FTS5
│   └── migrations/        ✅ COMPLETE
│
├── queries/
│   └── service.py         🔨 EXTEND TODAY - Add KG integration
│
├── kg_integration.py      🔨 EXTEND TODAY - Add decision linking
├── relationship_mapper.py ⭐ NEW TODAY - Build relationship views
├── suggestion_engine.py   ⭐ NEW TODAY - ADHD-optimized suggestions
│
└── tests/
    ├── test_kg_integration.py       🔨 EXTEND TODAY
    └── test_relationship_mapper.py  ⭐ NEW TODAY
```

**Data Flow**:
```
User/Agent → QueryService → RelationshipMapper → DDDPGKG → AGE (Postgres)
                          ↘ SuggestionEngine  ↗
```

---

## 🎯 What We're Building (Week 4 Day 2)

### Feature 1: Decision-Task Linking
**Why**: Connect DDDPG decisions to knowledge graph tasks
**Code**: 3 new methods in `DDDPGKG`
**Time**: 15 min

### Feature 2: Relationship Mapping
**Why**: Build composite views of task relationships
**Code**: New `RelationshipMapper` class
**Time**: 25 min

### Feature 3: ADHD-Optimized Suggestions
**Why**: Context-aware task recommendations (energy, time, focus)
**Code**: New `SuggestionEngine` class
**Time**: 35 min

### Feature 4: QueryService Integration
**Why**: Wire everything together with graceful fallbacks
**Code**: Extend `QueryService` with KG support
**Time**: 20 min

---

## ✅ Current Status

**What's Working**:
- ✅ Core models (Decision, Relationship, WorkSession)
- ✅ Multi-instance support (workspace + instance isolation)
- ✅ SQLite storage with FTS5 search
- ✅ ADHD-optimized query patterns (Top-3)
- ✅ KG integration foundation (DDDPGKG)
- ✅ 100% test coverage on KG layer (19/19 passing)

**What's Next** (TODAY):
- ⏳ Decision-task linking
- ⏳ Relationship mapping
- ⏳ Enhanced suggestions
- ⏳ QueryService KG integration

**What's After** (Week 4 Days 3-5):
- [ ] Semantic search (embeddings)
- [ ] Performance optimization
- [ ] EventBus integration
- [ ] Agent integrations

---

## 📊 Key Metrics

**Codebase Size**:
- Production: ~1,400 lines Python
- Tests: ~300 lines
- Documentation: ~50 pages

**Quality**:
- Test coverage: 100% (KG layer)
- Security: Parameterized queries throughout
- ADHD design: Top-3 pattern everywhere

**Week 4 Day 1 Efficiency**:
- Planned: 3.5 hours
- Actual: 1 hour
- **Speedup: 3.5x** 🚀

---

## 🧠 Key Design Principles

### 1. ADHD-Optimized
- **Top-3 Pattern**: Never show more than 3 items by default
- **Progressive Disclosure**: Overview → Exploration → Deep
- **Graceful Degradation**: Works even when KG unavailable
- **Context Preservation**: Save focus state in WorkSession

### 2. Multi-Instance Ready
- **workspace_id**: Main workspace root
- **instance_id**: Specific instance (A, B, feature-auth, etc)
- **visibility**: PRIVATE | SHARED | GLOBAL
- **Why**: Supports Git worktrees, prevents collisions

### 3. Agent-Friendly
- **agent_metadata**: Flexible JSON dict for any agent
- **No schema changes** needed for new agents
- **Event-driven**: Future EventBus integration planned

### 4. Graph-Native
- **DecisionRelationship**: Typed graph edges
- **PostgreSQL AGE**: Knowledge graph backend
- **Cypher queries**: Relationship traversal
- **Semantic search**: Future embeddings support

### 5. Security-First
- **Parameterized queries**: No SQL injection
- **Input validation**: Pydantic models
- **Error handling**: Graceful degradation
- **Logging**: LOUD errors for monitoring

---

## 🛠️ Technology Stack

**Core**:
- Python 3.9+
- Pydantic v2 (data models)
- asyncio (async/await)

**Storage**:
- SQLite (current: local backend)
- PostgreSQL AGE (future: graph queries)
- FTS5 (full-text search)

**Testing**:
- pytest
- pytest-asyncio
- unittest.mock

**Future**:
- Redis (caching, EventBus)
- Embeddings (semantic search)

---

## 📝 Common Tasks

### Run Tests
```bash
cd services/dddpg
pytest test_kg_integration.py -v
pytest test_relationship_mapper.py -v  # After Day 2
```

### Check Test Coverage
```bash
pytest --cov=. --cov-report=term-missing
```

### Lint Code
```bash
pylint kg_integration.py relationship_mapper.py suggestion_engine.py
```

### Run Full Test Suite
```bash
pytest -v --tb=short
```

---

## 🤝 Integration Points

**With Other Services**:

- **Task-Orchestrator**: Tasks are decisions with `decision_type=IMPLEMENTATION`
- **Serena (LSP)**: Hover shows decision context
- **Zen**: Validates decisions via consensus
- **ADHD Engine**: Suggests breaks based on cognitive load
- **Desktop Commander**: Logs file operation decisions
- **Dope-Context**: Provides workspace state

**Events** (future EventBus):
- Publish: `decision.created`, `decision.updated`, `decision.related`
- Subscribe: `task.completed`, `session.ended`, `agent.suggested`

---

## ❓ FAQ

### Q: What's the difference between DDDPG and ConPort?
**A**: ConPort is legacy SQLite-only. DDDPG is graph-native with multi-instance support and ADHD optimizations.

### Q: Why both SQLite and PostgreSQL?
**A**: Hybrid approach - SQLite for fast local reads, Postgres AGE for graph queries and sharing.

### Q: What's the Top-3 pattern?
**A**: Never show more than 3 items by default. Matches ADHD working memory limits (3-4 items).

### Q: How do worktrees work with DDDPG?
**A**: Each worktree gets unique `instance_id`. Decisions can be PRIVATE (instance-only) or SHARED (across instances).

### Q: Is the KG required?
**A**: No! Everything gracefully degrades without it. KG adds intelligence but isn't required.

---

## 🚀 Ready to Build!

**Next Steps**:
1. ✅ Read `DEEP_ANALYSIS_CURRENT_STATE.md` (you're almost done!)
2. ⏭️ Open `WEEK4_DAY2_IMPLEMENTATION_PLAN.md`
3. 🔨 Start Phase 1: Decision-Task Linking

**Estimated Time**: 95 minutes
**Confidence**: Very High
**Let's go!** 🎯

---

**Last Updated**: 2025-10-29
**Version**: Week 4 Day 2 Ready
**Status**: 🟢 Ready to build
