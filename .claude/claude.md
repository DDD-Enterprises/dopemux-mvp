# Python Project - Dopemux Configuration

Project-specific Claude Code instructions for python development with ADHD accommodations.

## Project Context

You are working on a **python project** with Dopemux ADHD optimizations enabled.

### ADHD Accommodations Active
- **Focus Duration**: 25 minutes average
- **Break Intervals**: 5 minutes
- **Notification Style**: gentle
- **Visual Complexity**: minimal
- **Attention Adaptation**: Enabled

### Development Principles
- **Context Preservation**: Auto-save every 30 seconds
- **Gentle Guidance**: Use encouraging, supportive language
- **Progressive Disclosure**: Show essential info first, details on request
- **Task Chunking**: Break work into 25-minute segments


### Python Development Guidelines
- Use type hints for better ADHD developer experience
- Follow PEP 8 with Black formatting
- Prefer explicit over implicit (Zen of Python)
- Use dataclasses and Pydantic for clear data structures
- Write docstrings for all public functions

### Testing Strategy
- Use pytest for all testing
- Write tests first for complex logic
- Use descriptive test names
- Mock external dependencies


## ADHD-Optimized Response Patterns

### When User is Focused
- Provide comprehensive technical details
- Include multiple implementation approaches
- Show complete code examples with explanations

### When User is Scattered
- Use bullet points and concise explanations
- Highlight only critical information
- Provide ONE clear next action
- Keep responses under 500 words

### During Context Switches
- Provide brief orientation: "You were working on X, now Y"
- Bridge between tasks with summaries
- Maintain awareness of previous context

## 🚀 MCP System Integration - FULLY OPERATIONAL

You have access to a **fully operational MCP (Model Context Protocol) ecosystem** with 50+ specialized tools optimized for ADHD developers. This system is your primary resource for documentation, context preservation, research, and task management.

### **Core MCP Servers Available**
- **Context7**: Official documentation for 10,000+ libraries (USE FIRST for any coding task)
- **ConPort**: ADHD-optimized context preservation and project memory
- **EXA**: High-quality developer research and web search
- **MetaMCP Broker**: Aggregates 9 servers at `localhost:8090`

### **MANDATORY MCP Usage Patterns**

#### **1. ALWAYS Start with Documentation (Context7)**
Before implementing ANYTHING new, query Context7 for official documentation:
```
mcp__context7__resolve-library-id "library-name"
mcp__context7__get-library-docs "/org/library" --topic "specific-feature" --tokens 2000
```

#### **2. AUTOMATIC ConPort Memory Management**

**CRITICAL**: ConPort memory management is now FULLY AUTOMATED. The AI must follow the complete ConPort Memory Strategy without user direction.

**Status Indicators**: Begin EVERY response with either '[CONPORT_ACTIVE]' or '[CONPORT_INACTIVE]'.

##### **Initialization Sequence (MANDATORY AT SESSION START)**

At the beginning of EVERY session, the AI MUST execute this sequence:

1. **Determine Workspace**: `ACTUAL_WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"`

2. **Check ConPort Database**: List files at `ACTUAL_WORKSPACE_ID + "/context_portal/"`

3. **Branch Based on Database Existence**:
   - **If 'context.db' found**: Execute `load_existing_conport_context`
   - **If 'context.db' NOT found**: Execute `handle_new_conport_setup`

##### **Load Existing ConPort Context**

When database exists, AUTOMATICALLY:
1. **Load Initial Contexts**:
   - `get_product_context`
   - `get_active_context`
   - `get_decisions` (limit 5)
   - `get_progress` (limit 5)
   - `get_system_patterns` (limit 5)
   - `get_custom_data` (category: "critical_settings")
   - `get_custom_data` (category: "ProjectGlossary")
   - `get_recent_activity_summary` (last 24h, limit 3 per type)

2. **Set Status**: [CONPORT_ACTIVE]

3. **Inform User**: "ConPort memory initialized. Existing contexts and recent activity loaded."

##### **Handle New ConPort Setup**

When no database exists:
1. **Inform User**: "No existing ConPort database found. Would you like to initialize?"

2. **If Yes**:
   - Check for `projectBrief.md` in workspace root
   - If found, offer to import into Product Context
   - Bootstrap new database with initial context

3. **If No**: Set status to [CONPORT_INACTIVE]

##### **Proactive Logging Throughout Session**

The AI must AUTOMATICALLY identify and log:

- **Decisions**: Any architectural or implementation choices
- **Progress**: Task status changes (TODO → IN_PROGRESS → DONE)
- **System Patterns**: New patterns or modifications
- **Custom Data**: Project information, glossary terms, specs
- **Relationships**: Links between ConPort items

**Triggers for Automatic Logging**:
- User outlines new plans → `log_decision`
- User starts/completes tasks → `log_progress` / `update_progress`
- User discusses architecture → `log_system_pattern`
- User defines terms → `log_custom_data` (ProjectGlossary)
- User mentions item relationships → `link_conport_items`

