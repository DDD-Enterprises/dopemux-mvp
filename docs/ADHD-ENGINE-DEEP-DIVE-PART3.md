# ADHD Engine Deep Dive - Part 3: Attention Management & Session Orchestration

**Series**: ADHD Engine Deep Dive (Part 3 of 4)
**Author**: Dopemux Documentation Team
**Date**: 2025-10-05
**Prerequisites**: Read [Part 1](ADHD-ENGINE-DEEP-DIVE-PART1.md) and [Part 2](ADHD-ENGINE-DEEP-DIVE-PART2.md)
**Reading Time**: ~15 minutes

---

## Table of Contents

1. [Introduction](#introduction)
2. [Attention State Detection](#attention-state-detection)
3. [Hyperfocus Protection System](#hyperfocus-protection)
4. [Break Timing Intelligence](#break-timing)
5. [Context Switch Analysis](#context-switch-analysis)
6. [Session Orchestration](#session-orchestration)
7. [State Transition Management](#state-transitions)
8. [Redis State Architecture](#redis-architecture)
9. [What's Next](#whats-next)

---

## Introduction

Parts 1-2 established **what** the ADHD Engine does and **how** it matches tasks to energy. Part 3 reveals the **protective systems** that prevent burnout and maximize sustainable productivity.

This is where the ADHD Engine goes beyond task routing into **active health protection**. The system continuously monitors attention states, detects dangerous patterns (hyperfocus without breaks), and intervenes with graduated escalation to prevent both physical and mental harm.

### The Protection Challenge

**ADHD Hyperfocus Reality**:
- Can work 8-12 hours straight without noticing
- Forget to eat, drink, use bathroom
- Develop repetitive strain injuries from immobility
- Experience multi-day recovery crashes
- Damage relationships by missing commitments

**Traditional Tools**: Silent. No protection. Developer burnout is their problem.

**ADHD Engine**: Active monitoring + graduated interventions + mandatory enforcement.

This is **controversial** - some developers resist forced breaks. But the alternative is preventable harm. The ADHD Engine prioritizes **long-term health over short-term productivity**.

---

## Attention State Detection

### The Five Attention States

The ADHD Engine models attention as a **state machine** with five distinct states (`models.py:21-27`):

```python
class AttentionState(str, Enum):
    SCATTERED = "scattered"           # Difficulty focusing, need structure
    TRANSITIONING = "transitioning"   # Moving between tasks/contexts
    FOCUSED = "focused"              # Good concentration, productive
    HYPERFOCUSED = "hyperfocused"    # Intense focus, needs protection
    OVERWHELMED = "overwhelmed"      # Too much information, need reduction
```

**Why States Matter**: Each state has different **task compatibility constraints** (covered in Part 2) and requires different **protective interventions**.

### Detection Algorithm

Attention state is assessed every **2 minutes** from four behavioral indicators (`engine.py:629-664`):

#### Indicator 1: Context Switching Frequency

```python
indicators = await self._get_attention_indicators(user_id)
rapid_switching = indicators.get("context_switches_per_hour", 0) > 10
```

**Interpretation**:
- **> 10 switches/hour**: SCATTERED or OVERWHELMED
- **3-7 switches/hour**: TRANSITIONING
- **< 3 switches/hour**: FOCUSED or HYPERFOCUSED

**Data Source**: ConPort `custom_data.activity_log`

**Example**:
```
Last hour context switches: 12
- auth.py → README.md (10:05)
- README.md → tests/ (10:12)
- tests/ → package.json (10:18)
- package.json → auth.py (10:23)
... (8 more switches)

Result: rapid_switching = True
Likely state: SCATTERED
```

#### Indicator 2: Task Abandonment Rate

```python
task_abandonment = indicators.get("abandoned_tasks", 0) > 2
```

**Interpretation**:
- **> 3 abandoned tasks**: OVERWHELMED (can't complete anything)
- **2-3 abandoned tasks**: SCATTERED (struggling to maintain focus)
- **0-1 abandoned tasks**: FOCUSED or better

**Data Source**: ConPort `progress_entries` with status transitions

**Example**:
```
Last hour:
- Task A: TODO → IN_PROGRESS → TODO (abandoned after 5min)
- Task B: TODO → IN_PROGRESS → TODO (abandoned after 8min)
- Task C: TODO → IN_PROGRESS → TODO (abandoned after 3min)
- Task D: TODO → IN_PROGRESS → DONE (completed!)

Abandoned count: 3
Result: task_abandonment = True
Likely state: OVERWHELMED
```

#### Indicator 3: Focus Duration

```python
focus_duration = indicators.get("average_focus_duration", 25)
```

**Interpretation**:
- **> 60 minutes**: HYPERFOCUSED
- **20-60 minutes**: FOCUSED
- **10-20 minutes**: TRANSITIONING
- **< 10 minutes**: SCATTERED

**Data Source**: Redis activity timestamps + ConPort session tracking

**Calculation**:
```python
# ActivityTracker calculates from ConPort activity_log
session_starts = [entry['start_time'] for entry in activity_log]
session_ends = [entry['end_time'] for entry in activity_log]

durations = [
    (end - start).total_seconds() / 60
    for start, end in zip(session_starts, session_ends)
]

average_focus_duration = sum(durations) / len(durations)
```

**Example**:
```
Recent sessions:
- 10:00-10:05: 5 minutes (auth.py)
- 10:05-10:12: 7 minutes (README.md)
- 10:12-10:16: 4 minutes (tests/)
- 10:16-10:22: 6 minutes (package.json)

Average: (5 + 7 + 4 + 6) / 4 = 5.5 minutes
Result: focus_duration < 10
Likely state: SCATTERED
```

#### Indicator 4: Distraction Events

```python
distraction_events = indicators.get("distraction_events", 0)
```

**Distraction Event Detection**:
- Tab switches to non-work applications (Twitter, YouTube, etc.)
- Rapid file opening without editing
- Search queries unrelated to current task
- Multiple failed test runs (indicates guessing, not focused debugging)

**Interpretation**:
- **> 10 events/hour**: OVERWHELMED
- **5-10 events/hour**: SCATTERED
- **2-5 events/hour**: TRANSITIONING
- **< 2 events/hour**: FOCUSED or HYPERFOCUSED

### State Classification Logic

All four indicators combine into a decision tree (`engine.py:641-650`):

```python
# Priority 1: OVERWHELMED (emergency state)
if task_abandonment > 3 or distraction_events > 10:
    return AttentionState.OVERWHELMED

# Priority 2: SCATTERED (low capacity state)
elif rapid_switching and focus_duration < 10:
    return AttentionState.SCATTERED

# Priority 3: HYPERFOCUSED (needs protection)
elif focus_duration > 60 and distraction_events < 2:
    return AttentionState.HYPERFOCUSED

# Priority 4: FOCUSED (optimal state)
elif focus_duration > 20 and distraction_events < 5:
    return AttentionState.FOCUSED

# Default: TRANSITIONING
else:
    return AttentionState.TRANSITIONING
```

**Why This Order?** Medical urgency. OVERWHELMED state can trigger anxiety spirals and needs immediate intervention. HYPERFOCUSED needs protection before harm occurs.

### Real Detection Examples

#### Example 1: Developer Entering Hyperfocus

```
Time: 10:00am - Initial assessment
- Context switches: 2 (low)
- Task abandonment: 0
- Focus duration: 35 minutes
- Distraction events: 1

Classification: FOCUSED

Time: 11:00am - One hour later
- Context switches: 0 (none!)
- Task abandonment: 0
- Focus duration: 75 minutes (increasing)
- Distraction events: 0

Classification: HYPERFOCUSED
→ Trigger: Start hyperfocus protection monitoring
```

#### Example 2: Developer Becoming Overwhelmed

```
Time: 2:00pm - Initial assessment
- Context switches: 7 (moderate)
- Task abandonment: 2
- Focus duration: 15 minutes
- Distraction events: 6

Classification: TRANSITIONING

Time: 2:30pm - 30 minutes later
- Context switches: 15 (rapid increase!)
- Task abandonment: 5 (can't complete anything)
- Focus duration: 4 minutes (degrading)
- Distraction events: 12

Classification: OVERWHELMED
→ Trigger: Immediate intervention needed
```

#### Example 3: Scattered Morning Recovery

```
Time: 9:00am - Morning start
- Context switches: 12
- Task abandonment: 3
- Focus duration: 6 minutes
- Distraction events: 8

Classification: SCATTERED

Time: 10:00am - After 15min break + simple task
- Context switches: 4 (improving)
- Task abandonment: 1
- Focus duration: 18 minutes (building)
- Distraction events: 3

Classification: TRANSITIONING (recovery in progress)
```

---

## Hyperfocus Protection System

### The Three-Tier Intervention Model

The ADHD Engine uses **graduated escalation** to protect hyperfocused developers (`engine.py:815-877`):

#### Tier 1: Gentle Reminder (25-40 minutes)

**Trigger**: User in FOCUSED state for 25+ minutes

```python
if session_duration > profile.optimal_task_duration:
    # Gentle suggestion, not mandatory
    message = "⏰ Great work! Time for a 5-minute break"
    urgency = "when_convenient"
    action_required = False
```

**User Experience**:
```
⏰ Great work! Time for a 5-minute break

You've been focused for 25 minutes. Taking a break helps:
- Prevent burnout
- Maintain attention quality
- Process what you learned

Choose:
1. Take 5min break (recommended)
2. Continue for 10 more min
3. Save and switch tasks
```

**Philosophy**: Respect user flow state. This is **informational**, not mandatory. Developer can dismiss if deeply engaged.

#### Tier 2: Warning (60 minutes)

**Trigger**: User in HYPERFOCUSED state for 60+ minutes

```python
if session_duration > profile.optimal_task_duration * 1.5:  # 25 * 1.5 = 37.5min
    # Warning with increased urgency
    message = "🎯 You've been in hyperfocus for a while - consider a brief break soon"
    urgency = "soon"
    action_required = True
```

**User Experience**:
```
⚠️ Hyperfocus Alert: 60 minutes straight!

You're doing great work, but hyperfocus can be exhausting.
Please take a break soon to avoid burnout.

Physical reminders:
- Hydrate (when did you last drink water?)
- Stretch (your back/neck may be tight)
- Eye rest (look at something 20 feet away)

🛡️ Your work has been auto-saved
```

**Implementation**:
```python
warning_data = {
    "user_id": user_id,
    "message": "🎯 You've been in hyperfocus for a while...",
    "session_duration": session_duration,
    "timestamp": datetime.now(timezone.utc).isoformat()
}

await self.redis_client.lpush(
    f"adhd:hyperfocus_warnings:{self.workspace_id}",
    json.dumps(warning_data)
)
```

**Why 60 Minutes?** Research shows cognitive performance degrades significantly after 60 minutes of sustained focus. This is the **evidence-based threshold** for health intervention.

#### Tier 3: Mandatory Enforcement (90 minutes)

**Trigger**: User in HYPERFOCUSED state for 90+ minutes

```python
if session_duration > profile.max_task_duration:  # Default: 90min
    # Force break - no option to dismiss
    await self._recommend_break(user_id, "hyperfocus_protection", session_duration)

    # Reduce recommended task complexity
    await self._adjust_task_recommendations_for_protection(user_id)
```

**User Experience**:
```
🛑 MANDATORY BREAK: 90 minutes is the limit!

For your health and code quality, you need a 10-minute break now.

Why this is mandatory:
- Physical health: Risk of RSI, eye strain, dehydration
- Mental health: Recovery requires 2-3x the hyperfocus duration
- Code quality: Error rates increase significantly after 90min

✅ Your work has been auto-saved
⏰ Break timer started: 10 minutes

After break: You can resume or we'll suggest a different task
```

**Enforcement Mechanism**:
```python
# Week 3: Create mandatory break task in ConPort
entry_id = self.conport.log_progress_entry(
    status="BLOCKED",
    description="🛑 MANDATORY BREAK (90min hyperfocus protection)",
    linked_item_type="hyperfocus_session",
    linked_item_id=session_id
)

# Temporarily block complex task recommendations
await self._adjust_task_recommendations_for_protection(user_id)
```

**Controversy**: Some developers hate forced breaks during flow.

**Response**: This is **medical intervention**, not productivity optimization. The alternative (8-hour hyperfocus sessions) causes:
- Repetitive strain injuries (permanent damage)
- Multi-day exhaustion crashes
- Relationship damage from missed commitments
- Degraded code quality (too tired to notice bugs)

**Compromise**: 90 minutes is **generous**. Research suggests 60 minutes maximum. The ADHD Engine already gives extra time.

### Hyperfocus Session Tracking

**Session Start Detection** (`engine.py:843-850`):

```python
session_start_key = f"adhd:hyperfocus_start:{user_id}"
session_start_str = await self.redis_client.get(session_start_key)

if not session_start_str:
    # First time entering hyperfocus - start tracking
    await self.redis_client.setex(
        session_start_key,
        7200,  # 2-hour TTL (auto-expire)
        datetime.now(timezone.utc).isoformat()
    )
```

**Session Duration Calculation**:

```python
if session_start_str:
    session_start = datetime.fromisoformat(session_start_str)
    session_duration = (datetime.now(timezone.utc) - session_start).total_seconds() / 60
```

**Auto-Expiry**: Redis TTL ensures stale sessions clean up automatically after 2 hours (beyond maximum enforcement threshold).

---

## Break Timing Intelligence

The break recommendation system goes beyond simple timers. It uses **five signals** to determine optimal break timing (`engine.py:695-813`).

### Signal 1: Time Since Last Break

**Core Logic**:
```python
last_break_key = f"adhd:last_break:{user_id}"
last_break_str = await self.redis_client.get(last_break_key)

if last_break_str:
    last_break = datetime.fromisoformat(last_break_str)
    time_since_break = (datetime.now(timezone.utc) - last_break).total_seconds() / 60
```

**Thresholds**:
```python
if time_since_break >= profile.max_task_duration:  # 90min
    break_needed = True
    break_reason = "maximum_duration_reached"

elif time_since_break >= profile.optimal_task_duration * 2:  # 50min
    break_needed = True
    break_reason = "extended_work_period"
```

### Signal 2: Energy Level Collapse

**Low Energy Override**:
```python
current_energy = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)

if current_energy == EnergyLevel.VERY_LOW and time_since_break >= 15:
    break_needed = True
    break_reason = "low_energy_recovery"
```

**Rationale**: VERY_LOW energy after just 15 minutes indicates **energy crash**, not gradual depletion. Immediate break can prevent spiral.

### Signal 3: Completion Rate Decline

**Pattern Detection**:
```python
# Compare last 15min completion rate vs last hour
recent_completion = calculate_completion_rate(last_15_min_tasks)
hourly_completion = calculate_completion_rate(last_hour_tasks)

if recent_completion < hourly_completion * 0.5:  # 50% drop
    break_needed = True
    break_reason = "productivity_decline"
```

**Example**:
```
Last hour: 80% completion (8/10 tasks)
Last 15min: 33% completion (1/3 tasks)

Interpretation: Sudden productivity crash
Recommendation: Immediate break for recovery
```

### Signal 4: Context Switch Acceleration

**Rapid Increase Detection**:
```python
current_hour_switches = count_context_switches(last_60_min)
previous_hour_switches = count_context_switches(60-120_min_ago)

if current_hour_switches > previous_hour_switches * 2:
    break_needed = True
    break_reason = "attention_degradation"
```

### Signal 5: Hyperfocus Protection

**Covered in previous section** - breaks mandatory after 90 minutes of hyperfocus.

### Personalized Break Messages

Messages adapt to user profile and break reason (`engine.py:751-760`):

```python
break_messages = {
    "maximum_duration_reached":
        f"🛡️ You've been focused for {work_duration:.0f} minutes - time for a healthy break!",

    "extended_work_period":
        f"☕ Great work! After {work_duration:.0f} minutes, a break will help maintain productivity",

    "low_energy_recovery":
        f"💙 Low energy detected - a short break might help recharge",

    "hyperfocus_protection":
        f"🚀 Hyperfocus mode detected - protecting your wellbeing with a break reminder"
}
```

**Tone**: Always **positive and supportive**, never punitive. "Great work!" not "You've been working too long."

### Break Activity Suggestions

**Personalization Based on Profile** (`engine.py:761-769`):

```python
break_suggestions = ["5-minute walk", "Hydrate", "Stretch"]

if profile.break_activity_suggestions:
    break_suggestions.extend([
        "Deep breathing exercise",
        "Look away from screen (20-20-20 rule)",
        "Quick snack if needed"
    ])
```

**Why Suggestions Matter**: ADHD developers often **don't know what to do** during breaks, leading to:
- Checking Twitter (not actually restful)
- Immediately starting another task
- Wandering aimlessly (decision paralysis)

**Structured suggestions** reduce activation energy for effective breaks.

### Break Compliance Tracking

**Recording Breaks in Redis**:

```python
break_data = {
    "user_id": user_id,
    "reason": reason,
    "work_duration": work_duration,
    "message": message,
    "suggestions": break_suggestions,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "taken": False  # Updated when user confirms break
}

await self.redis_client.lpush(
    f"adhd:break_recommendations:{self.workspace_id}",
    json.dumps(break_data)
)
```

**Compliance Analysis** (from Part 2):

```python
break_history = await self.redis.lrange(f"adhd:breaks:{user_id}", 0, 10)
breaks_taken = [b for b in break_history if json.loads(b)['taken']]
compliance = len(breaks_taken) / len(break_history)
```

**Feedback Loop**: Low compliance (< 50%) triggers earlier break recommendations and increased urgency.

---

## Context Switch Analysis

### Why Context Switches Matter for ADHD

**Neurotypical Context Switch Cost**: 5-10 minutes to regain focus
**ADHD Context Switch Cost**: 15-30 minutes to rebuild mental model

**Compounding Damage**:
```
3 context switches in 2 hours (neurotypical):
  Work time: 120 - (3 × 7) = 99 minutes (83% efficiency)

3 context switches in 2 hours (ADHD):
  Work time: 120 - (3 × 22) = 54 minutes (45% efficiency)
```

**ADHD Engine Goal**: Minimize avoidable context switches, provide support for unavoidable ones.

### Context Switch Tracking

**Recording Switches** (`engine.py:879-901`):

```python
# Triggered by file/task changes in ActivityTracker
self.context_switch_history.append((
    datetime.now(timezone.utc),
    previous_context,  # "auth.py implementation"
    new_context        # "README.md documentation"
))
```

**Pattern Detection**:

```python
recent_switches = [
    switch for switch in self.context_switch_history
    if switch[0] > datetime.now(timezone.utc) - timedelta(hours=1)
]

if len(recent_switches) > 10:
    logger.warning(f"⚠️ High context switching detected: {len(recent_switches)} in 1 hour")
```

### Context Switch Recommendations

**When Excessive Switching Detected**:

```python
if len(recent_switches) > 10:
    recommendation = AccommodationRecommendation(
        accommodation_type="context_switch_reduction",
        urgency="soon",
        message="🔄 High context switching detected - consider focusing on one task",
        suggested_actions=[
            "Pick one task and commit for 25 minutes",
            "Use timer to prevent switching",
            "Enable focus mode (block distractions)",
            "Break large task into smaller chunks if it feels overwhelming"
        ],
        cognitive_benefit="Reduces cognitive load from constant mental model rebuilding"
    )
```

### Context Bridging Support

**For Unavoidable Switches** (meeting, emergency, etc.):

```python
# Before switch: Auto-save + capture state
await self.conport.update_active_context(
    workspace_id=workspace_id,
    patch_content={
        "pre_switch_context": {
            "task": current_task,
            "mental_model": mental_model_summary,
            "next_steps": next_steps,
            "files_open": open_files,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
)

# After switch: Provide bridging summary
bridging_summary = f"""
🔄 Context Switch: {previous_context} → {new_context}

📋 Previous context: {previous_task}
🎯 New context: {new_task}

💡 Tip: Take 2 minutes to mentally transition before diving in
"""
```

---

## Session Orchestration

### The 25-Minute Focus Block

**Default Session Pattern** (based on Pomodoro, adapted for ADHD):

```python
class ADHDProfile:
    optimal_task_duration: int = 25  # minutes
    max_task_duration: int = 90     # minutes
```

**Why 25 Minutes?**
- Research-backed optimal focus duration for ADHD
- Short enough to prevent attention drift
- Long enough for meaningful progress
- Matches Pomodoro technique (widely validated)

**Session Flow**:

```
┌─ Session Start (0 min)
│  ├─ Load task from ConPort
│  ├─ Start auto-save timer (5min intervals)
│  └─ Begin work
│
├─ 5min: First auto-save checkpoint
├─ 10min: Second auto-save checkpoint
├─ 15min: Third auto-save checkpoint
├─ 20min: Fourth auto-save checkpoint
│
├─ 25min: ⏰ GENTLE BREAK REMINDER
│  ├─ Option 1: Take 5min break (recommended)
│  ├─ Option 2: Continue 10 more min
│  └─ Option 3: Save and switch tasks
│
├─ If continued...
├─ 35min: Final auto-save before reminder
│
├─ 40min: ⏰ STRONGER BREAK REMINDER
│  ├─ "Consider a break soon"
│  └─ Next reminder: 60min
│
├─ 60min: ⚠️ WARNING
│  └─ "Take break soon to avoid burnout"
│
└─ 90min: 🛑 MANDATORY BREAK
   └─ No option to continue
```

### Auto-Save Pattern

**Every 5 Minutes**: Preserve work + mental state

```python
# Triggered by background timer
async def auto_save_session(user_id: str):
    current_state = {
        "files_modified": get_modified_files(),
        "cursor_positions": get_cursor_positions(),
        "mental_model": extract_mental_model(),
        "task_progress": calculate_progress(),
        "energy_level": current_energy,
        "attention_state": current_attention,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    await self.conport.update_active_context(
        workspace_id=workspace_id,
        patch_content={"auto_save": current_state}
    )
```

**Why 5 Minutes?** Balance between:
- Frequent enough: Interruptions lose max 5min work
- Infrequent enough: Not distracting to user

**Interruption Recovery**:

```
User: *Emergency meeting interruption at 18 minutes*

Auto-save: Last save at 15 minutes (3 minutes lost max)

After meeting:
/dx:load → Restore state from 15min checkpoint
  ✅ Files restored
  ✅ Mental model summary provided
  ✅ Next steps visible
  → Resume work with minimal context rebuild
```

---

## State Transition Management

### Tracking State Changes

**Energy Level Transitions** (`engine.py:601-606`):

```python
previous_energy = self.current_energy_levels.get(user_id)
self.current_energy_levels[user_id] = current_energy

if previous_energy and previous_energy != current_energy:
    await self._log_energy_change(user_id, previous_energy, current_energy)
```

**Attention State Transitions** (`engine.py:653-658`):

```python
previous_state = self.current_attention_states.get(user_id)
self.current_attention_states[user_id] = attention_state

if previous_state and previous_state != attention_state:
    await self._log_attention_change(user_id, previous_state, attention_state)
```

### Transition Event Logging

**ConPort Integration**:

```python
async def _log_energy_change(self, user_id: str, previous: EnergyLevel, current: EnergyLevel):
    # Log to ConPort custom_data for pattern analysis
    transition_event = {
        "user_id": user_id,
        "previous_energy": previous.value,
        "current_energy": current.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": self.current_task_context.get(user_id, "unknown")
    }

    self.conport.log_custom_data(
        category="energy_transitions",
        key=f"{user_id}_{int(time.time())}",
        value=transition_event
    )
```

**Why Log Transitions?** Pattern learning. Over time, ConPort can identify:
- Times of day when energy typically drops
- Tasks that drain energy faster
- Recovery patterns after breaks
- Personal energy cycles (daily, weekly)

### Transition-Triggered Actions

**HIGH → HYPERFOCUS**:
```python
if previous == EnergyLevel.HIGH and current == EnergyLevel.HYPERFOCUS:
    # Start hyperfocus protection monitoring
    await self._start_hyperfocus_session_tracking(user_id)
```

**FOCUSED → SCATTERED**:
```python
if previous == AttentionState.FOCUSED and current == AttentionState.SCATTERED:
    # Recommend break or task switch
    recommendation = "🌀 Attention seems scattered - consider a 5min break or simpler task"
```

**LOW → VERY_LOW**:
```python
if previous == EnergyLevel.LOW and current == EnergyLevel.VERY_LOW:
    # Immediate break recommendation
    await self._recommend_break(user_id, "energy_crash", time_since_break)
```

---

## Redis State Architecture

### Key Patterns

The ADHD Engine uses Redis for **low-latency state access** with structured key patterns:

#### User State Keys

```
adhd:profile:{user_id}              → ADHDProfile JSON
adhd:energy_level:{user_id}         → Current energy level
adhd:attention_state:{user_id}      → Current attention state
adhd:last_break:{user_id}           → ISO timestamp of last break
adhd:hyperfocus_start:{user_id}     → ISO timestamp of hyperfocus session start
```

#### History Keys (Lists)

```
adhd:breaks:{user_id}               → Break history (JSON list, FIFO)
adhd:energy_history:{user_id}       → Energy level history (last 24h)
adhd:break_recommendations:{workspace_id} → Recent break recommendations
adhd:hyperfocus_warnings:{workspace_id}   → Recent hyperfocus warnings
```

#### Example: Break History List

```python
# Add break event
break_event = {
    "timestamp": "2025-10-05T14:30:00Z",
    "duration": 5,
    "taken": True,
    "reason": "optimal_task_duration"
}

await redis.lpush(f"adhd:breaks:{user_id}", json.dumps(break_event))
await redis.ltrim(f"adhd:breaks:{user_id}", 0, 9)  # Keep last 10
```

### TTL Strategy

**Auto-Expiration** prevents stale data accumulation:

```python
# Hyperfocus session auto-expires after 2 hours
await redis.setex(
    f"adhd:hyperfocus_start:{user_id}",
    7200,  # 2-hour TTL
    datetime.now(timezone.utc).isoformat()
)

# Break recommendations expire after 1 hour
await redis.expire(f"adhd:break_recommendations:{workspace_id}", 3600)
```

### ConPort vs Redis Division

**Redis** (fast, ephemeral):
- Current energy/attention state
- Session timers and countdowns
- Recent break recommendations
- Hyperfocus warnings

**ConPort** (persistent, queryable):
- State transition history
- Long-term pattern data
- Task completion metrics
- Decision logs and rationale

**Why Both?** Redis provides < 5ms latency for real-time decisions. ConPort provides persistent storage for pattern learning and cross-session analysis.

---

## What's Next

This completes Part 3's exploration of **attention management and session orchestration**. You now understand:

✅ Five-state attention detection from behavioral indicators
✅ Three-tier hyperfocus protection (gentle → warning → mandatory)
✅ Five-signal break recommendation intelligence
✅ Context switch analysis and minimization strategies
✅ 25-minute session orchestration with auto-save
✅ State transition tracking and triggered interventions
✅ Redis architecture for low-latency state management

### Coming in Part 4: Integration & Workflows

Part 4 will complete the series with **real-world workflows** and **cross-system integration patterns**:

**Topics Covered**:
- `/dx:implement` command workflow (energy matching in action)
- `/dx:load` / `/dx:save` context preservation flow
- ConPort + Serena + ADHD Engine coordination
- Integration Bridge event routing
- Complete day-in-the-life workflow examples
- Performance metrics and validation
- Future enhancements roadmap

**Preview Question**: What happens when a developer runs `/dx:implement` at 9am with SCATTERED attention and VERY_LOW energy after a long weekend?

The answer involves state assessment, task compatibility filtering, gentle recommendations, session orchestration, and protective interventions - all coordinated across ConPort, Serena, and the ADHD Engine. Part 4 reveals the complete integrated experience.

---

**Word Count**: ~3,000 words
**Series Total**: 8,500 / ~11,000 target words
**Next**: Part 4 - Integration & Workflows (Final, ~2,500 words)

