---
id: adhd-features-p2-design
title: Adhd Features P2 Design
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Adhd Features P2 Design (explanation) for dopemux documentation and developer
  workflows.
---
# P2 Priority ADHD Features - Design Document

**Version**: 1.0
**Date**: 2026-02-02
**Status**: Design Phase
**Estimated Total Effort**: 31-42 hours

## Overview

This document outlines **7 P2 priority features** for the ADHD Engine, building on the 15 already-implemented features. P2 features add deeper integrations, advanced analytics, and quality-of-life improvements.

**Design Principles**:
- Build on existing P1 foundation
- Leverage DopeconBridge, ConPort, Task Orchestrator integrations
- Maintain ADHD-optimized UX (consent-first, gentle, transparent)
- Prioritize features with measurable impact on ADHD challenges

---

## Feature Categories

### 🎯 Task Management (2 features, 12-16h)
### 📊 Analytics & Insights (2 features, 8-10h)
### 🔗 Integrations (2 features, 10-14h)
### 🎮 Motivation (1 feature, 4-6h)

---

## 1. Transition Coach (P2 - Medium Priority)

**Category**: Task Management
**Effort**: 4-6 hours
**Dependencies**: Working Memory Support, Context Preserver

### Problem Statement

ADHD users struggle with transitions between tasks, contexts, and work modes:
- **Context switching cost**: 15-30 minutes to fully switch mental models
- **Forgotten goals**: Original intent lost during transition
- **Anxiety**: "What if I forget where I was?"
- **Momentum loss**: Hard to restart after breaks

### Proposed Solution

A **Transition Coach** that actively manages context switches with structured protocols.

### Features

#### 1.1 Pre-Transition Protocol
Before switching tasks:
1. **Capture current state**: Auto-save files, cursor positions, mental model
1. **Quick summary**: "What were you working on?" (voice or text)
1. **Set intention**: "What will you work on next?"
1. **Estimate return time**: "When will you return to this?" (optional)

#### 1.2 Transition Types
Handle different transition patterns:
- **Break → Work**: Gentle ramp-up with context restoration
- **Work → Break**: Full state capture, permission to disconnect
- **Task A → Task B**: Structured handoff with breadcrumbs
- **Meeting → Deep Work**: Buffer time + context restoration
- **End of Day → Tomorrow**: Tomorrow prep checklist

#### 1.3 Post-Transition Support
When resuming work:
1. **Context restoration**: "You were implementing X at line 156"
1. **Goal reminder**: "Your goal was: Get OAuth working"
1. **Progress recap**: "You completed 3/6 subtasks"
1. **Next action**: "Start with: Write client registration endpoint"

#### 1.4 Transition Quality Metrics
Track transition success:
- Time to full context restoration
- Forgotten context incidents (per week)
- Successful returns to interrupted work
- User-reported transition quality

### API Design

```python
# services/adhd_engine/transition_coach.py

@dataclass
class Transition:
    transition_id: str
    transition_type: str  # "break", "task_switch", "meeting", "end_of_day"
    from_context: ContextBreadcrumb
    to_context: Optional[ContextBreadcrumb]
    initiated_at: datetime
    completed_at: Optional[datetime]
    quality_rating: Optional[int]  # 1-5 user rating

class TransitionCoach:
    """Manage context transitions with ADHD accommodations."""

    async def initiate_transition(
        self,
        transition_type: str,
        to_description: Optional[str] = None
    ) -> Transition:
        """
        Start a transition with structured protocol.

        Steps:
1. Capture current state (via WorkingMemorySupport)
1. Ask for quick summary (optional, low friction)
1. Set intention for next context
1. Generate transition ID
        """
        pass

    async def complete_transition(
        self,
        transition_id: str,
        quality_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete transition and restore context.

        Returns:
- Context summary
- Goal reminder
- Progress recap
- Suggested next action
        """
        pass

    async def suggest_transition_timing(
        self,
        from_context: str,
        to_context: str,
        calendar_events: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Suggest optimal transition timing.

        Factors:
- Current hyperfocus state
- Natural break points in work
- Upcoming calendar events
- Energy level trends
        """
        pass
```

### REST API Endpoints

