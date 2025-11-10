---
id: NEXT_PHASE_DEEP_RESEARCH
title: Next_Phase_Deep_Research
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Next Phase Deep Research & Planning

**Date:** 2025-10-29
**Session:** Post-Day 2 Analysis
**Philosophy:** Zen research → Clear thinking → Strategic planning

---

## 🔍 CURRENT STATE ANALYSIS

### What We Have Built

**Day 1-2 Achievements:**
- ✅ 510-line Textual dashboard (`dopemux_dashboard.py`)
- ✅ 3 HTTP wrapper services (ADHD, ConPort, Serena)
- ✅ 17 total HTTP endpoints
- ✅ MetricsFetcher with async parallel loading
- ✅ 100% dashboard integration (services → dashboard)

**Files Inventory:**
```
Core Dashboard:
├── dopemux_dashboard.py (510 lines, Textual-based)
├── MetricsFetcher class (async HTTP client)
└── 3 integrated services (ADHD, ConPort, Serena)

HTTP Services:
├── services/adhd_engine/main.py (Port 8000, 10 endpoints)
├── services/conport/http_server.py (Port 8005, 3 endpoints)
└── services/serena/v2/http_server.py (Port 8003, 4 endpoints)

Documentation:
├── TMUX_DASHBOARD_README.md (Quick start guide)
├── TMUX_DASHBOARD_DESIGN.md (Research-backed design)
├── TMUX_METRICS_INVENTORY.md (50+ metrics catalog)
├── DASHBOARD_ENHANCEMENTS.md (150+ future features)
└── tmux-dashboard-sprint-plan.md (2-week implementation plan)
```

### Service Status Check

**Current State (2025-10-29 07:36 UTC):**
```
Port 8000 - ADHD Engine:    ❌ Not running (was running earlier)
Port 8005 - ConPort:        ❌ Not running (was running earlier)
Port 8003 - Serena:         ❌ Not running (was running earlier)

Reason: Background processes stopped (normal for testing)
Solution: Simple restart commands
```

**Data Quality:**
- ADHD Engine: 100% real data (when running)
- ConPort: Mock data (PostgreSQL ready, SSL issue)
- Serena: Mock data (MetricsAggregator loaded, detectors ready)

---

## 🤔 STRATEGIC QUESTIONS

### Question 1: What Should We Do Next?

**Option A: Quick Wins (DASHBOARD_ENHANCEMENTS.md Tier 0)**
```python
# 1-2 hour tasks, high impact
Features:
├── Interactive controls (b=break, f=focus mode)
├── Theme switcher (Catppuccin, Nord, Dracula)
├── Keyboard shortcuts help ('?' key)
└── Desktop notifications (macOS osascript)

Total Time: 5-8 hours
Value: Dashboard becomes actionable, not just informative
```

**Option B: Actually Run & Test the Dashboard**
```bash
# We built it but haven't seen it in action!
Tasks:
├── Restart all 3 services
├── Run dopemux_dashboard.py
├── Verify all panels display correctly
├── Test MetricsFetcher integration
└── Screenshot/demo for documentation

Total Time: 1 hour
Value: Validate our 2 days of work, find bugs
```

**Option C: Sprint Plan Week 1 (Advanced Features)**
```python
# From tmux-dashboard-sprint-plan.md
Features:
├── Enhanced sparklines (Prometheus historical data)
├── Interactive keyboard navigation (tab, 1-4 keys)
├── Panel focusing and expansion
└── Real-time auto-updates

Total Time: 2-3 days
Value: Professional-grade dashboard, power user features
```

**Option D: Real Data Integration**
```python
# Fix the mock data issues
Tasks:
├── Fix ConPort PostgreSQL SSL connection
├── Wire Serena detection results
├── Add Prometheus metrics scraping
└── Historical data persistence

Total Time: 3-4 hours
Value: Dashboard shows 100% real data
```

**🧘 Zen Analysis:**