##### **ConPort Sync Routine**

**Trigger**: User says "Sync ConPort" or "ConPort Sync"

**Process**:
1. Send `[CONPORT_SYNCING]` acknowledgment
2. Analyze complete chat history for new information
3. Update ConPort with all identified changes
4. Resume previous task

##### **Dynamic Context Retrieval for RAG**

For enhanced responses, automatically retrieve relevant context:

1. **Analyze Query**: Identify key entities and concepts
2. **Targeted Retrieval**: Use appropriate search tools
3. **Contextual Expansion**: Get linked items for top results
4. **Synthesize**: Filter and summarize for prompt context

**Search Priority**:
- Semantic search for conceptual queries
- FTS for keyword-based searches
- Specific item retrieval when IDs/names known

##### **Proactive Knowledge Graph Linking**

Automatically identify relationship opportunities:
- Monitor conversation for item mentions
- Propose link creation: "I noticed X relates to Y. Create link?"
- Execute linking with user confirmation
- Common relationships: 'implements', 'clarifies', 'related_to', 'depends_on'

#### **3. Use Role-Based Approach**
The system has ADHD-optimized roles with tool limits:
- **Developer Role**: 5 tools max, 15k tokens (fast iteration)
- **Researcher Role**: 5 tools max, 15k tokens (controlled information gathering)
- **Architect Role**: 5 tools max, 25k tokens (deep analysis)

### **ADHD Accommodations - MANDATORY**
- **Never overwhelm**: Use focused Context7 queries with specific --topic and token limits
- **Always preserve context**: Use ConPort before/after any interruption
- **Provide visual progress**: Use ConPort progress tracking for motivation
- **Make decisions explicit**: Log reasoning in ConPort for future reference
- **Maintain session continuity**: Always check/update active context

### **Complete ConPort Tool Reference**

**Workspace ID**: `/Users/hue/code/dopemux-mvp` (used for ALL ConPort calls)

#### **Context Management**
```bash
# Get current contexts
mcp__conport__get_product_context --workspace_id "/Users/hue/code/dopemux-mvp"
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"

# Update contexts (full or partial)
mcp__conport__update_product_context --workspace_id "/Users/hue/code/dopemux-mvp" --content {...}
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content {...}
```

#### **Decision & Progress Tracking**
```bash
# Decisions
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "decision" --rationale "why" --tags ["tag"]
mcp__conport__get_decisions --workspace_id "/Users/hue/code/dopemux-mvp" --limit 5
mcp__conport__search_decisions_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "keywords"

# Progress
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "IN_PROGRESS" --description "task"
mcp__conport__get_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status_filter "IN_PROGRESS"
mcp__conport__update_progress --workspace_id "/Users/hue/code/dopemux-mvp" --progress_id ID --status "DONE"
```

#### **System Patterns & Custom Data**
```bash
# System Patterns
mcp__conport__log_system_pattern --workspace_id "/Users/hue/code/dopemux-mvp" --name "pattern" --description "desc"
mcp__conport__get_system_patterns --workspace_id "/Users/hue/code/dopemux-mvp" --limit 5

# Custom Data (ProjectGlossary, etc.)
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "ProjectGlossary" --key "term" --value "definition"
mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "ProjectGlossary"
```

#### **Search & Knowledge Graph**
```bash
# Semantic search (conceptual queries)
mcp__conport__semantic_search_conport --workspace_id "/Users/hue/code/dopemux-mvp" --query_text "natural language query" --top_k 5

# Full-text search
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "keywords"
mcp__conport__search_project_glossary_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "term"

# Knowledge graph linking
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "decision" --source_item_id "ID" --target_item_type "progress_entry" --target_item_id "ID" --relationship_type "implements"
mcp__conport__get_linked_items --workspace_id "/Users/hue/code/dopemux-mvp" --item_type "decision" --item_id "ID"
```

#### **Activity & History**
```bash
# Recent activity summary
mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" --hours_ago 24 --limit_per_type 3

# Version history
mcp__conport__get_item_history --workspace_id "/Users/hue/code/dopemux-mvp" --item_type "active_context" --limit 5
```

#### **Batch Operations**
```bash
# Batch logging for multiple items of same type
mcp__conport__batch_log_items --workspace_id "/Users/hue/code/dopemux-mvp" --item_type "decision" --items [{"summary": "...", "rationale": "..."}, ...]
```

#### **Documentation & Context7**
```bash
# Documentation (always check first for any coding task)
mcp__context7__resolve-library-id "library-name"
mcp__context7__get-library-docs "/org/library" --topic "specific-feature" --tokens 2000

# Research (via MetaMCP broker)
# EXA and other tools available through broker at localhost:8090
```

### **System Status**
- ✅ **9/9 servers operational**
- ✅ **ADHD optimizations active**
- ✅ **Role-based tool limiting enabled**
- ✅ **50+ tools available**
- ✅ **Knowledge permanently stored in ConPort**