```
POST   /api/v1/transitions/initiate
POST   /api/v1/transitions/{id}/complete
GET    /api/v1/transitions/{id}
GET    /api/v1/transitions/suggest-timing
GET    /api/v1/transitions/stats
```

### Integration Points

- **Working Memory Support**: Use breadcrumbs for context capture
- **Context Preserver**: Leverage existing context capture logic
- **Social Battery**: Check battery before accepting meetings
- **Calendar**: Detect upcoming transitions (meetings)
- **ConPort**: Persist transition history and quality ratings

### Success Metrics

- **Primary**: Time to context restoration (target: <3 minutes)
- **Secondary**: Forgotten context incidents (target: -50%)
- **Tertiary**: User-reported transition quality (target: >4/5 avg)

---

## 2. Sensory Overload Detection (P2 - Medium Priority)

**Category**: Safety & Protection
**Effort**: 5-7 hours
**Dependencies**: Overwhelm Detector, Attention Calibrator

### Problem Statement

ADHD often comes with sensory processing challenges:
- **Visual overload**: Too many windows, tabs, terminal panes
- **Notification fatigue**: Constant pings and alerts
- **Auditory distractions**: Slack, Discord, system sounds
- **Cognitive overload**: Information density too high

### Proposed Solution

Detect sensory overload signals and automatically reduce stimulation.

### Features

#### 2.1 Visual Overload Detection
Monitor visual environment:
- **Window count**: >10 windows = potential overload
- **Browser tabs**: >20 tabs = research rabbit hole
- **Terminal panes**: >6 panes = overwhelming
- **Notification badges**: Unread counts climbing

#### 2.2 Notification Overload Detection
Track notification frequency:
- **Spikes**: >10 notifications in 5 minutes
- **Constant pinging**: Notifications every <2 minutes
- **Badge anxiety**: Mounting unread counts
- **Multiple sources**: Slack + Discord + email simultaneously

#### 2.3 Automatic Interventions
When overload detected:

**Level 1 - Gentle** (first warning):
- "I notice you have 23 browser tabs open. Would you like me to:"
1. Save tabs to ConPort for later
1. Close all but active tab
1. Group tabs by topic

**Level 2 - Moderate** (persistent overload):
- Enable Do Not Disturb mode automatically
- Minimize all windows except active workspace
- Suggest 10-minute sensory reset break

**Level 3 - Severe** (critical overload):
- **Sensory Circuit Breaker**:
1. Save all state to ConPort
1. Close everything except terminal + 1 editor window
1. Enable DND across all apps
1. Show breathing exercise (optional)
1. Suggest ending session if late in day

#### 2.4 Sensory Profile Calibration
Learn individual thresholds:
- **Visual tolerance**: Some users handle 30 tabs fine
- **Notification sensitivity**: Varies widely
- **Time-of-day patterns**: Lower tolerance when tired
- **Sensory preferences**: Some need white noise, others silence

### API Design

```python
# services/adhd_engine/sensory_overload_detector.py

@dataclass
class SensoryState:
    visual_load: float  # 0.0-1.0
    auditory_load: float  # 0.0-1.0
    notification_load: float  # 0.0-1.0
    overall_load: float  # 0.0-1.0
    overload_detected: bool
    severity: str  # "none", "mild", "moderate", "severe"

@dataclass
class SensoryProfile:
    user_id: str
    visual_threshold: float = 0.7
    auditory_threshold: float = 0.6
    notification_threshold: float = 0.8
    # Learned from feedback
    calibrated: bool = False

class SensoryOverloadDetector:
    """Detect and mitigate sensory overload."""

    async def check_sensory_state(self) -> SensoryState:
        """
        Check current sensory load across all dimensions.

        Factors:
- Open windows/tabs count
- Notification frequency
- Terminal panes
- Unread badge counts
- Audio activity (if detectable)
        """
        pass

    async def apply_circuit_breaker(
        self,
        severity: str,
        user_consent: bool = True
    ) -> Dict[str, Any]:
        """
        Apply sensory circuit breaker at appropriate level.

        Always requires consent unless severity == "severe"
        and user has pre-authorized emergency intervention.
        """
        pass

    async def save_sensory_state(self) -> str:
        """
        Save current environment to ConPort for restoration.

        Saves:
- Window positions
- Open tabs (URLs)
- Terminal session state
- Active file/line
        """
        pass

    async def restore_sensory_state(
        self,
        state_id: str
    ) -> bool:
        """
        Restore saved sensory state (after reset break).
        """
        pass
```

