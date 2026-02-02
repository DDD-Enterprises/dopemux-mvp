---
id: adhd-features-user-guide
title: Adhd Features User Guide
type: how-to
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# ADHD Features User Guide

**Version**: 2.0
**Last Updated**: 2026-02-02
**For**: Dopemux MVP Users with ADHD

> **Complete guide to all 15 ADHD accommodation features**

## Overview

Dopemux provides **15 ADHD accommodation features** working together to support your cognitive needs throughout the development workflow.

**Philosophy**: Consent-first, gentle, transparent, empowering

---

## Quick Reference

| Feature | When to Use | Key Benefit |
|---------|-------------|-------------|
| **Core ML Features** |||
| Energy Predictor | Start of session | Know optimal focus times |
| Context Preserver | Before breaks | Resume without mental load |
| Attention Calibrator | Ongoing | Personalized focus detection |
| Correlation Engine | Weekly | Discover hidden patterns |
| Voice Assistant | Hands-free | Quick status checks |
| Mobile Push | Away from desk | Break reminders on phone |
| **Quick Wins** |||
| Overwhelm Detector | Feeling stuck | Emergency circuit breaker |
| Hyperfocus Guard | Deep work | Protect flow, prevent crashes |
| End-of-Day Ritual | Session close | Reduce tomorrow anxiety |
| Weekly Report | Friday | Data-driven improvements |
| Procrastination Help | Avoiding tasks | Gentle nudge forward |
| **P1 Priority Features** |||
| Task Decomposition | Large tasks | Break into micro-tasks |
| Medication Tracker | Daily dosing | Track effectiveness |
| Social Battery | Meetings/events | Prevent social burnout |
| Working Memory | Fleeting thoughts | Capture ideas instantly |

---

## Core Features (Phase 3)

### 1. ML Energy Pattern Learning

Learns when you have high/medium/low energy and predicts optimal work times.

**Usage**:
```bash
curl http://localhost:8095/api/v1/energy-prediction
curl -X POST http://localhost:8095/api/v1/energy-prediction/train
```

**Features**: 9-factor model, confidence scoring, recommendations

**Tips**: Collect 2+ weeks data, retrain weekly

### 2. Context Preservation

Saves mental model before breaks for effortless resume.

**Saved**: Files, cursors, symbols, git status, decisions, mental model

**Example restoration**:
```
📌 Welcome back! Here's where you were:
Files: engine.py (line 145), test_engine.py (line 67)
You were: Implementing attention detection
Next: Add tests for edge cases
```

### 3. Attention Calibration

Learns YOUR attention patterns through feedback.

**Feedback**:
```bash
curl -X POST http://localhost:8095/api/v1/attention/feedback \
  -d '{"predicted": "focused", "actual": "scattered"}'
```

**Personalizes**: Focus confidence, scatter threshold, hyperfocus duration

### 4. Correlation Engine

Finds hidden patterns across all ADHD services.

**Insights**:
- "High energy (9-11 AM) + complex tasks = 2.3x commits"
- "3+ switches in 15 min predicts scattered attention"
- "Breaks every 25 min = 40% higher output"

### 5. Voice Assistant

Hands-free queries via natural language (macOS initially).

**Commands**: "How's my focus?", "What's my energy?", "Do I need a break?"

### 6. Mobile Push Notifications

Break reminders on your phone (Ntfy free, Pushover paid).

**Setup**:
```bash
export MOBILE_PUSH_PROVIDER=ntfy
export MOBILE_PUSH_TOPIC=dopemux-yourusername
```

---

## Quick Win Features

### 7. Overwhelm Circuit Breaker

Detects overwhelm and provides emergency interventions.

**Signals**: Rapid switching (>10/15min), no progress (>45min), energy mismatch, break resistance, attention overwhelmed

**Interventions**:
- Mild: Check-in
- Moderate: Task simplification
- Severe: 15-min forced break
- Critical: Immediate intervention

### 8. Hyperfocus Protection

Protects deep work while preventing crashes.

**Phases**: Building (15-30min) → Active (30-90min) → Extended (90-120min) → Critical (120+min) → Crashed

**Protections**: Auto-save every 5min, block notifications, gentle reminders, crash detection

### 9. End-of-Day Wind Down

7-step ritual: stats → wins → thoughts → context → tasks → recovery → message

**Example**:
```
🎉 Wins: 4 tasks, 7 commits, 3.2h focused
📋 Tomorrow: 1) Auth refactor 2) JWT decision 3) PR review
💙 "You worked hard. Your brain needs rest."
```

### 10. Weekly Pattern Report

Friday analysis of focus windows, energy, breaks, trends.

