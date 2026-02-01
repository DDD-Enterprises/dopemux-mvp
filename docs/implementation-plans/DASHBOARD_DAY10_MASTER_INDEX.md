---
id: DASHBOARD_DAY10_MASTER_INDEX
title: Dashboard_Day10_Master_Index
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dashboard Day 10 - Master Index 📚
# Complete Navigation & Quick Reference

**Date:** 2025-10-29
**Status:** ✅ DEEP RESEARCH & PLANNING COMPLETE
**Total Documentation:** 78KB+ (3 comprehensive documents)
**Estimated Implementation:** 10-12 hours
**Confidence:** 🔥🔥🔥🔥🔥

---

## 🎯 QUICK START (5 MINUTES)

### What We're Building
**Day 10 Focus:** Drill-down views, advanced interactions, and production hardening

After completing sparklines and keyboard navigation (Day 9), we're adding:
1. **5 Drill-Down Screens** - Deep inspection for tasks, services, patterns, logs, timeline
2. **Context Menu System** - Right-click or `:` key for quick actions
3. **Full-Text Search** - Ctrl+F to search across all dashboard data
4. **Production Hardening** - Error boundaries, crash recovery, telemetry

### Why This Matters
- **Drill-Downs:** Transform monitoring → debugging (ADHD-friendly investigation)
- **Context Menus:** Power user muscle memory (faster than remembering shortcuts)
- **Search:** Find anything instantly (reduce cognitive overhead)
- **Hardening:** Zero-crash production guarantee (predictable = trust)