### REST API Endpoints

```
GET    /api/v1/sensory/status
POST   /api/v1/sensory/circuit-breaker
POST   /api/v1/sensory/save-state
POST   /api/v1/sensory/restore-state
GET    /api/v1/sensory/profile
PUT    /api/v1/sensory/profile
```

### Integration Points

- **Desktop Commander MCP**: Window/tab control
- **Overwhelm Detector**: Coordinate interventions
- **Social Battery**: Sensory overload drains social battery
- **ConPort**: Save/restore environmental state
- **DopeconBridge**: Publish overload events

### Success Metrics

- **Primary**: Overload incidents detected (target: 80% accuracy)
- **Secondary**: User acceptance of interventions (target: >70%)
- **Tertiary**: Time to recover from overload (target: <15 minutes)

---

## 3. Habit Streak Tracker (P2 - Low Priority)

**Category**: Motivation & Gamification
**Effort**: 4-5 hours
**Dependencies**: None (standalone)

### Problem Statement

ADHD users struggle with:
- **Consistency**: Hard to maintain habits
- **Streak anxiety**: Traditional streak systems cause shame
- **Motivation**: External structure helps
- **Visible progress**: Need tangible evidence of improvement

**Critical Design Constraint**: **NO DAILY STREAKS** - these create anxiety and shame when broken.

### Proposed Solution

ADHD-friendly habit tracking with flexible streaks and grace periods.

### Features

#### 3.1 Habit Types

Track ADHD-relevant habits:
- **Development**: Daily commits, code reviews, documentation
- **Self-Care**: Breaks taken, medication adherence, sleep time
- **Focus**: Pomodoros completed, hyperfocus sessions
- **Social**: 1-on-1s held, team updates posted
- **Learning**: Tutorials completed, docs read

#### 3.2 Flexible Streak System

**Grace Periods**:
- **1-day grace**: Miss one day = streak continues
- **Weekly goals**: 5/7 days = full credit
- **Monthly consistency**: 20/30 days = success

**No Shame Mechanics**:
- "You took 4 breaks this week (vs. 2 last week) - nice!"
- "18/30 days logged medication (60% adherence)"
- No "STREAK BROKEN" messages
- Focus on trends, not perfection

#### 3.3 Celebration Style

ADHD-appropriate rewards:
- **Micro-celebrations**: "3 breaks today - crushing it!"
- **Trend highlights**: "Best week for commits in 2 months"
- **Comparison to self**: "20% more focused time than last week"
- **No pressure**: "No habit tracking this week? That's okay."

### API Design

```python
# services/adhd_engine/habit_streak_tracker.py

@dataclass
class Habit:
    habit_id: str
    name: str
    category: str  # "development", "self_care", "focus", "social", "learning"
    target_frequency: str  # "daily", "5_per_week", "3_per_week"
    grace_period_days: int = 1

@dataclass
class HabitStreak:
    habit_id: str
    current_streak: int  # flexible count with grace periods
    longest_streak: int
    weekly_completion_rate: float  # 0.0-1.0
    monthly_completion_rate: float
    last_completed: datetime

class HabitStreakTracker:
    """ADHD-friendly habit tracking (no shame!)."""

    async def log_habit_completion(
        self,
        habit_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log habit completion with celebration.

        Returns encouraging message, never shame.
        """
        pass

    async def get_weekly_summary(self) -> Dict[str, Any]:
        """
        Weekly summary focusing on wins, not failures.

        Format:
- "Best week for X in Y months!"
- "Improvement: +20% vs last week"
- "Maintained consistency on 3/5 habits"
        """
        pass
```

### REST API Endpoints

```
POST   /api/v1/habits
GET    /api/v1/habits
POST   /api/v1/habits/{id}/complete
GET    /api/v1/habits/{id}/streak
GET    /api/v1/habits/weekly-summary
GET    /api/v1/habits/monthly-summary
```

### Success Metrics

