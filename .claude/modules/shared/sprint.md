# Sprint Management Module (mem4sprint)

**Module Version**: 1.0.0
**Framework**: mem4sprint - Comprehensive sprint management on ConPort
**Modes**: Both PLAN and ACT with mode-aware behavior
**Authority**: Sprint structure and cross-system coordination

## mem4sprint Framework Overview

**mem4sprint** provides structured sprint management with ADHD-friendly scaffolding built on ConPort's knowledge graph. It implements clear authority separation and supports the full sprint lifecycle.

### Entity Types & Authority Boundaries

#### ConPort Authority: Decisions & Patterns
- `decision`: Architectural and implementation choices with rationale
- `system_pattern`: Reusable patterns and approaches
- `retrospective_item`: Lessons learned (keep_doing/stop_doing/start_doing/action)
- `custom_data`: Project glossary, specifications, research

#### ConPort Progress Authority: Task Status & Tracking
- All task status updates via `progress_entry` (TODO → IN_PROGRESS → BLOCKED → DONE)
- Task metadata via `custom_data` (ADHD metrics, energy, complexity)
- Task dependencies via `link_conport_items`

#### SuperClaude Authority: PRD Decomposition
- PRD parsing via `/dx:prd-parse` with Zen planner
- Human review workflow (Approach C quality gate)
- ADHD metadata injection before ConPort import

#### mem4sprint Authority: Sprint Structure (ConPort custom_data)
- `sprint_goal`: High-level objectives for sprint (S-YYYY.MM format)
- `sprint_subtask`: Specific work items linked to goals
- `story`: User-facing requirements with acceptance criteria
- `epic`: Large features spanning multiple sprints
- `artifact`: Code, docs, data, APIs produced during sprint
- `test`: Validation criteria and test cases
- `bug`: Issues discovered during development
- `blocker`: Obstacles preventing progress
- `risk`: Potential issues with mitigation plans
- `sprint_metric`: Velocity, burndown, team performance data

## Sprint Entity Templates

### Core Sprint Entities

#### Sprint Goal Template
```json
{
  "type": "sprint_goal",
  "content": "<goal statement>",
  "sprint_id": "S-YYYY.MM",
  "status": "planned|active|blocked|done",
  "tags": ["feature-area"],
  "provenance": {"agent": "planner", "tool": "mem4sprint", "ts": ""}
}
```

#### Sprint Subtask Template
```json
{
  "type": "sprint_subtask",
  "content": "<subtask description>",
  "sprint_id": "S-YYYY.MM",
  "goal_id": "<goal-id>",
  "status": "planned|active|blocked|done",
  "tags": ["component"],
  "provenance": {"agent": "dev", "tool": "mem4sprint", "ts": ""}
}
```

#### Story Template
```json
{
  "type": "story",
  "content": "<user story>",
  "sprint_id": "S-YYYY.MM",
  "status": "planned|active|blocked|done",
  "acceptance_criteria": ["criterion1", "criterion2"],
  "epic_id": "<epic-id>",
  "tags": ["user-facing"],
  "provenance": {"agent": "planner", "tool": "mem4sprint", "ts": ""}
}
```

#### Artifact Template
```json
{
  "type": "artifact",
  "content": "<artifact description>",
  "artifact_kind": "file|function|api|doc|dataset|run|env",
  "status": "planned|active|blocked|done",
  "goal_id": "<goal-id>",
  "sprint_id": "S-YYYY.MM",
  "tags": ["component"],
  "provenance": {"agent": "dev", "tool": "mem4sprint", "ts": ""}
}
```

### Extended Entity Templates

#### Bug Template
```json
{
  "type": "bug",
  "content": "<bug description>",
  "status": "open|in_progress|blocked|fixed|closed",
  "severity": "low|medium|high|critical",
  "sprint_id": "S-YYYY.MM",
  "tags": ["bug-area"],
  "provenance": {"agent": "qa", "tool": "mem4sprint", "ts": ""}
}
```

#### Blocker Template
```json
{
  "type": "blocker",
  "content": "<blocker description>",
  "affects_id": "<entity-id>",
  "status": "open|resolved",
  "tags": ["blocker-type"],
  "provenance": {"agent": "pm", "tool": "mem4sprint", "ts": ""}
}
```

#### Risk Template
```json
{
  "type": "risk",
  "content": "<risk description>",
  "severity": "low|medium|high",
  "likelihood": "rare|possible|likely",
  "mitigation": "<mitigation plan>",
  "tags": ["risk-area"],
  "provenance": {"agent": "architect", "tool": "mem4sprint", "ts": ""}
}
```

## PLAN/ACT Mode Management

### PLAN Mode (active_context.mode = "PLAN")
**Triggers:** Sprint planning, architecture discussions, story breakdown, goal setting

**Behaviors:**
- Load recent contexts and relevant entities
- Synthesize approaches and ask clarifying questions
- Log decisions with rationale
- Focus on strategic thinking

**Commands:**
```bash
# Set planning mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09", "focus": "Sprint planning"}'
```

### ACT Mode (active_context.mode = "ACT")
**Triggers:** Feature implementation, bug fixing, testing, code review

