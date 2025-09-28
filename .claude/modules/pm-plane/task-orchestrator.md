# Task-Orchestrator Module

**Module Version**: 1.0.0
**Authority**: Dependency Analysis and Execution Planning
**Mode**: ACT primarily, some PLAN support
**Repository**: https://github.com/jpicklyk/task-orchestrator

## Authority Boundaries

**Task-Orchestrator Owns:**
- Dependency analysis and conflict resolution
- Task scheduling and execution planning
- Cross-project dependency tracking
- Automated workflow optimization
- Risk assessment and mitigation planning
- 37 specialized orchestration tools

**Task-Orchestrator NEVER:**
- Updates task status (Leantime authority)
- Creates initial task hierarchy (Task-Master authority)
- Stores architectural decisions (ConPort authority)

## Core Capabilities

### Dependency Analysis Tools (37 Specialized Tools)
- **Conflict Detection**: Identifies scheduling and resource conflicts
- **Critical Path Analysis**: Finds task sequences that determine project duration
- **Resource Optimization**: Balances workload across team members
- **Risk Mitigation**: Identifies potential blockers and suggests alternatives
- **Cross-Project Coordination**: Manages dependencies between different projects

### Integration Commands

```bash
# Analyze dependencies for current sprint
# Task-Orchestrator provides dependency mapping and conflict detection
# Results flow back through Integration Bridge to ConPort

# Example dependency analysis workflow:
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
  --summary "Running dependency analysis via Task-Orchestrator" \
  --rationale "Task-Orchestrator provides 37 specialized tools for complex dependency resolution" \
  --tags ["dependency-analysis", "task-orchestrator"]

# Create dependency analysis reference
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "external_refs" --key "TO-ANALYSIS-SPRINT-ID" \
  --value '{"type": "orchestrator_analysis", "sprint_id": "SPRINT-ID", "analysis_status": "running", "tools_used": ["conflict_detection", "critical_path"]}'
```

## Workflow Integration

### ACT Mode Operations
- **Real-time Dependency Updates**: Monitors task progress and updates dependencies
- **Blocker Resolution**: Suggests alternative paths when tasks are blocked
- **Next-Action Optimization**: Recommends optimal task sequencing

### Event-Driven Coordination
```bash
# Task lifecycle events handled by Task-Orchestrator
# Task Created → Dependency Analysis → Risk Assessment → Schedule Optimization
# Status Changed → Impact Analysis → Downstream Updates → Team Notifications

# Example event handling:
HANDLE_TASK_STATUS_CHANGE() {
    TASK_ID="$1"
    NEW_STATUS="$2"

    # Task-Orchestrator analyzes impact of status change
    # Updates dependent tasks and schedules
    # Provides recommendations for next actions

    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Task-Orchestrator processed status change for $TASK_ID" \
      --rationale "Dependency analysis updated downstream tasks and identified next actions" \
      --tags ["status-change", "dependency-update"]
}
```

## ADHD Optimizations

- **Visual Dependency Maps**: Clear graphical representation of task relationships
- **Blocker Alerts**: Immediate notifications when dependencies create conflicts
- **Next-Action Clarity**: Always provides specific next steps to reduce decision paralysis
- **Context Switching Support**: Maintains dependency awareness across interruptions
- **Progressive Complexity**: Shows simple dependencies first, details on request

## Integration Points

- **Task-Master Integration**: Receives initial hierarchy, adds dependency analysis
- **Leantime Integration**: Provides scheduling data for team dashboards
- **ConPort Integration**: Logs dependency decisions and analysis results
- **Serena Integration**: Provides code-level dependency context during development