- **Primary**: Habit logging consistency (target: >60% weekly adherence)
- **Secondary**: User-reported motivation increase
- **Tertiary**: No user reports of streak anxiety

---

## 4. Sleep Pattern Analysis (P2 - Medium Priority)

**Category**: Analytics & Wellbeing
**Effort**: 4-6 hours
**Dependencies**: Energy Predictor, Weekly Pattern Report

### Problem Statement

ADHD and sleep disorders are highly comorbid:
- **Irregular sleep**: Delayed sleep phase, insomnia
- **Medication effects**: Stimulants affect sleep
- **Energy correlation**: Sleep quality → next-day energy
- **Pattern blindness**: Don't notice sleep trends

### Proposed Solution

Track sleep patterns and correlate with cognitive performance.

### Features

#### 4.1 Sleep Logging
- **Simple input**: "Slept 11pm - 7am" or "Slept 6.5 hours"
- **Quality rating**: 1-5 scale
- **Interruptions**: Count wake-ups
- **Medication correlation**: Track meds taken vs sleep quality

#### 4.2 Sleep-Energy Correlation
- **Next-day energy**: Link sleep → morning energy level
- **Optimal sleep duration**: Discover personal sweet spot (7h? 8h? 9h?)
- **Consistency impact**: Regular schedule vs. variable
- **Medication timing**: "Late dose → poor sleep" detection

#### 4.3 Circadian Rhythm Detection
- **Natural sleep time**: When do you naturally get tired?
- **Chronotype**: Morning lark vs. night owl patterns
- **Shift recommendations**: "You're a night owl - peak focus at 2pm"

### API Design

```python
# services/adhd_engine/sleep_pattern_analyzer.py

@dataclass
class SleepEntry:
    date: datetime
    sleep_start: datetime
    sleep_end: datetime
    duration_hours: float
    quality_rating: int  # 1-5
    interruptions: int
    medication_taken: List[str]
    notes: Optional[str]

class SleepPatternAnalyzer:
    """Analyze sleep patterns and correlate with performance."""

    async def log_sleep(
        self,
        sleep_start: datetime,
        sleep_end: datetime,
        quality: int,
        interruptions: int = 0
    ) -> SleepEntry:
        """Log sleep entry and calculate correlations."""
        pass

    async def analyze_sleep_energy_correlation(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Correlate sleep with next-day energy.

        Returns:
- Optimal sleep duration
- Quality vs. duration trade-offs
- Medication timing recommendations
        """
        pass

    async def detect_circadian_rhythm(self) -> Dict[str, Any]:
        """
        Detect natural circadian patterns.

        Returns:
- Chronotype (morning/evening/neither)
- Natural sleep time window
- Peak performance hours
        """
        pass
```

### REST API Endpoints

```
POST   /api/v1/sleep/log
GET    /api/v1/sleep/entries
GET    /api/v1/sleep/correlation
GET    /api/v1/sleep/circadian
GET    /api/v1/sleep/recommendations
```

### Success Metrics

- **Primary**: Sleep-energy correlation strength (r > 0.6)
- **Secondary**: Sleep consistency improvement (target: ±1h variation)
- **Tertiary**: User-reported sleep awareness increase

---

## 5. Code Review Accommodations (P2 - High Priority)

**Category**: Development Workflow
**Effort**: 8-10 hours
**Dependencies**: Complexity Coordinator, Energy Predictor

### Problem Statement

Code reviews are especially challenging for ADHD developers:
- **Context switching**: Hard to shift from coding to reviewing
- **Sustained attention**: Long PR reviews are exhausting
- **Detail focus**: Easy to miss bugs when skimming
- **Social pressure**: Anxiety about thorough-enough reviews

### Proposed Solution

ADHD-optimized code review workflow with accommodations.

### Features

#### 5.1 Review Complexity Assessment
Before starting review:
- **PR size analysis**: Lines changed, files modified
- **Code complexity**: Average cyclomatic complexity
- **Estimated review time**: Based on user's historical data
- **Chunking recommendations**: "Review in 3 chunks: 20min each"

#### 5.2 Review Chunking
Break large PRs into reviewable chunks:
- **Chunk 1**: Core business logic changes
- **Chunk 2**: Tests and documentation
- **Chunk 3**: Peripheral changes, config, etc.
- **Save progress**: Resume where you left off

