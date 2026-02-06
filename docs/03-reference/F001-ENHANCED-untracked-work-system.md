---
id: F001-ENHANCED-untracked-work-system
title: 'F001 Enhanced: Complete Untracked Work Management System'
type: reference
owner: '@hu3mann'
date: '2025-10-18'
status: design
adhd_score: 10.0
tags:
- adhd-critical
- task-completion
- false-starts
- untracked-work
- gentle-nudging
last_review: '2025-10-18'
next_review: '2025-11-18'
prelude: Enhanced F001 specification adding false-starts dashboard, design-first prompting,
  abandoned work revival, and prioritization context to the base untracked work detection.
author: '@hu3mann'
---
# F001 Enhanced: Complete Untracked Work Management System

**Building on F001 Base Specification**
**Version:** 3.0 (Enhanced with 4 Critical Features)
**Status:** Design Complete - Ready for Implementation Planning

---

## Executive Summary

**Base F001 Provides:**
- ✅ Multi-signal untracked work detection
- ✅ Gentle nudging UX (Track/Snooze/Ignore)
- ✅ Privacy-first, configurable architecture
- ✅ ADHD-optimized timing and backoff

**Critical Enhancements Add:**
- 🆕 **E1**: Aggregate "50 false-starts" dashboard
- 🆕 **E2**: Design-first prompting (ADR/RFC integration)
- 🆕 **E3**: Abandoned work revival suggestions
- 🆕 **E4**: Prioritization context helper

**2025 Research Validation:**
- Cleveland Clinic (April 2025): Task completion is THE new ADHD management paradigm
- CBT Meta-Analysis (2024): External reminders + task breakdown = 87% symptom improvement
- Digital Interventions (2024): Self-guided systems effective (g = −0.32)

---

## Enhancement 1: False-Starts Dashboard

### Purpose
Show aggregate statistics to create awareness without shame.

### User Experience

**Session Start Message:**
```
┌─────────────────────────────────────────────────┐
│ 📊 UNFINISHED WORK SUMMARY                      │
├─────────────────────────────────────────────────┤
│ Total unfinished projects: 47                   │
│                                                  │
│ Status breakdown:                                │
│   🔄 Acknowledged (still working): 12            │
│   ⏸️  Snoozed: 8                                 │
│   🗑️  Abandoned: 27                              │
│                                                  │
│ New untracked work detected:                     │
│   ⚠️  "API refactor" (5 files, feature/api)     │
│                                                  │
│ ❓ Sure you want to make it 48?                 │
│                                                  │
│ Quick actions:                                   │
│   [1] Track this work in ConPort                 │
│   [2] Create ADR/RFC first (formal design) 📐   │
│   [3] Snooze (1h | 4h | 1d)                     │
│   [4] View abandoned projects (maybe revive?)    │
│   [5] Ignore this work                           │
│   [Enter] Acknowledge and continue               │
└─────────────────────────────────────────────────┘
```

### Technical Implementation

**New ConPort Query:**
```python
async def get_false_starts_summary(workspace_id: str) -> dict:
    """Get aggregate unfinished work statistics"""

    # Query all untracked work
    untracked = await conport.get_custom_data(
        workspace_id=workspace_id,
        category="untracked_work"
    )

    # Calculate stats
    stats = {
        "total_unfinished": 0,
        "acknowledged": 0,
        "snoozed": 0,
        "abandoned": 0,
        "oldest_date": None,
        "newest_date": None,
        "top_abandoned": []  # For revival feature
    }

    for work in untracked:
        data = work["value"]
        status = data.get("status", "detected")

        if status != "converted_to_task":
            stats["total_unfinished"] += 1

        if status == "acknowledged":
            stats["acknowledged"] += 1
        elif status == "snoozed":
            stats["snoozed"] += 1
        elif status == "abandoned":
            stats["abandoned"] += 1
            stats["top_abandoned"].append({
                "name": data["auto_generated_name"],
                "detected_at": data["detected_at"],
                "files": data["detection_signals"]["git_uncommitted_files"]
            })

    # Sort abandoned by recency for revival suggestions
    stats["top_abandoned"].sort(
        key=lambda x: x["detected_at"],
        reverse=True
    )
    stats["top_abandoned"] = stats["top_abandoned"][:5]  # Top 5 only

    return stats
```