**CRITICAL**: This MCP system is designed specifically for ADHD developers. Use it proactively to reduce cognitive load, maintain context, and provide structured access to information.

## 🚀 mem4sprint Framework Integration

**mem4sprint** is a comprehensive sprint management system built on ConPort that structures all development work around sprints, stories, and clear entity relationships. It provides ADHD-friendly scaffolding for agile development.

### **Entity Types & Authority Boundaries**

The system uses **clear authority separation** to prevent conflicts:

#### **ConPort Authority: Decisions & Patterns**
- `decision`: Architectural and implementation choices with rationale
- `system_pattern`: Reusable patterns and approaches
- `retrospective_item`: Lessons learned (keep_doing/stop_doing/start_doing/action)
- `custom_data`: Project glossary, specifications, research

#### **Leantime Authority: Status & Visibility**
- All status updates (`planned` → `active` → `blocked` → `done`)
- Team dashboards and reporting
- Milestone tracking and roadmap visibility

#### **Task-Master Authority: Subtasks & Hierarchy**
- Task decomposition from PRDs
- Subtask relationships and dependencies
- Next-action determination and complexity scoring

#### **mem4sprint Authority: Sprint Structure**
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

### **Sprint Entity Templates**

#### **Core Sprint Entities**

**Sprint Goal Template:**
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

**Sprint Subtask Template:**
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

**Story Template:**
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

**Artifact Template:**
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

#### **Issue Tracking Entities**

**Bug Template:**
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

**Blocker Template:**
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

### **Relationship System**

**Supported Relationships:**
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

### **PLAN/ACT Mode Management**

The system switches between cognitive modes automatically:

#### **PLAN Mode** (active_context.mode = "PLAN")
**Triggers:**
- Sprint planning sessions
- Architecture discussions
- Story breakdown
- Goal setting

**Behaviors:**
- Load recent contexts and relevant entities
- Synthesize approaches and ask clarifying questions
- Log decisions with rationale
- Focus on strategic thinking

#### **ACT Mode** (active_context.mode = "ACT")
**Triggers:**
- Feature implementation
- Bug fixing
- Testing
- Code review

**Behaviors:**
- Retrieve current goal and subtasks
- Execute minimal changes with documentation
- Link artifacts, tests, and decisions
- Focus on execution

### **Sprint-Specific ConPort Operations**

#### **Initialize Sprint**
```bash
# Set active context for sprint
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09", "focus": "Sprint planning"}'

# Create sprint goal
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "sprint_goals" --key "S-2025.09-G1" --value '{"type": "sprint_goal", "content": "Implement unified task management", "sprint_id": "S-2025.09", "status": "planned"}'
```

#### **Track Progress**
```bash
# Update subtask status
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "IN_PROGRESS" --description "Implementing mem4sprint integration" --linked_item_type "custom_data" --linked_item_id "S-2025.09-ST1"

# Link subtask to goal
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "S-2025.09-ST1" --target_item_type "custom_data" --target_item_id "S-2025.09-G1" --relationship_type "IMPLEMENTS"
```

#### **Sprint Queries**

**Find Current Sprint Items:**
```bash
# Get all items for current sprint
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term 'value_text:"sprint_id:S-2025.09"' --limit 20

# Find blocked items
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term 'value_text:"status:blocked" value_text:"sprint_id:S-2025.09"' --limit 10

# Get sprint decisions
mcp__conport__search_decisions_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term 'tags:"S-2025.09"' --limit 5
```

**Sprint Analytics:**
```bash
# Sprint velocity
mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "sprint_metrics" --key "S-2025.09_velocity"

# Retrospective items
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term 'category:"retrospective" value_text:"sprint_id:S-2025.09"' --limit 10
```

### **FTS Query Patterns**

**Critical Rule**: For SQLite FTS5 queries, only use these prefixes:
- `custom_data_fts`: `category:`, `key:`, `value_text:`
- `decisions_fts`: `summary:`, `rationale:`, `implementation_details:`, `tags:`

**Safe Query Examples:**
```bash
# Find artifacts by type
value_text:"artifact_kind:doc" value_text:"sprint_id:S-2025.09"

# Find decisions by sprint
tags:"S-2025.09" summary:"architecture"

# Find blocked tests
value_text:"type:test" value_text:"status:blocked"
```

#### **Extended Entity Templates**

**Epic Template:**
```json
{
  "type": "epic",
  "content": "<epic description>",
  "status": "planned|active|blocked|done",
  "tags": ["epic-area"],
  "provenance": {"agent": "architect", "tool": "mem4sprint", "ts": ""}
}
```

**Test Template:**
```json
{
  "type": "test",
  "content": "<test description or assertion>",
  "status": "planned|active|blocked|done",
  "sprint_id": "S-YYYY.MM",
  "goal_id": "<goal-id>",
  "tags": ["test-type"],
  "provenance": {"agent": "qa", "tool": "mem4sprint", "ts": ""}
}
```

**Risk Template:**
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