#### 5.3 Focus Aids
Help maintain attention during review:
- **Line-by-line mode**: Advance only when explicitly requested
- **Checklist mode**: "Security check", "Error handling", "Tests"
- **Timer**: Pomodoro-style 20-minute review sessions
- **Bookmark system**: Flag lines for second pass

#### 5.4 Energy-Aware Scheduling
- **Morning reviews**: Schedule for high-energy periods
- **Post-break reviews**: Do reviews after recharge
- **Batch reviews**: Group similar PRs to minimize context switching

### API Design

```python
# services/adhd_engine/code_review_assistant.py

@dataclass
class PRReviewPlan:
    pr_id: str
    complexity_score: float
    estimated_time_minutes: int
    recommended_chunks: List[Dict[str, Any]]
    optimal_review_time: str  # "morning", "post-break", etc.

class CodeReviewAssistant:
    """ADHD accommodations for code reviews."""

    async def analyze_pr(
        self,
        pr_url: str,
        pr_size: int,
        files_changed: List[str]
    ) -> PRReviewPlan:
        """
        Analyze PR and create review plan.

        Returns:
- Complexity assessment
- Chunking recommendations
- Time estimate
- Optimal scheduling
        """
        pass

    async def start_review_session(
        self,
        pr_id: str,
        chunk_index: int = 0
    ) -> Dict[str, Any]:
        """
        Start focused review session.

        Features:
- Timer: 20-minute default
- Checklist: Security, errors, tests
- Progress tracking
        """
        pass

    async def save_review_progress(
        self,
        pr_id: str,
        current_file: str,
        current_line: int,
        notes: str
    ) -> bool:
        """Save progress to resume later."""
        pass
```

### REST API Endpoints

```
POST   /api/v1/code-review/analyze-pr
POST   /api/v1/code-review/start-session
POST   /api/v1/code-review/save-progress
GET    /api/v1/code-review/resume
POST   /api/v1/code-review/complete
GET    /api/v1/code-review/stats
```

### Integration Points

- **GitHub API**: Fetch PR details, file diffs
- **Complexity Coordinator**: Calculate code complexity
- **Energy Predictor**: Suggest optimal review time
- **ConPort**: Save review progress and notes

### Success Metrics

- **Primary**: Review completion rate (target: >80%)
- **Secondary**: Review session duration (target: <25 minutes each)
- **Tertiary**: User-reported review quality

---

## 6. Meeting Accommodations (P2 - High Priority)

**Category**: Social & Collaboration
**Effort**: 6-8 hours
**Dependencies**: Social Battery, Working Memory Support, Calendar Integration

### Problem Statement

Meetings are uniquely challenging for ADHD individuals:
- **Pre-meeting anxiety**: What if I forget to join?
- **During meeting**: Hard to follow, easy to zone out
- **Post-meeting**: Forget action items immediately
- **Context switching**: Hard to resume work after meetings

### Proposed Solution

End-to-end meeting accommodations from prep to follow-up.

### Features

#### 6.1 Pre-Meeting Support
**30 minutes before**:
- Notification: "Meeting in 30min - wrap up current task?"
- Context capture: Save current work state
- Social battery check: "Battery at 65%, meeting will drain to ~50%"
- Meeting prep: Show agenda, participants, previous notes

**5 minutes before**:
- Final reminder with join link
- Transition protocol: Close distracting tabs, enable focus mode
- Intention setting: "Your role in this meeting: Contribute X"

#### 6.2 During-Meeting Support
**Real-time accommodations**:
- **Action item capture**: Quick button to save action items
- **Thought capture**: "Brilliant idea" button → saves to working memory
- **Focus timer**: Silent vibration every 10 minutes (gentle attention reset)
- **Emergency exit**: "Need to leave early" templates

**Automated capture** (if recording enabled):
- Transcript with timestamps
- Action items extracted via NLP
- Decision points highlighted

#### 6.3 Post-Meeting Support
**Immediately after**:
- Action items review: "You have 3 action items, add to task list?"
- Thought dump: "Capture any fleeting thoughts from meeting"
- Social battery update: Log actual drain
- Context restoration: "Resume: Implementing OAuth at auth.py:156"

