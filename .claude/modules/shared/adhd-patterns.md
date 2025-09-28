# ADHD Patterns Module

**Module Version**: 1.0.0
**Purpose**: ADHD accommodations and attention state management
**Scope**: Cross-system cognitive support and neurodivergent-friendly patterns
**Integration**: All systems with attention-aware adaptations

## Core ADHD Principles

### Fundamental Accommodations
- **Context Preservation**: Always maintain awareness of where the user left off
- **Gentle Guidance**: Use encouraging, non-judgmental language with clear next steps
- **Decision Reduction**: Present maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Break complex work into 25-minute focused segments
- **Progressive Disclosure**: Show essential information first, details on request

## Attention State Detection

### Attention States
```bash
# Detect attention state via behavioral metrics and user indicators
DETECT_ATTENTION_STATE() {
    TYPING_CADENCE="$1"      # fast, normal, slow
    SESSION_DURATION="$2"    # minutes
    TASK_SWITCHING="$3"      # frequent, normal, minimal
    USER_INDICATED="$4"      # scattered, focused, hyperfocus, auto

    if [ "$USER_INDICATED" != "auto" ]; then
        echo "$USER_INDICATED"
        return
    fi

    # Behavioral detection
    if [ "$TASK_SWITCHING" = "frequent" ] && [ "$TYPING_CADENCE" = "fast" ]; then
        echo "scattered"
    elif [ "$SESSION_DURATION" -gt 45 ] && [ "$TASK_SWITCHING" = "minimal" ]; then
        echo "hyperfocus"
    else
        echo "focused"
    fi
}
```

### Attention-Aware Response Adaptation

#### Scattered Attention Mode
```bash
ADAPT_FOR_SCATTERED() {
    echo "🧠 Attention State: Scattered - Optimizing for quick wins"

    # Response patterns
    RESPONSE_STYLE="bullet_points"
    MAX_OPTIONS=1
    CONTEXT_DEPTH=1
    TOKEN_LIMIT=500

    # Tool selection
    PREFERRED_MODEL="gemini-2.5-flash"  # Fast responses
    MODULE_LOADING="minimal"            # Essential only

    # Visual patterns
    echo "💡 Quick next action: [Single clear step]"
    echo "🎯 Time estimate: 5-15 minutes"
    echo "✅ Small win opportunity identified"
}
```

#### Focused Attention Mode
```bash
ADAPT_FOR_FOCUSED() {
    echo "🧠 Attention State: Focused - Providing comprehensive support"

    # Response patterns
    RESPONSE_STYLE="structured_detail"
    MAX_OPTIONS=3
    CONTEXT_DEPTH=3
    TOKEN_LIMIT=2000

    # Tool selection
    PREFERRED_MODEL="gemini-2.5-pro"   # Comprehensive analysis
    MODULE_LOADING="contextual"        # Relevant modules

    # Visual patterns
    echo "🎯 Current focus: [Clear objective]"
    echo "📋 Next 3 actions: [Prioritized list]"
    echo "⏱️ Time estimate: 25-45 minutes"
}
```

#### Hyperfocus Mode
```bash
ADAPT_FOR_HYPERFOCUS() {
    echo "🧠 Attention State: Hyperfocus - Supporting deep work"

    # Response patterns
    RESPONSE_STYLE="comprehensive_detail"
    MAX_OPTIONS=5
    CONTEXT_DEPTH=5
    TOKEN_LIMIT=4000

    # Tool selection
    PREFERRED_MODEL="o3"               # Deep analysis
    MODULE_LOADING="comprehensive"     # All relevant modules

    # Visual patterns
    echo "🔬 Deep analysis mode active"
    echo "🌊 Flow state supported"
    echo "🎯 Extended session: 1-3 hours"
    echo "⚠️  Remember breaks: Set timer for 90 minutes"
}
```

## Context Preservation Patterns