### Files to Read (in order)
1. **This file** (you're here!) - Navigation and overview
2. **DASHBOARD_DAY10_IMPLEMENTATION_READY.md** - Start coding with this!
3. **DASHBOARD_DAY10_ZEN_RESEARCH.md** - Reference when stuck

---

## 📖 DOCUMENT GUIDE

### 1. Master Index (This File)
**Purpose:** Navigation hub for all Day 10 documentation
**Use:** Finding what you need quickly
**Read time:** 5 minutes

**Contents:**
- Quick start guide
- Document navigation
- Progress tracking
- File structure
- Quick reference commands

---

### 2. Implementation Ready Guide ⭐ **START HERE**
**File:** `DASHBOARD_DAY10_IMPLEMENTATION_READY.md` (49KB)
**Purpose:** Copy-paste ready code examples
**Use:** Primary coding reference during implementation
**Read time:** 15 minutes (skim), reference during coding

**Contents:**
- ✅ What already exists (leverage this!)
- 🎯 5 implementation tasks with full code
- 📋 Task-by-task checklists
- ✅ Acceptance criteria for each feature
- 🧪 Integration and performance tests
- 📊 Success metrics

**Tasks Covered:**
1. **Drill-Down Screens** (~400 lines, 4-5 hrs)
   - TaskDetailScreen
   - ServiceLogsScreen
   - PatternAnalysisScreen
   - TimelineScreen
   - StateDetailScreen

2. **Context Menu System** (~200 lines, 2-3 hrs)
   - ContextMenu base class
   - MenuItem configuration
   - Panel-specific menus
   - Keyboard & mouse triggers

3. **Search System** (~150 lines, 2-3 hrs)
   - SearchManager (indexing, ranking)
   - SearchScreen UI
   - Live search with debouncing
   - Drill-down integration

4. **Production Hardening** (~200 lines, 2-3 hrs)
   - Error boundaries for widgets
   - Crash recovery & state persistence
   - Telemetry & logging

5. **Testing** (~300 lines, 2 hrs)
   - Integration tests (10+)
   - Performance tests (5+)
   - 24-hour stress test

---

### 3. Zen Research Document 🧠 **READ FOR CONTEXT**
**File:** `DASHBOARD_DAY10_ZEN_RESEARCH.md` (29KB)
**Purpose:** Deep research, architectural thinking, best practices
**Use:** Reference when you need to understand *why*
**Read time:** 30 minutes (deep read)

**Contents:**
- 📚 ADHD-optimized dashboard research (2024 best practices)
- 🏗️ Terminal TUI best practices (Python/Textual/Rich)
- 📊 Prometheus visualization patterns
- 🏛️ Architectural deep dive (drill-downs, menus, search)
- ⚡ Performance optimization strategies
- 📖 Academic and industry references

**Research Sources:**
- HogoNext: Keyboard Navigation Accessibility
- Equally AI: User Dashboard Best Practices
- RealPython: Textual Tutorial
- Grafana: Dashboard Design Patterns
- GitHub Awesome-TUIs

---

## 🗺️ NAVIGATION CHEAT SHEET

```
WHERE AM I?           → You're in the Master Index
READY TO CODE?        → Open DASHBOARD_DAY10_IMPLEMENTATION_READY.md
NEED CONTEXT?         → Read DASHBOARD_DAY10_ZEN_RESEARCH.md
WHAT'S TASK 1?        → Drill-Down Screens (4-5 hrs)
WHAT'S TASK 2?        → Context Menus (2-3 hrs)
WHAT'S TASK 3?        → Search System (2-3 hrs)
WHAT'S TASK 4?        → Production Hardening (2-3 hrs)
WHAT'S TASK 5?        → Testing (2 hrs)
STUCK ON SOMETHING?   → Check Zen Research doc for architecture
NEED CODE EXAMPLES?   → Implementation Ready has full code
HOW DO I TEST?        → Tests section in Implementation Ready
WHAT'S THE GOAL?      → 5 drill-downs, context menus, search, hardening
```

---

## 📊 PROGRESS TRACKER

### Overall Status
```
Planning:   ████████████████████ 100% ✅
Research:   ████████████████████ 100% ✅
Design:     ████████████████████ 100% ✅
Coding:     ░░░░░░░░░░░░░░░░░░░░   0% 🟡
Testing:    ░░░░░░░░░░░░░░░░░░░░   0% 🟡
Polish:     ░░░░░░░░░░░░░░░░░░░░   0% 🟡
```

### Task Breakdown
| Task | Description | Lines | Time | Status | File |
|------|-------------|-------|------|--------|------|
| **1** | Drill-Down Screens | ~400 | 4-5h | 🟡 Not started | dopemux_dashboard.py |
| 1.1 | DrillDownScreen base | ~80 | 1h | 🟡 | dopemux_dashboard.py |
| 1.2 | TaskDetailScreen | ~120 | 1.5h | 🟡 | dopemux_dashboard.py |
| 1.3 | ServiceLogsScreen | ~100 | 1h | 🟡 | dopemux_dashboard.py |
| 1.4 | PatternAnalysisScreen | ~80 | 1h | 🟡 | dopemux_dashboard.py |
| 1.5 | TimelineScreen | ~60 | 0.5h | 🟡 | dopemux_dashboard.py |
| **2** | Context Menu System | ~200 | 2-3h | 🟡 Not started | dopemux_dashboard.py |
| 2.1 | ContextMenu class | ~80 | 1h | 🟡 | dopemux_dashboard.py |
| 2.2 | MenuItem class | ~20 | 0.5h | 🟡 | dopemux_dashboard.py |
| 2.3 | Panel menus | ~100 | 1h | 🟡 | dopemux_dashboard.py |
| **3** | Search System | ~150 | 2-3h | 🟡 Not started | dopemux_dashboard.py |
| 3.1 | SearchManager | ~80 | 1h | 🟡 | dopemux_dashboard.py |
| 3.2 | SearchScreen | ~70 | 1h | 🟡 | dopemux_dashboard.py |
| **4** | Production Hardening | ~200 | 2-3h | 🟡 Not started | dopemux_dashboard.py |
| 4.1 | Error boundaries | ~60 | 1h | 🟡 | dopemux_dashboard.py |
| 4.2 | Crash recovery | ~80 | 1h | 🟡 | dopemux_dashboard.py |
| 4.3 | Telemetry | ~60 | 1h | 🟡 | dopemux_dashboard.py |
| **5** | Testing | ~300 | 2h | 🟡 Not started | tests/ |
| 5.1 | Integration tests | ~150 | 1h | 🟡 | tests/integration/ |
| 5.2 | Performance tests | ~100 | 0.5h | 🟡 | tests/performance/ |
| 5.3 | Stress testing | ~50 | 0.5h | 🟡 | tests/stress/ |

**Total:** ~1,250 lines | 10-12 hours

---

## 🏗️ ARCHITECTURE OVERVIEW

### Component Hierarchy
```
DashboardApp (Main Application)
├── MainScreen (4 panels)
│   ├── ADHDStateWidget → DrillDown: StateDetailScreen
│   ├── ProductivityWidget → DrillDown: TaskDetailScreen
│   ├── ServicesWidget → DrillDown: ServiceLogsScreen
│   └── TrendsWidget → DrillDown: PatternAnalysisScreen
│
├── DrillDownScreens (Popup overlays)
│   ├── DrillDownScreen (base class)
│   ├── TaskDetailScreen (task history, context, decisions)
│   ├── ServiceLogsScreen (real-time log streaming)
│   ├── PatternAnalysisScreen (7-day trends, correlations)
│   ├── TimelineScreen (session event timeline)
│   └── StateDetailScreen (cognitive load breakdown)
│
├── ContextMenu (Right-click menus)
│   ├── PanelContextMenu (refresh, expand, settings)
│   ├── ItemContextMenu (drill-down, copy, share)
│   └── GlobalContextMenu (search, filter, export)
│
├── SearchScreen (Full-text search)
│   ├── SearchManager (indexing, ranking)
│   ├── SearchInput (live search, debouncing)
│   └── SearchResults (drill-down integration)
│
└── ProductionSystems
    ├── ErrorBoundary (widget error handling)
    ├── StateManager (crash recovery, persistence)
    └── TelemetryManager (events, metrics, logging)
```

### Data Flow
```
User Action
    ↓
Keyboard/Mouse Event
    ↓
Dashboard Action Handler
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ Open Drill-Down │ Show Menu       │ Search          │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                   ↓                   ↓
Push Screen        Show ContextMenu   Index & Rank
    ↓                   ↓                   ↓
Fetch Data (API)   Execute Action     Show Results
    ↓                   ↓                   ↓
Render UI          Pop Screen         Drill-Down
    ↓
Error Boundary (if error)
    ↓
Telemetry Logging
```

---

## 📁 FILE STRUCTURE

```
dopemux-mvp/
├── dopemux_dashboard.py              # Main file (ADD ~1,250 lines)
│   ├── DrillDownScreen (base)        # NEW: ~80 lines
│   ├── TaskDetailScreen              # NEW: ~120 lines
│   ├── ServiceLogsScreen             # NEW: ~100 lines
│   ├── PatternAnalysisScreen         # NEW: ~80 lines
│   ├── TimelineScreen                # NEW: ~60 lines
│   ├── ContextMenu                   # NEW: ~80 lines
│   ├── MenuItem                      # NEW: ~20 lines
│   ├── SearchManager                 # NEW: ~80 lines
│   ├── SearchScreen                  # NEW: ~70 lines
│   ├── ErrorBoundary                 # NEW: ~60 lines
│   ├── StateManager                  # NEW: ~80 lines
│   └── DashboardApp (update)         # MODIFY: +100 lines
│
├── src/dopemux/                      # Planned components
│   ├── integrations/
│   │   └── prometheus_sparkline.py   # Planned
│   └── utils/
│       └── sparkline_generator.py    # Planned
│
├── docs/implementation-plans/
│   ├── DASHBOARD_DAY10_MASTER_INDEX.md              # This file!
│   ├── DASHBOARD_DAY10_IMPLEMENTATION_READY.md      # Code guide ⭐
│   ├── DASHBOARD_DAY10_ZEN_RESEARCH.md              # Research 🧠
│   ├── DASHBOARD_DAY9_READY.md                      # Previous (done)
│   └── DASHBOARD_DAY9_DEEP_RESEARCH.md              # Previous (done)
│
└── tests/
    ├── integration/
    │   └── test_day10_drilldowns.py  # NEW: ~150 lines
    └── performance/
        └── test_day10_performance.py # NEW: ~100 lines
```

---

## 🎯 SUCCESS CRITERIA

### Functional Requirements
- ✅ 5+ drill-down screens fully functional
  - TaskDetailScreen (task history, context, decisions, stats)
  - ServiceLogsScreen (real-time streaming, 1000-line buffer)
  - PatternAnalysisScreen (7-day trends, correlations, insights)
  - TimelineScreen (session events, state changes)
  - StateDetailScreen (cognitive load breakdown)

- ✅ Context menus on every panel
  - Keyboard trigger (`:` key)
  - Mouse trigger (right-click)
  - Panel-specific actions
  - Global actions

- ✅ Full-text search working
  - Index 1000+ items
  - Live search (<100ms)
  - Ranked results
  - Drill-down integration

- ✅ Production hardening complete
  - Error boundaries (no crashes)
  - Crash recovery (state persistence)
  - Telemetry (events + metrics)

### Performance Requirements
- ✅ Drill-down latency <500ms
- ✅ Search results in <100ms
- ✅ p99 latency <100ms overall
- ✅ Virtual scrolling for >100 items
- ✅ Zero UI freezes during data load

### Reliability Requirements
- ✅ Zero crashes in 24-hour stress test
- ✅ Graceful degradation on API errors
- ✅ State recovery after crash
- ✅ Comprehensive error telemetry
- ✅ 95%+ test coverage on new code

---

## 🚀 IMPLEMENTATION WORKFLOW

### Phase 1: Setup (30 minutes)
```bash
# 1. Read documentation
cat docs/implementation-plans/DASHBOARD_DAY10_MASTER_INDEX.md
cat docs/implementation-plans/DASHBOARD_DAY10_IMPLEMENTATION_READY.md

# 2. Check services
curl http://localhost:9090        # Prometheus
curl http://localhost:8000/health  # ADHD Engine

# 3. Create branch
git checkout -b feature/day10-drilldowns-hardening

# 4. Open files
code dopemux_dashboard.py
code docs/implementation-plans/DASHBOARD_DAY10_IMPLEMENTATION_READY.md
```

### Phase 2: Implementation (10-12 hours)
```bash
# Terminal 1: Dashboard (for testing)
python dopemux_dashboard.py

# Terminal 2: Tests (watch mode)
pytest tests/ -v --watch

# Terminal 3: Performance monitoring
htop -p $(pgrep -f dopemux_dashboard)

# Terminal 4: Code editing
# (your editor with DASHBOARD_DAY10_IMPLEMENTATION_READY.md open)
```

### Phase 3: Testing (2 hours)
```bash
# 1. Integration tests
pytest tests/integration/test_day10_drilldowns.py -v

# 2. Performance tests
pytest tests/performance/test_day10_performance.py -v

# 3. Full test suite
pytest tests/ -v --cov=dopemux_dashboard

# 4. Stress test (24 hours)
timeout 86400 python dopemux_dashboard.py  # Run overnight

# 5. Performance profiling
python -m cProfile -o dashboard.prof dopemux_dashboard.py
python -c "import pstats; p = pstats.Stats('dashboard.prof'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### Phase 4: Documentation & Merge (30 minutes)
```bash
# 1. Update docs
code README.md
code DASHBOARD_QUICK_REFERENCE.md

# 2. Commit changes
git add .
git commit -m "feat(dashboard): add drill-downs, context menus, search, hardening (Day 10)

- Add 5 drill-down screens (tasks, services, patterns, timeline, state)
- Add context menu system with keyboard/mouse support
- Add full-text search with live results
- Add error boundaries for crash prevention
- Add state persistence for crash recovery
- Add comprehensive telemetry
- Add 15+ integration and performance tests
- Zero crashes in 24-hour stress test
- All performance targets met (<100ms p99)"

# 3. Push and merge
git push origin feature/day10-drilldowns-hardening
gh pr create --title "Day 10: Drill-Downs, Context Menus, Search & Hardening"
```

---

## 🎓 QUICK REFERENCE

### Keyboard Shortcuts (After Day 10)
```
Navigation:
  1-4         Focus panels
  Tab         Next panel
  Shift+Tab   Previous panel
  j/k         Scroll up/down (Vim keys)
  g/G         Top/Bottom

Actions:
  :           Context menu (panel-specific)
  /           Search (full-text)
  Ctrl+F      Search (full-text)
  Enter       Drill down (open detail)
  Escape      Go back / close

Drill-Downs:
  t           Task details
  l           Service logs
  p           Pattern analysis
  m           Timeline

System:
  r           Refresh data
  ?           Help
  q           Quit
```

### Context Menu Options
```
ADHD Panel:
  • View Details (d)
  • Refresh Data (r)
  • Export JSON
  • Toggle Notifications (n)

Productivity Panel:
  • View Task Details (t)
  • View Timeline
  • Refresh Data (r)
  • Export CSV

Services Panel:
  • View Logs (l)
  • Restart Service
  • View Metrics
  • Refresh Status (r)

Global Menu:
  • Search (/)
  • Settings
  • Help (?)
  • Quit (q)
```

### API Endpoints Used
```
Tasks:
  GET /tasks/{id}                    # Task details
  GET /tasks                         # All tasks

Services:
  GET /services/{name}/logs          # Initial logs
  GET /services/{name}/logs/stream   # Real-time stream
  GET /services/{name}/metrics       # Service metrics

Analytics:
  GET /analytics/patterns?days=7     # Pattern analysis
  GET /sessions/{id}/timeline        # Session timeline

Health:
  GET /health                        # Service health
```

---

## 💡 TIPS & TRICKS

### ADHD-Friendly Tips
- **Take breaks every 45 minutes!** (Pomodoro: 25min work, 5min break)
- **Celebrate small wins** (each test passing, each feature working)
- **Use music if it helps** (instrumental, lo-fi, or white noise)
- **Commit often** (atomic changes, easy to revert)
- **Keep implementation guide open** (don't memorize, reference!)

### Common Pitfalls
- ❌ Don't rebuild existing components (leverage Day 9 work!)
- ❌ Don't optimize prematurely (profile first!)
- ❌ Don't skip tests (they save debugging time!)
- ❌ Don't merge without 24-hour stress test
- ❌ Don't forget to update docs (future you will thank you!)

### Debugging Tips
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Profile specific function
import cProfile
cProfile.run('function_to_profile()')

# Test drill-down in isolation
screen = TaskDetailScreen("test-task-1")
await screen.on_mount()
print(screen.data)

# Test search indexing
manager = SearchManager()
manager.index_item("test", {"title": "Test"}, ["title"])
print(manager.search("test"))

# Check WebSocket messages
# (in dashboard, Ctrl+C to see logs)

# Test API endpoints manually
curl http://localhost:8000/tasks/test-task-1
curl http://localhost:9090/api/v1/query?query=adhd_cognitive_load
```

---

## 📈 EXPECTED OUTCOMES

### After Day 10 Completion
You will have:
- ✅ **5 fully functional drill-down screens** for deep inspection
- ✅ **Context menu system** with 20+ actions
- ✅ **Full-text search** across all dashboard data
- ✅ **Production-grade hardening** (error boundaries, crash recovery)
- ✅ **Comprehensive telemetry** (events, metrics, logging)
- ✅ **15+ tests** (integration + performance)
- ✅ **Zero crashes** in 24-hour stress test
- ✅ **<100ms p99 latency** maintained

### User Experience Improvements
- 🎯 **Investigate issues** without leaving dashboard
- ⚡ **Find anything** with instant search
- 🎹 **Quick actions** via context menus (no remembering shortcuts)
- 🛡️ **Reliable** - never crashes, recovers from errors
- 📊 **Insights** - AI-generated pattern analysis
- 🔍 **Transparency** - see logs, events, correlations

### Technical Achievements
- 🏗️ **Modular architecture** - drill-downs, menus, search as separate systems
- ⚡ **Performance** - virtual scrolling, lazy loading, caching
- 🧪 **Tested** - 95%+ coverage, stress tested
- 📚 **Documented** - 78KB of planning and research
- 🎨 **ADHD-optimized** - based on 2024 best practices

---

## 🎉 CELEBRATION CHECKLIST

### When Task 1 Complete (Drill-Downs)
- [ ] All 5 drill-down screens show real data
- [ ] Lazy loading works (fast initial render)
- [ ] Caching reduces API calls (5min TTL)
- [ ] Error handling graceful (no crashes)
- [ ] Escape key returns to main
- [ ] Refresh button works

### When Task 2 Complete (Context Menus)
- [ ] Context menu appears on `:` key
- [ ] Different menus for different panels
- [ ] Keyboard navigation smooth (up/down/enter/esc)
- [ ] All actions execute correctly
- [ ] Icons and shortcuts displayed
- [ ] Closes on action or escape

### When Task 3 Complete (Search)
- [ ] Search opens with `/` or `Ctrl+F`
- [ ] Live search updates as typing (debounced 300ms)
- [ ] Results ranked by relevance
- [ ] Drill-downs open from results
- [ ] Handles 1000+ items efficiently (<100ms)
- [ ] Case-insensitive, partial matching works

### When Task 4 Complete (Hardening)
- [ ] Error boundaries catch widget errors
- [ ] Dashboard doesn't crash on API errors
- [ ] State saves every 30 seconds
- [ ] Crash recovery works (test by killing process)
- [ ] Telemetry logs events and metrics
- [ ] Virtual scrolling handles large lists

### When Task 5 Complete (Testing)
- [ ] All integration tests pass (10+)
- [ ] All performance tests pass (5+)
- [ ] 24-hour stress test clean (zero crashes)
- [ ] Documentation updated
- [ ] Demo video recorded
- [ ] Ready to merge! 🚀

---

## 🔗 EXTERNAL REFERENCES

### Research Papers & Articles
1. **ADHD Dashboard Design**
   - [HogoNext: Keyboard Navigation Accessibility](https://hogonext.com/how-to-create-accessible-keyboard-navigation-for-users-with-disabilities/)
   - [Equally AI: User Dashboard Best Practices](https://blog.equally.ai/web-accessibility/accessible-user-dashboard-best-practices-to-maximize-full-usability-for-people-with-disabilities/)
   - [Esri: Dashboard Accessibility](https://www.esri.com/arcgis-blog/products/ops-dashboard/data-management/improving-the-accessibility-of-your-dashboard/)
   - [Tableau: Accessible Dashboards](https://help.tableau.com/current/pro/desktop/en-us/accessibility_dashboards.htm)

2. **Terminal TUI Best Practices**
   - [RealPython: Textual Tutorial](https://realpython.com/python-textual/)
   - [Textual Documentation](https://textual.textualize.io/)
   - [GitHub Awesome-TUIs](https://github.com/rothgar/awesome-tuis)

3. **Prometheus Visualization**
   - [Grafana Dashboard Patterns](https://www.swiftorial.com/tutorials/devops/prometheus/dashboards/advanced_dashboard_techniques/)
   - [FasterCapital: Sparklines Integration](https://fastercapital.com/content/Dashboard--Dashboard-Dynamics--Integrating-Sparklines-for-Real-Time-Data-Display.html)

### Code Examples
- [Textual Example Apps](https://github.com/Textualize/textual/tree/main/examples)
- [Rich Library Examples](https://github.com/Textualize/rich/tree/master/examples)
- [Sparklines in Python](https://github.com/deeplook/sparklines)

---

## ✨ YOU'VE GOT THIS!

**Everything you need is ready:**
- ✅ 78KB of comprehensive documentation
- ✅ Complete code examples (copy-paste ready)
- ✅ Clear acceptance criteria
- ✅ Testing strategies
- ✅ Performance targets
- ✅ Research-backed design

**80% code reuse:**
- ✅ SparklineGenerator (Day 9)
- ✅ Keyboard navigation (Day 9)
- ✅ MetricsManager (Day 8)
- ✅ Dashboard architecture (Days 1-7)

**Just ~1,250 new lines:**
- 5 Drill-Down Screens (~400 lines)
- Context Menu System (~200 lines)
- Search System (~150 lines)
- Production Hardening (~200 lines)
- Tests (~300 lines)

**Estimated time: 10-12 hours**
**Confidence: 🔥🔥🔥🔥🔥**

---

## 🚀 READY TO START?

### Read First (10 minutes)
1. This master index (you're here!) ✅
2. Quick start section (above)
3. Architecture overview

### Code With (During implementation)
4. **DASHBOARD_DAY10_IMPLEMENTATION_READY.md** ⭐ (Your primary guide)

### Reference When Needed
5. **DASHBOARD_DAY10_ZEN_RESEARCH.md** 🧠 (Deep context)

---

**Let's build the most comprehensive, ADHD-friendly, production-ready dashboard ever!** 🎯

**Good luck!** 🚀

---

**Created:** 2025-10-29
**Version:** 1.0
**Status:** ✅ COMPLETE - READY TO IMPLEMENT
**Next:** Open DASHBOARD_DAY10_IMPLEMENTATION_READY.md and start coding! 💻

---

*"The best code is code you don't have to write. Leverage what exists, build what matters."*