**Buffer time**:
- Recommend 10-15 minute buffer after meetings
- "Take 10 minutes to process before coding"
- Optional guided reflection: "What was decided? What's your next action?"

#### 6.4 Meeting Analytics
Track meeting patterns:
- **Most draining**: Which meeting types drain battery most?
- **Action item completion**: % of meeting actions actually done
- **Context switch cost**: Time to resume work post-meeting
- **Optimal meeting times**: When are meetings least disruptive?

### API Design

```python
# services/adhd_engine/meeting_accommodations.py

@dataclass
class Meeting:
    meeting_id: str
    title: str
    start_time: datetime
    duration_minutes: int
    participants_count: int
    meeting_type: str  # "1on1", "small", "large", "presentation"
    agenda: Optional[str]

@dataclass
class MeetingCapture:
    meeting_id: str
    action_items: List[str]
    decisions: List[str]
    captured_thoughts: List[str]
    social_battery_drain: float
    context_switch_time: Optional[float]

class MeetingAccommodations:
    """End-to-end meeting support for ADHD."""

    async def prepare_for_meeting(
        self,
        meeting: Meeting,
        minutes_before: int = 30
    ) -> Dict[str, Any]:
        """
        Pre-meeting preparation protocol.

        Steps:
1. Check social battery
1. Capture current context
1. Show agenda & prep notes
1. Set intention
        """
        pass

    async def capture_during_meeting(
        self,
        meeting_id: str,
        capture_type: str,  # "action_item", "decision", "thought"
        content: str
    ) -> bool:
        """
        Quick capture during meeting (ultra-low friction).
        """
        pass

    async def post_meeting_protocol(
        self,
        meeting_id: str,
        actual_duration: int
    ) -> MeetingCapture:
        """
        Post-meeting processing and context restoration.

        Returns:
- Action items (with option to add to task list)
- Decisions (synced to ConPort)
- Captured thoughts
- Battery drain
- Context restoration info
        """
        pass
```

### REST API Endpoints

```
POST   /api/v1/meetings/prepare
POST   /api/v1/meetings/{id}/capture
POST   /api/v1/meetings/{id}/complete
GET    /api/v1/meetings/upcoming
GET    /api/v1/meetings/analytics
POST   /api/v1/meetings/{id}/action-items
```

### Integration Points

- **Calendar API**: Detect upcoming meetings
- **Social Battery**: Predict drain, log actual drain
- **Working Memory**: Capture thoughts and action items
- **Context Preserver**: Save/restore work context
- **ConPort**: Persist decisions and action items

### Success Metrics

- **Primary**: Action item completion rate (target: >70%)
- **Secondary**: Context restoration time (target: <5 minutes)
- **Tertiary**: User-reported meeting stress (target: -30%)

---

## 7. Emergency Reset Protocol (P2 - High Priority)

**Category**: Safety & Recovery
**Effort**: 8-9 hours
**Dependencies**: All protection features (Overwhelm, Hyperfocus, Sensory, Social Battery)

### Problem Statement

Sometimes everything goes wrong simultaneously:
- **Compound overwhelm**: Multiple stressors at once
- **Burnout crashes**: Complete executive function shutdown
- **Sensory meltdowns**: Can't handle any stimulation
- **No energy for recovery**: Too burned out to self-rescue

### Proposed Solution

One-button emergency reset that safely saves state and initiates recovery.

### Features

#### 8.1 Emergency Detection

Auto-detect emergency situations:
- **Overwhelm score >0.9** (nearly maxed out)
- **Social battery <10%** (critical)
- **Sensory overload = severe**
- **Hyperfocus >150 minutes** (crash imminent)
- **Multiple protection triggers** (>3 systems alerting)

#### 8.2 One-Button Reset

**Emergency Reset Button**:
```
┌─────────────────────────────────────┐
│  🚨 EMERGENCY RESET                 │
│                                      │
│  Press to safely pause everything   │
│  and start recovery protocol        │
│                                      │
│  [         RESET NOW        ]       │
└─────────────────────────────────────┘
```

When pressed (consent required unless pre-authorized):
1. **Save everything** to ConPort (30 seconds max)
1. **Close all applications** except terminal
1. **Enable full DND** (OS-level + all apps)
1. **Start recovery mode** (see below)

