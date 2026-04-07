# ADHD Finishing Helpers Feature Specification

**Status**: Implementation Ready
**Priority**: High - Addresses core ADHD development challenges

## Overview

The ADHD Finishing Helpers system addresses the specific challenge where ADHD developers get projects to 80-90% completion but struggle to cross the finish line. Unlike traditional productivity tools that focus on task initiation, this system specifically targets completion workflows.

## Core Problem Statement

### ADHD-Specific Completion Challenges

1. **"There is NOW and NEVER"** - Time blindness creates urgency distortion around completion
2. **"Finishing is harder than starting"** - Completion requires different energy than activation
3. **"Out of sight = out of mind"** - Almost-finished work disappears after context switches
4. **Dopamine crashes near completion** - Need external reward systems for motivation
5. **Context switching kills momentum** - Losing "finishing state" during interruptions
6. **Executive dysfunction** - Need structured external completion support

### User Requirements (Validated)
- **Visual indicators ARE helpful** (progress bars, emojis, urgency levels)
- **Progressive disclosure done right** enhances rather than overwhelms
- **NOT half-baked implementations** - must integrate naturally with existing workflows
- **Persistent visibility** across all session interruptions and system restarts
- **Focus on finishing, not starting** - activation energy is not the primary problem

## Feature Components

### 1. In-Progress Work Tracking

**Core Functionality**:
- Dynamic list of in-progress work items with completion status
- Shown automatically on Claude startup
- Available via slash command: `/work status`, `/work add`, `/work update`, `/work complete`
- Manual management: add, update, remove, mark complete

**ADHD Accommodations**:
- **Persistent across interruptions**: Survives session switches, container restarts, system reboots
- **Zero cognitive load**: Automatically appears when needed, no need to remember to check
- **Visual priority indicators**: Clear distinction between different urgency levels
- **Context preservation**: Remembers where you left off on each work item

**Data Structure**:
```python
@dataclass
class WorkItem:
    id: str
    title: str
    description: str
    completion_percentage: float
    priority: WorkPriority  # LOW, MEDIUM, HIGH, URGENT
    created_at: datetime
    updated_at: datetime
    estimated_completion_time: Optional[datetime]
    git_context: Optional[Dict[str, str]]  # branch, repo, last_commit
    file_context: List[str]  # files being worked on
    next_steps: List[str]
    blockers: List[str]
    celebration_earned: bool = False
```

**Display Format**:
```
🎯 In-Progress Work (3 items)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 URGENT  Feature X API Integration    [████████░░] 85% ← SO CLOSE!
   ↳ Next: Write final tests, update docs
   ↳ Branch: feature/api-integration
   ↳ Time since 80%: 2 days

🟠 HIGH    Bug fix for user auth       [██████░░░░] 65%
   ↳ Next: Debug session timeout logic
   ↳ Branch: fix/auth-timeout

🟡 MEDIUM  Documentation updates       [███░░░░░░░] 30%
   ↳ Next: Complete architecture section
   ↳ Started 3 days ago

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Tip: Focus on Feature X - you're almost there! 🎯
```

### 2. Completion Detection Engine

**Automatic Detection Signals**:
- **Git State Analysis**:
  - Clean working directory (no uncommitted changes)
  - Feature branch ready for merge (all commits pushed)
  - Pull request approved and passing checks
  - No merge conflicts detected

- **Code Quality Signals**:
  - All tests passing (>90% pass rate)
  - Linting rules satisfied
  - Type checking clean
  - Code coverage meets thresholds

- **Documentation Signals**:
  - README updated with new functionality
  - Function/class docstrings present
  - API documentation current
  - Changelog entries added

- **Issue Tracking Integration**:
  - Associated tickets marked "review ready"
  - Acceptance criteria met
  - QA sign-off obtained

**Completion Percentage Calculation**:
```python
def calculate_completion_percentage(work_item: WorkItem) -> float:
    """
    Calculate completion percentage based on multiple signals.

    Weights:
    - Git state: 40%
    - Code quality: 30%
    - Documentation: 20%
    - Issue tracking: 10%
    """
    git_score = analyze_git_completion(work_item.git_context)
    quality_score = analyze_code_quality(work_item.file_context)
    docs_score = analyze_documentation_completeness(work_item)
    tracking_score = analyze_issue_tracking_status(work_item.id)

    return (
        git_score * 0.40 +
        quality_score * 0.30 +
        docs_score * 0.20 +
        tracking_score * 0.10
    )
```

### 3. ADHD-Optimized Visual System

**Progressive Intensity Design**:
- **0-60%**: Minimal visibility, gentle progress indication
- **60-80%**: Active awareness with gentle encouragement
- **80-95%**: Clear "almost done" signals with specific next steps
- **95-99%**: Urgent focus with "final push" motivation
- **100%**: Celebration and dopamine reward system