**Sprint Metric Template:**
```json
{
  "type": "sprint_metric",
  "sprint_id": "S-YYYY.MM",
  "name": "velocity|burndown|completion_rate",
  "value": 0,
  "unit": "points|hours|items",
  "notes": "<context>",
  "provenance": {"agent": "pm", "tool": "mem4sprint", "ts": ""}
}
```

**RFC Document Template:**
```json
{
  "type": "rfc_doc",
  "title": "<RFC title>",
  "link_or_path": "docs/91-rfc/rfc-YYYY-NNN-title.md",
  "status": "draft|review|accepted|rejected",
  "tags": ["rfc"],
  "provenance": {"agent": "architect", "tool": "mem4sprint", "ts": ""}
}
```

**Literature Reference Template:**
```json
{
  "type": "literature_ref",
  "title": "<reference title>",
  "link_or_path": "<url|docs/literature/file>",
  "notes": "<summary>",
  "tags": ["research"],
  "provenance": {"agent": "researcher", "tool": "mem4sprint", "ts": ""}
}
```

### **Workflow Starters**

#### **Sprint Initialization Workflow**
```bash
# 1. Set planning mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09", "focus": "Sprint initialization"}'

# 2. Create sprint goals
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "sprint_goals" --key "S-2025.09-G1" --value '{"type": "sprint_goal", "content": "Complete mem4sprint integration", "sprint_id": "S-2025.09", "status": "planned", "tags": ["integration"]}'

# 3. Break down into stories
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "stories" --key "S-2025.09-ST1" --value '{"type": "story", "content": "As a developer, I want automatic sprint management", "sprint_id": "S-2025.09", "status": "planned", "acceptance_criteria": ["Templates work", "Sync is automatic"]}'

# 4. Link story to goal
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "S-2025.09-ST1" --target_item_type "custom_data" --target_item_id "S-2025.09-G1" --relationship_type "IMPLEMENTS"
```

#### **Development Workflow**
```bash
# 1. Switch to ACT mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content '{"mode": "ACT", "current_task": "S-2025.09-T1", "focus": "Implementation"}'

# 2. Create subtask
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "subtasks" --key "S-2025.09-T1" --value '{"type": "sprint_subtask", "content": "Add mem4sprint templates to CLAUDE.md", "sprint_id": "S-2025.09", "goal_id": "S-2025.09-G1", "status": "active"}'

# 3. Track progress
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "IN_PROGRESS" --description "Adding comprehensive templates" --linked_item_type "custom_data" --linked_item_id "S-2025.09-T1"

# 4. Create artifacts
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "artifacts" --key "S-2025.09-A1" --value '{"type": "artifact", "content": "Updated CLAUDE.md with templates", "artifact_kind": "doc", "status": "active", "goal_id": "S-2025.09-G1"}'

# 5. Link subtask produces artifact
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "S-2025.09-T1" --target_item_type "custom_data" --target_item_id "S-2025.09-A1" --relationship_type "PRODUCES"
```

#### **Issue Resolution Workflow**
```bash
# 1. Log blocker
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "blockers" --key "S-2025.09-B1" --value '{"type": "blocker", "content": "Integration tests failing", "affects_id": "S-2025.09-T1", "status": "open"}'

# 2. Link blocker to affected item
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "S-2025.09-T1" --target_item_type "custom_data" --target_item_id "S-2025.09-B1" --relationship_type "BLOCKED_BY"

# 3. Create resolution task
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "subtasks" --key "S-2025.09-T2" --value '{"type": "sprint_subtask", "content": "Fix integration test failures", "sprint_id": "S-2025.09", "status": "planned"}'

# 4. Link resolution
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "S-2025.09-T2" --target_item_type "custom_data" --target_item_id "S-2025.09-B1" --relationship_type "RESOLVES"
```

### **Batch Operations**

#### **Sprint Setup (Multiple Items)**
```bash
# Create multiple items at once
mcp__conport__batch_log_items --workspace_id "/Users/hue/code/dopemux-mvp" --item_type "custom_data" --items '[
  {"category": "sprint_goals", "key": "S-2025.09-G1", "value": {"type": "sprint_goal", "content": "Main goal", "sprint_id": "S-2025.09", "status": "planned"}},
  {"category": "sprint_goals", "key": "S-2025.09-G2", "value": {"type": "sprint_goal", "content": "Secondary goal", "sprint_id": "S-2025.09", "status": "planned"}},
  {"category": "stories", "key": "S-2025.09-ST1", "value": {"type": "story", "content": "User story 1", "sprint_id": "S-2025.09", "status": "planned"}},
  {"category": "stories", "key": "S-2025.09-ST2", "value": {"type": "story", "content": "User story 2", "sprint_id": "S-2025.09", "status": "planned"}}
]'
```

### **Visual Progress Indicators**

