# ADHD Engine Deep Dive - Part 1: Architecture & Philosophy

**Series**: ADHD Engine Deep Dive (Part 1 of 4)
**Author**: Dopemux Documentation Team
**Date**: 2025-10-05
**Audience**: Developers, researchers, ADHD advocates interested in cognitive support systems
**Reading Time**: ~12 minutes

---

## Table of Contents

1. [Introduction](#introduction)
2. [The ADHD Challenge in Software Development](#the-adhd-challenge)
3. [Cognitive Load Theory Foundations](#cognitive-load-theory)
4. [System Architecture Overview](#architecture-overview)
5. [Core Design Principles](#design-principles)
6. [Component Breakdown](#component-breakdown)
7. [Integration Philosophy](#integration-philosophy)
8. [What's Next](#whats-next)

---

## Introduction

The **ADHD Accommodation Engine** is Dopemux's central nervous system for neurodivergent-friendly development. Unlike traditional productivity tools that assume neurotypical cognitive patterns, this engine actively monitors, adapts, and optimizes the development environment for ADHD-specific challenges.

This is **not** a cosmetic layer of "friendly reminders." This is a deeply integrated cognitive support system that coordinates across ConPort (knowledge graph), Serena (code intelligence), and the Integration Bridge to create an environment where ADHD developers can achieve sustained productivity without fighting their neurology.

### Why This Matters

**Traditional development tools fail ADHD developers in three critical ways:**

1. **Context Loss**: A 5-minute interruption means 20 minutes rebuilding mental models
2. **Energy Mismatch**: Complex tasks assigned during low-energy periods lead to burnout
3. **Hyperfocus Traps**: No protection mechanisms result in exhaustion and health impacts

The ADHD Engine addresses these systematically through **real-time monitoring**, **intelligent task routing**, and **protective interventions**.

---

## The ADHD Challenge in Software Development

### Executive Function Deficits

ADHD is fundamentally an **executive function disorder**. This impacts software development in specific, measurable ways:

#### Working Memory Limitations

**Neurotypical**: 7±2 items in working memory
**ADHD**: 3-5 items in working memory (40% reduction)

**Development Impact**:
- Difficulty tracking multiple function parameters
- Frequent loss of context when switching between files
- Challenges maintaining mental model of system architecture
- Code reviews become overwhelming with 10+ files

**ADHD Engine Solution**: Progressive disclosure (max 3 options), external memory via ConPort, visual progress indicators

#### Attention Regulation Challenges

**ADHD attention exists in three problematic states:**

1. **Scattered**: Difficulty initiating and sustaining focus (executive function deficit)
2. **Hyperfocus**: Inability to disengage from engaging tasks (regulation failure)
3. **Transitioning**: High cognitive cost switching between contexts (set-shifting impairment)

**Traditional Tool Response**: "Just focus" (useless)
**ADHD Engine Response**: Detect state → adapt environment → protect user health

#### Time Blindness

**ADHD developers struggle with:**
- Estimating task duration (errors of 200-400%)
- Tracking elapsed time ("where did 3 hours go?")
- Planning work within time constraints
- Remembering to take breaks

**ADHD Engine Solution**: Visual timers, automatic time tracking, gentle reminders, mandatory break enforcement

### Energy Variability

**Neurotypical Energy**: Relatively stable throughout the day, predictable patterns
**ADHD Energy**: Highly variable, influenced by interest/novelty/task type

**ADHD Energy Levels** (defined in `models.py:12-18`):

```python
class EnergyLevel(str, Enum):
    VERY_LOW = "very_low"      # Post-hyperfocus crash, need simple tasks
    LOW = "low"                # Limited capacity, easy wins only
    MEDIUM = "medium"          # Normal capacity, standard tasks
    HIGH = "high"              # Peak performance, complex tasks OK
    HYPERFOCUS = "hyperfocus"  # Intense concentration, single complex task
```

**Critical Insight**: Energy level determines **task compatibility**, not just "how much work can be done." A very_low energy developer attempting a complex debugging task will fail and feel demoralized. The same developer with a simple, well-defined task can still make valuable progress.

### Context Switching Penalty

**Neurotypical Context Switch Cost**: 5-10 minutes to regain focus
**ADHD Context Switch Cost**: 15-30 minutes to rebuild mental model

**Compounding Effect**:
- 3 interruptions in a day = 90 minutes lost (neurotypical: 30 minutes)
- Emergency context switches can destroy the entire day's productivity
- Multiple context switches trigger "scattered" attention state

**ADHD Engine Strategy**:
- Minimize unavoidable switches (batch similar work)
- Provide bridging summaries for necessary switches
- Auto-save every 5 minutes (interruption safety)
- ConPort context preservation for zero-cost restoration

---

## Cognitive Load Theory Foundations

The ADHD Engine's design is grounded in **Cognitive Load Theory** (CLR), adapted for ADHD-specific constraints.

### Three Types of Cognitive Load

#### 1. Intrinsic Load
**Definition**: The inherent complexity of the task itself
**Example**: Understanding a recursive algorithm vs reading a constant definition

**ADHD Adaptation**:
```python
class CognitiveLoadLevel(str, Enum):
    MINIMAL = "minimal"    # 0.0-0.2: Autopilot tasks
    LOW = "low"            # 0.2-0.4: Easy tasks, minimal thinking
    MODERATE = "moderate"  # 0.4-0.6: Standard effort
    HIGH = "high"          # 0.6-0.8: Focused attention required
    EXTREME = "extreme"    # 0.8-1.0: Peak concentration
```

**Serena Integration**: Complexity scoring (see `SERENA-V2-DEEP-DIVE.md`) measures intrinsic load automatically, enabling **energy matching** (covered in Part 2).

#### 2. Extraneous Load
**Definition**: Cognitive load from poor information presentation
**Example**: Dense paragraphs vs structured bullet points

**ADHD-Specific Problem**: ADHD developers have **reduced capacity** for filtering extraneous load. A dense error message that a neurotypical developer can parse becomes overwhelming.

**ADHD Engine Mitigation**:
- **Progressive Disclosure**: Essential info first, details on request
- **Visual Structure**: Headers, bullets, emojis for rapid scanning
- **Symbol System**: `✅ ❌ ⚠️ 🔄 ⏳` for instant status recognition
- **Max 3 Options**: Reduce decision paralysis

#### 3. Germane Load
**Definition**: Cognitive load that contributes to learning/schema building
**Example**: Understanding *why* a pattern works, not just memorizing it

**ADHD Optimization**: ConPort decision logging with rationale creates **external schema storage**, reducing need to maintain mental models of architectural decisions.

### ADHD-Specific Cognitive Load Formula

**Traditional CLR**: `Total Load = Intrinsic + Extraneous + Germane`
**ADHD Adaptation**:

```
Effective Capacity = Base Capacity × Energy Multiplier × Attention Multiplier

Where:
- Base Capacity = 0.6 (ADHD working memory ~60% of neurotypical)
- Energy Multiplier = 0.3 (very_low) to 1.5 (hyperfocus)
- Attention Multiplier = 0.4 (scattered) to 1.3 (hyperfocused)
```

**Example Calculation**:

```
Scattered Attention + Very Low Energy:
Capacity = 0.6 × 0.3 × 0.4 = 0.072 (7% of neurotypical peak)

Focused Attention + High Energy:
Capacity = 0.6 × 1.2 × 1.0 = 0.72 (72% of neurotypical peak)

Hyperfocused + Hyperfocus Energy:
Capacity = 0.6 × 1.5 × 1.3 = 1.17 (117% of neurotypical peak!)
```

**Critical Insight**: ADHD cognitive capacity varies by **16x** depending on state. Task routing **must** account for current state, not just task priority.

---

## System Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ADHD Accommodation Engine                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Layer 1: Real-Time Monitoring               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐ │  │
│  │  │  Activity  │  │  Energy    │  │   Attention   │ │  │
│  │  │  Tracker   │  │  Monitor   │  │   Detector    │ │  │
│  │  └────────────┘  └────────────┘  └───────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Layer 2: Analysis & Decision                │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐ │  │
│  │  │  Cognitive │  │ Break      │  │   Task        │ │  │
│  │  │  Load Calc │  │ Recommender│  │   Router      │ │  │
│  │  └────────────┘  └────────────┘  └───────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Layer 3: Intervention & Adaptation          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐ │  │
│  │  │ UI         │  │ Hyperfocus │  │   Context     │ │  │
│  │  │ Adaptation │  │ Protection │  │   Preserver   │ │  │
│  │  └────────────┘  └────────────┘  └───────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ┌────┴─────┐      ┌──────┴──────┐      ┌─────┴──────┐
    │ ConPort  │      │   Serena    │      │Integration │
    │ (Memory) │      │(Code Intel) │      │   Bridge   │
    └──────────┘      └─────────────┘      └────────────┘
```

### Data Flow

1. **Input**: Activity signals from ConPort (task completion), Serena (navigation patterns), user input
2. **Processing**: Real-time state detection, cognitive load calculation, accommodation recommendation
3. **Output**: UI adaptations, task routing decisions, break interventions, context preservation

### Storage Architecture

**Redis** (`engine.py:54-59`): Real-time state and session data
- Current energy levels per user
- Active attention states
- Break history (last 10 breaks)
- Session timers and hyperfocus warnings

**ConPort SQLite** (`activity_tracker.py:46-51`): Persistent activity tracking
- Progress entries (task completion data)
- Activity logs (context switches, focus duration)
- Break compliance metrics
- Long-term ADHD patterns

**Why Two Storage Systems?**
- **Redis**: < 5ms latency for real-time decisions (energy level queries)
- **ConPort**: Persistent storage for pattern learning and cross-session insights
- **Cache Layer**: 5-minute TTL to prevent excessive SQLite queries

---

## Core Design Principles

### 1. Gentle, Non-Judgmental Guidance

**Anti-Pattern**: "You've been distracted 15 times today!" (shame-based)
**ADHD Engine**: "🌟 Quick win opportunity identified" (encouragement-based)

**Implementation** (`.claude/modules/shared/adhd-patterns.md:325-353`):

```bash
CELEBRATE_COMPLETION() {
    case "$COMPLETION_TYPE:$EFFORT_LEVEL" in
        "task:small")
            echo "✅ Nice! Quick win completed! 🌟"
            ;;
        "task:large")
            echo "🚀 Amazing! Major task completed! 🎉"
            ;;
    esac
}
```

**Psychological Rationale**: ADHD developers face constant internal criticism. External shame compounds executive dysfunction. **Positive reinforcement** builds momentum and reduces activation energy.

### 2. Progressive Disclosure

**Problem**: Information overload triggers "scattered" state
**Solution**: Essential → Details → Comprehensive (on request)

**Three Disclosure Levels**:

```
Level 1 (Scattered): "🎯 One clear action: [Most important step]"

Level 2 (Focused):   "📋 Breaking this down into steps:
                      1. [First step]
                      2. [Second step]
                      3. [Third step]"

Level 3 (Hyperfocus): "🔬 Comprehensive breakdown:
                       [Full analysis, implementation, alternatives]"
```

**Adaptive Behavior**: System detects attention state and adjusts disclosure level automatically.

### 3. External Memory Coordination

**ADHD Working Memory Constraint**: 3-5 items vs neurotypical 7±2

**Solution**: Offload to ConPort for zero cognitive load

**What Gets Externalized**:
- Architectural decisions with rationale (`log_decision`)
- Task dependencies and relationships (`log_progress` with `parent_id`)
- Context switches and mental models (`update_active_context`)
- System patterns and accommodations (`log_system_pattern`)

**Cognitive Benefit**: Developer can fully release mental models after `dx:save` without anxiety. ConPort preserves **everything** for later restoration.

### 4. Hyperfocus Protection

**ADHD Hyperfocus Danger**: Can work for 8+ hours without breaks, leading to:
- Physical health impacts (dehydration, hunger ignored)
- Mental exhaustion (multi-day recovery)
- Degraded code quality (too tired to notice bugs)
- Relationship damage (missed commitments)

**Three-Tier Protection** (`adhd-patterns.md:595-614`):

```
25min: Gentle suggestion
  "⏰ Great work! Time for a 5-minute break
   Choose: 1) Take break 2) 10 more min 3) Switch tasks"

60min: Warning
  "⚠️ Hyperfocus Alert: 60 minutes straight!
   Please take a break soon to avoid burnout."

90min: Mandatory Enforcement
  "🛑 Mandatory Break: 90 minutes is the limit!
   For your health and code quality, taking 10-min break now.
   Your work has been auto-saved."
```

**Controversy**: Some ADHD developers resist forced breaks during flow state.

**Justification**:
- Flow states can be restored (ADHD Engine helps rebuild context)
- Health damage from 8-hour hyperfocus sessions is **permanent**
- Code quality degrades after 90 minutes (research-backed)
- This is **harm reduction**, not productivity optimization

### 5. Energy-Aware Task Routing

**Core Principle**: Match task complexity to current cognitive capacity

**Traditional Approach**: Priority-based (high priority tasks first)
**ADHD Approach**: Capacity-matched (compatible tasks first)

**Example Scenario**:

```
User: Very Low Energy (0.3 multiplier) + Scattered Attention (0.4 multiplier)
Capacity: 0.6 × 0.3 × 0.4 = 0.072 (7% of peak)

Available Tasks:
1. Refactor authentication module (complexity: 0.8, priority: HIGH)
2. Update README documentation (complexity: 0.2, priority: LOW)
3. Fix typo in error message (complexity: 0.1, priority: LOW)

Traditional Tool: Routes task #1 (highest priority)
Outcome: Developer stares at code for 30min, makes no progress, feels demoralized

ADHD Engine: Routes task #3 (complexity 0.1 < capacity 0.072... wait, that's still too high!)
Actually Routes: "🌟 Your energy is very low. Recommend: Take 15min break, then try documentation task."
```

**Implementation Preview**: Part 2 will cover the full energy matching algorithm with ConPort integration.

### 6. Context Preservation as First-Class Feature

**Traditional IDEs**: "Restore tabs on reopen" (file list only)
**ADHD Engine**: Full mental model restoration

**What Gets Preserved** (`adhd-patterns.md:123-171`):

```json
{
  "attention_state": "focused",
  "current_task": "Implement JWT validation middleware",
  "mental_model": "Working on auth.py:45-120, session.py provides token storage",
  "next_steps": ["Add expiry check", "Write tests", "Update docs"],
  "time_invested": "35 minutes",
  "interruption_type": "meeting",
  "timestamp": "2025-10-05T14:30:00Z"
}
```

**Restoration Experience**:

```
🔄 Welcome back! Restoring your context...

🎯 You were working on: Implement JWT validation middleware
🧠 Mental model: Working on auth.py:45-120, session.py provides token storage
📍 Attention state: focused
⚡ Ready to continue!

Next steps:
1. Add expiry check
2. Write tests
3. Update docs
```

**Cognitive Benefit**: Zero context rebuild time. Developer can resume immediately, even after multi-day interruptions.

---

## Component Breakdown

### Core Components

#### 1. ADHDAccommodationEngine (`engine.py:40-51`)

**Purpose**: Central orchestrator for all ADHD accommodations

**Key Responsibilities**:
- Initialize Redis and ConPort connections
- Load user ADHD profiles
- Coordinate monitoring tasks
- Generate accommodation recommendations
- Track intervention statistics

**Initialization Pattern**:

```python
async def initialize(self) -> None:
    # Redis for real-time state (< 5ms latency)
    self.redis_client = redis.from_url(self.redis_url)

    # ConPort for persistent tracking
    self.conport = ConPortSQLiteClient(
        db_path=settings.workspace_id + "/context_portal/context.db",
        read_only=False  # Week 3: Enable writes
    )

    # Activity tracker bridges Redis + ConPort
    self.activity_tracker = ActivityTracker(
        redis_client=self.redis_client,
        conport_db_path=conport_db_path
    )

    # Start background monitoring
    await self._start_accommodation_monitoring()
```

**Background Monitoring**: Three async tasks run continuously:
1. Energy level monitor (every 5 minutes)
2. Attention state detector (every 2 minutes)
3. Break recommendation engine (every 1 minute)

#### 2. ActivityTracker (`activity_tracker.py:25-51`)

**Purpose**: Bridge between real-time Redis and persistent ConPort data

**Data Sources**:
- **ConPort**: Task completion rate from `progress_entries` table
- **ConPort**: Context switches from `custom_data.activity_log`
- **Redis**: Break history (last 10 breaks)
- **Redis**: Last break timestamp

**Caching Strategy**:
```python
# 5-minute TTL cache prevents excessive SQLite queries
self._activity_cache: Dict[str, tuple] = {}
self._cache_ttl = 300  # seconds
```

**Why Caching Matters**: ConPort SQLite queries take 2-5ms. With checks every minute across all monitoring tasks, uncached queries would create unnecessary I/O load. 5-minute cache balances freshness with performance.

#### 3. ADHDProfile (`models.py:40-72`)

**Purpose**: Personalized ADHD characteristic storage per user

**Key Characteristics**:

```python
@dataclass
class ADHDProfile:
    # ADHD traits (0.0-1.0 scales)
    hyperfocus_tendency: float = 0.7        # Likelihood of hyperfocus
    distraction_sensitivity: float = 0.6    # Easily distracted
    context_switch_penalty: float = 0.4     # Context switch cost
    break_resistance: float = 0.3           # Resists breaks

    # Time preferences
    optimal_task_duration: int = 25         # Pomodoro-style
    max_task_duration: int = 90            # Hard limit

    # Accommodation preferences
    visual_progress_bars: bool = True       # Wants visual feedback
    gentle_reminders: bool = True          # Soft vs sharp reminders
    celebration_feedback: bool = True       # Completion celebrations
```

**Personalization**: Different ADHD developers have different profiles. Some hyperfocus frequently (tendency: 0.9), others rarely (tendency: 0.3). The engine adapts interventions based on individual patterns.

**Learning Over Time**: Future enhancement (Phase 4) will adjust profiles based on observed behavior patterns.

---

## Integration Philosophy

### Cross-System Coordination

The ADHD Engine doesn't work in isolation. It coordinates with:

#### ConPort Integration

**What ADHD Engine Reads from ConPort**:
- Task completion rates (activity assessment)
- Progress entry status (energy level validation)
- Context switches (attention state detection)
- Decision history (working memory support)

**What ADHD Engine Writes to ConPort**:
- Break events for long-term pattern analysis
- Energy level transitions for capacity planning
- Accommodation effectiveness metrics
- ADHD profile adjustments

**Coordination Example**:
```python
# Read recent task completion for energy assessment
progress_entries = self.conport.get_progress_entries(limit=20, hours_ago=1)
completed = [p for p in progress_entries if p['status'] == 'DONE']
completion_rate = len(completed) / len(progress_entries)

# High completion rate suggests good energy/attention
if completion_rate > 0.8:
    energy_bonus = +0.2  # Boost energy assessment
```

#### Serena Integration

**What ADHD Engine Uses from Serena**:
- Code complexity scores (cognitive load calculation)
- Navigation patterns (attention state detection)
- Frequently accessed files (context preservation)

**Future Enhancement**: Serena's navigation cache will inform "likely next files" suggestions during context restoration.

#### Integration Bridge Coordination

**ADHD Engine communicates via Integration Bridge for**:
- Task routing decisions (send to Task-Orchestrator)
- Break recommendations (surfaced in UI)
- Energy level updates (broadcast to all systems)

**Authority Boundaries**: ADHD Engine is **authoritative** for cognitive state assessments. Other systems must respect energy/attention state when making decisions.

---

## What's Next

This completes Part 1's exploration of the ADHD Engine's **architecture and philosophical foundations**. You now understand:

✅ Why traditional tools fail ADHD developers
✅ How Cognitive Load Theory informs system design
✅ The three-layer architecture (Monitor → Analyze → Intervene)
✅ Core principles (gentle guidance, progressive disclosure, hyperfocus protection)
✅ Component roles and integration patterns

### Coming in Part 2: Energy Matching & Task Selection

Part 2 will dive deep into the **most innovative aspect** of the ADHD Engine: energy-aware task routing.

**Topics Covered**:
- Energy level detection algorithms
- ConPort task metadata schema (complexity, energy requirements)
- Task compatibility scoring formulas
- Real-world routing examples
- Break recommendation engine
- Energy transition handling

**Preview Question**: How does the engine decide whether a "very_low" energy developer should attempt a "moderate" complexity task, take a break, or switch to documentation work?

The answer involves real-time activity analysis, ConPort task metadata, Redis state tracking, and a sophisticated compatibility scoring algorithm. Part 2 reveals the complete system.

---

**Word Count**: ~2,500 words
**Next**: Part 2 - Energy Matching & Task Selection (3,000 words)