**Display Logic:**
```python
def format_dashboard_message(stats: dict, new_work_name: str) -> str:
    """Format the 'Sure you want to make it 48?' message"""

    total = stats["total_unfinished"]

    # Gentle, non-judgmental messaging
    if total == 0:
        return "✨ Clean slate! No unfinished projects right now."
    elif total <= 5:
        return f"📊 You have {total} unfinished projects. Let's track this one properly!"
    elif total <= 20:
        return f"📊 {total} unfinished projects. Sure you want to add another?"
    else:
        # Gentle reality check without shame
        return f"📊 You have {total} unfinished projects. Sure you want to make it {total + 1}?\n\n💡 Maybe finish one first? Or is this truly urgent?"
```

**ADHD Accommodations:**
- **No Shame**: Language is factual, not judgmental
- **Progressive Disclosure**: Summary first, details on request
- **Visual Clarity**: Color-coded status, emoji indicators
- **Actionable**: Every stat links to actions (view abandoned, track new, etc.)

---

## Enhancement 2: Design-First Prompting

### Purpose
Encourage formal design (ADR/RFC) for substantial features before implementation.

### Detection Heuristic

**When to Suggest Design-First:**
```python
def should_prompt_for_design(signals: DetectionSignals) -> bool:
    """Determine if work warrants formal design"""

    # Heuristic 1: Significant code volume
    if len(signals.git_uncommitted_files) >= 5:
        return True

    # Heuristic 2: Multiple directories (cross-cutting)
    unique_dirs = set(Path(f).parent for f in signals.git_uncommitted_files)
    if len(unique_dirs) >= 3:
        return True

    # Heuristic 3: Architecture/core files
    architecture_indicators = [
        'architecture', 'system', 'core', 'engine',
        'orchestrator', 'coordinator', 'manager'
    ]
    files_str = ' '.join(signals.git_uncommitted_files).lower()
    if any(indicator in files_str for indicator in architecture_indicators):
        return True

    # Heuristic 4: New service or major component
    if any('services/' in f or 'components/' in f
           for f in signals.new_files_created):
        dirs_created = set(Path(f).parent for f in signals.new_files_created)
        if len(dirs_created) >= 2:  # Creating multiple directories
            return True

    return False
```

### User Experience

**Enhanced Prompt:**
```
┌─────────────────────────────────────────────────┐
│ 🏗️  SIGNIFICANT WORK DETECTED                   │
├─────────────────────────────────────────────────┤
│ Detected: "API refactor" (8 files, 3 modules)   │
│                                                  │
│ This looks like a substantial change!            │
│                                                  │
│ 💡 Have you designed this formally?             │
│                                                  │
│ Options:                                         │
│   [1] Quick track (ConPort task only)           │
│   [2] Create ADR (architecture decision) 📐     │
│   [3] Create RFC (request for comments) 📝      │
│   [4] Brainstorm first (/sc:brainstorm) 🧠      │
│   [5] Just experimenting (snooze/ignore)        │
│                                                  │
│ ℹ️  Formal design helps:                        │
│   • Clarify the "why" before the "how"          │
│   • Catch issues early                           │
│   • Share context with future you               │
│   • Build knowledge base                         │
└─────────────────────────────────────────────────┘
```

### Integration with Slash Commands

**Option 2: Create ADR**
```python
async def create_adr_for_untracked_work(untracked_work: dict):
    """Launch ADR creation with pre-filled context"""

    # Pre-fill ADR template
    adr_context = {
        "title": f"ADR: {untracked_work['auto_generated_name']}",
        "context": f"Detected untracked work in {', '.join(untracked_work['detection_signals']['git_branch'])}",
        "affected_files": untracked_work['detection_signals']['git_uncommitted_files'],
        "decision_drivers": [
            "Feature requested",
            "Technical improvement needed"
        ]
    }

    # Launch /sc:design with context
    await run_slash_command("/sc:design", context=adr_context)

    # Update untracked work status
    await conport.update_custom_data(
        workspace_id=workspace_id,
        category="untracked_work",
        key=untracked_work["key"],
        patch={"status": "designing", "adr_in_progress": True}
    )
```

**Option 4: Brainstorm First**
```python
async def brainstorm_untracked_work(untracked_work: dict):
    """Launch brainstorming session"""

    prompt = f"""I've started work on {untracked_work['auto_generated_name']}.

    Files involved: {', '.join(untracked_work['detection_signals']['git_uncommitted_files'])}

    Help me think through:
    - What problem am I actually solving?
    - Is this the right approach?
    - What are the alternatives?
    - Should this be designed formally?
    """

    await run_slash_command("/sc:brainstorm", prompt=prompt)
```