**Immediate Value Priority:**
1. **Option B** (1 hour) - See what we built, validate it works
2. **Option A** (5-8 hours) - Make it useful and delightful
3. **Option D** (3-4 hours) - Get real data flowing
4. **Option C** (2-3 days) - Polish to professional quality

**Recommendation:** B → A → D → C (progressive value delivery)

---

### Question 2: What Do We Actually Need?

**MVP Dashboard (What Users Need Now):**
```
Must Have:
├── ✅ Display ADHD metrics (we have this)
├── ✅ Show service health (we have this)
├── ✅ Pattern detection summary (we have this)
├── ⏳ Actually run it (not done yet!)
├── ⏳ Take action from dashboard (not done yet!)
└── ⏳ Persist across sessions (not done yet!)

Nice to Have:
├── ⏳ Historical trends (sparklines ready, data pending)
├── ⏳ Keyboard navigation (design ready, code pending)
├── ⏳ Theme customization (easy to add)
└── ⏳ Desktop alerts (simple implementation)
```

**Critical Gap:** We haven't actually run the dashboard yet!

**🧘 Insight:** Before adding features, we should verify the foundation works.

---

### Question 3: What's the Smartest Path?

**Path 1: Build More Features**
```
Pros: Impressive feature list, sprint plan progress
Cons: Unknown if foundation works, potential wasted effort
Risk: Building on untested foundation
```

**Path 2: Test & Validate First**
```
Pros: Find bugs early, validate architecture, confidence
Cons: "Just testing" feels less exciting than shipping features
Risk: Minimal (1 hour investment)
```

**Path 3: Quick Wins First**
```
Pros: Actionable dashboard, user delight, ADHD dopamine hit
Cons: Still building on untested foundation
Risk: Moderate
```

**🧘 Zen Decision:** Path 2 → Path 3 → Path 1

**Why:**
- Test foundation (1 hr) → confidence
- Add quick wins (5-8 hrs) → user value
- Then advanced features (2-3 days) → professional polish

---

## 📐 RECOMMENDED PLAN

### Phase 0: Foundation Validation (1 hour)

**Goal:** Verify everything works before building more

**Tasks:**
1. **Restart Services** (10 min)
   ```bash
   # Terminal 1: ADHD Engine
   cd services/adhd_engine && source venv/bin/activate && python main.py

   # Terminal 2: ConPort
   cd services/conport && python3 http_server.py

   # Terminal 3: Serena
   cd services/serena/v2 && python3 http_server.py
   ```

2. **Run Dashboard** (5 min)
   ```bash
   python3 dopemux_dashboard.py
   ```

3. **Verify All Panels** (10 min)
   - ADHD State panel shows energy, attention, cognitive load
   - Productivity panel shows tasks, decisions
   - Services panel shows all 3 services healthy
   - Trends panel shows patterns (mock data OK)

4. **Test MetricsFetcher** (10 min)
   ```python
   # Quick integration test
   python3 -c "
   import asyncio
   from dopemux_dashboard import MetricsFetcher

   async def test():
       fetcher = MetricsFetcher()
       adhd = await fetcher.get_adhd_state()
       decisions = await fetcher.get_decisions()
       patterns = await fetcher.get_patterns()
       print('✅ All endpoints working')
       await fetcher.close()

   asyncio.run(test())
   "
   ```

5. **Document Issues** (15 min)
   - Screenshot dashboard
   - Note any bugs or missing features
   - Update planning doc

6. **Celebrate** (10 min)
   - We built a working dashboard in 2 days!
   - Take a break
   - Plan next steps with confidence

**Success Criteria:**
- [ ] Dashboard launches without errors
- [ ] All 4 panels display data
- [ ] No Python exceptions
- [ ] Response times < 500ms
- [ ] Visual layout looks good

---

### Phase 1: Quick Wins (5-8 hours total)

**Goal:** Make dashboard actionable and delightful

#### Quick Win 1: Interactive Controls (2-3 hours)

