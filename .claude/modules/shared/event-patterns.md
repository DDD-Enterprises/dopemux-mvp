# Event Patterns Module

**Module Version**: 1.0.0
**Purpose**: Event schemas and async handling patterns
**Scope**: Cross-system event coordination and propagation
**Integration**: Two-Plane Architecture event flows

## Core Event Flow Patterns

### Mandatory Event Routing Rules
```
🚨 CRITICAL: All cross-plane communication MUST go through Integration Bridge

Project Management Plane ←→ Integration Bridge ←→ Cognitive Plane
```

### Event Flow Sequences

#### Task Lifecycle Events
```
1. Task Created: Task-Master → Integration Bridge → ConPort → Serena
2. Status Changed: Leantime → Integration Bridge → ConPort (log only)
3. Code Changed: Serena → ConPort → Integration Bridge → Leantime
4. Decision Made: ConPort → Integration Bridge (broadcast) → All systems
```

#### Event Priority Levels
- **Critical**: System failures, security alerts
- **High**: Task blockers, status changes affecting dependencies
- **Medium**: Progress updates, decision logging
- **Low**: Metrics collection, background sync

## Event Schemas

### Task Lifecycle Events

#### Task Created Event
```json
{
  "event_type": "task_created",
  "event_id": "uuid",
  "timestamp": "2025-09-28T04:22:00Z",
  "source_system": "task-master",
  "target_systems": ["integration-bridge", "conport", "serena"],
  "priority": "medium",
  "data": {
    "task_id": "S-2025.09-T1",
    "task_title": "Implement sprint module",
    "sprint_id": "S-2025.09",
    "goal_id": "S-2025.09-G1",
    "status": "planned",
    "estimated_hours": 4,
    "tags": ["implementation", "claude-md"]
  },
  "routing": {
    "next_hop": "integration-bridge",
    "final_destinations": ["conport", "serena"],
    "requires_ack": true
  }
}
```

#### Status Change Event
```json
{
  "event_type": "status_changed",
  "event_id": "uuid",
  "timestamp": "2025-09-28T04:22:00Z",
  "source_system": "leantime",
  "target_systems": ["integration-bridge", "conport"],
  "priority": "high",
  "data": {
    "task_id": "S-2025.09-T1",
    "old_status": "planned",
    "new_status": "active",
    "changed_by": "developer",
    "reason": "Starting implementation"
  },
  "routing": {
    "authoritative": true,
    "requires_propagation": true,
    "affected_dependencies": ["S-2025.09-T2", "S-2025.09-T3"]
  }
}
```

#### Code Change Event
```json
{
  "event_type": "code_changed",
  "event_id": "uuid",
  "timestamp": "2025-09-28T04:22:00Z",
  "source_system": "serena",
  "target_systems": ["conport", "integration-bridge", "leantime"],
  "priority": "medium",
  "data": {
    "file_path": "/Users/hue/code/dopemux-mvp/.claude/modules/shared/sprint.md",
    "change_type": "modified",
    "lines_added": 45,
    "lines_removed": 2,
    "related_task": "S-2025.09-T1",
    "symbols_affected": ["Sprint", "mem4sprint"]
  },
  "routing": {
    "update_progress": true,
    "notify_stakeholders": true
  }
}
```

### Decision Events

#### Decision Logged Event
```json
{
  "event_type": "decision_logged",
  "event_id": "uuid",
  "timestamp": "2025-09-28T04:22:00Z",
  "source_system": "conport",
  "target_systems": ["integration-bridge"],
  "priority": "medium",
  "data": {
    "decision_id": "D-123",
    "summary": "Use mem4sprint for sprint management",
    "rationale": "Provides ADHD-friendly structure with ConPort integration",
    "tags": ["architecture", "sprint-management"],
    "affects_systems": ["task-master", "leantime", "serena"]
  },
  "routing": {
    "broadcast": true,
    "requires_acknowledgment": false
  }
}
```

## Async Handling Patterns

### Event Queue Management
```bash
# Priority-based event processing
PROCESS_EVENT_QUEUE() {
    ATTENTION_STATE="$1"

    case "$ATTENTION_STATE" in
        "scattered")
            # Process only critical and high priority events
            # Batch medium and low priority events
            # Provide simple notifications
            PROCESS_PRIORITY="critical,high"
            BATCH_SIZE=1
            ;;
        "focused")
            # Process events in order
            # Provide detailed feedback
            # Maintain current task focus
            PROCESS_PRIORITY="critical,high,medium"
            BATCH_SIZE=3
            ;;
        "hyperfocus")
            # Process all events
            # Provide comprehensive status
            # Support deep work sessions
            PROCESS_PRIORITY="critical,high,medium,low"
            BATCH_SIZE=10
            ;;
    esac

    process_events_by_priority "$PROCESS_PRIORITY" "$BATCH_SIZE"
}
```

### Circuit Breaker Pattern
```bash
# Prevent event overwhelm and cascade failures
EVENT_CIRCUIT_BREAKER() {
    SERVICE="$1"
    EVENT_TYPE="$2"

    # Check service health
    if ! check_service_health "$SERVICE"; then
        # Open circuit - route around failed service
        echo "⚠️  Circuit breaker OPEN for $SERVICE - routing around failure"
        route_around_failed_service "$SERVICE" "$EVENT_TYPE"
        return 1
    fi

    # Half-open - test with single event
    if circuit_is_half_open "$SERVICE"; then
        echo "🔄 Circuit breaker HALF-OPEN for $SERVICE - testing with single event"
        test_service_with_event "$SERVICE" "$EVENT_TYPE"
        return $?
    fi

    # Closed - normal operation
    return 0
}
```

