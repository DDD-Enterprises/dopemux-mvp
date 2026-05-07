# ⚠️ DEPRECATED: Leantime Bridge Module

**STATUS**: **DEPRECATED** - No longer used in simplified architecture
**REPLACED BY**: ConPort `progress_entry` for task status tracking
**DECISION**: #132 (Simplified architecture - ConPort is single source of truth)

---

**Why Deprecated**: Leantime status authority (planned→active→blocked→done) is now handled directly in ConPort via `progress_entry` with statuses: TODO, IN_PROGRESS, BLOCKED, DONE. This eliminates cross-system synchronization complexity while maintaining full task management capabilities.

**Migration**: Use ConPort MCP tools directly - see `.claude/modules/pm-plane/task-orchestrator.md`

---

# Leantime Bridge Module (Historical Reference Only)

**Module Version**: 1.0.0
**Authority**: Task Status and Team Visibility (DEPRECATED)
**Modes**: ACT and PLAN
**Integration**: Official MCP + Custom ADHD Bridge

## Authority Boundaries

**Leantime ONLY Authority:**
- Task status updates (planned → active → blocked → done)
- Team dashboards and reporting
- Milestone tracking and roadmap visibility
- Stakeholder reporting and communication

**Leantime NEVER:**
- Creates task hierarchies (Task-Master authority)
- Stores architectural decisions (ConPort authority)
- Provides code navigation (Serena authority)

## Status Management Commands

### Core Status Operations
```bash
# Sync task status TO Leantime (authoritative)
SYNC_TO_LEANTIME() {
    TASK_ID="$1"
    NEW_STATUS="$2"

    # Get current ConPort state
    TASK_DATA=$(mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "subtasks" --key "$TASK_ID")

    # Sync to Leantime (external API call)
    echo "📤 Syncing $TASK_ID to Leantime with status: $NEW_STATUS"

    # Log the handoff decision
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Handed off $TASK_ID to Leantime for status management" \
      --rationale "Leantime provides team visibility and dashboard integration" \
      --tags ["handoff", "leantime", "status-sync"]

    # Create reference link
    mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
      --source_item_type "custom_data" --source_item_id "$TASK_ID" \
      --target_item_type "custom_data" --target_item_id "LT-REF-$TASK_ID" \
      --relationship_type "TRACKED_IN"
}
```

### Status Conflict Resolution
```bash
# Handle conflicts where systems disagree on status
CHECK_STATUS_CONFLICTS() {
    SPRINT_ID="$1"
    TASK_ID="$2"

    # 1. Check Leantime first (authority for status)
    LEANTIME_STATUS=$(echo "Check Leantime API for $TASK_ID status")

    # 2. Compare with local mem4sprint status
    LOCAL_STATUS=$(mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "subtasks" --key "$TASK_ID" | jq -r '.status')

    # 3. Resolve conflicts (Leantime wins)
    if [ "$LEANTIME_STATUS" != "$LOCAL_STATUS" ]; then
        mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
          --summary "Status conflict resolved for $TASK_ID" \
          --rationale "Leantime status ($LEANTIME_STATUS) takes precedence over local status ($LOCAL_STATUS)" \
          --tags ["$SPRINT_ID", "conflict-resolution", "leantime"]

        # Update local to match Leantime
        mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
          --category "subtasks" --key "$TASK_ID" \
          --value "{\"status\": \"$LEANTIME_STATUS\", \"sync_timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    fi
}
```

## Official MCP Tools Available

### Core Project Management
- **create_milestone** - Creates project milestones
- **create_timesheet** - Time tracking functionality
- **create_todo** - Task creation
- **update_todo** - Task modification

### Event Triggers (Webhooks)
- new_todo, new_comment, new_goal, new_idea
- new_milestone, new_project, new_timesheet
- updated_* versions of all above

## ADHD Integration Features

### Team Dashboard Optimization
```bash
# ADHD-friendly dashboard sync
SYNC_ADHD_DASHBOARD() {
    SPRINT_ID="$1"

    # Create ADHD-optimized status reference
    mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
      --category "external_refs" --key "$SPRINT_ID-LT-DASHBOARD" \
      --value '{
        "type": "leantime_dashboard",
        "sprint_id": "'$SPRINT_ID'",
        "adhd_features": {
          "visual_progress": true,
          "celebration_points": true,
          "next_action_clarity": true,
          "overwhelm_prevention": true
        },
        "sync_status": "active"
      }'
}
```

### Status Communication Patterns
- **Visual Progress Indicators**: `[████░░░░] 4/8 complete ✅`
- **Celebration Moments**: `🎉 Amazing! Task completed!`
- **Clear Next Actions**: Always show what to work on next
- **Blocker Visibility**: `🚨 Blocker: Needs API review`

## Integration Workflows

### Morning Standup Sync
```bash
# Sync overnight Leantime changes to local context
MORNING_LEANTIME_SYNC() {
    echo "🌅 Syncing Leantime updates from overnight..."

    # Check for status changes in Leantime
    # Update local ConPort with authoritative status
    # Identify newly unblocked tasks
    # Provide ADHD-friendly progress summary
}
```

### End-of-Day Reporting
```bash
# Push day's progress to Leantime dashboards
EOD_LEANTIME_SYNC() {
    echo "🌙 Syncing day's progress to Leantime..."

    # Push completed tasks
    # Update time tracking
    # Sync blockers and issues
    # Set tomorrow's focus in team dashboard
}
```

## Error Handling

- **Graceful Degradation**: System continues without Leantime
- **Retry Logic**: Exponential backoff for API failures
- **Status Validation**: Ensures status changes are valid
- **ADHD Context**: Preserves mental model during outages