**Add to dopemux_dashboard.py:**
```python
class DopemuxDashboard(App):
    BINDINGS = [
        ("b", "force_break", "Take Break"),
        ("f", "toggle_focus", "Focus Mode"),
        ("r", "refresh", "Refresh Now"),
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def action_force_break(self):
        """Trigger break timer"""
        # Call ADHD Engine break endpoint
        asyncio.create_task(self.trigger_break())
        self.notify("Break timer started! ☕")

    def action_toggle_focus(self):
        """Toggle focus mode"""
        self.focus_mode = not self.focus_mode
        status = "ON" if self.focus_mode else "OFF"
        self.notify(f"Focus mode {status} 🎯")
```

**Features:**
- Press `b` to force a break
- Press `f` to toggle focus mode (dim distractions)
- Press `r` to refresh all panels
- Press `?` to show keyboard shortcuts

**Acceptance Criteria:**
- [ ] All keybindings work
- [ ] Notifications appear
- [ ] Break endpoint called successfully
- [ ] No crashes

#### Quick Win 2: Theme Switcher (2-3 hours)

**Add theme support:**
```python
THEMES = {
    "mocha": {
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "accent": "#89b4fa",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
    },
    "nord": {
        "background": "#2e3440",
        "foreground": "#d8dee9",
        "accent": "#88c0d0",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "error": "#bf616a",
    },
    "dracula": {
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "accent": "#bd93f9",
        "success": "#50fa7b",
        "warning": "#f1fa8c",
        "error": "#ff5555",
    },
}

# Press 't' to cycle themes
BINDINGS.append(("t", "cycle_theme", "Change Theme"))
```

**Acceptance Criteria:**
- [ ] 3 themes available
- [ ] Press `t` to cycle
- [ ] Theme persists in config file
- [ ] All panels update correctly

#### Quick Win 3: Keyboard Help Screen (1 hour)

**Add help popup:**
```python
def action_help(self):
    """Show keyboard shortcuts"""
    help_text = """
    ╔════════════════════════════════════╗
    ║   Dopemux Keyboard Shortcuts      ║
    ╠════════════════════════════════════╣
    ║  q        Quit dashboard           ║
    ║  r        Refresh all panels       ║
    ║  b        Take a break now         ║
    ║  f        Toggle focus mode        ║
    ║  t        Change theme             ║
    ║  ?        Show this help           ║
    ╠════════════════════════════════════╣
    ║  Tab      Next panel               ║
    ║  1-4      Jump to panel            ║
    ║  Enter    Expand panel             ║
    ║  Esc      Collapse panel           ║
    ╚════════════════════════════════════╝
    """
    self.push_screen(HelpScreen(help_text))
```

**Acceptance Criteria:**
- [ ] Press `?` shows help
- [ ] Help screen looks good
- [ ] Esc closes help
- [ ] All shortcuts documented

#### Quick Win 4: Desktop Notifications (2-3 hours)

**macOS notifications via osascript:**
```python
import subprocess

async def send_notification(title: str, message: str):
    """Send macOS notification"""
    script = f'''
    display notification "{message}"
    with title "{title}"
    sound name "Glass"
    '''
    subprocess.run(['osascript', '-e', script])

# Use it:
await send_notification("Dopemux", "Time for a break! ☕")
await send_notification("Dopemux", "High cognitive load detected 🧠")
await send_notification("Dopemux", "Great focus session! 🎯")
```

**Triggers:**
- Break timer expires
- Cognitive load > 80% for 10 min
- Flow state achieved
- Service goes down

**Acceptance Criteria:**
- [ ] Notifications appear on macOS
- [ ] Not too frequent (max 1 per 5 min)
- [ ] Can be disabled in config
- [ ] Sound is subtle

**Total Phase 1 Time:** 5-8 hours
**Total Phase 1 Value:** Dashboard becomes actionable and delightful

---

### Phase 2: Real Data Integration (3-4 hours)

**Goal:** 100% real data, no mocks