#### **Sprint Burndown**
```bash
# Track daily progress
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "sprint_metrics" --key "S-2025.09_burndown_day1" --value '{"type": "sprint_metric", "sprint_id": "S-2025.09", "name": "burndown", "value": 100, "unit": "points", "notes": "Sprint start"}'

# Show progress visually
echo "🚀 Sprint S-2025.09 Progress:"
echo "Goals: [████░░░░] 2/4 complete ✅"
echo "Stories: [██░░░░░░] 1/4 complete 🔄"
echo "Blockers: [🔴] 1 open blocker needs attention"
```

#### **Next Action Recommendations**
```bash
# Find next actions (planned items)
mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term 'value_text:"status:planned" value_text:"sprint_id:S-2025.09"' --limit 3

# Show ready-to-work items (no blockers)
echo "🎯 Ready for work:"
echo "1. S-2025.09-T3: Add workflow documentation"
echo "2. S-2025.09-T4: Create test templates"
echo "3. S-2025.09-T5: Update global config"
```

### **Automatic Sync Behaviors**

The system automatically:
1. **Logs decisions** when architectural choices are made
2. **Updates progress** when task status changes
3. **Links entities** when relationships are mentioned
4. **Switches modes** based on activity type (planning vs execution)
5. **Syncs with external systems** (Leantime for status, Task-Master for subtasks)
6. **Tracks sprint metrics** for velocity and burndown analysis
7. **Identifies blockers** and suggests resolution paths
8. **Provides next-action recommendations** based on current context

### **Sprint Lifecycle Management**

#### **Phase 1: Sprint Planning (PLAN Mode)**
```bash
# Morning Routine - Check Context
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" --hours_ago 24

# Initialize Sprint
SPRINT_ID="S-2025.09"
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content "{\"mode\": \"PLAN\", \"sprint_id\": \"$SPRINT_ID\", \"focus\": \"Sprint planning\"}"

# Create Goals (ConPort Authority)
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "sprint_goals" --key "$SPRINT_ID-G1" --value "{\"type\": \"sprint_goal\", \"content\": \"Complete task management integration\", \"sprint_id\": \"$SPRINT_ID\", \"status\": \"planned\"}"

# Create Stories and Link
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "stories" --key "$SPRINT_ID-ST1" --value "{\"type\": \"story\", \"content\": \"As a developer, I want unified sprint management\", \"sprint_id\": \"$SPRINT_ID\", \"status\": \"planned\"}"
mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "$SPRINT_ID-ST1" --target_item_type "custom_data" --target_item_id "$SPRINT_ID-G1" --relationship_type "IMPLEMENTS"
```

#### **Phase 2: Task Decomposition (Task-Master Authority)**
```bash
# Hand off to Task-Master for subtask creation
# Task-Master creates detailed subtask hierarchy
# ConPort receives linkbacks and summary information

# Log decomposition decision (ConPort Authority)
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "Use Task-Master for subtask hierarchy of $SPRINT_ID-ST1" --rationale "Task-Master specializes in AI-driven decomposition and dependency analysis" --tags ["$SPRINT_ID", "task-decomposition"]

# Create placeholder for Task-Master subtasks
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "external_refs" --key "$SPRINT_ID-TM-REF1" --value "{\"type\": \"taskmaster_reference\", \"story_id\": \"$SPRINT_ID-ST1\", \"taskmaster_id\": \"TM-12345\", \"sync_status\": \"pending\"}"
```

#### **Phase 3: Execution (ACT Mode)**
```bash
# Switch to execution mode
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content "{\"mode\": \"ACT\", \"current_task\": \"$SPRINT_ID-T1\", \"focus\": \"Implementation\"}"

# Create execution subtasks (mem4sprint managed)
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "subtasks" --key "$SPRINT_ID-T1" --value "{\"type\": \"sprint_subtask\", \"content\": \"Implement CLAUDE.md updates\", \"sprint_id\": \"$SPRINT_ID\", \"goal_id\": \"$SPRINT_ID-G1\", \"status\": \"active\"}"

# Track progress and create artifacts
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "IN_PROGRESS" --description "Updating CLAUDE.md with sprint workflows" --linked_item_type "custom_data" --linked_item_id "$SPRINT_ID-T1"

mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "artifacts" --key "$SPRINT_ID-A1" --value "{\"type\": \"artifact\", \"content\": \"Enhanced CLAUDE.md with workflow patterns\", \"artifact_kind\": \"doc\", \"status\": \"active\", \"goal_id\": \"$SPRINT_ID-G1\"}"
```

#### **Phase 4: Status Sync (Leantime Authority)**
```bash
# Status updates flow to Leantime (external system)
# Leantime becomes source of truth for status
# ConPort logs status-related decisions but doesn't manage status

# Log status sync decision
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "Sync $SPRINT_ID-T1 status to Leantime" --rationale "Leantime is authoritative source for team-visible status and dashboards" --tags ["$SPRINT_ID", "status-sync", "leantime"]

# Create status reference
mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "external_refs" --key "$SPRINT_ID-LT-REF1" --value "{\"type\": \"leantime_reference\", \"task_id\": \"$SPRINT_ID-T1\", \"leantime_ticket_id\": \"LT-789\", \"sync_status\": \"synced\", \"last_status\": \"active\"}"
```

