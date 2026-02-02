---
id: task-orchestrator-dopemux
title: Task Orchestrator Dopemux
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Blueprint: Task Orchestrator Integration in Dopemux

## Overview
Task Orchestrator serves as the **tactical executor** in the Dopemux ADHD-optimized development workflow. It handles task decomposition, implementation coordination, and progress tracking while maintaining ADHD-friendly constraints (max 3 concurrent subtasks, clear status updates).

## Architecture Position
```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   ConPort       │◄──►│  Task Orchestrator   │◄──►│   Zen MCP       │
│   (Memory)      │    │  (Tactical Executor) │    │   (Escalation)  │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Leantime      │    │     Morph Fast-Apply │    │   Playwright    │
│   (Strategy)    │    │    (Code Edits)      │    │   (Validation)   │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
```

## Core Capabilities

### Task Decomposition
- **Input**: Natural language task descriptions from ConPort upcoming queue
- **Output**: 3-5 actionable subtasks with dependencies
- **ADHD Optimization**: Maximum 3 subtasks to prevent cognitive overload

### Implementation Coordination
- **Status Tracking**: Real-time subtask progress updates
- **Dependency Management**: Prevents starting tasks with unmet prerequisites
- **Artifact Linking**: Associates code changes with specific subtasks

### Progress Synchronization
- **ConPort Integration**: Updates work item status in real-time
- **Decision Logging**: Records implementation choices and rationales
- **Validation Triggers**: Signals when tasks are ready for Playwright testing

## Integration Points

### With ConPort (Memory Layer)
```python
# Pull next work item
upcoming = conport.upcoming_next(limit=3)

# Plan implementation
plan = task_orchestrator.plan(upcoming[0])

# Execute with status updates
for subtask in plan.subtasks:
    # Implement using Morph
    morph.edit_file(file_path=subtask.target_file,
                   instruction=subtask.description,
                   editSnippet=subtask.code_changes)

    # Update progress
    task_orchestrator.set_status(subtask.id, "done")
    conport.decisions_add(title=f"Completed: {subtask.title}",
                         rationale="Implementation successful",
                         links=[{"work_item": task_id}])
```

### With Morph (Code Edits)
- **Edit Operations**: All code changes routed through Morph Fast-Apply
- **Verification**: Post-edit file reads to confirm changes applied correctly
- **Error Recovery**: Automatic revert and re-apply on edit mismatches

### With Playwright (Validation)
- **Trigger Points**: Validation initiated after task completion
- **Evidence Collection**: Screenshots and traces attached to ConPort artifacts
- **Status Updates**: Failed validations move tasks to "blocked" status

### With Zen (Escalation)
- **Trigger Conditions**: Task ambiguity, complex technical decisions
- **Escalation Path**: Zen consensus provides clarification for task execution
- **Fallback Integration**: Complex tasks get multi-model analysis before implementation

## Workflow Patterns

### Standard Task Execution
1. **Task Intake**: Pull from ConPort upcoming queue
2. **Planning Phase**: Decompose into 3-5 subtasks maximum
3. **Implementation**: Execute subtasks using Morph for code edits
4. **Validation**: Run Playwright scenarios for UI features
5. **Completion**: Update ConPort with results and artifacts

### Escalation Scenarios
1. **Ambiguous Requirements**: Escalate to Zen for consensus clarification
2. **Complex Architecture**: Route through Zen for multi-model analysis
3. **Implementation Blockers**: Use Zen debug workflow for problem resolution

### Recovery Patterns
1. **Edit Failures**: Automatic Morph revert and re-apply with expanded context
2. **Validation Flakes**: Playwright retry with exponential backoff
3. **Service Outages**: Continue with local state, spool operations for replay

## ADHD Optimizations

### Cognitive Load Management
- **Subtask Limits**: Maximum 3 concurrent subtasks
- **Status Granularity**: Clear progress indicators (todo → in_progress → done)
- **Atomic Operations**: Each subtask represents a complete, verifiable unit of work

### Context Preservation
- **State Synchronization**: Real-time updates to ConPort prevent context loss
- **Decision Documentation**: Every implementation choice logged with rationale
- **Artifact Linking**: Screenshots and diffs preserve validation evidence

