# ADHD Feature Development Specification

## Overview

This document specifies the comprehensive ADHD feature set for Dopemux, prioritized by impact and implementation complexity. These features form the core value proposition of the platform.

## Feature Priority Matrix

### P0 - Critical ADHD Features (MVP Required)

#### 1. Context Preservation System
**Problem Addressed**: Working memory deficits (d = 1.62-2.03 effect size)

```yaml
feature: Automatic Context Preservation
components:
  - auto_save:
      trigger: "Every 30 seconds OR on context switch"
      data_saved:
        - current_files: "All open files and cursor positions"
        - command_history: "Last 20 commands with timestamps"
        - mental_model: "Current task description and goals"
        - decision_log: "Recent decisions made"

  - context_restoration:
      trigger: "dopemux restore OR automatic on restart"
      behavior: "Restore exact state with summary of previous work"
      ui_feedback: "You were working on X, last action was Y..."

  - interruption_recovery:
      detection: "Sudden session termination or extended pause"
      recovery_prompt: "Welcome back! Here's where you left off..."
      visual_cue: "Highlight changed files since last session"
```

#### 2. Task Decomposition Engine
**Problem Addressed**: Executive function impairments (75-81% of ADHD population)

```yaml
feature: Intelligent Task Breakdown
components:
  - automatic_chunking:
      max_chunk_duration: "25 minutes (Pomodoro-sized)"
      complexity_scoring: "AI estimates cognitive load"
      dependency_mapping: "Identifies prerequisites"

  - visual_progress:
      display: "ASCII progress bar with emoji states"
      format: "[████░░░░] 4/8 tasks ✅"
      location: "Always visible in status bar"

  - gentle_guidance:
      next_task_suggestion: "Non-intrusive prompt for next action"
      decision_reduction: "Max 3 options presented at once"
      default_actions: "Smart defaults based on context"
```

#### 3. Attention State Monitoring
**Problem Addressed**: Attention regulation difficulties

```yaml
feature: Real-time Attention Tracking
components:
  - activity_monitoring:
      metrics:
        - keystroke_frequency: "Keys per minute"
        - file_switch_rate: "Context switches per hour"
        - pause_patterns: "Duration and frequency of pauses"
        - error_rate: "Typos and corrections"

  - state_classification:
      states:
        - deep_focus: "Sustained activity, low switch rate"
        - normal: "Regular activity patterns"
        - distracted: "High switch rate, many pauses"
        - hyperfocus: "Extended activity without breaks"

  - adaptive_interface:
      deep_focus: "Minimize all distractions"
      distracted: "Increase guidance and simplification"
      hyperfocus: "Schedule gentle break reminders"
```

### P1 - High-Impact ADHD Features

#### 4. Time Blindness Compensation
**Problem Addressed**: 25-40% time underestimation in ADHD

```yaml
feature: Enhanced Time Awareness
components:
  - multiple_time_displays:
      analog_clock: "Visual representation (better for ADHD)"
      session_timer: "How long on current task"
      deadline_countdown: "Time until next commitment"

  - time_anchors:
      format: "Started X at 2:30pm (45 min ago)"
      frequency: "Update every significant action"
      persistence: "Maintain in status bar"

  - predictive_warnings:
      15_min_warning: "🟡 Meeting in 15 minutes"
      5_min_warning: "🔴 Meeting in 5 minutes - save work!"
      transition_time: "Account for task switching overhead"
```

#### 5. Cognitive Load Management
**Problem Addressed**: Information processing limitations

```yaml
feature: Dynamic Complexity Reduction
components:
  - progressive_disclosure:
      initial_view: "Only essential information"
      expand_on_demand: "Details available via hotkey"
      context_sensitive: "Show relevant info based on task"

  - visual_hierarchy:
      priority_highlighting:
        critical: "Bold red with emoji ⚠️"
        important: "Yellow highlight 💡"
        standard: "Normal text"
        background: "Dimmed gray"

  - information_chunking:
      group_size: "5-7 items maximum"
      related_grouping: "Logical clusters"
      visual_separation: "Clear boundaries between groups"
```

#### 6. Executive Function Scaffolding
**Problem Addressed**: Planning and organization challenges