**ADHD Benefit**: Reduces impulsive coding, encourages thoughtful planning

---

## Enhancement 3: Abandoned Work Revival

### Purpose
Surface "cool ideas you started but never finished" for potential revival.

### User Experience

**Weekly/Monthly Revival Prompt:**
```
┌─────────────────────────────────────────────────┐
│ 💡 REMEMBER THESE COOL IDEAS?                   │
├─────────────────────────────────────────────────┤
│ You started these but never finished:            │
│                                                  │
│ 1. "Dark mode system" (6 months ago)            │
│    📁 3 files in feature/dark-mode              │
│    🏷️  ui, design-system, theming               │
│    [Revive] [Archive Forever] [Details]         │
│                                                  │
│ 2. "Real-time collaboration" (4 months ago)     │
│    📁 8 files in feature/collab                 │
│    🏷️  websockets, sync, multi-user             │
│    [Revive] [Archive Forever] [Details]         │
│                                                  │
│ 3. "Plugin system architecture" (2 months ago)  │
│    📁 5 files in feature/plugins                │
│    🏷️  extensibility, api, architecture         │
│    [Revive] [Archive Forever] [Details]         │
│                                                  │
│ [Skip] No thanks, not interested                │
└─────────────────────────────────────────────────┘
```

### Revival Timing

**When to Show:**
- **Weekly**: During low-energy sessions (creative work suits low energy)
- **Monthly**: First of month (natural reflection point)
- **On Request**: `/dx:abandoned` command
- **Smart Timing**: Not when user is deep in focused work

**Filtering Logic:**
```python
async def get_revival_candidates(workspace_id: str) -> list:
    """Get abandoned work worth reviving"""

    untracked = await conport.get_custom_data(
        workspace_id=workspace_id,
        category="untracked_work"
    )

    candidates = []
    for work in untracked:
        data = work["value"]

        # Only abandoned work
        if data["status"] != "abandoned":
            continue

        # At least 7 days old (avoid recent abandons)
        age_days = (datetime.now() - datetime.fromisoformat(data["detected_at"])).days
        if age_days < 7:
            continue

        # Score revival potential
        revival_score = calculate_revival_score(data)
        if revival_score < 0.5:
            continue

        candidates.append({
            "work": data,
            "age_days": age_days,
            "revival_score": revival_score
        })

    # Sort by revival score (interesting ideas first)
    candidates.sort(key=lambda x: x["revival_score"], reverse=True)
    return candidates[:5]  # Top 5 only (ADHD limit)


def calculate_revival_score(work_data: dict) -> float:
    """Score abandoned work by revival potential"""
    score = 0.0

    # More files = more substantial work = worth reviving
    file_count = len(work_data["detection_signals"]["git_uncommitted_files"])
    if file_count >= 5:
        score += 0.3
    elif file_count >= 3:
        score += 0.2

    # Feature branch = intentional work = worth reviving
    branch = work_data["detection_signals"].get("git_branch", "")
    if branch.startswith("feature/"):
        score += 0.3

    # Recent enough to still be relevant (< 6 months)
    age_days = (datetime.now() - datetime.fromisoformat(work_data["detected_at"])).days
    if age_days < 30:
        score += 0.2
    elif age_days < 90:
        score += 0.15
    elif age_days < 180:
        score += 0.1

    # User notes indicate interest
    if work_data.get("user_notes"):
        score += 0.2

    return min(score, 1.0)
```

**Revival Actions:**

**[Revive]**:
1. Restore git branch (if exists)
2. Create ConPort task with context
3. Ask: "Want to /sc:design this properly?"
4. Update status to `revived`

**[Archive Forever]**:
1. Change status to `archived_permanent`
2. Never show in revival suggestions again
3. Still queryable if user wants to browse

**[Details]**:
1. Show full file list
2. Show git branch and commit history
3. Show original detection signals
4. Ask: "Want to revive this?"

---

## Enhancement 2: Design-First Prompting

### Purpose
Encourage ADR/RFC creation for substantial features before implementation.

### Detection Criteria