**Visual Language**:
```
Completion States:
[░░░░░░░░░░] 0-60%   🟢 "Making progress..."
[███░░░░░░░] 60-80%  🟡 "Getting there! 65% complete"
[███████░░░] 80-95%  🟠 "Almost there! 85% - Final sprint!"
[█████████░] 95-99%  🔥 "SO CLOSE! 97% - You've got this!"
[██████████] 100%    🎉 "FINISHED! Amazing work! 🚀"
```

**Terminal Integration Points**:
- **Dopemux Status Display**: Completion info in `dopemux status` output
- **Session Restore Messages**: "Welcome back! You're 85% done with Feature X"
- **Prompt Integration**: Optional completion percentage in terminal prompt
- **Break Reminders**: Enhanced with completion context awareness

### 4. Celebration and Reward System

**Dopamine Reinforcement Design**:
- **Milestone Celebrations**: Special recognition at 80%, 90%, 95%, 100%
- **ASCII Art Rewards**: Visual celebration displays for major completions
- **Achievement Logging**: Permanent record of completed projects
- **Progress Streaks**: Recognition for sustained completion momentum
- **Personalized Messages**: Encouraging feedback based on completion patterns

**Celebration Examples**:
```
🎉 MILESTONE ACHIEVED! 🎉
╔═══════════════════════════════════════╗
║     Feature X API Integration         ║
║           COMPLETED!                  ║
║                                       ║
║    You did it! Time to celebrate! 🚀  ║
║                                       ║
║  Total time: 5 days                   ║
║  Final push: 2 hours                  ║
║  Completion streak: 3 projects        ║
╚═══════════════════════════════════════╝

🏆 Added to your Hall of Fame! 🏆
```

## Integration Architecture

### SessionManager Extension
```python
# Extend existing SessionMetrics class
@dataclass
class CompletionMetrics:
    active_work_items: Dict[str, WorkItem] = field(default_factory=dict)
    completion_history: List[CompletedWork] = field(default_factory=list)
    completion_streaks: int = 0
    time_at_80_percent: Dict[str, datetime] = field(default_factory=dict)
    time_at_95_percent: Dict[str, datetime] = field(default_factory=dict)
    celebration_preferences: Dict[str, Any] = field(default_factory=dict)
```

### ContextSnapshot Extension
```python
# Add completion context to existing ContextSnapshot
current_work_focus: Optional[str] = None
completion_percentage: float = 0.0
finishing_momentum: str = "none"  # none, building, strong, urgent
next_completion_steps: List[str] = field(default_factory=list)
completion_blockers: List[str] = field(default_factory=list)
```

### Claude Code Integration
**Slash Commands**:
- `/work status` - Show current in-progress work
- `/work add <title> [description]` - Add new work item
- `/work update <id> [percentage] [description]` - Update work item
- `/work complete <id> [celebration_message]` - Mark work complete
- `/work focus <id>` - Set primary focus item
- `/work remove <id>` - Remove work item

**Startup Integration**:
- Automatically display in-progress work on Claude session start
- Show most urgent/closest-to-completion items first
- Provide quick action suggestions based on current state

## Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-3)
1. **Week 1**: Extend SessionManager with WorkItem and CompletionMetrics
2. **Week 2**: Implement basic CRUD operations for work items
3. **Week 3**: Add persistence and session integration

### Phase 2: Visual System (Weeks 4-6)
1. **Week 4**: Terminal display integration and formatting
2. **Week 5**: Progressive intensity visual design
3. **Week 6**: Celebration and reward system implementation

### Phase 3: Intelligence (Weeks 7-9)
1. **Week 7**: Git state analysis for automatic completion detection
2. **Week 8**: Code quality and documentation signal integration
3. **Week 9**: Claude Code slash command implementation

## Success Metrics

### User Experience Metrics
- Time from 80% → 100% completion decreases by 25%
- Number of projects abandoned at >80% completion decreases
- User reports of completion anxiety reduce
- Celebration system engagement increases over time

### Technical Metrics
- Zero performance degradation in existing Dopemux commands
- 100% persistence across session interruptions
- <2 second response time for work item operations
- 95% accuracy in automatic completion detection

### ADHD-Specific Metrics
- Context switching away from >80% complete work decreases
- Time to resume work after interruption decreases
- User satisfaction scores for "feeling supported during completion" increase
- Number of "almost done" items that actually get finished increases

## Configuration and Customization

### User Preferences
```yaml
finishing_helpers:
  visual_intensity: moderate  # minimal, moderate, high
  celebration_style: encouraging  # minimal, encouraging, enthusiastic
  completion_thresholds:
    almost_done: 80
    final_push: 95
  display_preferences:
    show_on_startup: true
    max_items_shown: 5
    priority_filter: high_and_urgent
  notification_preferences:
    completion_reminders: true
    milestone_celebrations: true
    streak_tracking: true
```

## Related Documentation
- [ADR-037: ADHD Finishing Helpers System](../90-adr/037-adhd-finishing-helpers-system.md)
- [Implementation Guide](../02-how-to/finishing-helpers-implementation.md)
- [User Guide](../02-how-to/using-finishing-helpers.md)
- [SessionManager Extension](../03-reference/session-manager-completion-api.md)