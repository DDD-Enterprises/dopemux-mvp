# ⚠️ DEPRECATED: Task-Master-AI Module

**STATUS**: **DEPRECATED** - No longer used in simplified architecture
**REPLACED BY**: SuperClaude `/dx:prd-parse` with Zen planner
**DECISION**: #132, #133 (Simplified architecture - skip Task-Master-AI)

---

**Why Deprecated**: Task-Master-AI PRD parsing is redundant with SuperClaude's `/dx:prd-parse` command which uses Zen planner for decomposition and includes human review workflow (Approach C quality gate). SuperClaude provides superior integration with the Dopemux MCP stack.

**Migration**: Use `/dx:prd-parse` instead - see `.claude/modules/superclaude-integration.md` and `.claude/modules/custom-commands.md`

---

# Task-Master-AI Module (Historical Reference Only)

**Module Version**: 1.0.0
**Authority**: PRD Parsing and Task Decomposition
**Mode**: PLAN only
**Repository**: https://github.com/eyaltoledano/claude-task-master

## Authority Boundaries

**Task-Master Owns:**
- PRD parsing and analysis
- AI-driven task decomposition from requirements
- Subtask hierarchy creation
- Next-action determination and complexity scoring
- Task dependency identification

**Task-Master NEVER:**
- Updates task status (Leantime authority)
- Creates ConPort decisions (ConPort authority)
- Provides code navigation (Serena authority)

## Core Commands

### PRD Analysis & Decomposition
```bash
# Parse PRD and create task hierarchy (PLAN mode only)
# Hand off PRD to Task-Master for AI-driven analysis
# Task-Master returns structured subtask breakdown
# ConPort logs decomposition decision for future reference

# Example workflow:
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
  --summary "Use Task-Master for subtask hierarchy of STORY-ID" \
  --rationale "Task-Master specializes in AI-driven decomposition and dependency analysis" \
  --tags ["task-decomposition", "prd-analysis"]

# Create reference to Task-Master decomposition
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "external_refs" --key "TM-REF-STORY-ID" \
  --value '{"type": "taskmaster_reference", "story_id": "STORY-ID", "taskmaster_id": "TM-12345", "sync_status": "pending"}'
```

## Integration Patterns

### Task-Master → ConPort Handoff
```bash
# Receive decomposition results from Task-Master
RECEIVE_FROM_TASKMASTER() {
    STORY_ID="$1"
    TASKMASTER_RESULT="$2"

    # Log the decomposition decision
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Received task decomposition for $STORY_ID from Task-Master" \
      --rationale "Task-Master provided AI-driven subtask hierarchy with dependency analysis" \
      --tags ["handoff", "task-master"]

    # Create subtasks based on Task-Master output
    # (Parse TASKMASTER_RESULT and create ConPort entities)

    # Link back to original story
    mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
      --source_item_type "custom_data" --source_item_id "TM-SUBTASK-1" \
      --target_item_type "custom_data" --target_item_id "$STORY_ID" \
      --relationship_type "IMPLEMENTS"
}
```

## ADHD Optimizations

- **PLAN Mode Only**: Task-Master operates only during strategic thinking sessions
- **Complexity Scoring**: Provides difficulty indicators for task prioritization
- **Next-Action Clarity**: Identifies specific first steps to reduce activation energy
- **Dependency Visualization**: Clear hierarchy prevents overwhelm during execution