# Integration Bridge Module

**Module Version**: 1.0.0
**Authority**: Cross-Plane Coordination and Event Routing
**Modes**: Both PLAN and ACT
**Service**: `/services/mcp-integration-bridge/` at PORT_BASE+16

## Authority Boundaries

**Integration Bridge ONLY Authority:**
- Cross-plane communication coordination
- Event routing between Project Management and Cognitive planes
- Multi-instance coordination via shared database
- Event queue management and propagation
- Authority boundary enforcement

**Integration Bridge NEVER:**
- Updates task status directly (routes to Leantime)
- Creates task hierarchies directly (routes to Task-Master)
- Stores decisions directly (routes to ConPort)
- Performs code navigation directly (routes to Serena)

## Core Coordination Patterns

### Cross-Plane Event Routing
```bash
# NO direct cross-plane communication allowed
# ALL must go through Integration Bridge

# Task lifecycle events flow:
# Task-Master → Integration Bridge → ConPort → Serena
# Code change events flow:
# Serena → ConPort → Integration Bridge → Leantime
# Status updates flow:
# Leantime → Integration Bridge → ConPort (log only)
```

### Port Allocation Strategy
```bash
# Integration Bridge port calculation
INSTANCE_NAME=$(echo $DOPEMUX_INSTANCE)  # default, primary, secondary
PORT_BASE=$(echo $PORT_BASE)             # 3000, 3030, 3060

# Dynamic port assignment
MCP_INTEGRATION_PORT=$((PORT_BASE + 16))  # 3016, 3046, 3076

# Service discovery for current instance
CONTAINER_PREFIX="mcp-${INSTANCE_NAME}"
TASK_MASTER_URL="http://${CONTAINER_PREFIX}-task-master-ai:3005"
SERENA_URL="http://${CONTAINER_PREFIX}-serena:3006"
TASK_ORCHESTRATOR_URL="http://${CONTAINER_PREFIX}-task-orchestrator:3014"
LEANTIME_BRIDGE_URL="http://${CONTAINER_PREFIX}-leantime-bridge:3015"
```

## Event Coordination Commands

### Task Lifecycle Management
```bash
# Route task creation from PM plane to Cognitive plane
ROUTE_TASK_CREATED() {
    TASK_DATA="$1"
    SOURCE_SYSTEM="$2"  # task-master, task-orchestrator

    # 1. Log routing decision in ConPort
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Routing task creation event from $SOURCE_SYSTEM" \
      --rationale "Integration Bridge coordinating cross-plane task propagation" \
      --tags ["integration-bridge", "task-lifecycle", "cross-plane"]

    # 2. Update Integration Bridge coordination state
    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "integration_events" --key "task-created-$(date +%s)" \
      --value "{\"type\": \"task_created\", \"source\": \"$SOURCE_SYSTEM\", \"status\": \"routing\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

    # 3. Route to Serena for code context preparation
    # (This would be an API call to Serena)

    # 4. Log completion
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Task creation event routed successfully" \
      --rationale "Serena notified and code context prepared for new task" \
      --tags ["integration-bridge", "task-lifecycle", "completed"]
}
```

### Status Synchronization
```bash
# Route status updates from Leantime to other systems
ROUTE_STATUS_CHANGE() {
    TASK_ID="$1"
    NEW_STATUS="$2"
    SOURCE="leantime"

    # 1. Log status change in ConPort (for history, not authority)
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Status change routed: $TASK_ID → $NEW_STATUS" \
      --rationale "Leantime authoritative status update propagated through Integration Bridge" \
      --tags ["integration-bridge", "status-sync", "leantime"]

    # 2. Update coordination state
    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "integration_events" --key "status-change-$(date +%s)" \
      --value "{\"type\": \"status_change\", \"task_id\": \"$TASK_ID\", \"new_status\": \"$NEW_STATUS\", \"source\": \"$SOURCE\"}"

    # 3. Notify dependent systems (Task-Orchestrator for dependency updates)
    # (API calls would go here)

    # 4. Update Serena context if task becomes active
    if [ "$NEW_STATUS" = "active" ]; then
        # Notify Serena to prepare code context
        echo "📋 Notifying Serena to prepare context for active task: $TASK_ID"
    fi
}
```

