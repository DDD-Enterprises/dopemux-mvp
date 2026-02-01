---
id: MONITORING-DESIGN-SPRINT-SUMMARY
title: Monitoring Design Sprint Summary
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# 🎯 Monitoring Code Design Sprint - Quick Reference

**Created:** 2025-10-28
**Purpose:** Design sprint documentation for ADHD monitoring dashboard
**Full Doc:** See MONITORING-DESIGN-SPRINT-GUIDE.md (1,500+ lines)

---

## 📋 Quick Overview

### What We Have

**Production Ready:**
- ✅ Bash 3-pane dashboard (~25 KB, 3 scripts)
- ✅ Typer/Rich dashboard (15 KB Python)
- ✅ Full orchestrator (4-pane tmux layout)
- ✅ Minimal orchestrator (2-pane tmux)
- ✅ 26 ADHD metrics tracked
- ✅ Real-time cognitive state monitoring

**Designed, Not Implemented:**
- 📐 Compact dashboard (templates created)
- 📐 Serena v2 integration (paths identified)
- 📐 Leantime API integration (spec complete)
- 📐 ConPort API integration (endpoints mapped)

### File Inventory

```
scripts/
├── dashboard-pane1-focus.sh              (8.1 KB) ✅
├── dashboard-pane2-tasks.sh              (8.3 KB) ✅
├── dashboard-pane3-system.sh             (8.8 KB) ✅
├── launch-adhd-dashboard.sh              (1.8 KB) ✅
├── dopemux-dashboard.py                  (15 KB)  ✅
├── dopemux-compact-dashboard.py          (NOT SAVED) ❌
├── dashboard_integrations.py             (NOT SAVED) ❌
├── launch-dopemux-orchestrator.sh        (9.0 KB) ✅
├── launch-dopemux-minimal.sh             (1.1 KB) ✅
└── setup-dopemux-top-pane.sh             (1.1 KB) ✅

Documentation:
├── ORCHESTRATOR-INTEGRATION-COMPLETE.md   (10 KB) ✅
├── COMPACT-DASHBOARD-COMPLETE.md          (8.3 KB) ✅
├── FINAL-COMPLETE-SESSION-SUMMARY.md      (12 KB) ✅
└── MONITORING-DESIGN-SPRINT-GUIDE.md      (Full spec)
```

---

## 🎯 5-Sprint Roadmap

### Sprint 1: Foundation (2-3 days, 16-24 hours)

**Goal:** Fix technical debt, save all code

**Tasks:**
1. Save compact dashboard script to disk ❌
2. Save dashboard_integrations.py ❌
3. Add error handling to bash scripts ❌
4. Create config file system ❌
5. Add logging to Python dashboards ❌
6. Write unit tests ❌

**Acceptance:**
- All designed code saved
- Bash scripts handle API failures
- Config externalized
- Test coverage >70%

---

### Sprint 2: Serena Integration (3-4 days, 24-32 hours)

**Goal:** Wire up untracked work detection

**Tasks:**
1. Import abandonment_tracker.py
2. Call from SerenaIntegration class
3. Test git detection
4. Add to compact dashboard line 2
5. Wire up ConPort storage (optional)

**Acceptance:**
- Dashboard shows real untracked work
- Abandonment scores working
- Stale branch detection live
- Days idle displayed

---

### Sprint 3: Leantime Integration (2-3 days, 16-24 hours)

**Goal:** Connect to Leantime API

**Tasks:**
1. Get API credentials
2. Implement LeantimeIntegration
3. Test GET /tasks
4. Add to compact dashboard line 3
5. Handle overdue warnings

**Acceptance:**
- In-progress + todo counts shown
- Task names displayed
- Overdue tasks highlighted
- API failures handled

---

### Sprint 4: ConPort Integration (2 days, 12-16 hours)

**Goal:** Add context tracking

**Tasks:**
1. Implement ConPortIntegration
2. Test GET /context/current
3. Add to dashboard
4. Integrate with health score

**Acceptance:**
- Context name shown
- Switches counted
- Health penalty working

---

### Sprint 5: Polish (3-4 days, 24-32 hours)

**Goal:** Production polish

**Tasks:**
1. Click handlers (Rich mouse)
2. Historical view
3. Export metrics (JSON/CSV)
4. Custom themes
5. Performance optimization
6. Documentation update

**Acceptance:**
- <1% CPU idle
- <20 MB memory
- No memory leaks
- Complete docs

---

## ⚠️  Critical Technical Debt

### 1. Hardcoded URLs

**Current:**
```bash
ADHD_ENGINE="http://localhost:8095"  # In every file!
```

**Fix:**
```bash
# ~/.dopemux/config.sh
export DOPEMUX_ADHD_ENGINE="http://localhost:8095"
export DOPEMUX_ACTIVITY_CAPTURE="http://localhost:8096"
```