**Substantial Work Indicators:**
```python
def is_substantial_feature(signals: DetectionSignals) -> tuple[bool, str]:
    """Determine if work needs formal design"""

    reasons = []
    substantial = False

    # Indicator 1: File count (5+ files = substantial)
    if len(signals.git_uncommitted_files) >= 5:
        substantial = True
        reasons.append(f"{len(signals.git_uncommitted_files)} files modified")

    # Indicator 2: Cross-cutting (3+ directories)
    dirs = set(Path(f).parent for f in signals.git_uncommitted_files)
    if len(dirs) >= 3:
        substantial = True
        reasons.append(f"Changes across {len(dirs)} modules")

    # Indicator 3: Architecture keywords
    arch_keywords = ['architecture', 'system', 'engine', 'core',
                     'orchestrator', 'coordinator', 'manager', 'service']
    files_str = ' '.join(signals.git_uncommitted_files).lower()
    if any(kw in files_str for kw in arch_keywords):
        substantial = True
        reasons.append("Architecture/core changes detected")

    # Indicator 4: New service/component creation
    new_dirs = set(Path(f).parent for f in signals.new_files_created)
    if any('services/' in str(d) or 'components/' in str(d) for d in new_dirs):
        if len(signals.new_files_created) >= 3:
            substantial = True
            reasons.append("New service/component being created")

    return substantial, ' | '.join(reasons) if reasons else ""
```

### Enhanced UX Flow

**Step 1: Detection**
```
🏗️  SUBSTANTIAL WORK DETECTED

Detected: "API refactor"
Scope: 8 files across 3 modules

This looks like a significant architectural change!
```

**Step 2: Design Prompt**
```
💡 Recommendation: Design Before Implementation

Benefits:
  ✅ Clarify the "why" and "what" first
  ✅ Catch design issues early (cheaper than code fixes)
  ✅ Document rationale for future you
  ✅ Enable collaboration and review

Options:
  [1] Quick track (ConPort task, skip design)
  [2] Create ADR (architectural decision record) 📐
  [3] Create RFC (request for comments) 📝
  [4] Brainstorm (/sc:brainstorm - interactive) 🧠
  [5] Already designed (show me the doc)

Choose option [1-5]:
```

**Step 3: Design Workflow Integration**

**If user selects [2] Create ADR:**
```python
async def launch_adr_creation(untracked_work: dict):
    """Create ADR with pre-filled context"""

    # Use ADR template
    adr_num = await get_next_adr_number()
    adr_path = f"docs/90-adr/ADR-{adr_num}-{slugify(untracked_work['auto_generated_name'])}.md"

    # Pre-fill template
    template = load_adr_template()
    template.fill({
        "title": untracked_work['auto_generated_name'],
        "context": f"Detected untracked work with {len(signals.git_uncommitted_files)} files changed",
        "affected_components": extract_components_from_files(signals.git_uncommitted_files),
        "status": "draft"
    })

    # Write draft ADR
    await write_file(adr_path, template.render())

    # Update untracked work
    await conport.update_custom_data(
        workspace_id=workspace_id,
        category="untracked_work",
        key=untracked_work["key"],
        patch={
            "status": "designing",
            "adr_path": adr_path,
            "design_started_at": datetime.now().isoformat()
        }
    )

    # Open ADR for editing
    print(f"✅ Created draft ADR: {adr_path}")
    print(f"📝 Please complete the design, then return to track implementation.")
```

**If user selects [4] Brainstorm:**
```python
async def launch_brainstorm(untracked_work: dict):
    """Interactive brainstorming session"""

    context = f"""I've started work on {untracked_work['auto_generated_name']}.

    Files involved:
    {chr(10).join('  - ' + f for f in signals.git_uncommitted_files)}

    Let's think through:
    1. What problem am I solving?
    2. Is this the right approach?
    3. What are the alternatives?
    4. What are the trade-offs?
    5. Does this need formal design (ADR/RFC)?
    """

    # Launch /sc:brainstorm with Zen MCP
    await run_slash_command("/sc:brainstorm", context=context)
```

**ADHD Benefit**: Reduces impulsive implementation, channels energy into thoughtful planning

---

## Enhancement 3: Abandoned Work Revival System

### Purpose
Help users rediscover and potentially revive interesting abandoned projects.

### Data Structure