#### 8.3 Recovery Mode

**Phase 1: Immediate** (5 minutes)
- Breathing exercise (optional, guided)
- "You're safe. Everything is saved."
- Water reminder
- Dim screen, minimal UI

**Phase 2: Assessment** (10 minutes)
- "What happened?" (optional, voice or text)
- Check core needs: hunger, thirst, bathroom, sleep
- Rate current state: 1-5 scale
- Choose recovery path:
- Short break (20 min)
- Long break (2 hours)
- End of day (call it done)

**Phase 3: Recovery** (20-120 minutes)
- Block all notifications
- Optional: Meditation, walk, nap, snack
- No pressure to return
- Automatic check-in after chosen duration

**Phase 4: Return (when ready)**
- Gradual context restoration
- Choose: "Resume last work" or "Start fresh"
- Reduced stimulation mode for first hour
- Extra protection: auto-save every 5 min

#### 8.4 Emergency Insights

After recovery, analyze what led to emergency:
- **Triggers**: What combination caused breakdown?
- **Warning signs**: How early were signals visible?
- **Prevention**: What could prevent this next time?
- **Pattern detection**: Is this recurring?

### API Design

```python
# services/adhd_engine/emergency_reset_protocol.py

@dataclass
class EmergencyState:
    emergency_id: str
    triggered_at: datetime
    trigger_reasons: List[str]  # ["overwhelm", "social_battery_critical", ...]
    severity: str  # "moderate", "severe", "critical"
    auto_detected: bool
    user_initiated: bool

@dataclass
class RecoveryPlan:
    emergency_id: str
    phase: str  # "immediate", "assessment", "recovery", "return"
    duration_minutes: int
    activities: List[str]
    check_in_time: datetime

class EmergencyResetProtocol:
    """One-button emergency reset and recovery."""

    async def detect_emergency(self) -> Optional[EmergencyState]:
        """
        Detect emergency situation from multiple signals.

        Checks:
- Overwhelm detector
- Social battery
- Sensory overload
- Hyperfocus duration
- Combined stress score
        """
        pass

    async def initiate_emergency_reset(
        self,
        user_consent: bool = False,
        user_initiated: bool = False
    ) -> EmergencyState:
        """
        Execute emergency reset protocol.

        Steps:
1. Save all state (30s timeout)
1. Close applications (requires Desktop Commander)
1. Enable DND everywhere
1. Enter recovery mode
        """
        pass

    async def guide_recovery(
        self,
        emergency_id: str,
        user_input: Optional[Dict] = None
    ) -> RecoveryPlan:
        """
        Guide user through recovery phases.

        Adaptive based on:
- Severity of emergency
- User preferences
- Time of day
- User feedback
        """
        pass

    async def analyze_emergency_triggers(
        self,
        emergency_id: str
    ) -> Dict[str, Any]:
        """
        Post-recovery analysis of what went wrong.

        Returns:
- Trigger combination
- Warning signs timeline
- Prevention recommendations
- Pattern detection
        """
        pass
```

### REST API Endpoints

```
GET    /api/v1/emergency/detect
POST   /api/v1/emergency/reset
POST   /api/v1/emergency/{id}/recovery
GET    /api/v1/emergency/{id}/status
POST   /api/v1/emergency/{id}/complete
GET    /api/v1/emergency/history
GET    /api/v1/emergency/{id}/analysis
```

### Integration Points

- **All Protection Features**: Coordinate signals
- **Desktop Commander**: Close windows, enable DND
- **ConPort**: Emergency state save/restore
- **Working Memory**: Full context preservation
- **DopeconBridge**: Publish emergency events

### Success Metrics

- **Primary**: Successful recovery rate (target: 100% - no data loss)
- **Secondary**: Time to recovery (target: user chooses, no pressure)
- **Tertiary**: Emergency recurrence prevention (target: -50% repeat incidents)

---

## Implementation Priority

### Phase 1 (High Impact)
1. **Transition Coach** (4-6h) - Address #1 ADHD challenge
1. **Meeting Accommodations** (6-8h) - High daily impact
1. **Emergency Reset** (8-9h) - Safety critical