### Session Continuity
```bash
# Preserve mental model across interruptions
PRESERVE_SESSION_CONTEXT() {
    INTERRUPTION_TYPE="$1"  # meeting, break, emergency, day_end

    # Save current context to ConPort
    CURRENT_CONTEXT='{
        "attention_state": "'$ATTENTION_STATE'",
        "current_task": "'$CURRENT_TASK'",
        "mental_model": "'$MENTAL_MODEL'",
        "next_steps": ['$NEXT_STEPS'],
        "time_invested": "'$TIME_INVESTED'",
        "interruption_type": "'$INTERRUPTION_TYPE'",
        "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }'

    mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
      --patch_content "$CURRENT_CONTEXT"

    case "$INTERRUPTION_TYPE" in
        "meeting")
            echo "💾 Context saved - Meeting time! I'll be here when you return."
            ;;
        "break")
            echo "💾 Context saved - Enjoy your break! 🌟"
            ;;
        "day_end")
            echo "💾 Context saved - Great work today! See you tomorrow! 🌙"
            ;;
    esac
}

# Restore context after interruption
RESTORE_SESSION_CONTEXT() {
    echo "🔄 Welcome back! Restoring your context..."

    # Get saved context from ConPort
    SAVED_CONTEXT=$(mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp")

    # Restore mental model
    ATTENTION_STATE=$(jq -r '.attention_state' <<< "$SAVED_CONTEXT")
    CURRENT_TASK=$(jq -r '.current_task' <<< "$SAVED_CONTEXT")
    MENTAL_MODEL=$(jq -r '.mental_model' <<< "$SAVED_CONTEXT")

    echo "🎯 You were working on: $CURRENT_TASK"
    echo "🧠 Mental model: $MENTAL_MODEL"
    echo "📍 Attention state: $ATTENTION_STATE"
    echo "⚡ Ready to continue!"
}
```

### Context Switch Support
```bash
# Handle transitions between different types of work
HANDLE_CONTEXT_SWITCH() {
    FROM_CONTEXT="$1"  # code, planning, meeting, debugging
    TO_CONTEXT="$2"
    TRANSITION_TIME="$3"  # immediate, 5min, planned

    echo "🔄 Context switch: $FROM_CONTEXT → $TO_CONTEXT"

    # Provide bridging summary
    echo "📋 Previous context: You were $FROM_CONTEXT"
    echo "🎯 New context: Now moving to $TO_CONTEXT"

    # Adjust cognitive load based on transition
    if [ "$TRANSITION_TIME" = "immediate" ]; then
        # Emergency context switch - minimal cognitive load
        echo "⚡ Quick transition - simplified context"
        COGNITIVE_LOAD="minimal"
    else
        # Planned transition - preserve rich context
        echo "🌉 Smooth transition - full context preserved"
        COGNITIVE_LOAD="normal"
    fi

    # Save bridging information in ConPort
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Context switch: $FROM_CONTEXT → $TO_CONTEXT" \
      --rationale "ADHD context preservation during work transition" \
      --tags ["context-switch", "adhd", "transition"]
}
```

## Cognitive Load Management

### Information Chunking
```bash
# Break complex information into digestible chunks
CHUNK_INFORMATION() {
    COMPLEXITY_LEVEL="$1"  # simple, medium, complex
    ATTENTION_STATE="$2"
    CONTENT="$3"

    case "$ATTENTION_STATE:$COMPLEXITY_LEVEL" in
        "scattered:complex")
            # Show only essential information
            echo "📝 Essential info only (detailed explanation available on request)"
            echo "🎯 One clear action: [Most important step]"
            ;;
        "focused:complex")
            # Break into numbered steps
            echo "📋 Breaking this down into steps:"
            echo "1. [First step]"
            echo "2. [Second step]"
            echo "3. [Third step]"
            echo ""
            echo "💡 Focus on step 1 first, then ask for step 2 details"
            ;;
        "hyperfocus:complex")
            # Provide full detail with clear organization
            echo "🔬 Comprehensive breakdown available:"
            echo "📊 Full analysis, implementation details, and alternatives"
            ;;
    esac
}
```