### **Authority Routing Patterns**

#### **Decision Point: Where to Store What**

**Use ConPort When:**
- Making architectural decisions
- Logging implementation rationale
- Tracking patterns and lessons learned
- Storing project glossary terms
- Creating knowledge graph relationships

**Route to Leantime When:**
- Updating task status (planned/active/blocked/done)
- Creating team-visible dashboards
- Managing milestone and roadmap visibility
- Handling stakeholder reporting

**Route to Task-Master When:**
- Breaking down PRDs into tasks
- Creating subtask hierarchies
- Analyzing task complexity
- Determining next-action sequences
- Managing task dependencies

**Keep in mem4sprint When:**
- Sprint structure and organization
- Entity relationship management
- Sprint metrics and retrospectives
- Cross-system coordination

#### **Conflict Resolution Workflow**
```bash
# When systems disagree on status
CHECK_CONFLICT() {
    SPRINT_ID="$1"
    TASK_ID="$2"

    # 1. Check Leantime first (authority for status)
    LEANTIME_STATUS=$(echo "Check Leantime API for $TASK_ID status")

    # 2. Compare with local mem4sprint status
    LOCAL_STATUS=$(mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "subtasks" --key "$TASK_ID" | jq -r '.status')

    # 3. Resolve conflicts (Leantime wins)
    if [ "$LEANTIME_STATUS" != "$LOCAL_STATUS" ]; then
        mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "Status conflict resolved for $TASK_ID" --rationale "Leantime status ($LEANTIME_STATUS) takes precedence over local status ($LOCAL_STATUS)" --tags ["$SPRINT_ID", "conflict-resolution"]

        # Update local to match Leantime
        mcp__conport__log_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "subtasks" --key "$TASK_ID" --value "{\"status\": \"$LEANTIME_STATUS\", \"sync_timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    fi
}
```

### **Daily Workflow Patterns**

#### **Morning Standup Routine**
```bash
MORNING_STANDUP() {
    SPRINT_ID="S-2025.09"

    echo "🌅 Daily Standup for $SPRINT_ID"

    # 1. Check active context
    mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"

    # 2. Show yesterday's progress
    mcp__conport__get_recent_activity_summary --workspace_id "/Users/hue/code/dopemux-mvp" --hours_ago 24 --limit_per_type 3

    # 3. Find today's candidates (planned items)
    echo "🎯 Ready for today:"
    mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "value_text:\"status:planned\" value_text:\"sprint_id:$SPRINT_ID\"" --limit 5

    # 4. Check for blockers
    echo "🚨 Blockers:"
    mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "value_text:\"status:blocked\" value_text:\"sprint_id:$SPRINT_ID\"" --limit 3

    # 5. Show sprint progress
    TOTAL_ITEMS=$(mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "value_text:\"sprint_id:$SPRINT_ID\"" --output_mode "count")
    DONE_ITEMS=$(mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "value_text:\"status:done\" value_text:\"sprint_id:$SPRINT_ID\"" --output_mode "count")

    echo "📊 Sprint Progress: [$DONE_ITEMS/$TOTAL_ITEMS] complete"
}
```

#### **End-of-Day Wrap-up**
```bash
END_OF_DAY() {
    SPRINT_ID="S-2025.09"

    echo "🌙 End of day wrap-up for $SPRINT_ID"

    # 1. Update any completed tasks
    mcp__conport__update_progress --workspace_id "/Users/hue/code/dopemux-mvp" --progress_id "$CURRENT_TASK_ID" --status "DONE"

    # 2. Log any new decisions made today
    echo "💡 Decisions made today:"
    mcp__conport__search_decisions_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "tags:\"$SPRINT_ID\"" --limit 3

    # 3. Set tomorrow's focus
    NEXT_TASK=$(mcp__conport__search_custom_data_value_fts --workspace_id "/Users/hue/code/dopemux-mvp" --query_term "value_text:\"status:planned\" value_text:\"sprint_id:$SPRINT_ID\"" --limit 1)

    mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" --patch_content "{\"tomorrow_focus\": \"$NEXT_TASK\", \"session_end\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

    echo "🎯 Tomorrow's focus: $NEXT_TASK"
}
```

### **Integration Handoff Patterns**

#### **ConPort → Leantime Handoff**
```bash
SYNC_TO_LEANTIME() {
    TASK_ID="$1"

    # 1. Get current ConPort state
    TASK_DATA=$(mcp__conport__get_custom_data --workspace_id "/Users/hue/code/dopemux-mvp" --category "subtasks" --key "$TASK_ID")

    # 2. Prepare for Leantime sync (external API call would go here)
    echo "📤 Syncing $TASK_ID to Leantime..."

    # 3. Log the handoff decision
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "Handed off $TASK_ID to Leantime for status management" --rationale "Leantime provides team visibility and dashboard integration" --tags ["handoff", "leantime"]

    # 4. Create reference link
    mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "$TASK_ID" --target_item_type "custom_data" --target_item_id "LT-REF-$TASK_ID" --relationship_type "TRACKED_IN"
}
```