**Abandoned Work Metadata:**
```json
{
  "category": "untracked_work",
  "key": "untracked_work_abc123",
  "value": {
    "status": "abandoned",
    "abandoned_at": "2025-04-15T10:30:00Z",
    "abandoned_reason": "user_selected_ignore",
    "revival_score": 0.75,
    "revival_metadata": {
      "interesting_files": [
        "services/plugin-system/core.py",
        "services/plugin-system/loader.py"
      ],
      "keywords": ["plugin", "extensibility", "api"],
      "estimated_completion_pct": 30,
      "git_branch_exists": true,
      "git_branch_name": "feature/plugins"
    },
    "revival_attempts": 0,
    "last_shown_in_revival": null
  }
}
```

### Revival UI Patterns

**Pattern 1: Weekly Revival Email (Non-Intrusive)**
```
Subject: 💡 5 Cool Ideas You Started

Hey! Remember these?

1. Dark Mode System (6 months ago)
   - 3 files ready, 40% done
   - Last: "Was implementing theme toggle"
   [Revive in 1-Click]

2. Plugin Architecture (4 months ago)
   - 5 files, 30% done
   - Last: "Designed core loader interface"
   [Revive in 1-Click]

No pressure - just thought you might want to finish one! 😊
```

**Pattern 2: Contextual Suggestions**
```python
async def suggest_revival_during_low_energy():
    """Show revival suggestions during low-energy periods"""

    # Check current energy level
    energy = await adhd_engine.get_energy_level(user_id)

    # Low energy = good time for creative/revisiting (not new implementation)
    if energy.level == "low" and energy.attention_state != "scattered":
        candidates = await get_revival_candidates(workspace_id)

        if candidates:
            print("""
            ⚡ Energy check: Low energy detected

            💡 Low energy is perfect for:
              • Revisiting old ideas
              • Creative brainstorming
              • Light refactoring

            Want to revive an abandoned project instead of starting fresh?
            [View Abandoned Work] [Start New] [Take Break]
            """)
```

**Pattern 3: Serendipitous Discovery**
```python
async def show_related_abandoned_work(current_task: str):
    """Show abandoned work related to current task"""

    # Semantic search for related abandoned work
    abandoned = await query_abandoned_with_keywords(current_task)

    if abandoned:
        print(f"""
        🔍 Related abandoned work found:

        While working on "{current_task}", noticed you previously
        started "{abandoned[0]['name']}" which might be related.

        [View Details] [Ignore]
        """)
```

### Revival Analytics

**Track What Gets Revived:**
```python
revival_analytics = {
    "total_abandoned": 47,
    "revival_attempts": 8,
    "successful_revivals": 3,  # Converted to completed tasks
    "failed_revivals": 2,       # Re-abandoned
    "in_progress_revivals": 3,  # Currently being worked on
    "revival_rate": 0.375       # 3/8 = 37.5% success
}
```

---

## Enhancement 4: Prioritization Helper

### Purpose
Help users decide if new untracked work is worth starting given current commitments.

### User Experience

**Contextual Prioritization Display:**
```
┌─────────────────────────────────────────────────┐
│ ⚖️  PRIORITIZATION CHECK                        │
├─────────────────────────────────────────────────┤
│ New work detected: "API refactor"               │
│                                                  │
│ Your current commitments:                        │
│   🔄 3 tasks IN_PROGRESS:                       │
│      • Auth system (complexity: 0.7, 15m left)  │
│      • Bug fix #142 (complexity: 0.4, 30m left) │
│      • Docs update (complexity: 0.2, 10m left)  │
│                                                  │
│   ⏳ 12 tasks TODO (roadmap)                    │
│                                                  │
│ 🧠 Cognitive Load Assessment:                   │
│   Current: 67% (moderate)                        │
│   +New work: 89% (high risk of overwhelm)       │
│                                                  │
│ 💡 Recommendation:                              │
│   Consider finishing one IN_PROGRESS task       │
│   before starting new work.                      │
│                                                  │
│ Options:                                         │
│   [1] View IN_PROGRESS tasks (finish one first) │
│   [2] Track anyway (I know what I'm doing)      │
│   [3] Snooze new work (come back later)         │
└─────────────────────────────────────────────────┘
```

### Cognitive Load Calculation