### Decision Simplification
```bash
# Reduce decision paralysis with limited options
SIMPLIFY_DECISIONS() {
    OPTIONS=("$@")
    ATTENTION_STATE="$1"
    shift

    MAX_OPTIONS=3
    if [ "$ATTENTION_STATE" = "scattered" ]; then
        MAX_OPTIONS=1
    fi

    echo "🎯 Simplified decision (max $MAX_OPTIONS options):"

    for i in $(seq 1 $MAX_OPTIONS); do
        if [ $i -le ${#OPTIONS[@]} ]; then
            echo "$i. ${OPTIONS[$i]}"
        fi
    done

    if [ ${#OPTIONS[@]} -gt $MAX_OPTIONS ]; then
        echo ""
        echo "💡 More options available if needed - just ask!"
    fi
}
```

## Progress Visualization

### Visual Progress Indicators
```bash
# Provide motivating progress visualization
SHOW_PROGRESS() {
    CONTEXT="$1"  # task, sprint, day, session
    COMPLETED="$2"
    TOTAL="$3"

    # Calculate progress percentage
    PERCENTAGE=$((COMPLETED * 100 / TOTAL))

    # Create visual progress bar
    FILLED=$((PERCENTAGE / 10))
    EMPTY=$((10 - FILLED))

    PROGRESS_BAR=""
    for i in $(seq 1 $FILLED); do PROGRESS_BAR+="█"; done
    for i in $(seq 1 $EMPTY); do PROGRESS_BAR+="░"; done

    # Context-specific messaging
    case "$CONTEXT" in
        "task")
            echo "🎯 Task Progress: [$PROGRESS_BAR] $COMPLETED/$TOTAL steps ✅"
            ;;
        "sprint")
            echo "🚀 Sprint Progress: [$PROGRESS_BAR] $COMPLETED/$TOTAL items complete 🎉"
            ;;
        "day")
            echo "☀️ Daily Progress: [$PROGRESS_BAR] $COMPLETED/$TOTAL goals achieved 💪"
            ;;
        "session")
            echo "⚡ Session Progress: [$PROGRESS_BAR] $COMPLETED/$TOTAL milestones 🔥"
            ;;
    esac

    # Celebration for milestones
    if [ $PERCENTAGE -ge 25 ] && [ $PERCENTAGE -lt 50 ]; then
        echo "🌟 Quarter way there! Keep going!"
    elif [ $PERCENTAGE -ge 50 ] && [ $PERCENTAGE -lt 75 ]; then
        echo "🎉 Halfway point reached! Awesome progress!"
    elif [ $PERCENTAGE -ge 75 ] && [ $PERCENTAGE -lt 100 ]; then
        echo "🔥 Almost there! Final stretch!"
    elif [ $PERCENTAGE -eq 100 ]; then
        echo "🎊 COMPLETED! Fantastic work! 🏆"
    fi
}
```

### Completion Celebrations
```bash
# Provide ADHD-friendly completion celebrations
CELEBRATE_COMPLETION() {
    COMPLETION_TYPE="$1"  # task, goal, milestone, sprint
    EFFORT_LEVEL="$2"     # small, medium, large, huge

    case "$COMPLETION_TYPE:$EFFORT_LEVEL" in
        "task:small")
            echo "✅ Nice! Quick win completed! 🌟"
            ;;
        "task:medium")
            echo "🎯 Excellent! Task completed! 💪"
            ;;
        "task:large")
            echo "🚀 Amazing! Major task completed! 🎉"
            ;;
        "goal:*")
            echo "🏆 GOAL ACHIEVED! Outstanding work! 🎊"
            ;;
        "milestone:*")
            echo "🎖️ MILESTONE REACHED! Incredible progress! ⭐"
            ;;
        "sprint:*")
            echo "🎊 SPRINT COMPLETED! Phenomenal achievement! 🏅"
            ;;
    esac

    # Track completion streak
    INCREMENT_COMPLETION_STREAK "$COMPLETION_TYPE"
}

INCREMENT_COMPLETION_STREAK() {
    COMPLETION_TYPE="$1"

    # Get current streak from ConPort
    CURRENT_STREAK=$(mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "adhd_metrics" --key "completion_streak_$COMPLETION_TYPE" | jq -r '.value // 0')

    NEW_STREAK=$((CURRENT_STREAK + 1))

    # Update streak in ConPort
    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "adhd_metrics" --key "completion_streak_$COMPLETION_TYPE" \
      --value "$NEW_STREAK"

    # Special celebrations for streaks
    if [ $NEW_STREAK -eq 3 ]; then
        echo "🔥 THREE IN A ROW! You're on fire! 🔥"
    elif [ $NEW_STREAK -eq 5 ]; then
        echo "⚡ FIVE STREAK! Absolutely unstoppable! ⚡"
    elif [ $NEW_STREAK -eq 10 ]; then
        echo "🏆 TEN STREAK! LEGENDARY STATUS ACHIEVED! 🏆"
    fi
}
```