### Failure Recovery
- **Graceful Degradation**: Continue operation when services are unavailable
- **Automatic Retry**: Intelligent backoff for transient failures
- **Manual Escalation**: Clear indicators when human intervention is required

## Configuration

### MCP Server Setup
```json
{
  "task-orchestrator": {
    "command": "python",
    "args": ["services/task-orchestrator/server.py"],
    "env": {
      "DOPEMUX_INSTANCE_ID": "${DOPEMUX_INSTANCE_ID:-main}",
      "DOPEMUX_WORKSPACE_ID": "/Users/hue/code/dopemux-mvp"
    }
  }
}
```

### Environment Variables
- `TASK_ORCHESTRATOR_PATH`: Custom binary path (optional)
- `USE_DOCKER`: Enable Docker container mode (default: false)
- `OPENAI_API_KEY`: Required for AI-powered planning

## Tool Interface

### Core Tools
- `task_orchestrator_plan`: Break down tasks into subtasks
- `task_orchestrator_next_task`: Get next pending subtask
- `task_orchestrator_set_status`: Update subtask completion status
- `task_orchestrator_attach_artifact`: Link files to subtasks

### Integration Tools
- `task_orchestrator_sync_conport`: Update ConPort with progress
- `task_orchestrator_validate_task`: Trigger validation workflows
- `task_orchestrator_escalate_complex`: Route to Zen for complex analysis

## Performance Characteristics

### Response Times
- **Task Planning**: 5-15 seconds (depends on complexity)
- **Status Updates**: < 2 seconds
- **Subtask Execution**: Variable (depends on implementation complexity)

### Scalability Limits
- **Concurrent Tasks**: 1 active task per workspace (ADHD optimization)
- **Subtask Maximum**: 5 subtasks per task
- **History Retention**: Unlimited (stored in ConPort)

### Resource Usage
- **Memory**: ~50MB base + 10MB per active task
- **CPU**: Minimal (primarily coordination logic)
- **Storage**: Depends on artifact attachments

## Quality Assurance

### Validation Gates
- **Pre-Execution**: Task clarity assessment
- **Post-Implementation**: Code syntax validation
- **Pre-Completion**: Playwright scenario execution
- **Post-Completion**: ConPort status synchronization

### Error Handling
- **Automatic Recovery**: Retry failed operations with backoff
- **Manual Escalation**: Clear indicators for human intervention
- **Audit Trail**: Complete decision and action history

## Deployment Patterns

### Development Environment
- **Local Installation**: Python package with MCP server
- **Container Mode**: Docker deployment for isolation
- **IDE Integration**: VS Code/Cursor MCP extension

### Production Deployment
- **Scalability**: Single instance per workspace
- **High Availability**: Stateless design enables easy restart
- **Monitoring**: Health checks and performance metrics

## Future Extensions

### Planned Enhancements
- **Multi-Workspace Support**: Coordinate across multiple projects
- **Template Library**: Reusable task patterns and implementations
- **Collaborative Mode**: Multi-user task coordination

### Integration Opportunities
- **CI/CD Integration**: Automated task triggering from pipeline events
- **IDE Plugins**: Direct integration with development environments
- **Mobile Companion**: Task progress tracking on mobile devices

## Troubleshooting

### Common Issues
1. **Planning Failures**: Check task description clarity and provide more context
2. **Status Sync Issues**: Verify ConPort connectivity and permissions
3. **Validation Timeouts**: Increase Playwright timeouts for complex scenarios

### Debug Tools
- **Status Inspection**: Check current task and subtask states
- **Log Analysis**: Review execution logs for failure patterns
- **Manual Override**: Force status updates for stuck operations

## Success Metrics

### Effectiveness Measures
- **Task Completion Rate**: Percentage of tasks completed successfully
- **Time to Completion**: Average time from task intake to validation
- **Escalation Frequency**: How often Zen escalation is required

### Quality Indicators
- **Validation Pass Rate**: Percentage of validations that pass on first attempt
- **Decision Documentation**: Completeness of rationale logging
- **Artifact Coverage**: Percentage of tasks with validation evidence

This blueprint ensures Task Orchestrator serves as a reliable, ADHD-optimized tactical executor that seamlessly integrates with the broader Dopemux ecosystem while maintaining high standards of quality and reliability.