**Total Phase 1**: 18-23 hours

### Phase 2 (Medium Impact)
1. **Sensory Overload** (5-7h) - Protection feature
1. **Sleep Pattern Analysis** (4-6h) - Foundation for other features
1. **Code Review Accommodations** (8-10h) - Development workflow

**Total Phase 2**: 17-23 hours

### Phase 3 (Quality of Life)
1. **Habit Streak Tracker** (4-5h) - Motivation boost

**Total Phase 3**: 4-5 hours

---

## Testing Strategy

### Unit Tests
- Each feature module: >80% coverage
- Mock external dependencies (calendar, Desktop Commander)
- Test ADHD-specific edge cases

### Integration Tests
- End-to-end flows for each feature
- Cross-feature interactions (e.g., Emergency → Recovery → Transition)
- ConPort persistence verification

### User Testing
- ADHD community beta testing
- Collect qualitative feedback on UX
- Measure stress reduction vs. feature overhead

### Success Validation
- A/B testing where possible
- Pre/post surveys on ADHD challenges
- Objective metrics (task completion, context restoration time)

---

## Configuration

```bash
# Transition Coach
TRANSITION_COACH_ENABLED=true
TRANSITION_COACH_AUTO_DETECT=true
TRANSITION_COACH_QUALITY_TRACKING=true

# Sensory Overload
SENSORY_OVERLOAD_ENABLED=true
SENSORY_VISUAL_THRESHOLD=0.7
SENSORY_NOTIFICATION_THRESHOLD=0.8
SENSORY_AUTO_INTERVENTION=true  # Requires consent for severe

# Habit Streaks
HABIT_TRACKER_ENABLED=true
HABIT_TRACKER_GRACE_PERIOD=1  # days
HABIT_TRACKER_WEEKLY_SUMMARY=true

# Sleep Analysis
SLEEP_ANALYSIS_ENABLED=true
SLEEP_CORRELATION_MIN_DAYS=14

# Code Review
CODE_REVIEW_ACCOMMODATIONS=true
CODE_REVIEW_CHUNK_SIZE=20  # minutes
CODE_REVIEW_MORNING_PREFERENCE=true

# Meeting Accommodations
MEETING_ACCOMMODATIONS_ENABLED=true
MEETING_PRE_ALERT_MINUTES=30
MEETING_BUFFER_MINUTES=15
MEETING_ACTION_ITEM_AUTO_ADD=true

# Emergency Reset
EMERGENCY_RESET_ENABLED=true
EMERGENCY_RESET_AUTO_DETECT=true
EMERGENCY_RESET_PRE_AUTHORIZED=false  # Requires consent
```

---

## Dependencies

### External Services
- **Calendar API**: Google Calendar, Outlook (OAuth)
- **Desktop Commander MCP**: Window/notification control
- **GitHub API**: PR data for code review assistant

### Internal Services
- **ConPort**: All state persistence
- **DopeconBridge**: Event coordination
- **Task Orchestrator**: Meeting → task conversion
- **ADHD Engine**: All P1 features as foundation

---

## Success Criteria

### Adoption Metrics
- **P2 features enabled**: Target >60% of users
- **Daily active usage**: Target >40% of users use P2 features daily

### Effectiveness Metrics
- **Transition time**: Reduced by 50% (from 15min → 7min avg)
- **Meeting stress**: Reduced by 30% (user-reported)
- **Emergency recoveries**: 100% successful (no data loss)
- **Review completion**: +40% (vs. without accommodations)

### User Satisfaction
- **Feature usefulness**: >4/5 average rating
- **Would recommend**: >80% would recommend to other ADHD developers
- **Reduced ADHD burden**: User-reported improvement in daily functioning

---

## Future Enhancements (P3)

Beyond P2, consider:
- **Medication optimization AI**: ML model for medication effectiveness
- **Team ADHD awareness**: Help neurotypical teammates understand accommodations
- **External accountability**: Integration with ADHD coaches/therapists
- **Advanced analytics**: Predictive models for burnout, productivity forecasts

---

**Document Version**: 1.0
**Last Updated**: 2026-02-02
**Status**: Ready for Implementation Planning
**Estimated Total Effort**: 39-51 hours (across all 7 features)