**Recommendations**:
- "Schedule important work 09:00-11:00 (best window)"
- "Break acceptance dropped - try more breaks"
- "Low energy at 14:00 - schedule simple tasks"

### 11. Procrastination Detection

Detects 5 patterns with gentle interventions.

**Patterns**: Research rabbit holes, productive procrastination, task switching, perfectionism, decision paralysis

**Micro-tasks** (pattern-specific):
- Research → "Write 3 bullet points" (3min)
- Productive → "Work on priority 5 min" (5min)
- Switching → "Pick ONE, close others" (2min)
- Perfectionism → "Commit as 'WIP'" (2min)
- Decision → "Flip coin, pick one" (1min)

**Gamification**: Streaks, badges at 5/25/100 tasks

---

## API Reference

Base: `http://localhost:8095/api/v1/`

```
# Energy
GET  /energy-prediction
POST /energy-prediction/train

# Context
POST /context/capture
GET  /context/restore

# Attention
POST /attention/feedback
GET  /attention/calibration

# Insights
GET  /correlations/insights
GET  /correlations/energy-complexity

# Voice & Notifications
POST /voice/command
POST /notifications/test

# Protection
GET  /overwhelm/status
POST /overwhelm/reset
GET  /hyperfocus/status
GET  /hyperfocus/stats

# Rituals
POST /wind-down
GET  /weekly-report

# Procrastination
GET  /procrastination/status
POST /procrastination/complete
```

---

## P1 Priority Features

### 12. Task Decomposition Assistant

Breaks down large, overwhelming tasks into ADHD-friendly micro-tasks (5-15 minutes each).

**When to Use**: Task feels too big, paralysis setting in, unclear where to start

**API Usage**:
```bash
# Analyze task complexity
curl -X POST http://localhost:8095/api/v1/task-decomposition/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Migrate authentication to OAuth2",
    "estimated_hours": 4.0,
    "current_energy": "medium"
  }'

# Response:
# {
#   "complexity_score": 0.85,
#   "complexity_level": "challenging",
#   "decomposition_recommended": true,
#   "reasoning": "High complexity + multi-hour task = overwhelm risk"
# }

# Decompose task
curl -X POST http://localhost:8095/api/v1/task-decomposition/decompose \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-123",
    "description": "Migrate authentication to OAuth2",
    "estimated_hours": 4.0
  }'

# Returns 6-8 micro-tasks with energy levels and ordering
```

**Features**:
- **Complexity Scoring**: 6 levels (trivial → epic), 0.0-1.0 score
- **3 Decomposition Patterns**: Implementation, refactoring, bug fix
- **Energy-Aware Ordering**: High-energy tasks first, admin tasks last
- **Micro-Task Sizing**: Each subtask 5-15 minutes (one Pomodoro)
- **ConPort Integration**: Persists decomposition for future reference

**Tips**:
- Accept decomposition suggestions - they work!
- Start with first subtask immediately (momentum!)
- Mark subtasks complete as you go (dopamine boost)
- Use voice assistant for status: "How many subtasks left?"

---

### 13. Medication Effectiveness Tracker

Track medication timing, dosing, and effectiveness for ADHD medications.

**When to Use**: Daily dosing, doctor appointments, medication optimization

**API Usage**:
```bash
# Log medication dose
curl -X POST http://localhost:8095/api/v1/medication/dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication_name": "Adderall XR",
    "dosage_mg": 20.0,
    "medication_type": "stimulant_long",
    "notes": "With breakfast"
  }'

# Log side effect
curl -X POST http://localhost:8095/api/v1/medication/side-effect \
  -H "Content-Type: application/json" \
  -d '{
    "effect": "mild_headache",
    "severity": "mild",
    "notes": "Afternoon, may be dehydration"
  }'

# Generate doctor report
curl http://localhost:8095/api/v1/medication/report?days=30

# Response:
# {
#   "period": "2026-01-03 to 2026-02-02",
#   "doses": 28,
#   "adherence_rate": 0.93,
#   "peak_effectiveness_time": "9:30 AM - 2:00 PM",
#   "side_effects_by_type": {...},
#   "recommendations": [
#     "Consistent peak performance 9:30 AM - 2:00 PM",
#     "Consider scheduling complex tasks in this window"
#   ]
# }
```

**Medication Types**:
- **stimulant_short**: IR Adderall, Ritalin (4-6h duration)
- **stimulant_long**: XR Adderall, Concerta, Vyvanse (8-12h duration)
- **non_stimulant**: Strattera, Intuniv (24h duration)
- **combination**: Multiple meds