### Code Change Propagation
```bash
# Route code changes from Cognitive plane to PM plane
ROUTE_CODE_CHANGE() {
    FILE_PATH="$1"
    CHANGE_TYPE="$2"
    RELATED_TASK="$3"

    # 1. Log code change in ConPort
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Code change detected: $FILE_PATH ($CHANGE_TYPE)" \
      --rationale "Serena detected change, routing through Integration Bridge for task tracking" \
      --tags ["integration-bridge", "code-change", "serena"]

    # 2. Route to Leantime for status updates
    if [ -n "$RELATED_TASK" ]; then
        echo "📤 Routing code change to Leantime for task: $RELATED_TASK"
        # API call to Leantime to update task with implementation progress
    fi

    # 3. Update coordination state
    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "integration_events" --key "code-change-$(date +%s)" \
      --value "{\"type\": \"code_change\", \"file\": \"$FILE_PATH\", \"change_type\": \"$CHANGE_TYPE\", \"task\": \"$RELATED_TASK\"}"
}
```

## Authority Enforcement

### Boundary Validation
```bash
# Prevent direct cross-plane communication
VALIDATE_COMMUNICATION() {
    SOURCE_SYSTEM="$1"
    TARGET_SYSTEM="$2"
    OPERATION="$3"

    # Check authority matrix
    if is_cross_plane_communication "$SOURCE_SYSTEM" "$TARGET_SYSTEM"; then
        if [ "$SOURCE_SYSTEM" != "integration-bridge" ] && [ "$TARGET_SYSTEM" != "integration-bridge" ]; then
            echo "❌ AUTHORITY VIOLATION: $SOURCE_SYSTEM attempting direct communication with $TARGET_SYSTEM"
            echo "   All cross-plane communication must go through Integration Bridge"
            return 1
        fi
    fi

    # Validate operation authority
    case "$OPERATION" in
        "update_status")
            if [ "$TARGET_SYSTEM" != "leantime" ]; then
                echo "❌ AUTHORITY VIOLATION: Only Leantime can receive status updates"
                return 1
            fi
            ;;
        "create_hierarchy")
            if [ "$TARGET_SYSTEM" != "task-master" ]; then
                echo "❌ AUTHORITY VIOLATION: Only Task-Master can create task hierarchies"
                return 1
            fi
            ;;
        "log_decision")
            if [ "$TARGET_SYSTEM" != "conport" ]; then
                echo "❌ AUTHORITY VIOLATION: Only ConPort can store architectural decisions"
                return 1
            fi
            ;;
    esac

    return 0  # Communication allowed
}
```

## Multi-Instance Coordination

### Shared State Management
```bash
# Coordinate across multiple Dopemux instances
COORDINATE_MULTI_INSTANCE() {
    INSTANCE_ID="$1"
    EVENT_TYPE="$2"
    EVENT_DATA="$3"

    # Use shared PostgreSQL for cross-instance coordination
    # Redis for performance caching
    # ConPort for persistent decisions across instances

    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "multi_instance" --key "instance-$INSTANCE_ID-event-$(date +%s)" \
      --value "{\"instance\": \"$INSTANCE_ID\", \"event_type\": \"$EVENT_TYPE\", \"data\": $EVENT_DATA, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
}
```

## ADHD Optimizations

### Context Preservation During Events
```bash
# Maintain ADHD context during event routing
PRESERVE_ADHD_CONTEXT() {
    EVENT_TYPE="$1"
    USER_CONTEXT="$2"

    # Ensure event routing doesn't break mental model
    # Preserve attention state through transitions
    # Provide clear feedback about what's happening

    case "$EVENT_TYPE" in
        "task_activated")
            echo "🎯 Task activated! Serena is preparing your code context..."
            ;;
        "status_synced")
            echo "✅ Progress synced to team dashboard!"
            ;;
        "blocker_detected")
            echo "⚠️  Blocker detected. Alternative paths being calculated..."
            ;;
    esac
}
```

### Event Queue Management
```bash
# Prevent event overwhelm for ADHD developers
MANAGE_EVENT_QUEUE() {
    ATTENTION_STATE="$1"

    case "$ATTENTION_STATE" in
        "scattered")
            # Process only critical events
            # Batch non-urgent events
            # Provide simple status updates
            ;;
        "focused")
            # Process events in order
            # Provide detailed feedback
            # Maintain current task focus
            ;;
        "hyperfocus")
            # Process all events
            # Provide comprehensive status
            # Support deep work sessions
            ;;
    esac
}
```

## Integration Health Monitoring

### Health Check Endpoint
```bash
# Monitor Integration Bridge health
CHECK_INTEGRATION_HEALTH() {
    echo "🔍 Integration Bridge Health Check:"
    echo "  Port: $MCP_INTEGRATION_PORT"
    echo "  Task-Master: $(check_service_health $TASK_MASTER_URL)"
    echo "  Serena: $(check_service_health $SERENA_URL)"
    echo "  Task-Orchestrator: $(check_service_health $TASK_ORCHESTRATOR_URL)"
    echo "  Leantime: $(check_service_health $LEANTIME_BRIDGE_URL)"
    echo "  ConPort: $(check_conport_health)"
}
```