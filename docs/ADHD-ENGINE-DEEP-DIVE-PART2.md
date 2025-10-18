---
id: ADHD-ENGINE-DEEP-DIVE-PART2
title: Adhd Engine Deep Dive Part2
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# ADHD Engine Deep Dive - Part 2: Energy Matching & Task Selection

**Series**: ADHD Engine Deep Dive (Part 2 of 4)
**Author**: Dopemux Documentation Team
**Date**: 2025-10-05
**Prerequisites**: Read [Part 1: Architecture & Philosophy](ADHD-ENGINE-DEEP-DIVE-PART1.md)
**Reading Time**: ~15 minutes

---

## Table of Contents

1. [Introduction](#introduction)
2. [Energy Level Detection System](#energy-detection)
3. [Task Cognitive Load Calculation](#cognitive-load-calculation)
4. [Energy Matching Algorithm](#energy-matching)
5. [Attention State Compatibility](#attention-compatibility)
6. [Task Suitability Assessment](#task-suitability)
7. [Real-World Routing Examples](#routing-examples)
8. [Break Recommendation Engine](#break-recommendations)
9. [What's Next](#whats-next)

---

## Introduction

Part 1 established the **why** behind the ADHD Engine. Part 2 reveals the **how** - the sophisticated algorithms that make energy-aware task routing possible.

This is the **most innovative aspect** of Dopemux. No other development tool actively measures developer cognitive capacity in real-time and routes tasks accordingly. The result: **ADHD developers can be productive even during low-energy periods** by working on appropriately matched tasks.

### The Core Innovation

**Traditional Task Assignment**:
```
User: "What should I work on next?"
Tool: "Task #47 has highest priority" (ignores user state)
Result: Developer struggles with complex task during low energy, feels demoralized
```

**ADHD Engine Task Assignment**:
```
User: "What should I work on next?"
Engine: Analyzes current energy (LOW) + attention (SCATTERED) + task complexity
Engine: "🌟 Your energy is low. Here's a simple documentation task (complexity: 0.2)"
Result: Developer makes progress, gains momentum, preserves energy
```

The difference: **State-aware routing** vs blind priority sorting.

---

## Energy Level Detection System

### Real-Time Monitoring Architecture

The ADHD Engine runs **six background monitoring tasks** continuously (`engine.py:148-160`):

```python
monitors = [
    self._energy_level_monitor(),        # Every 5 minutes
    self._attention_state_monitor(),     # Every 2 minutes
    self._cognitive_load_monitor(),      # Every 1 minute
    self._break_timing_monitor(),        # Every 1 minute
    self._hyperfocus_protection_monitor(), # Every 1 minute
    self._context_switch_analyzer()      # Every 5 minutes
]
```

**Why Background Tasks?** Energy and attention states change gradually. Polling every 1-5 minutes captures transitions without overwhelming the system.

### Energy Assessment Algorithm

Energy detection combines **four behavioral signals** from ConPort and Redis (`engine.py:555-612`):

#### Signal 1: Task Completion Rate

**Indicator**: High completion rate = good energy, low rate = depleted energy

```python
# Get recent progress entries from ConPort (last hour)
task_completion_rate = completed_tasks / total_tasks

if task_completion_rate > 0.8:
    energy_score += 0.3  # Boost for high productivity
elif task_completion_rate < 0.3:
    energy_score -= 0.4  # Penalty for struggles
```

**Rationale**: ADHD developers complete tasks quickly when energy is high. Low completion suggests energy depletion or task-energy mismatch.

**Real Example**:
```
Last hour: 5 tasks started, 4 completed
Completion rate: 0.8 (80%)
Energy boost: +0.3
Interpretation: Developer is productive, energy likely HIGH or MEDIUM
```

#### Signal 2: Context Switching Frequency

**Indicator**: Excessive switching = scattered energy/attention

```python
context_switches = activity_data.get("context_switches", 0)

if context_switches > 5:  # More than 5 switches per hour
    energy_score -= 0.3
```

**Rationale**: High-energy ADHD developers can sustain focus. Low-energy developers context-switch frequently seeking easier tasks or stimulation.

**ConPort Integration**:
```python
# ActivityTracker queries ConPort custom_data
activity_log = self.conport.get_custom_data(
    category="activity_log",
    key=f"user_{user_id}"
)
context_switches = activity_log.get('context_switches', 0)
```

**Real Example**:
```
Last hour context switches:
- 10:15am: auth.py → docs/README.md
- 10:22am: docs/README.md → tests/test_auth.py
- 10:28am: tests/test_auth.py → package.json
- 10:35am: package.json → auth.py
- 10:40am: auth.py → Twitter (distraction)
- 10:45am: Twitter → auth.py

Total: 6 switches in 30 minutes
Energy penalty: -0.3
Interpretation: Scattered attention, likely LOW energy
```

#### Signal 3: Break Compliance

**Indicator**: Taking recommended breaks = sustainable energy management

```python
break_compliance = self._calculate_break_compliance(break_history)

if break_compliance < 0.5:  # Skipping >50% of breaks
    energy_score -= 0.2
```

**Rationale**: ADHD developers who skip breaks often crash hard later. Poor break compliance predicts energy depletion.

**Redis Integration**:
```python
# Break history stored in Redis for fast access
break_history = await self.redis.lrange(f"adhd:breaks:{user_id}", 0, 10)

# Calculate compliance: breaks_taken / breaks_recommended
compliance = len([b for b in break_history if b['taken']]) / len(break_history)
```

**Real Example**:
```
Last 10 break recommendations:
✅ 9:30am - 5min break taken
❌ 10:00am - Break skipped (hyperfocus)
❌ 10:30am - Break skipped
✅ 11:00am - 10min break taken
❌ 11:30am - Break skipped
...

Compliance: 3/10 = 0.3 (30%)
Energy penalty: -0.2
Interpretation: Unsustainable pace, crash likely
```

#### Signal 4: Time Since Last Break

**Indicator**: Long sessions without breaks = depleted energy

```python
time_since_last_break = activity_data.get("minutes_since_break", 0)

if time_since_last_break > 60:  # Over 1 hour
    energy_score -= 0.3
```

**Rationale**: ADHD developers' energy depletes predictably over time without breaks. 60+ minutes = significant depletion.

**Redis Timestamp Tracking**:
```python
last_break_str = await self.redis.get(f"adhd:last_break:{user_id}")
minutes_since = self._calculate_minutes_since(last_break_str)
```

**Real Example**:
```
Current time: 11:45am
Last break: 9:30am (2h 15min ago = 135 minutes)

Energy penalty: -0.3
Interpretation: Overdue for break, energy depleted
```

### Energy Level Mapping

After calculating the energy score from all four signals, map to discrete levels (`engine.py:588-598`):

```python
# Composite energy score (0.0-1.0+)
energy_score = 0.6  # Base
energy_score += task_completion_bonus  # +0.3 if high
energy_score -= context_switch_penalty  # -0.3 if excessive
energy_score -= break_compliance_penalty  # -0.2 if poor
energy_score -= time_since_break_penalty  # -0.3 if overdue

# Map to discrete levels
if energy_score >= 0.9:
    return EnergyLevel.HYPERFOCUS      # 90%+ = peak performance
elif energy_score >= 0.7:
    return EnergyLevel.HIGH            # 70-90% = strong capacity
elif energy_score >= 0.4:
    return EnergyLevel.MEDIUM          # 40-70% = normal capacity
elif energy_score >= 0.2:
    return EnergyLevel.LOW             # 20-40% = limited capacity
else:
    return EnergyLevel.VERY_LOW        # <20% = minimal capacity
```

**Why Discrete Levels?** Simpler than continuous scores for task routing. Clear boundaries enable binary decisions ("can I tackle this task?").

### Energy Detection Examples

#### Example 1: High Energy Developer

```
Activity Data:
- Task completion rate: 0.9 (9/10 tasks completed)
- Context switches: 2 (minimal)
- Break compliance: 0.8 (4/5 breaks taken)
- Time since break: 25 minutes

Calculation:
energy_score = 0.6 (base)
             + 0.3 (high completion)
             + 0.0 (low context switching)
             + 0.0 (good break compliance)
             + 0.0 (recent break)
             = 0.9

Result: EnergyLevel.HYPERFOCUS
```

#### Example 2: Low Energy Developer

```
Activity Data:
- Task completion rate: 0.2 (1/5 tasks completed)
- Context switches: 8 (excessive)
- Break compliance: 0.3 (1/3 breaks taken)
- Time since break: 75 minutes

Calculation:
energy_score = 0.6 (base)
             - 0.4 (low completion)
             - 0.3 (high context switching)
             - 0.2 (poor break compliance)
             - 0.3 (overdue break)
             = -0.6 → capped at 0.0

Result: EnergyLevel.VERY_LOW
```

#### Example 3: Transitioning Developer

```
Activity Data:
- Task completion rate: 0.6 (3/5 tasks completed)
- Context switches: 4 (moderate)
- Break compliance: 0.7 (3/4 breaks taken)
- Time since break: 30 minutes

Calculation:
energy_score = 0.6 (base)
             + 0.0 (moderate completion)
             + 0.0 (moderate switching)
             + 0.0 (decent compliance)
             + 0.0 (reasonable break)
             = 0.6

Result: EnergyLevel.MEDIUM
```

---

## Task Cognitive Load Calculation

Before matching tasks to energy, we must **quantify task complexity**. The ADHD Engine calculates cognitive load from five factors (`engine.py:239-284`):

### Factor 1: Base Complexity

**Source**: Serena complexity scoring (see `SERENA-V2-DEEP-DIVE.md`)

```python
# Task metadata from ConPort progress_entry
complexity = task_data.get("complexity_score", 0.5)  # 0.0-1.0

base_load = complexity * 0.4  # Weight: 40% of total load
```

**Example**:
```
Task: "Refactor authentication module"
Serena complexity: 0.8 (high complexity code)
Base load: 0.8 × 0.4 = 0.32
```

### Factor 2: Duration

**Rationale**: Longer tasks have higher cognitive load due to sustained attention requirements

```python
estimated_duration = task_data.get("estimated_minutes", 25)

# Max 0.3 for duration (longer tasks capped)
duration_factor = min(duration / 60.0, 0.3)
```

**Examples**:
```
10-minute task: 10/60 = 0.17
30-minute task: 30/60 = 0.30 (capped)
90-minute task: 90/60 = 1.5 → capped at 0.30
```

**Why Cap?** Prevents duration from dominating the score. A 90-minute simple task shouldn't have higher load than a 30-minute complex task.

### Factor 3: Task Type

**Rationale**: Different work types have inherently different cognitive loads

```python
task_type_loads = {
    "documentation": 0.1,   # Low load: mostly writing
    "research": 0.2,        # Low-medium: reading/analysis
    "testing": 0.2,         # Low-medium: mechanical process
    "architecture": 0.3,    # Medium-high: system thinking
    "implementation": 0.3,  # Medium-high: coding
    "debugging": 0.4        # High: problem-solving under uncertainty
}

# Detect type from task description
task_description = task_data.get("description", "").lower()
for task_type, load in task_type_loads.items():
    if task_type in task_description:
        task_type_load = load
        break
```

**Examples**:
```
"Update README documentation" → 0.1 (documentation)
"Debug memory leak in auth module" → 0.4 (debugging)
"Implement JWT validation" → 0.3 (implementation)
```

**ADHD Insight**: Debugging has highest load because it requires **sustained problem-solving with uncertain outcomes** - the hardest cognitive activity for ADHD brains.

### Factor 4: Dependencies

**Rationale**: More dependencies = more mental model juggling

```python
dependencies = task_data.get("dependencies", [])
dependency_load = min(len(dependencies) * 0.05, 0.1)  # Max 0.1
```

**Example**:
```
Task: "Implement user profile endpoint"
Dependencies: ["auth_middleware", "database_connection", "user_model"]
Dependency count: 3
Dependency load: 3 × 0.05 = 0.15 → capped at 0.10
```

**Why 0.05 per dependency?** Each dependency adds ~5% cognitive load for context tracking. Caps at 2 dependencies to prevent over-penalization.

### Total Cognitive Load Formula

```python
total_load = min(
    base_load + duration_factor + task_type_load + dependency_load,
    1.0  # Cap at 1.0
)
```

**Complete Example**:

```
Task: "Debug authentication timeout issue (estimated 45min)"
- Complexity score: 0.7 (complex code)
- Duration: 45 minutes
- Type: debugging
- Dependencies: ["auth_module", "session_manager", "redis_cache"]

Calculation:
base_load = 0.7 × 0.4 = 0.28
duration_factor = min(45/60, 0.3) = 0.3
task_type_load = 0.4 (debugging)
dependency_load = min(3 × 0.05, 0.1) = 0.1

total_load = min(0.28 + 0.3 + 0.4 + 0.1, 1.0)
           = min(1.08, 1.0)
           = 1.0 (EXTREME cognitive load)
```

### Cognitive Load Categories

After calculating total load, categorize for decision-making:

```python
def _categorize_cognitive_load(self, load: float) -> CognitiveLoadLevel:
    if load < 0.2:
        return CognitiveLoadLevel.MINIMAL    # Autopilot tasks
    elif load < 0.4:
        return CognitiveLoadLevel.LOW        # Easy tasks
    elif load < 0.6:
        return CognitiveLoadLevel.MODERATE   # Standard tasks
    elif load < 0.8:
        return CognitiveLoadLevel.HIGH       # Complex tasks
    else:
        return CognitiveLoadLevel.EXTREME    # Very complex tasks
```

---

## Energy Matching Algorithm

Now we can match **task cognitive load** to **current energy capacity** (`engine.py:286-320`).

### Energy Capacity Mapping

Each energy level provides a **cognitive capacity**:

```python
energy_capacity = {
    EnergyLevel.VERY_LOW: 0.1,    # 10% capacity
    EnergyLevel.LOW: 0.3,         # 30% capacity
    EnergyLevel.MEDIUM: 0.6,      # 60% capacity
    EnergyLevel.HIGH: 0.8,        # 80% capacity
    EnergyLevel.HYPERFOCUS: 1.0   # 100%+ capacity
}

current_capacity = energy_capacity[current_energy]
```

**Critical Insight**: These values represent **actual measured capacity**, not theoretical maximums. A VERY_LOW developer truly has only 10% of peak capacity available.

### Perfect Match Scoring

**Best case**: Task cognitive load matches energy capacity within 20%

```python
# Example: MEDIUM energy (0.6 capacity) + MODERATE task (0.5 load)
if abs(current_capacity - cognitive_load) < 0.2:
    return 1.0  # Perfect match score
```

**Why 20% tolerance?** Allows some flexibility. A 0.6 capacity developer can handle 0.4-0.8 load tasks comfortably.

### Mismatch Penalty

**Problem case**: Task load doesn't match capacity

```python
mismatch_penalty = abs(current_capacity - cognitive_load)
energy_match = max(0.0, 1.0 - (mismatch_penalty * 2))
```

**Examples**:

```
Scenario 1: VERY_LOW energy (0.1) + EXTREME task (1.0)
mismatch = |0.1 - 1.0| = 0.9
energy_match = 1.0 - (0.9 × 2) = 1.0 - 1.8 = -0.8 → capped at 0.0
Result: TERRIBLE match, don't recommend

Scenario 2: LOW energy (0.3) + MODERATE task (0.5)
mismatch = |0.3 - 0.5| = 0.2
energy_match = 1.0 - (0.2 × 2) = 1.0 - 0.4 = 0.6
Result: ACCEPTABLE match, could work with accommodations

Scenario 3: HIGH energy (0.8) + HIGH task (0.7)
mismatch = |0.8 - 0.7| = 0.1
energy_match = 1.0 - (0.1 × 2) = 1.0 - 0.2 = 0.8
Result: GOOD match, recommend
```

**Why 2x multiplier?** Mismatches are dangerous for ADHD developers. A 0.3 mismatch should reduce score by 0.6, making poor matches clearly unacceptable.

### Profile Adjustments

**Hyperfocus tendency** modifies scoring:

```python
if current_energy == EnergyLevel.HYPERFOCUS and profile.hyperfocus_tendency > 0.8:
    energy_match += 0.2  # Bonus for high hyperfocus tendency
```

**Rationale**: Some ADHD developers hyperfocus frequently (tendency: 0.9) and can handle higher loads during hyperfocus. Others rarely hyperfocus (tendency: 0.3) and shouldn't be pushed.

**Example**:
```
Developer A: hyperfocus_tendency = 0.9
Developer B: hyperfocus_tendency = 0.3

Both in HYPERFOCUS state with EXTREME task (1.0 load)

Developer A:
  base_match = 1.0 (perfect match)
  bonus = +0.2 (high tendency)
  final = 1.0 (capped)

Developer B:
  base_match = 1.0 (perfect match)
  bonus = 0.0 (low tendency, no bonus)
  final = 1.0

Result: Both get high scores, but Developer A gets confidence boost
```

---

## Attention State Compatibility

Energy isn't the only factor. **Attention state** determines task type compatibility (`engine.py:322-379`).

### Compatibility Matrix

Different attention states have different constraints:

```python
compatibility_matrix = {
    AttentionState.SCATTERED: {
        "max_cognitive_load": 0.3,      # Can't handle complex tasks
        "preferred_duration": 10,       # Short bursts only
        "complexity_penalty": 0.5       # Avoid complexity
    },
    AttentionState.TRANSITIONING: {
        "max_cognitive_load": 0.4,
        "preferred_duration": 15,
        "complexity_penalty": 0.3
    },
    AttentionState.FOCUSED: {
        "max_cognitive_load": 0.8,      # Standard capacity
        "preferred_duration": 25,       # Pomodoro-style
        "complexity_penalty": 0.0       # No penalty
    },
    AttentionState.HYPERFOCUSED: {
        "max_cognitive_load": 1.0,      # Can handle anything
        "preferred_duration": 90,       # Extended sessions
        "complexity_penalty": -0.2      # BONUS for complex tasks!
    },
    AttentionState.OVERWHELMED: {
        "max_cognitive_load": 0.1,      # Only trivial tasks
        "preferred_duration": 5,        # Micro-tasks only
        "complexity_penalty": 0.8       # Heavy complexity penalty
    }
}
```

### Load Compatibility Check

```python
max_load = state_config["max_cognitive_load"]

if cognitive_load > max_load:
    load_compatibility = max_load / max(cognitive_load, 0.1)
else:
    load_compatibility = 1.0
```

**Example**:
```
SCATTERED state (max_load: 0.3) + MODERATE task (load: 0.5)
load_compatibility = 0.3 / 0.5 = 0.6 (60% compatible)

Interpretation: Task is too complex for scattered attention
Recommendation: Break task down or wait for better attention state
```

### Duration Compatibility

```python
task_duration = task_data.get("estimated_minutes", 25)
preferred_duration = state_config["preferred_duration"]

duration_compatibility = 1.0 - abs(task_duration - preferred_duration) / max(preferred_duration, task_duration)
```

**Examples**:
```
SCATTERED (prefers 10min) + 30min task:
compatibility = 1.0 - |30 - 10| / 30 = 1.0 - 20/30 = 0.33 (poor)

FOCUSED (prefers 25min) + 25min task:
compatibility = 1.0 - |25 - 25| / 25 = 1.0 (perfect)

HYPERFOCUSED (prefers 90min) + 45min task:
compatibility = 1.0 - |45 - 90| / 90 = 1.0 - 45/90 = 0.5 (acceptable)
```

### Final Compatibility Score

```python
adjusted_compatibility = max(0.0, min(1.0,
    (load_compatibility + duration_compatibility) / 2 - complexity_penalty
))
```

**Complete Example**:

```
SCATTERED attention + "Debug auth timeout (45min, load: 0.7)"

load_compatibility = 0.3 / 0.7 = 0.43
duration_compatibility = 1.0 - |45 - 10| / 45 = 0.22
complexity_penalty = 0.5

adjusted = (0.43 + 0.22) / 2 - 0.5
         = 0.325 - 0.5
         = -0.175 → capped at 0.0

Result: INCOMPATIBLE - Don't recommend this task
```

---

## Task Suitability Assessment

The final routing decision combines **energy match** and **attention compatibility** (`engine.py:164-237`):

### Overall Suitability Score

```python
suitability_score = (energy_match * 0.5) + (attention_compatibility * 0.5)
```

**Why 50/50 split?** Both factors are equally critical. High energy with scattered attention is just as problematic as focused attention with low energy.

### Complete Assessment Flow

```python
async def assess_task_suitability(self, user_id: str, task_data: Dict) -> Dict:
    # 1. Get current state
    current_energy = self.current_energy_levels.get(user_id, EnergyLevel.MEDIUM)
    current_attention = self.current_attention_states.get(user_id, AttentionState.FOCUSED)
    user_profile = self.user_profiles.get(user_id)

    # 2. Calculate task cognitive load
    cognitive_load = self._calculate_task_cognitive_load(...)

    # 3. Energy matching
    energy_match = self._assess_energy_match(current_energy, cognitive_load, user_profile)

    # 4. Attention compatibility
    attention_compatibility = self._assess_attention_compatibility(...)

    # 5. Overall suitability
    suitability_score = (energy_match * 0.5) + (attention_compatibility * 0.5)

    # 6. Generate recommendations
    recommendations = await self._generate_task_recommendations(...)

    return {
        "suitability_score": suitability_score,
        "energy_match": energy_match,
        "attention_compatibility": attention_compatibility,
        "cognitive_load": cognitive_load,
        "recommendations": recommendations,
        "adhd_insights": {...}
    }
```

---

## Real-World Routing Examples

### Example 1: Perfect Match Scenario

**Developer State**:
- Energy: HIGH (0.8 capacity)
- Attention: FOCUSED
- Time since break: 15 minutes
- Task completion rate: 85%

**Task**: "Implement user profile API endpoint"
- Complexity: 0.7
- Duration: 30 minutes
- Type: implementation
- Dependencies: 2
- **Cognitive load**: 0.28 + 0.3 + 0.3 + 0.1 = 0.98 → capped at 0.8 (HIGH)

**Assessment**:
```
energy_match:
  mismatch = |0.8 - 0.8| = 0.0
  score = 1.0 (perfect)

attention_compatibility:
  load_ok = 0.8 ≤ 0.8 (focused max) → 1.0
  duration = 1.0 - |30 - 25| / 30 = 0.83
  penalty = 0.0
  score = (1.0 + 0.83) / 2 - 0.0 = 0.92

suitability = (1.0 * 0.5) + (0.92 * 0.5) = 0.96
```

**Recommendation**: ✅ **EXCELLENT MATCH - Start immediately**

### Example 2: Energy Mismatch

**Developer State**:
- Energy: VERY_LOW (0.1 capacity)
- Attention: SCATTERED
- Time since break: 90 minutes (overdue!)
- Task completion rate: 20%

**Task**: "Refactor authentication module"
- Complexity: 0.9
- Duration: 60 minutes
- Type: architecture
- Dependencies: 5
- **Cognitive load**: 0.36 + 0.3 + 0.3 + 0.1 = 1.0 (EXTREME)

**Assessment**:
```
energy_match:
  mismatch = |0.1 - 1.0| = 0.9
  score = 1.0 - (0.9 × 2) = -0.8 → capped at 0.0

attention_compatibility:
  load_ok = 0.3 / 1.0 = 0.3 (way over scattered max)
  duration = 1.0 - |60 - 10| / 60 = 0.17
  penalty = 0.5
  score = (0.3 + 0.17) / 2 - 0.5 = -0.265 → capped at 0.0

suitability = (0.0 * 0.5) + (0.0 * 0.5) = 0.0
```

**Recommendations**:
```
🛑 INCOMPATIBLE TASK - DO NOT START

Suggested actions:
1. ⏸️ Take 15-minute break (you're 90min overdue)
2. 🌟 After break, try simpler task:
   - "Update README" (complexity: 0.2)
   - "Fix typo in error messages" (complexity: 0.1)
3. 📅 Schedule complex task for tomorrow morning (peak energy)
```

### Example 3: Acceptable with Accommodations

**Developer State**:
- Energy: MEDIUM (0.6 capacity)
- Attention: TRANSITIONING
- Time since break: 40 minutes
- Task completion rate: 60%

**Task**: "Write integration tests for auth module"
- Complexity: 0.5
- Duration: 30 minutes
- Type: testing
- Dependencies: 1
- **Cognitive load**: 0.2 + 0.3 + 0.2 + 0.05 = 0.75 → 0.55 (MODERATE)

**Assessment**:
```
energy_match:
  mismatch = |0.6 - 0.55| = 0.05
  score = 1.0 - (0.05 × 2) = 0.9

attention_compatibility:
  load_ok = 0.55 > 0.4 (transitioning max) → 0.4/0.55 = 0.73
  duration = 1.0 - |30 - 15| / 30 = 0.5
  penalty = 0.3
  score = (0.73 + 0.5) / 2 - 0.3 = 0.32

suitability = (0.9 * 0.5) + (0.32 * 0.5) = 0.61
```

**Recommendation**: ⚠️ **ACCEPTABLE with accommodations**

```
Suggested accommodations:
1. 🔄 Use 15-minute focus blocks (shorter than 30min estimate)
2. ✅ Start with simplest test case for momentum
3. ⏰ Set timer to prevent overrun
4. 💡 Take 5min break halfway through

Cognitive benefit: Accommodations reduce effective load from 0.55 → 0.4
After adjustment: Task becomes better match for transitioning state
```

---

## Break Recommendation Engine

The ADHD Engine doesn't just route tasks - it **protects developers from burnout** through intelligent break recommendations (`engine.py:381-451`).

### Break Recommendation Triggers

#### Trigger 1: Energy-Cognitive Load Mismatch

```python
if energy in [EnergyLevel.VERY_LOW, EnergyLevel.LOW] and cognitive_load > 0.4:
    recommendations.append(AccommodationRecommendation(
        accommodation_type="energy_mismatch",
        urgency="soon",
        message="💙 This task might be challenging at your current energy level",
        suggested_actions=[
            "Take a 10-minute energizing break",
            "Switch to a simpler task first",
            "Break this task into smaller pieces"
        ],
        cognitive_benefit="Prevents frustration and preserves energy"
    ))
```

**Example**: VERY_LOW energy developer attempting MODERATE task

#### Trigger 2: Scattered Attention with Long Task

```python
if attention == AttentionState.SCATTERED and task_duration > 15:
    recommendations.append(AccommodationRecommendation(
        accommodation_type="attention_fragmentation",
        urgency="immediate",
        message="🌀 Consider breaking this task down - attention seems scattered",
        suggested_actions=[
            "Use 10-minute focus blocks",
            "Start with the simplest part",
            "Enable focus mode to reduce distractions"
        ]
    ))
```

#### Trigger 3: Hyperfocus Protection

```python
if energy == EnergyLevel.HYPERFOCUS and task_duration > 60:
    recommendations.append(AccommodationRecommendation(
        accommodation_type="hyperfocus_protection",
        urgency="when_convenient",
        message="🚀 Hyperfocus detected - setting up protection boundaries",
        suggested_actions=[
            "Automatic break reminders every 30 minutes",
            "Hydration reminders",
            "Eye rest breaks"
        ],
        cognitive_benefit="Prevents hyperfocus burnout and maintains health"
    ))
```

**Critical**: This is **harm reduction**, not productivity optimization. Hyperfocus can last 8+ hours without breaks, causing health damage.

### Break Timing Intelligence

The engine uses **multiple signals** to determine optimal break timing:

```python
# Signal 1: Time since last break (Redis)
last_break_time = await self.redis.get(f"adhd:last_break:{user_id}")
minutes_since = calculate_minutes_since(last_break_time)

# Signal 2: Task completion trajectory (ConPort)
recent_tasks = self.conport.get_progress_entries(hours_ago=1)
completion_trend = analyze_completion_trend(recent_tasks)

# Signal 3: Energy level trend (Redis)
energy_history = await self.redis.lrange(f"adhd:energy_history:{user_id}", 0, 5)
energy_declining = is_energy_declining(energy_history)

# Recommendation
if minutes_since > 25 and (completion_trend == "declining" or energy_declining):
    urgency = "immediate"
elif minutes_since > 45:
    urgency = "soon"
elif minutes_since > 60:
    urgency = "mandatory"  # Forced break
```

---

## What's Next

This completes Part 2's exploration of **energy matching and task selection algorithms**. You now understand:

✅ Real-time energy detection from 4 behavioral signals
✅ Cognitive load calculation from 5 task factors
✅ Energy matching algorithm with mismatch penalties
✅ Attention state compatibility matrix
✅ Complete task suitability assessment flow
✅ Real-world routing examples
✅ Break recommendation intelligence

### Coming in Part 3: Attention Management & Session Orchestration

Part 3 will cover the **protective and supportive systems** that keep ADHD developers healthy and productive:

**Topics Covered**:
- Attention state detection algorithms
- Hyperfocus protection (3-tier intervention system)
- Context preservation and restoration
- Session orchestration (25min focus blocks)
- Auto-save and interruption recovery
- Context switch minimization strategies

**Preview Question**: How does the engine detect when a developer is transitioning from "focused" to "hyperfocused" state, and what interventions does it trigger to prevent burnout?

The answer involves real-time activity pattern analysis, Redis state tracking, background monitoring tasks, and graduated intervention escalation. Part 3 reveals the complete protective system.

---

**Word Count**: ~3,000 words
**Next**: Part 3 - Attention Management & Session Orchestration (3,000 words)