#### Task 1: Fix ConPort PostgreSQL (1-2 hours)

**Current Issue:**
```python
# asyncpg connection fails with "unexpected connection_lost()"
# Likely SSL/network config mismatch
```

**Solutions to Try:**
```python
# Option 1: Disable SSL
pool = await asyncpg.create_pool(
    **DB_CONFIG,
    ssl=False  # Try this first
)

# Option 2: Use unix socket instead
pool = await asyncpg.create_pool(
    host='/var/run/postgresql',  # Unix socket
    port=5432,
    ...
)

# Option 3: Use psycopg2 instead
import psycopg2
conn = psycopg2.connect(...)  # This worked in testing!
```

**Acceptance Criteria:**
- [ ] ConPort connects to PostgreSQL
- [ ] Real decisions displayed (not mock)
- [ ] Graph stats from real database
- [ ] Source field shows "database"

#### Task 2: Wire Serena Detections (1-2 hours)

**Current State:**
- MetricsAggregator loaded ✅
- Mock data being used ⏳
- Real detectors not running ❌

**Solution:**
```python
# In http_server.py
from git_detector import GitDetector
from pattern_learner import PatternLearner

detector = GitDetector(workspace_path)
learner = PatternLearner()

async def get_real_detections():
    """Get real detection results"""
    results = await detector.detect_untracked_work()
    metrics = aggregator.aggregate_detections(results)
    return metrics
```

**Acceptance Criteria:**
- [ ] Real git detection running
- [ ] Real patterns learned
- [ ] Source field shows "real"
- [ ] Detections update every 5 min

---

### Phase 3: Advanced Features (2-3 days)

**Goal:** Professional-grade dashboard

From `tmux-dashboard-sprint-plan.md` Week 1:

#### Feature 1: Enhanced Sparklines (Day 1-2)
- Fetch Prometheus historical data
- Generate sparklines from time series
- Show trends in panels

#### Feature 2: Keyboard Navigation (Day 3-4)
- Tab between panels
- 1-4 keys jump to panel
- Enter expands, Esc collapses
- Arrow keys scroll within panel

#### Feature 3: Drill-Down Views (Day 5)
- Press `d` on any panel for details
- Popup with full data
- Scrollable tables
- Copy to clipboard

---

## 🎯 EXECUTION ROADMAP

### Week 1: Foundation & Quick Wins

**Day 1 (Today - Oct 29):**
```
Morning:   Phase 0 - Foundation Validation (1 hr)
           ├── Restart all services
           ├── Run dashboard
           └── Verify everything works

Afternoon: Quick Win 1 - Interactive Controls (2-3 hrs)
           ├── Add keybindings
           ├── Implement break trigger
           └── Test all actions

Evening:   Quick Win 2 - Theme Switcher (2-3 hrs)
           ├── Define 3 themes
           ├── Add theme cycling
           └── Persist config
```

**Day 2 (Oct 30):**
```
Morning:   Quick Win 3 - Help Screen (1 hr)
           └── Keyboard shortcuts popup

Afternoon: Quick Win 4 - Desktop Notifications (2-3 hrs)
           ├── macOS osascript
           ├── Smart triggers
           └── Config options

Evening:   Polish & Test (2 hrs)
           ├── Bug fixes
           ├── Screenshots
           └── Documentation
```

**Day 3 (Oct 31):**
```
Morning:   Real Data Task 1 - ConPort PostgreSQL (2 hrs)
           └── Fix SSL connection

Afternoon: Real Data Task 2 - Serena Detections (2 hrs)
           └── Wire real git detector

Evening:   Integration Testing (2 hrs)
           └── Verify 100% real data
```

**Day 4-5 (Nov 1-2):**
```
Advanced Features (Sprint Plan Week 1):
├── Enhanced sparklines
├── Keyboard navigation
└── Panel drill-downs
```

### Success Metrics

**Phase 0 (Foundation):**
- Dashboard runs without errors
- All panels show data
- Response times acceptable