**Features**:
- **Dose Logging**: Time, amount, medication type
- **Side Effect Tracking**: Severity levels (mild, moderate, severe)
- **Effectiveness Correlation**: Links medication timing to cognitive metrics
- **Doctor-Ready Reports**: Formatted for medical appointments
- **Adherence Tracking**: % doses taken on schedule
- **Peak Time Detection**: When medication is most effective

**Tips**:
- Log doses immediately (working memory!)
- Note any unusual side effects right away
- Generate report before doctor appointments
- Use insights to optimize task scheduling

---

### 14. Social Battery Monitor

Tracks social interaction drain and provides recovery recommendations (ADHD masking awareness).

**When to Use**: Before/after meetings, event planning, preventing social burnout

**API Usage**:
```bash
# Log social interaction
curl -X POST http://localhost:8095/api/v1/social-battery/interaction \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_type": "meeting_large",
    "duration_minutes": 60,
    "masking_level": "high",
    "participants_count": 15,
    "description": "All-hands meeting"
  }'

# Response:
# {
#   "drain_amount": 150.0,
#   "new_battery_level": 50.0,
#   "state": "low",
#   "recovery_recommended": true
# }

# Check current state
curl http://localhost:8095/api/v1/social-battery/status

# Predict calendar impact
curl -X POST http://localhost:8095/api/v1/social-battery/predict \
  -H "Content-Type: application/json" \
  -d '{
    "upcoming_events": [
      {"type": "meeting_small", "duration": 30, "masking": "medium"},
      {"type": "presentation", "duration": 45, "masking": "high"},
      {"type": "one_on_one", "duration": 30, "masking": "low"}
    ]
  }'

# Response:
# {
#   "current_level": 75.0,
#   "predicted_end_of_day_level": 25.0,
#   "recovery_needed": true,
#   "recommendation": "Schedule 30min recharge after presentation"
# }
```

**Interaction Types & Drain Rates**:
- **meeting_large** (10+ people): 2.5 pts/min (high drain)
- **meeting_small** (3-9 people): 1.5 pts/min (medium drain)
- **presentation** (any size): 3.0 pts/min (highest drain)
- **one_on_one**: 1.0 pts/min (low drain)
- **async_comm** (email/Slack): 0.3 pts/min (minimal drain)
- **casual** (water cooler): 0.5 pts/min (minimal drain)
- **deep_work** (solo coding): -0.5 pts/min (recharge!)

**Masking Levels** (multiply drain):
- **none** (1.0x): Being authentic
- **low** (1.2x): Minor filtering
- **medium** (1.5x): Professional mask
- **high** (2.0x): Heavy masking (executive meetings)

**Battery States**:
- **critical** (<20%): Immediate recovery needed
- **low** (20-40%): Recovery recommended
- **medium** (40-70%): Sustainable
- **optimal** (>70%): Fully charged

**Features**:
- **Real-Time Tracking**: Updates after each interaction
- **Calendar Integration**: Predict end-of-day battery level
- **Recovery Recommendations**: Immediate, scheduled, preventive
- **Recharge Session Logging**: Track what actually helps you recover
- **Weekly Patterns**: "Wednesdays drain you most" insights

**Recovery Recommendations**:
- **Immediate**: "Take 20min solo time NOW"
- **Scheduled**: "Block 30min after 3pm presentation"
- **Preventive**: "Schedule deep work block after meetings"

**Tips**:
- Log interactions honestly (masking level matters!)
- Use predictions when planning your week
- Trust low battery warnings - rest before crash
- Deep work time = recharge time
- Block recovery time after draining events

---

### 15. Working Memory Support

Ultra-fast thought capture and context tracking for ADHD working memory challenges.

**When to Use**: Fleeting ideas, before interruptions, context switches, resuming work

**API Usage**:
```bash
# Quick capture (< 2 seconds!)
curl -X POST http://localhost:8095/api/v1/working-memory/capture \
  -H "Content-Type: application/json" \
  -d '{
    "content": "TODO: Fix bug in auth.py line 156"
  }'

# Auto-detects type (TODO), captures current context
# Response:
# {
#   "thought_id": "TH-1",
#   "type": "todo",
#   "current_file": "services/adhd_engine/engine.py",
#   "current_line": 42
# }

# Drop breadcrumb before interruption
curl -X POST http://localhost:8095/api/v1/working-memory/breadcrumb \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Implementing OAuth client",
    "file_path": "auth.py",
    "line_number": 156,
    "goal": "Get OAuth working for production",
    "action": "implementing"
  }'

# Detect interruption (meeting notification)
curl -X POST http://localhost:8095/api/v1/working-memory/interruption \
  -H "Content-Type: application/json" \
  -d '{
    "interruption_type": "meeting",
    "source": "calendar"
  }'

# Later: Restore context
curl -X POST http://localhost:8095/api/v1/working-memory/restore

# Response:
# {
#   "description": "You were implementing OAuth client in auth.py at line 156",
#   "goal": "Get OAuth working for production",
#   "hints": [
#     "Open auth.py",
#     "Go to line 156",
#     "Find function setup_oauth_client",
#     "You were implementing"
#   ]
# }

# Get active thoughts
curl http://localhost:8095/api/v1/working-memory/thoughts?active_only=true

# Get forgotten context reminder
curl http://localhost:8095/api/v1/working-memory/reminder
```

