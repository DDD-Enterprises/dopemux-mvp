# ConPort Memory Module

**Module Version**: 1.0.0
**Authority**: Decision Logging and Knowledge Graph
**Modes**: Both PLAN and ACT
**Workspace**: `/Users/hue/code/dopemux-mvp`

## Authority Boundaries

**ConPort ONLY Authority:**
- Architectural decisions and implementation rationale
- Project knowledge graph maintenance
- Progress tracking and decision history
- Context preservation across interruptions and instances
- Cross-system relationship tracking

**ConPort NEVER:**
- Updates task status (Leantime authority)
- Creates task hierarchies (Task-Master authority)
- Performs code navigation (Serena authority)

## Core Memory Operations

### Context Management
```bash
# Get current project and active contexts
mcp__conport__get_product_context --workspace_id "/Users/hue/code/dopemux-mvp"
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"

# Update contexts (full or partial)
mcp__conport__update_product_context --workspace_id "/Users/hue/code/dopemux-mvp" --content {...}
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content {...}
```

### Decision & Progress Tracking
```bash
# Log architectural and implementation decisions
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
  --summary "decision" --rationale "why" --tags ["tag"]

# Track task progress with automatic linking
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" \
  --status "IN_PROGRESS" --description "task" \
  --linked_item_type "custom_data" --linked_item_id "task-ref"

# Update progress status
mcp__conport__update_progress --workspace_id "/Users/hue/code/dopemux-mvp" \
  --progress_id ID --status "DONE"
```

### Knowledge Graph Operations
```bash
# Create semantic links between entities
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
  --source_item_type "decision" --source_item_id "ID" \
  --target_item_type "progress_entry" --target_item_id "ID" \
  --relationship_type "implements"

# Retrieve linked items
mcp__conport__get_linked_items --workspace_id "/Users/hue/code/dopemux-mvp" \
  --item_type "decision" --item_id "ID"
```

## ADHD-Optimized Patterns

### Automatic Context Preservation
```bash
# Session initialization sequence (MANDATORY AT SESSION START)
INITIALIZE_CONPORT_CONTEXT() {
    # 1. Determine workspace
    WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

    # 2. Check for existing database
    if [ -f "$WORKSPACE_ID/context_portal/context.db" ]; then
        LOAD_EXISTING_CONTEXT
    else
        HANDLE_NEW_SETUP
    fi
}

LOAD_EXISTING_CONTEXT() {
    # Load all essential contexts
    mcp__conport__get_product_context --workspace_id "/Users/hue/code/dopemux-mvp"
    mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
    mcp__conport__get_decisions --workspace_id "/Users/hue/code/dopemux-mvp" --limit 5
    mcp__conport__get_progress --workspace_id "/Users/hue/code/dopemux-mvp" --limit 5
    mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" --hours_ago 24

    echo "[CONPORT_ACTIVE] - Memory initialized. Existing contexts and recent activity loaded."
}
```

### Proactive Logging Triggers
```bash
# Automatic decision logging when user makes architectural choices
AUTO_LOG_DECISION() {
    TRIGGER_TYPE="$1"  # architecture_choice, implementation_decision, pattern_adoption

    case $TRIGGER_TYPE in
        "architecture_choice")
            # User discusses system design → Log decision
            mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
              --summary "$DECISION_SUMMARY" --rationale "$REASONING" --tags ["architecture"]
            ;;
        "implementation_decision")
            # User chooses implementation approach → Log decision
            mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
              --summary "$IMPLEMENTATION_CHOICE" --rationale "$WHY_THIS_WAY" --tags ["implementation"]
            ;;
    esac
}

# Automatic progress tracking when user completes tasks
AUTO_LOG_PROGRESS() {
    TASK_COMPLETION_EVENT="$1"

    mcp__conport__update_progress --workspace_id "/Users/hue/code/dopemux-mvp" \
      --progress_id "$CURRENT_TASK_ID" --status "DONE"

    # Log completion celebration for ADHD motivation
    echo "✅ Awesome! Task complete! Progress updated in ConPort."
}
```

## Search and Discovery