## Executive Function Support

### Activation Energy Reduction
```bash
# Reduce barriers to starting tasks
REDUCE_ACTIVATION_ENERGY() {
    TASK="$1"
    COMPLEXITY="$2"

    echo "🎯 Starting: $TASK"

    # Provide specific first step
    echo "👉 First step (takes ~2 minutes):"
    echo "   [Very specific, concrete action]"
    echo ""

    # Reduce decision fatigue
    echo "🛠️ Tools ready:"
    echo "   [Pre-configured environment]"
    echo ""

    # Set small win expectation
    echo "✅ Small win goal:"
    echo "   [Achievable milestone in 5-10 minutes]"
    echo ""

    # Provide momentum builder
    echo "🚀 Momentum builder:"
    echo "   After first step, next action becomes obvious"
}
```

### Task Sequencing
```bash
# Optimize task order for ADHD productivity
OPTIMIZE_TASK_SEQUENCE() {
    TASKS=("$@")
    ATTENTION_STATE="$1"
    shift

    case "$ATTENTION_STATE" in
        "scattered")
            # Start with easiest/quickest tasks for momentum
            echo "🎯 Starting with quick wins for momentum:"
            sort_tasks_by_effort "${TASKS[@]}" "ascending"
            ;;
        "focused")
            # Balanced approach - mix of easy and challenging
            echo "🎯 Balanced sequence for sustained focus:"
            sort_tasks_by_priority "${TASKS[@]}" "balanced"
            ;;
        "hyperfocus")
            # Start with most complex/interesting tasks
            echo "🎯 Tackling complex tasks while energy is high:"
            sort_tasks_by_complexity "${TASKS[@]}" "descending"
            ;;
    esac
}
```

## Memory and Organization Support

### Working Memory Aids
```bash
# Support working memory limitations
SUPPORT_WORKING_MEMORY() {
    CONTEXT="$1"
    ITEMS=("$@")
    shift

    # Limit to 7±2 items (working memory capacity)
    MAX_ITEMS=7

    echo "🧠 Working memory support (max $MAX_ITEMS items):"

    for i in $(seq 1 $MAX_ITEMS); do
        if [ $i -le ${#ITEMS[@]} ]; then
            echo "$i. ${ITEMS[$i]}"
        fi
    done

    if [ ${#ITEMS[@]} -gt $MAX_ITEMS ]; then
        echo ""
        echo "📝 Additional items available - stored in ConPort for later"

        # Store overflow in ConPort
        for i in $(seq $((MAX_ITEMS + 1)) ${#ITEMS[@]}); do
            mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
              --category "working_memory_overflow" --key "$CONTEXT-item-$i" \
              --value "${ITEMS[$i]}"
        done
    fi
}
```

### External Memory Integration
```bash
# Coordinate with ConPort for external memory
COORDINATE_EXTERNAL_MEMORY() {
    MEMORY_TYPE="$1"  # decisions, patterns, progress, context
    ATTENTION_STATE="$2"

    case "$ATTENTION_STATE" in
        "scattered")
            # Essential memory only
            echo "🧠 Essential memory items (details available on request):"
            mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" \
              --hours_ago 4 --limit_per_type 1
            ;;
        "focused")
            # Contextual memory
            echo "🧠 Relevant memory context:"
            mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" \
              --hours_ago 24 --limit_per_type 3
            ;;
        "hyperfocus")
            # Comprehensive memory
            echo "🧠 Full memory context available:"
            echo "   Use ConPort semantic search for deep exploration"
            ;;
    esac
}
```