**Behaviors:**
- Retrieve current goal and subtasks
- Execute minimal changes with documentation
- Link artifacts, tests, and decisions
- Focus on execution

**Commands:**
```bash
# Set execution mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{"mode": "ACT", "current_task": "S-2025.09-T1", "focus": "Implementation"}'
```

## Sprint Workflow Patterns

### Sprint Initialization Workflow
```bash
# 1. Set planning mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09", "focus": "Sprint initialization"}'

# 2. Create sprint goals
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "sprint_goals" --key "S-2025.09-G1" \
  --value '{"type": "sprint_goal", "content": "Complete mem4sprint integration", "sprint_id": "S-2025.09", "status": "planned", "tags": ["integration"]}'

# 3. Break down into stories
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "stories" --key "S-2025.09-ST1" \
  --value '{"type": "story", "content": "As a developer, I want automatic sprint management", "sprint_id": "S-2025.09", "status": "planned", "acceptance_criteria": ["Templates work", "Sync is automatic"]}'

# 4. Link story to goal
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
  --source_item_type "custom_data" --source_item_id "S-2025.09-ST1" \
  --target_item_type "custom_data" --target_item_id "S-2025.09-G1" \
  --relationship_type "IMPLEMENTS"
```

### Development Workflow
```bash
# 1. Switch to ACT mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{"mode": "ACT", "current_task": "S-2025.09-T1", "focus": "Implementation"}'

# 2. Create subtask
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "subtasks" --key "S-2025.09-T1" \
  --value '{"type": "sprint_subtask", "content": "Add mem4sprint templates to CLAUDE.md", "sprint_id": "S-2025.09", "goal_id": "S-2025.09-G1", "status": "active"}'

# 3. Track progress
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" \
  --status "IN_PROGRESS" --description "Adding comprehensive templates" \
  --linked_item_type "custom_data" --linked_item_id "S-2025.09-T1"

# 4. Create artifacts
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "artifacts" --key "S-2025.09-A1" \
  --value '{"type": "artifact", "content": "Updated CLAUDE.md with templates", "artifact_kind": "doc", "status": "active", "goal_id": "S-2025.09-G1"}'

# 5. Link subtask produces artifact
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
  --source_item_type "custom_data" --source_item_id "S-2025.09-T1" \
  --target_item_type "custom_data" --target_item_id "S-2025.09-A1" \
  --relationship_type "PRODUCES"
```

## Sprint Query Patterns

### Find Current Sprint Items
```bash
# Get all items for current sprint
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term 'value_text:"sprint_id:S-2025.09"' --limit 20

# Find blocked items
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term 'value_text:"status:blocked" value_text:"sprint_id:S-2025.09"' --limit 10

# Get sprint decisions
mcp__conport__search_decisions_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term 'tags:"S-2025.09"' --limit 5
```

### Sprint Analytics
```bash
# Sprint velocity
mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "sprint_metrics" --key "S-2025.09_velocity"

# Retrospective items
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
  --query_term 'category:"retrospective" value_text:"sprint_id:S-2025.09"' --limit 10
```

## ADHD Optimizations

### Visual Progress Indicators
```bash
# Sprint burndown
SHOW_SPRINT_PROGRESS() {
    SPRINT_ID="$1"

    TOTAL_ITEMS=$(mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
      --query_term "value_text:\"sprint_id:$SPRINT_ID\"" --output_mode "count")
    DONE_ITEMS=$(mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
      --query_term "value_text:\"status:done\" value_text:\"sprint_id:$SPRINT_ID\"" --output_mode "count")

    echo "🚀 Sprint $SPRINT_ID Progress:"
    echo "Goals: [████░░░░] $DONE_ITEMS/$TOTAL_ITEMS complete ✅"
    echo "🎯 Ready for work: $(count_ready_tasks $SPRINT_ID) items"
    echo "🔴 Blockers: $(count_blocked_tasks $SPRINT_ID) open"
}
```

### Next Action Recommendations
```bash
# Find next actions (planned items)
SUGGEST_NEXT_ACTIONS() {
    SPRINT_ID="$1"

    echo "🎯 Ready for work:"
    mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" \
      --query_term 'value_text:"status:planned" value_text:"sprint_id:'$SPRINT_ID'"' --limit 3
}
```

## Relationship System

### Supported Relationships
- `BLOCKED_BY`: Item cannot proceed due to dependency
- `IMPLEMENTS`: Implementation relationship (subtask → story)
- `VERIFIES`: Testing relationship (test → artifact)
- `DEPENDS_ON`: Dependency without blocking
- `PRODUCES`: Creation relationship (subtask → artifact)
- `CONSUMES`: Usage relationship (artifact → data)
- `DERIVED_FROM`: Evolution relationship (v2 → v1)
- `RELATED_TO`: General association
- `CLARIFIES`: Documentation relationship (rfc → decision)
- `RESOLVES`: Resolution relationship (action → bug)
- `TRACKS`: Monitoring relationship (metric → goal)

### Relationship Linking
```bash
# Link sprint entities
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" \
  --source_item_type "custom_data" --source_item_id "SOURCE-ID" \
  --target_item_type "custom_data" --target_item_id "TARGET-ID" \
  --relationship_type "IMPLEMENTS"
```