### Eventual Consistency Handling
```bash
# Handle out-of-order events and eventual consistency
HANDLE_EVENTUAL_CONSISTENCY() {
    EVENT="$1"
    EXPECTED_SEQUENCE="$2"

    # Check event sequence
    CURRENT_SEQUENCE=$(get_event_sequence "$EVENT")

    if [ "$CURRENT_SEQUENCE" -lt "$EXPECTED_SEQUENCE" ]; then
        # Event arrived out of order - queue for later processing
        echo "📥 Event out of order - queuing for later: $EVENT"
        queue_event_for_later "$EVENT" "$EXPECTED_SEQUENCE"
        return 1
    elif [ "$CURRENT_SEQUENCE" -gt "$EXPECTED_SEQUENCE" ]; then
        # Missing earlier events - request resync
        echo "🔄 Missing events detected - requesting resync from sequence $EXPECTED_SEQUENCE"
        request_event_resync "$EXPECTED_SEQUENCE" "$CURRENT_SEQUENCE"
        return 1
    fi

    # Event in correct sequence - process normally
    return 0
}
```

## Event Validation

### Schema Validation
```bash
# Validate event against schema
VALIDATE_EVENT() {
    EVENT="$1"
    SCHEMA_TYPE="$2"

    # Required fields check
    REQUIRED_FIELDS=("event_type" "event_id" "timestamp" "source_system" "target_systems")

    for field in "${REQUIRED_FIELDS[@]}"; do
        if ! jq -e ".$field" <<< "$EVENT" > /dev/null; then
            echo "❌ Event validation failed: Missing required field '$field'"
            return 1
        fi
    done

    # Schema-specific validation
    case "$SCHEMA_TYPE" in
        "task_lifecycle")
            validate_task_lifecycle_event "$EVENT"
            ;;
        "code_change")
            validate_code_change_event "$EVENT"
            ;;
        "decision")
            validate_decision_event "$EVENT"
            ;;
    esac
}
```

### Authority Validation
```bash
# Ensure events come from authoritative sources
VALIDATE_EVENT_AUTHORITY() {
    EVENT="$1"

    SOURCE_SYSTEM=$(jq -r '.source_system' <<< "$EVENT")
    EVENT_TYPE=$(jq -r '.event_type' <<< "$EVENT")

    # Check authority matrix
    case "$EVENT_TYPE" in
        "status_changed")
            if [ "$SOURCE_SYSTEM" != "leantime" ]; then
                echo "❌ Authority violation: Only Leantime can emit status_changed events"
                return 1
            fi
            ;;
        "task_created")
            if [ "$SOURCE_SYSTEM" != "task-master" ]; then
                echo "❌ Authority violation: Only Task-Master can emit task_created events"
                return 1
            fi
            ;;
        "decision_logged")
            if [ "$SOURCE_SYSTEM" != "conport" ]; then
                echo "❌ Authority violation: Only ConPort can emit decision_logged events"
                return 1
            fi
            ;;
        "code_changed")
            if [ "$SOURCE_SYSTEM" != "serena" ]; then
                echo "❌ Authority violation: Only Serena can emit code_changed events"
                return 1
            fi
            ;;
    esac

    return 0
}
```

## Event Monitoring and Debugging

### Event Tracing
```bash
# Trace event propagation across systems
TRACE_EVENT() {
    EVENT_ID="$1"

    echo "🔍 Tracing event: $EVENT_ID"

    # Find event in ConPort logs
    mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
      --query_term "value_text:\"event_id:$EVENT_ID\"" --limit 10

    # Show event propagation path
    echo "📊 Event propagation path:"
    get_event_propagation_path "$EVENT_ID"
}
```

### Event Metrics
```bash
# Track event processing metrics
TRACK_EVENT_METRICS() {
    EVENT_TYPE="$1"
    PROCESSING_TIME="$2"
    SUCCESS="$3"

    # Log metrics in ConPort
    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "event_metrics" --key "metric-$(date +%s)" \
      --value "{\"event_type\": \"$EVENT_TYPE\", \"processing_time_ms\": $PROCESSING_TIME, \"success\": $SUCCESS, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
}
```

## ADHD-Optimized Event Handling

### Attention-Aware Event Processing
```bash
# Adapt event processing to user's attention state
ADAPT_EVENT_PROCESSING() {
    ATTENTION_STATE="$1"
    EVENT_BATCH="$2"

    case "$ATTENTION_STATE" in
        "scattered")
            # Minimal notifications, batch non-critical events
            echo "📋 Processing critical events only..."
            filter_critical_events "$EVENT_BATCH"
            ;;
        "focused")
            # Normal processing with progress indicators
            echo "⚡ Processing events with progress updates..."
            process_with_progress_indicators "$EVENT_BATCH"
            ;;
        "hyperfocus")
            # Full detailed processing
            echo "🔬 Processing all events with detailed analysis..."
            process_with_full_analysis "$EVENT_BATCH"
            ;;
    esac
}
```

### Event Celebration Patterns
```bash
# Provide ADHD-friendly feedback for significant events
CELEBRATE_EVENT() {
    EVENT_TYPE="$1"
    EVENT_DATA="$2"

    case "$EVENT_TYPE" in
        "task_completed")
            echo "🎉 Awesome! Task completed: $(jq -r '.task_title' <<< "$EVENT_DATA")"
            echo "✅ Progress updated in team dashboard!"
            ;;
        "sprint_goal_achieved")
            echo "🚀 Amazing! Sprint goal achieved: $(jq -r '.goal_title' <<< "$EVENT_DATA")"
            echo "🏆 Celebrating with the team!"
            ;;
        "blocker_resolved")
            echo "💪 Fantastic! Blocker resolved: $(jq -r '.blocker_description' <<< "$EVENT_DATA")"
            echo "🎯 Ready to continue with next actions!"
            ;;
    esac
}
```