**Effort:** 2-4 hours

---

### 2. No Error Handling (Bash)

**Current:**
```bash
energy=$(curl -s http://localhost:8095/... | jq -r '.energy_level')
# Crashes if service down or jq missing!
```

**Fix:**
```bash
fetch_energy() {
    command -v curl &>/dev/null || { echo "unknown"; return 1; }
    local response=$(curl -s --max-time 2 "$url" 2>/dev/null)
    echo "$response" | jq -r '.energy_level // "unknown"' 2>/dev/null || echo "unknown"
}
```

**Effort:** 4-6 hours

---

### 3. Compact Dashboard Not Saved

**Current:** Templates created in session, not saved to disk

**Fix:** Save these files:
- `scripts/dopemux-compact-dashboard.py`
- `scripts/dashboard_integrations.py`

**Effort:** 1 hour

---

### 4. No Logging

**Current:** Silent failures, hard to debug

**Fix:**
```python
import logging

logging.basicConfig(
    filename="/tmp/dopemux-dashboard.log",
    level=logging.INFO
)

logger = logging.getLogger(__name__)
logger.info("Dashboard started")
```

**Effort:** 2-3 hours

---

## 🔌 API Integration Points

### ADHD Engine (Working ✅)

```bash
# Endpoint
GET http://localhost:8095/api/v1/energy-level/hue

# Response
{
  "energy_level": "medium",
  "timestamp": "2025-10-28T06:30:00Z"
}

# Energy levels
hyperfocus → high → medium → low → very_low
```

---

### Activity Capture (Working ✅)

```bash
# Endpoint
GET http://localhost:8096/metrics

# Response
{
  "current_session_duration_minutes": 23,
  "current_session_interruptions": 2,
  "total_focus_time_today_minutes": 87
}
```

---

### Serena v2 (To Implement 📐)

```python
# Import
from services.serena.v2.abandonment_tracker import AbandonmentTracker

# Use
tracker = AbandonmentTracker(workspace_id="dopemux-mvp")
score = tracker.calculate_abandonment_score(git_detection)

# Returns
{
  "score": 0.21,
  "severity": "stale",
  "is_abandoned": False,
  "days_idle": 3
}
```

---

### Leantime (To Implement 📐)

```python
# Endpoint
GET http://localhost:8080/api/tasks?status=in_progress,todo
Authorization: Bearer {api_key}

# Response
{
  "tasks": [
    {
      "id": 123,
      "title": "ADHD Dashboard",
      "status": "in_progress",
      "priority": "high"
    }
  ]
}
```

---

### ConPort (To Implement 📐)

```python
# Endpoint
GET http://localhost:8091/api/context/current

# Response
{
  "context_id": "ctx_123",
  "name": "ADHD Dashboard Development",
  "started_at": "2025-10-28T02:00:00Z",
  "duration_minutes": 240
}
```

---

## 📊 26 ADHD Metrics

### Cognitive (4)
1. Energy level (5 states)
2. Attention state (4 states)
3. Health score (0-100)
4. Peak hour detection

### Session (3)
5. Duration (minutes)
6. Interruptions (count)
7. Recovery cost (23 min × count)

### Work Context (7)
8. Git branch
9. Git project
10. Modified files
11. Untracked files
12. Stale branches
13. Unpushed commits
14. Workspace complexity

### Tasks (3)
15. In-progress count
16. Todo count
17. Overdue warnings

### System (9)
18-26. Services, Docker, CPU, Memory, etc.

---

## 🎨 Design Patterns

### 1. Presentation Layer
UI components only render, no business logic

### 2. Data Collector
Centralized fetching with error handling

### 3. Graceful Degradation
Show partial data if services fail

### 4. Coordinator
Orchestrators manage layout, not data

### 5. Configuration Over Hardcoding
Externalize all URLs and settings

---

## 💡 Enhancement Opportunities

### 1. Click Handlers (8-12 hours)
Make dashboard interactive with Rich mouse support

### 2. Historical Trends (12-16 hours)
Show patterns over time, momentum tracking

### 3. Export Metrics (4-6 hours)
JSON/CSV export for external analysis

### 4. Custom Themes (6-8 hours)
User-configurable colors, accessibility

### 5. Desktop Notifications (4-6 hours)
Proactive ADHD support, break reminders

---

## 📝 Next Steps for Sprint Planning

1. **Review this doc** - Understand current state
2. **Prioritize sprints** - Which integrations first?
3. **Set up tracking** - Leantime tasks for each sprint
4. **Reserve time** - Block calendar for sprint work
5. **Prepare environment** - Install dependencies, test APIs

**Estimated Total:** 88-128 hours (2-3 weeks)

---

**Built for ADHD developers, by ADHD developers** 🧠⚡

For full details, see: **MONITORING-DESIGN-SPRINT-GUIDE.md** (1,500+ lines)