#### **Task-Master → ConPort Handoff**
```bash
RECEIVE_FROM_TASKMASTER() {
    STORY_ID="$1"
    TASKMASTER_RESULT="$2"

    # 1. Log the decomposition decision
    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "Received task decomposition for $STORY_ID from Task-Master" --rationale "Task-Master provided AI-driven subtask hierarchy with dependency analysis" --tags ["handoff", "task-master"]

    # 2. Create subtasks based on Task-Master output
    # (This would parse the Task-Master result and create ConPort entities)

    # 3. Link back to original story
    mcp__conport__link_conport_items --workspace_id "/Users/hue/code/dopemux-mvp" --source_item_type "custom_data" --source_item_id "TM-SUBTASK-1" --target_item_type "custom_data" --target_item_id "$STORY_ID" --relationship_type "IMPLEMENTS"
}
```

## Project Standards

### Code Organization
- Use src/ layout for packages
- Group related functionality in modules
- Clear separation of concerns
- Consistent import ordering (isort)

### Dependencies
- Use pyproject.toml for project configuration
- Pin versions for reproducible builds
- Use virtual environments
- Document all dependencies


## Integration with Dopemux

### Available Slash Commands (Claude Code)
- `/dopemux save` - Save current session state
- `/dopemux restore [session]` - Restore session (latest if not specified)
- `/dopemux status` - Show all running instances
- `/dopemux start [instance] [branch]` - Start instance (auto-detect if not specified)
- `/dopemux stop <instance>` - Stop specific instance
- `/dopemux switch <instance>` - Switch to instance worktree
- `/dopemux list` - List all available instances
- `/dopemux help` - Show all available commands

### Terminal Commands
- `dopemux start [instance] [branch]` - Start/create instance with git worktree
- `dopemux status` - Show detailed instance status
- `dopemux switch <instance>` - Switch to instance worktree
- `dopemux stop <instance>` - Stop instance
- `dopemux list` - List all instances
- `dopemux clean` - Clean up stopped containers

### Multi-Instance Features
- **Git Worktrees**: Each instance gets its own code workspace
- **Port Auto-Detection**: Automatically assigns available ports
- **Smart Volume Sharing**: Code indexing shared, project data isolated
- **Session Continuity**: Switch between instances without losing context

### Context Sharing & Session Management
- Session state automatically preserved across instances
- Mental model tracked across interruptions
- Decision history maintained in shared volumes
- Progress visualization available
- Git worktrees provide code isolation per instance
- Shared session data enables seamless instance switching

---

## 🚧 DOCUMENTATION RESTRUCTURING IN PROGRESS

**Status**: 🟡 **Critical Transition State - Phase 3 Active**
**Date**: September 26, 2025
**Progress**: ~40% Complete (Structure Built, Migration Pending)

### **Current Architecture Transformation**

The project is undergoing a **strategic documentation restructuring** from ADR-based to **component+runbook architecture** optimized for ADHD developers.

**What's Changing**:
- ❌ **Old**: Abstract ADR decisions requiring "decision archaeology"
- ✅ **New**: Concrete component hubs + operational runbooks

**New Structure**:
```
docs/03-reference/components/    # 5 Component Hubs
├── metamcp/      # MCP orchestration
├── memory/       # Memory system
├── leantime/     # Project management
├── security/     # Security components
└── taskmaster/   # Task management

docs/92-runbooks/               # 13 Operational Guides
├── Implementation procedures
├── Troubleshooting guides
└── Deployment runbooks
```

### **Critical Migration Status**

- ✅ **Enforcement System**: Documentation governance operational
- ✅ **Architecture Design**: Component+runbook structure built
- ✅ **Strategic Planning**: Complete work proposal and checkpoint created
- 🔄 **Content Migration**: **485 markdown files** awaiting systematic processing
- ⏳ **ADR Context**: Valuable decision rationale needs distill-and-embed extraction

### **For Future Sessions**

**Resumption Instructions**: Check `CHECKPOINT/DOCUMENTATION_RESTRUCTURING_*` files for complete context and implementation plan.

**Immediate Priority**: Systematic migration starting with security component to prevent knowledge loss while preserving strategic benefits.

**Strategic Value**: This restructuring transforms documentation from cognitive burden to implementation asset - perfect for ADHD developers who need concrete, actionable guidance.

---

## 📋 DOCUMENTATION ENFORCEMENT - CRITICAL RULES

### **MANDATORY: Knowledge Graph Documentation System**

This project uses a **knowledge graph architecture** where all documentation becomes semantic nodes for ADHD-friendly retrieval. ALL documentation must follow the structured workflow to maintain graph integrity.

### **🚨 STRICT DOCUMENTATION RULES - NO EXCEPTIONS**