```python
def calculate_cognitive_load_impact(
    current_tasks: list,
    new_work: dict
) -> dict:
    """Calculate cognitive load impact of adding new work"""

    # Current load
    current_load = sum(
        task.get("adhd_metadata", {}).get("complexity_score", 0.5)
        for task in current_tasks
        if task["status"] == "IN_PROGRESS"
    )

    # Estimate new work complexity
    new_complexity = estimate_complexity_from_signals(
        new_work["detection_signals"]
    )

    # Calculate impact
    total_load = current_load + new_complexity

    # Normalize to 0-1 scale (assume max 5 concurrent tasks)
    normalized_load = min(total_load / 5.0, 1.0)

    return {
        "current_load_pct": int(current_load / 5.0 * 100),
        "projected_load_pct": int(normalized_load * 100),
        "risk_level": "low" if normalized_load < 0.6 else
                      "moderate" if normalized_load < 0.8 else "high",
        "recommendation": get_recommendation(normalized_load)
    }


def get_recommendation(load: float) -> str:
    """Get ADHD-friendly recommendation"""
    if load < 0.6:
        return "✅ Good capacity - safe to add new work"
    elif load < 0.8:
        return "⚠️ Moderate load - consider finishing something first"
    else:
        return "🚨 High load - strongly recommend finishing current work before adding more"
```

### Comparison View

**Show vs Current Tasks:**
```python
async def show_prioritization_comparison(new_work: dict, current_tasks: list):
    """Help user compare new work vs current commitments"""

    print("""
    ⚖️  Is this new work more important?

    Current IN_PROGRESS tasks:
    """)

    for i, task in enumerate(current_tasks[:3], 1):  # Max 3 for comparison
        importance = task.get("adhd_metadata", {}).get("importance", "medium")
        complexity = task.get("adhd_metadata", {}).get("complexity_score", 0.5)

        print(f"""
        {i}. {task['description']}
           Importance: {importance} | Complexity: {complexity:.1f}
           Time invested: {task.get('time_spent_minutes', 0)}min
        """)

    print(f"""

    NEW: {new_work['auto_generated_name']}
         Estimated complexity: {estimate_complexity(new_work)}
         Time to complete: Unknown

    Questions to consider:
      • Is this more urgent than current tasks?
      • Will this help current tasks or distract from them?
      • Can this wait until current work is done?

    [Track Anyway] [Defer to Roadmap] [Snooze 1 Day]
    """)
```

---

## Integration Architecture

### System Components

**F001 Enhanced System:**
```
┌─────────────────────────────────────────────┐
│ F001 Core Detection Engine                  │
│ • Git signal monitoring                     │
│ • ConPort absence detection                 │
│ • Multi-signal confidence scoring           │
└──────────────┬──────────────────────────────┘
               │
               ├──> Enhancement 1: Dashboard
               │    └─> get_false_starts_summary()
               │
               ├──> Enhancement 2: Design Prompting
               │    └─> is_substantial_feature()
               │    └─> launch_adr_creation()
               │
               ├──> Enhancement 3: Revival System
               │    └─> get_revival_candidates()
               │    └─> calculate_revival_score()
               │
               └──> Enhancement 4: Prioritization
                    └─> calculate_cognitive_load_impact()
                    └─> show_prioritization_comparison()
```

### ConPort Schema Extensions

**New Categories:**
```python
# Existing from F001
"untracked_work" - Individual untracked work items

# New for enhancements
"revival_analytics" - Track revival success rates
"false_starts_history" - Historical aggregate stats
"design_prompts_log" - Track when users chose design-first
```

### Slash Command Integration

**New Commands:**
- `/dx:unfinished` - Show false-starts dashboard (E1)
- `/dx:abandoned` - Browse abandoned work for revival (E3)
- `/dx:load-check` - Check current cognitive load (E4)

**Enhanced Existing:**
- `/dx:implement` - Integrated prioritization check
- `/dx:session start` - Show dashboard + check for untracked work
- `/sc:design` - Can be launched from design-first prompt

---

## Implementation Roadmap

### Phase 1: F001 Core (Week 1-2)
**Deliverables:**
- Detection engine with multi-signal confidence
- ConPort storage schema
- Basic 3-option UX (Track/Snooze/Ignore)
- Exponential backoff reminder logic

**Testing:**
- Detect at least 80% of real untracked work
- False positive rate < 15%
- Reminder timing works correctly

**Value**: 80% of total feature value

---

### Phase 2: Dashboard (Week 2)
**Deliverables:**
- Aggregate stats query function
- "50 false-starts" messaging
- Status breakdown display
- Integration with session start

**Testing:**
- Stats calculated accurately
- Display doesn't overwhelm (3-5 items max)
- Messaging is encouraging, not shaming