```yaml
feature: Automated Planning Assistance
components:
  - smart_prioritization:
      factors:
        - deadline_proximity: "Weight: 0.4"
        - dependency_count: "Weight: 0.3"
        - energy_requirement: "Weight: 0.2"
        - user_preference: "Weight: 0.1"

  - decision_support:
      option_presentation: "Max 3 choices with clear trade-offs"
      default_highlighting: "Recommended option pre-selected"
      consequence_preview: "What happens if you choose X"

  - initiation_assistance:
      startup_routine: "Consistent project opening sequence"
      first_task_selection: "AI suggests based on energy/time"
      momentum_building: "Start with easy win tasks"
```

### P2 - Enhancement Features

#### 7. Hyperfocus Protection
**Problem Addressed**: Difficulty regulating hyperfocus states

```yaml
feature: Healthy Hyperfocus Management
components:
  - flow_state_detection:
      indicators: "Sustained focus >45 minutes"
      preservation: "Protect from non-critical interruptions"

  - gentle_breaks:
      reminder_style: "Soft fade-in notification"
      snooze_option: "Delay 15 min if in flow"
      health_prompts: "Stand up, hydrate, look away"

  - session_extension:
      smart_extension: "Extend focus time if productive"
      hard_limits: "Force break after 90 minutes"
```

#### 8. Memory Augmentation
**Problem Addressed**: Working memory limitations

```yaml
feature: External Memory System
components:
  - automatic_note_taking:
      decision_capture: "Record all significant choices"
      rationale_logging: "Why you made that decision"
      context_snippets: "Code state at decision time"

  - intelligent_recall:
      semantic_search: "Find by meaning not keywords"
      temporal_search: "What was I doing yesterday?"
      pattern_recognition: "You usually do X after Y"

  - memory_prompts:
      reminder_style: "You decided to X because Y"
      relevance_scoring: "Show only pertinent memories"
```

## Implementation Architecture

### Core Services Required

```yaml
adhd_service_layer:
  attention_monitor:
    implementation: "Node.js service with activity tracking"
    data_store: "Redis for real-time metrics"
    update_frequency: "Every 5 seconds"

  context_manager:
    implementation: "SQLite for local persistence"
    sync_service: "Optional cloud backup"
    restoration_api: "Fast context retrieval (<500ms)"

  task_decomposer:
    implementation: "AI service with Claude/GPT integration"
    cache_layer: "Previously decomposed patterns"
    learning_system: "Improve based on completion data"

  time_awareness:
    implementation: "System service with OS integration"
    calendar_sync: "Optional Google/Outlook integration"
    notification_system: "Native OS notifications"
```

### Data Models

```typescript
interface ADHDUserProfile {
  // Core ADHD characteristics
  attentionProfile: {
    averageFocusDuration: number; // minutes
    distractibilityScore: number; // 0-10
    hyperfocusTendency: boolean;
    optimalSessionLength: number; // minutes
  };

  // Executive function support needs
  executiveSupport: {
    planningAssistance: 'minimal' | 'moderate' | 'extensive';
    decisionSupport: boolean;
    taskInitiationHelp: boolean;
    organizationLevel: 'low' | 'medium' | 'high';
  };

  // Time management
  timeManagement: {
    timeBlindnessLevel: 'mild' | 'moderate' | 'severe';
    preferredBreakInterval: number; // minutes
    deadlineWarningTime: number; // minutes before
  };

  // Sensory preferences
  sensoryPreferences: {
    visualComplexityTolerance: 'low' | 'medium' | 'high';
    animationSensitivity: boolean;
    colorContrastNeeds: 'standard' | 'high' | 'custom';
    notificationStyle: 'visual' | 'audio' | 'haptic' | 'multi';
  };
}

interface AttentionState {
  currentState: 'deep_focus' | 'normal' | 'distracted' | 'hyperfocus';
  stateStartTime: Date;
  stateDuration: number; // minutes
  transitionReason?: string;
  metrics: {
    keystrokeRate: number;
    errorRate: number;
    contextSwitches: number;
    pauseFrequency: number;
  };
}

interface ContextSnapshot {
  timestamp: Date;
  sessionId: string;
  workingDirectory: string;
  openFiles: Array<{
    path: string;
    cursorPosition: { line: number; column: number };
    scrollPosition: number;
    unsavedChanges: boolean;
  }>;
  recentCommands: string[];
  currentTask: {
    description: string;
    subtasks: string[];
    completedSubtasks: string[];
  };
  mentalModel: {
    goal: string;
    approach: string;
    decisions: Array<{ decision: string; rationale: string; timestamp: Date }>;
  };
  gitState: {
    branch: string;
    uncommittedChanges: string[];
    lastCommit: string;
  };
}
```