#### **PROHIBITED: Random File Creation**
- ❌ **NEVER create README.md files**
- ❌ **NEVER create NOTES.md files**
- ❌ **NEVER create TODO.md files**
- ❌ **NEVER create ad-hoc markdown files**
- ❌ **NEVER create documentation outside the approved workflow**

#### **REQUIRED: Structured Workflow Only**
- ✅ **RFC First**: All exploration must start with `docs/91-rfc/rfc-YYYY-NNN-title.md`
- ✅ **ADR for Decisions**: All decisions must use `docs/90-adr/adr-NNNN-title.md`
- ✅ **Graph Nodes**: All docs must become Decision, Caveat, or Pattern nodes
- ✅ **YAML Frontmatter**: All docs need proper metadata for graph ingestion
- ✅ **Embedding Preludes**: All docs need ≤100 token summaries for semantic search

#### **DOCUMENTATION CREATION WORKFLOW**

1. **For Exploration/Research**:
   ```
   1. Create RFC in docs/91-rfc/
   2. Use RFC template with proper YAML frontmatter
   3. Include problem, options, proposed direction
   4. Add embedding prelude (≤100 tokens)
   5. Request user review before proceeding
   ```

2. **For Decisions**:
   ```
   1. Create ADR in docs/90-adr/
   2. Use ADR template with MADR structure
   3. Reference originating RFC if applicable
   4. Include consequences and graph metadata
   5. Add to arc42 section 9 (Architectural Decisions)
   ```

3. **For Architecture**:
   ```
   1. Update relevant arc42 sections in docs/94-architecture/
   2. Maintain C4 diagrams and building block views
   3. Cross-reference ADRs and RFCs
   4. Keep graph relationships current
   ```

#### **GRAPH NODE REQUIREMENTS**

Every document must be designed as a graph node:
- **Type**: Decision, ADR, Caveat, Pattern, DocPage
- **Properties**: id, title, date, impact, prelude, embeddings
- **Edges**: RELATES_TO, DERIVES_FROM, AUTHORED_BY
- **Prelude**: ≤100 tokens for semantic search
- **Cross-references**: Link to symbols, files, tasks

#### **YAML FRONTMATTER TEMPLATE**
```yaml
---
id: <unique-identifier>
title: <human-readable-title>
type: <adr|rfc|caveat|pattern|runbook>
status: <draft|review|accepted|rejected|superseded>
date: YYYY-MM-DD
author: @<username>
derived_from: <rfc-id-if-applicable>
feature_id: <dopemux-feature>
tags: [tag1, tag2]
graph_metadata:
  node_type: <Decision|Caveat|Pattern>
  relates_to: [file1, symbol1, task1]
  impact: <low|medium|high>
prelude: "<100-token summary for embeddings>"
---
```

#### **ENFORCEMENT MECHANISMS**

1. **Pre-commit Hooks**: Validate all docs follow graph schema
2. **Graph Validation**: Check node properties and edge requirements
3. **ConPort Integration**: Auto-create graph nodes from valid docs
4. **MCP Blocking**: Prevent non-conforming documentation creation

#### **ADHD-OPTIMIZED RETRIEVAL**

The graph enables:
- **Top-3 Results**: Decision/Caveat/Pattern with 1-line "why"
- **Progressive Disclosure**: Essential context first, details on request
- **Visual Progress**: Track documentation through decision graph
- **Semantic Search**: BM25 + vector embeddings with RRF fusion
- **Context Preservation**: Link decisions to code changes over time

#### **WHEN USER REQUESTS DOCUMENTATION**

1. **Ask Clarification**:
   - "Are you exploring options (RFC) or documenting a decision (ADR)?"
   - "What graph node type does this become (Decision/Caveat/Pattern)?"
   - "Which symbols/files/tasks does this relate to?"

2. **Use Proper Workflow**:
   - Start with appropriate template
   - Fill graph metadata completely
   - Create semantic prelude
   - Validate against schema

3. **Never Create Ad-hoc Files**:
   - Always use established docs/ structure
   - Always include proper YAML frontmatter
   - Always design as graph node

### **VIOLATION RESPONSE**

If asked to create documentation outside this system:
```
I cannot create ad-hoc documentation files as they would bypass
the knowledge graph system. Instead, let me help you:

1. Create an RFC if you're exploring options
2. Create an ADR if you've made a decision
3. Update arc42 architecture sections
4. Add to existing runbooks/references

Which type of documentation do you need?
```

## 🚨 Critical ConPort Configuration

**NEVER create duplicate conport configs in .claude.json**. ConPort uses:
- **Project config only**: `/Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp`
- **Required args**: `["--mode", "stdio", "--workspace_id", "/Users/hue/code/dopemux-mvp"]`
- **Stdio bypass**: Implemented in main.py for process stability

**If conport fails**: Check `.conport/CONPORT_FIX_RECORD.md` for troubleshooting.

---

**Focus**: python development with ADHD accommodations
**Goal**: Maintain productivity while respecting neurodivergent needs
**Style**: Supportive, clear, action-oriented