### Semantic Search
```bash
# Natural language queries for conceptual searches
mcp__conport__semantic_search_conport --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_text "natural language query" --top_k 5
```

### Full-Text Search
```bash
# Keyword-based searches
mcp__conport__search_decisions_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term "keywords"

mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term "keywords"

# Project glossary search
mcp__conport__search_project_glossary_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term "term"
```

## Integration with Other Systems

### ConPort ↔ Serena Integration
```bash
# Link code exploration sessions to architectural decisions
LINK_CODE_TO_DECISION() {
    SERENA_SESSION="$1"
    DECISION_ID="$2"

    mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
      --source_item_type "custom_data" --source_item_id "$SERENA_SESSION" \
      --target_item_type "decision" --target_item_id "$DECISION_ID" \
      --relationship_type "informed_by"
}
```

### ConPort ↔ Task Management Integration
```bash
# Create task references while preserving authority boundaries
CREATE_TASK_REFERENCE() {
    TASK_ID="$1"
    EXTERNAL_SYSTEM="$2"  # leantime, taskmaster

    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "external_refs" --key "$EXTERNAL_SYSTEM-REF-$TASK_ID" \
      --value "{\"type\": \"${external_system}_reference\", \"task_id\": \"$TASK_ID\", \"sync_status\": \"active\"}"
}
```

## Dynamic Context Retrieval

### Context-Aware Response Enhancement
```bash
# Automatically retrieve relevant context for user queries
ENHANCE_RESPONSE_WITH_CONTEXT() {
    USER_QUERY="$1"

    # 1. Analyze query for key concepts
    CONCEPTS=$(extract_concepts "$USER_QUERY")

    # 2. Search ConPort for relevant context
    RELEVANT_DECISIONS=$(mcp__conport__semantic_search_conport \
      --workspace_id "/Users/hue/code/dopemux-mvp" \
      --query_text "$CONCEPTS" --top_k 3)

    # 3. Get linked items for context expansion
    LINKED_CONTEXT=$(get_linked_items_for_decisions "$RELEVANT_DECISIONS")

    # 4. Synthesize for prompt context
    SYNTHESIZED_CONTEXT=$(synthesize_context "$RELEVANT_DECISIONS" "$LINKED_CONTEXT")

    echo "Relevant context retrieved from ConPort: $SYNTHESIZED_CONTEXT"
}
```

## Error Handling and Resilience

### Graceful Degradation
```bash
# Handle ConPort unavailability
HANDLE_CONPORT_UNAVAILABLE() {
    echo "[CONPORT_INACTIVE] - ConPort unavailable, using fallback memory patterns"

    # Fall back to session-based memory
    # Continue with reduced context preservation
    # Log errors for later sync when ConPort returns
}

# Circuit breaker pattern for ConPort calls
CONPORT_WITH_CIRCUIT_BREAKER() {
    COMMAND="$1"

    if conport_health_check; then
        eval "$COMMAND"
    else
        HANDLE_CONPORT_UNAVAILABLE
        # Store command for retry when service returns
    fi
}
```

## ConPort Sync Routine

### Manual Sync Command
```bash
# User-triggered sync for session analysis
CONPORT_SYNC() {
    echo "[CONPORT_SYNCING] - Analyzing session for new information..."

    # Analyze complete chat history for new information
    # Update ConPort with all identified changes
    # Resume previous task with refreshed context

    echo "ConPort sync complete. Memory updated with session findings."
}
```

## Visual Progress and Motivation

### ADHD-Friendly Progress Indicators
```bash
# Show visual progress for motivation
SHOW_PROGRESS() {
    TOTAL_TASKS=$(get_total_tasks_for_sprint)
    COMPLETED_TASKS=$(get_completed_tasks_for_sprint)
    PROGRESS_BAR=$(create_progress_bar $COMPLETED_TASKS $TOTAL_TASKS)

    echo "🚀 Sprint Progress: $PROGRESS_BAR $COMPLETED_TASKS/$TOTAL_TASKS complete ✅"
    echo "🎯 Ready for work: $(get_ready_tasks | wc -l) items"
    echo "🚨 Blockers: $(get_blocked_tasks | wc -l) open"
}
```