**Thought Types** (auto-detected):
- **idea**: Sudden insights
- **todo**: Tasks to do later
- **question**: Things to research
- **reminder**: Don't forget X
- **context**: Current work state
- **interruption**: Interruption notes

**Features**:
- **< 2 Second Capture**: Just type content, auto-detects type
- **Auto-Context**: Captures current file/line/task automatically
- **Breadcrumbs**: Save where you are before interruptions
- **Interruption Detection**: Auto-save context when interrupted
- **Context Restoration**: "You were implementing X at line 156"
- **Forgotten Context Reminders**: "You have 8 active thoughts"
- **Priority Filtering**: urgent, high, normal, low
- **ConPort Integration**: Persists across sessions

**Context Types**:
- **file**: Current file being edited
- **task**: Current task
- **goal**: Current objective
- **code_location**: Specific code location
- **decision**: Decision being made
- **problem**: Problem being solved

**Tips**:
- Capture thoughts immediately (they vanish fast!)
- Drop breadcrumb before known interruptions (meetings)
- Use voice for capture: "Hey ADHD engine, capture thought: ..."
- Mark thoughts complete as you do them
- Check reminders when feeling lost
- Restore context after every break

---

## Configuration

```bash
# Core
ENERGY_PREDICTOR_ENABLED=true
END_OF_DAY_HOUR=18  # 6 PM

# Hyperfocus
HYPERFOCUS_AUTO_SAVE_INTERVAL=5    # minutes
HYPERFOCUS_GENTLE_REMINDER=90      # minutes
HYPERFOCUS_CRITICAL_THRESHOLD=120  # minutes

# Mobile
MOBILE_PUSH_PROVIDER=ntfy
MOBILE_PUSH_TOPIC=dopemux-yourusername

# Procrastination
PROCRASTINATION_RESEARCH_THRESHOLD=30   # minutes
PROCRASTINATION_SWITCHING_THRESHOLD=5   # switches
PROCRASTINATION_POLISH_THRESHOLD=45     # minutes

# Task Decomposition
TASK_DECOMPOSITION_AUTO_DETECT=true
TASK_DECOMPOSITION_THRESHOLD_HOURS=2.0
TASK_DECOMPOSITION_COMPLEXITY_THRESHOLD=0.6

# Medication Tracker
MEDICATION_TRACKER_REMINDER_ENABLED=true
MEDICATION_TRACKER_DAILY_REMINDER_TIME=08:00

# Social Battery
SOCIAL_BATTERY_CRITICAL_THRESHOLD=20    # %
SOCIAL_BATTERY_LOW_THRESHOLD=40         # %
SOCIAL_BATTERY_CALENDAR_INTEGRATION=true

# Working Memory
WORKING_MEMORY_BREADCRUMB_INTERVAL=15   # minutes
WORKING_MEMORY_INTERRUPTION_THRESHOLD=5 # minutes
WORKING_MEMORY_AUTO_REMINDER=true
```

---

## Quick Start

1. ✅ Enable energy predictor (2 weeks to learn)
2. ✅ Setup mobile push (ntfy easiest)
3. ✅ Configure end-of-day hour
4. ✅ Try voice: "How's my focus?"
5. ✅ Complete first micro-task when procrastinating
6. ✅ Accept breaks for calibration
7. ✅ Run end-of-day ritual tonight
8. ✅ Check weekly report Friday
9. ✅ Provide attention feedback when off

---

## Privacy

**Collected**: Energy levels, attention states, task switches
**NOT collected**: Code contents, personal info
**Storage**: Redis (ephemeral), ConPort (persistent), local ML
**Control**: All opt-in, export/delete anytime

---

**Full documentation**: See individual feature files in `services/adhd_engine/` for technical details.

**Support**: GitHub issues with `adhd-features` tag

**Remember**: Give features 2-4 weeks to learn your patterns. Use what works, skip what doesn't. You're in control. 💙