**Phase 1 (Quick Wins):**
- 5 interactive controls working
- 3 themes available
- Help screen complete
- Notifications functioning

**Phase 2 (Real Data):**
- ConPort: 100% real database
- Serena: Real detections
- Source fields all "real"

**Phase 3 (Advanced):**
- Sparklines from Prometheus
- Full keyboard navigation
- Drill-down views working

---

## 💡 ZEN INSIGHTS

### Insight 1: We Built But Didn't Validate
**Observation:** 2 days of development, dashboard never actually run
**Implication:** Foundation testing is critical before building more
**Action:** Phase 0 (validation) must come first

### Insight 2: Quick Wins Create Momentum
**Observation:** 150+ features identified, can't do all
**Implication:** Small, high-impact features build confidence
**Action:** Focus on 4-5 quick wins before advanced features

### Insight 3: Real Data Matters
**Observation:** Mock data is acceptable for MVP, but...
**Implication:** Users want to see their actual patterns
**Action:** Prioritize real data integration

### Insight 4: ADHD-First Still Applies
**Observation:** Planning docs emphasize progressive disclosure
**Implication:** Don't overwhelm with all features at once
**Action:** Ship incrementally, celebrate small wins

### Insight 5: Documentation is Investment
**Observation:** 6 planning docs created (49KB)
**Implication:** Clear thinking prevents wasted effort
**Action:** Keep documenting decisions and rationale

---

## 🚀 IMMEDIATE NEXT ACTIONS

### Action 1: Choose a Path

**Option A: Foundation First (Recommended)**
```
Time: 1 hour today
Value: Confidence in what we built
Risk: None
Output: Working dashboard demo
```

**Option B: Quick Wins First**
```
Time: 5-8 hours (1-2 days)
Value: Actionable dashboard
Risk: Building on untested foundation
Output: Interactive, delightful dashboard
```

**Option C: Advanced Features**
```
Time: 2-3 days
Value: Professional polish
Risk: Highest (untested foundation + complex features)
Output: Full sprint plan Week 1 complete
```

**🧘 Recommendation:** A → B → C (progressive confidence building)

---

### Action 2: Set Success Criteria

**Minimum Viable Dashboard (Today):**
- [ ] Launches without errors
- [ ] Shows ADHD metrics (energy, attention, cognitive)
- [ ] Shows service health (3/3 services)
- [ ] Shows patterns (even if mock)
- [ ] Refreshes automatically

**Delightful Dashboard (Week 1):**
- [ ] Minimum Viable ✅ +
- [ ] Interactive controls (5+ keybindings)
- [ ] Theme switcher (3+ themes)
- [ ] Help screen
- [ ] Desktop notifications

**Professional Dashboard (Week 2):**
- [ ] Delightful ✅ +
- [ ] 100% real data (no mocks)
- [ ] Enhanced sparklines
- [ ] Full keyboard navigation
- [ ] Drill-down views

---

## 📝 DECISION RECORD

**Decision:** Start with Phase 0 (Foundation Validation)

**Rationale:**
1. We've built a lot (510 lines, 3 services, 17 endpoints)
2. We haven't actually run the dashboard yet
3. Testing foundation gives confidence for next steps
4. Only 1 hour investment, high value
5. Find bugs early before building more features

**Alternative Considered:** Jump to Quick Wins
- Would be exciting and productive
- But risky without validation
- Could waste effort if foundation broken

**Next Decision Point:** After Phase 0 validation
- If dashboard works perfectly → Quick Wins (Phase 1)
- If bugs found → Fix bugs, then Quick Wins
- If major issues → Reassess architecture

**Expected Outcome:** Working dashboard in 1 hour, plan Phase 1

---

**Status:** ✅ **RESEARCH COMPLETE**
**Next Action:** Execute Phase 0 (Foundation Validation)
**Confidence:** HIGH (clear path forward)
**Philosophy:** Test first, build confidently, ship incrementally

🎯 **Ready to execute with clarity!**