## User Experience Flows

### Session Start Flow
```
1. User runs: dopemux start
2. System checks for previous session
3. If previous session exists:
   - Load context snapshot
   - Display summary: "Welcome back! You were working on [task]"
   - Restore file states and cursor positions
   - Show what changed while away (git updates, new messages)
4. If new session:
   - Run attention baseline calibration (optional)
   - Load user ADHD profile
   - Apply accommodation preferences
   - Suggest first task based on time/energy
```

### Interruption Recovery Flow
```
1. Interruption detected (sudden disconnect, long pause)
2. Save emergency context snapshot
3. On return:
   - Quick recognition: "Welcome back! (away for 23 minutes)"
   - Context bridge: "You were implementing auth validation"
   - Changed files summary: "2 files modified by others"
   - Recovery prompt: "Continue with auth? [Y/n]"
4. Restore exact state if requested
5. Log interruption pattern for learning
```

### Task Completion Flow
```
1. Task marked complete (manually or detected)
2. Celebration feedback: "✅ Awesome! Task complete!"
3. Energy check: "How are you feeling? [energized/normal/tired]"
4. Next task suggestion based on energy
5. Optional break reminder if worked >25 minutes
6. Update progress visualization
7. Save accomplishment to memory
```

## Measurement & Validation

### ADHD Effectiveness Metrics

```yaml
quantitative_metrics:
  task_completion_rate:
    baseline: "Measure without accommodations"
    target: "20-40% improvement"
    measurement: "Tasks completed / tasks started"

  focus_session_duration:
    baseline: "Average uninterrupted work time"
    target: "25% increase"
    measurement: "Time between major context switches"

  context_recovery_time:
    baseline: "Time to resume after interruption"
    target: "50% reduction"
    measurement: "Interruption to productive keystroke"

  cognitive_load_score:
    baseline: "Self-reported difficulty (1-10)"
    target: "30% reduction"
    measurement: "Regular user surveys"

qualitative_metrics:
  user_satisfaction:
    method: "Weekly brief surveys"
    questions:
      - "How supported do you feel? (1-10)"
      - "Did accommodations help today? (Y/N)"
      - "What was most helpful?"

  accommodation_effectiveness:
    method: "A/B testing accommodation features"
    tracking: "Which features used most"
    correlation: "Feature use vs. productivity"
```

### Success Criteria

```yaml
mvp_success_criteria:
  technical:
    - context_restoration: "< 2 seconds"
    - auto_save_reliability: "> 99.9%"
    - attention_detection_accuracy: "> 80%"

  user_experience:
    - setup_time: "< 5 minutes"
    - learning_curve: "Productive in < 1 hour"
    - daily_active_use: "> 70% of work time"

  adhd_specific:
    - task_completion_improvement: "> 20%"
    - user_reported_support: "> 8/10"
    - interruption_recovery_success: "> 90%"
```

## Integration with Claude Code

### Custom Claude Code Configuration

```yaml
claude_code_customization:
  ui_modifications:
    - simplified_interface: "Reduce visual complexity"
    - persistent_status_bar: "Always show context"
    - progress_indicators: "Visual task progress"

  behavior_modifications:
    - auto_save_frequency: "30 seconds"
    - context_preservation: "On every file switch"
    - gentle_notifications: "Soft, dismissible"

  ai_adaptations:
    - response_style: "Clear, structured, concise"
    - suggestion_frequency: "Adaptive to attention state"
    - error_handling: "Gentle, encouraging tone"
```

This comprehensive ADHD feature specification provides the foundation for building a truly accommodating development environment that addresses the specific challenges faced by neurodivergent developers.