**Value**: +10% (critical for user's main ask)

---

### Phase 3: Design-First & Prioritization (Week 3)
**Deliverables:**
- Substantial work detection heuristic
- ADR/RFC integration
- Cognitive load calculator
- Prioritization comparison view

**Testing:**
- Correctly identifies substantial features (90%+ accuracy)
- ADR creation workflow smooth
- Load calculations helpful

**Value**: +7%

---

### Phase 4: Revival System (Week 4)
**Deliverables:**
- Revival scoring algorithm
- Weekly/monthly revival prompts
- Revive action workflow
- Revival analytics

**Testing:**
- Revival scores correlate with user interest
- Timing doesn't interrupt focus
- Revival workflow is smooth

**Value**: +3% (nice-to-have, lower priority)

---

## Success Metrics (Enhanced)

### F001 Core Metrics (from original spec)
- False positive rate: < 10%
- Conversion rate: > 60%
- Detection latency: < 50ms

### Enhancement Metrics

**E1 Dashboard:**
- Users view dashboard: > 80% of sessions
- Dashboard influences decisions: > 50% of time
- Users report it's helpful: > 75%

**E2 Design-First:**
- Substantial features detected: > 85% accuracy
- Users choose design option: > 40% when prompted
- ADRs created from prompt: > 25 per quarter

**E3 Revival:**
- Revival suggestions shown: Weekly
- Users revive work: > 20% of suggestions
- Revived work completed: > 60% of revivals

**E4 Prioritization:**
- Users defer new work when load high: > 50%
- Reported reduced overwhelm: > 70%
- Task completion rate improves: > 20%

---

## ADHD Research Validation

### Evidence-Based Design Principles

**1. External Memory Systems (Validated)**
- **Research**: ADHD working memory deficits require external aids
- **F001 Application**: ConPort stores all untracked work, dashboard shows aggregate
- **Evidence**: CBT for ADHD emphasizes external reminders (87% improvement rate)

**2. Gentle Nudging vs Enforcement (Validated)**
- **Research**: Autonomy critical for ADHD engagement, shame counterproductive
- **F001 Application**: Never blocks work, offers choices, uses encouraging language
- **Evidence**: Nudge theory in health shows mixed results when too directive

**3. Visual Cues and Reminders (Validated)**
- **Research**: ADHD brain responds better to visual/external triggers than internal reminders
- **F001 Application**: Dashboard, emoji indicators, color-coded status
- **Evidence**: "Placing cues in physical world especially helpful for ADHD" (2024 research)

**4. Task Breakdown and Progressive Disclosure (Validated)**
- **Research**: Breaking tasks into smaller steps reduces ADHD overwhelm
- **F001 Application**: Shows 3-5 items max, progressive disclosure of details
- **Evidence**: CBT meta-analysis shows task breakdown = 87% symptom improvement

**5. No Mid-Flow Interruptions (Validated)**
- **Research**: ADHD hyperfocus states are precious and should be protected
- **F001 Application**: Detection at session start only, never during active work
- **Evidence**: ADHD accommodation research emphasizes respecting flow states

---

## Privacy & Ethics

### Privacy Principles
- ✅ All data local (no telemetry)
- ✅ User owns and controls data
- ✅ Can export/delete anytime
- ✅ Transparent about what's collected

### Ethical Considerations
- ✅ Non-judgmental language (no shame)
- ✅ Respects user autonomy (easy to disable)
- ✅ Gentle encouragement (not manipulation)
- ✅ Acknowledges ADHD as neurological (not moral failing)

### User Control
```python
config = {
    "enabled": true,  # Master on/off
    "show_dashboard": true,  # E1
    "prompt_for_design": true,  # E2
    "show_revival": "weekly",  # E3: off/weekly/monthly
    "show_prioritization": true,  # E4
    "messaging_style": "gentle"  # gentle/minimal/off
}
```

---

## Next Steps

1. **Validate Design**: Review this enhanced spec with stakeholders
2. **Create Implementation Plan**: Use /sc:workflow or Zen planner
3. **Set Up Infrastructure**: Ensure ConPort schema supports all features
4. **Build Phase 1**: Start with F001 core + E1 dashboard (highest value)

---

**Document Status:** Enhanced Design Complete - Ready for Planning

**Consensus Level:** Individual analysis (Zen consensus timed out)
**Recommendation:** Proceed with incremental implementation (F001 core → E1 → E2 → E3 → E4)
