# ConPort MCP - Context & Knowledge Graph

**Provider**: Dopemux
**Purpose**: Project context preservation, decision logging, knowledge graph, ADHD-optimized task management
**Database**: PostgreSQL with AGE extension (graph database)
**Port**: 5455

## Overview

ConPort provides persistent memory and knowledge graph capabilities for development projects. It stores decisions, progress, system patterns, and relationships across all development activities, enabling seamless context preservation and ADHD-optimized workflows.

## Core Capabilities

### 1. Product Context - Project-Level Configuration
**Purpose**: Store overall project goals, features, and architecture

**Tools**:
- `conport/get_product_context` - Retrieve project-level context
- `conport/update_product_context` - Update with full content or patch

**Use Case**: Store high-level project goals, tech stack, architectural patterns

**Example**:
```json
{
  "project_name": "Dopemux MVP",
  "architecture": "Two-plane (PM + Cognitive)",
  "tech_stack": ["Python", "PostgreSQL", "Redis", "Docker"],
  "goals": ["ADHD-optimized development", "Knowledge graph integration"]
}
```

### 2. Active Context - Session State
**Purpose**: Track current focus, recent changes, open issues

**Tools**:
- `conport/get_active_context` - Get current session state
- `conport/update_active_context` - Update current focus/progress

**Use Case**: Resume work after interruptions, track session progress

**Example**:
```json
{
  "current_focus": "SuperClaude integration",
  "mode": "ACT",
  "sprint_id": "S-2025.10",
  "next_steps": ["Create MCP documentation", "Test commands"]
}
```

### 3. Decisions - Architecture & Implementation Choices
**Purpose**: Log important decisions with rationale for future reference

**Tools**:
- `conport/log_decision` - Create new decision record
- `conport/get_decisions` - Retrieve decisions (with filters)
- `conport/search_decisions_fts` - Full-text search across decisions
- `conport/delete_decision_by_id` - Remove decision

**Parameters**:
- `summary`: Concise decision description
- `rationale`: Why this decision was made
- `implementation_details`: How it will be implemented
- `tags`: Categorization tags

**Use Case**: Document architectural decisions, track decision evolution

**Example**:
```
log_decision:
  summary: "Use Zen MCP instead of mas-sequential-thinking"
  rationale: "Empirical testing showed mas-sequential broken (MCP errors), Zen fully operational"
  tags: ["mcp-integration", "empirical-testing"]
```

### 4. Progress Tracking - Task Management
**Purpose**: Track tasks with ADHD-optimized metadata (complexity, energy, cognitive load)

**Tools**:
- `conport/log_progress` - Create task/progress entry
- `conport/get_progress` - Retrieve progress entries
- `conport/update_progress` - Update task status
- `conport/delete_progress_by_id` - Remove task

**Parameters**:
- `status`: TODO, IN_PROGRESS, DONE, BLOCKED
- `description`: Task description
- `parent_id`: Parent task for hierarchy
- `linked_item_id/type`: Link to decision/pattern

**Use Case**: Track implementation tasks, build task hierarchies

**Example**:
```
log_progress:
  status: "IN_PROGRESS"
  description: "Update SuperClaude commands with Dopemux MCPs"
  linked_item_type: "decision"
  linked_item_id: "143"
```

### 5. System Patterns - Coding & Architecture Patterns
**Purpose**: Document reusable patterns discovered during development

**Tools**:
- `conport/log_system_pattern` - Create/update pattern
- `conport/get_system_patterns` - Retrieve patterns (with tag filters)
- `conport/delete_system_pattern_by_id` - Remove pattern

**Parameters**:
- `name`: Unique pattern name
- `description`: Pattern details
- `tags`: Categorization

**Use Case**: Capture ADHD accommodations, architectural patterns, best practices

**Example**:
```
log_system_pattern:
  name: "ADHD 25-minute Focus Session"
  description: "Pomodoro-style sessions with energy matching, auto-save, break reminders"
  tags: ["adhd", "session-management", "focus"]
```

### 6. Custom Data - Flexible Key-Value Storage
**Purpose**: Store any custom project data (glossary, sprint goals, metadata)

**Tools**:
- `conport/log_custom_data` - Store key-value data
- `conport/get_custom_data` - Retrieve by category/key
- `conport/search_custom_data_value_fts` - Full-text search
- `conport/delete_custom_data` - Remove entry

**Parameters**:
- `category`: Data category (e.g., "sprint_goals", "glossary")
- `key`: Unique key within category
- `value`: JSON-serializable data

**Use Case**: Sprint management, project glossary, custom metadata

**Example**:
```
log_custom_data:
  category: "sprint_goals"
  key: "S-2025.10-G1"
  value: {"goal": "SuperClaude integration", "status": "complete"}
```

### 7. Knowledge Graph - Relationship Tracking
**Purpose**: Link decisions, patterns, progress entries to build knowledge graph

**Tools**:
- `conport/link_conport_items` - Create relationship between items
- `conport/get_linked_items` - Get items linked to specific item

**Parameters**:
- `source_item_type/id`: Source (e.g., decision, progress_entry)
- `target_item_type/id`: Target item
- `relationship_type`: builds_upon, validates, extends, implements, depends_on
- `description`: Optional relationship description

**Use Case**: Track decision genealogy, implementation dependencies

**Example**:
```
link_conport_items:
  source: decision #143
  target: decision #142
  relationship: "extends"
  description: "MCP customization extends SuperClaude installation"
```

### 8. Semantic Search - AI-Powered Discovery
**Purpose**: Find relevant context using natural language

**Tools**:
- `conport/semantic_search_conport` - Vector-based semantic search

**Parameters**:
- `query_text`: Natural language query
- `top_k`: Number of results (default 5, max 25)
- `filter_item_types`: Optionally filter by type
- `filter_tags_include_any/all`: Tag-based filtering

**Use Case**: Find related decisions, discover patterns, context recovery

**Example**:
```
semantic_search_conport:
  query: "ADHD focus session management"
  filter_item_types: ["system_pattern", "decision"]
  top_k: 5
```

### 9. Batch Operations - Bulk Data Management
**Purpose**: Efficiently log multiple items at once

**Tools**:
- `conport/batch_log_items` - Create multiple items in one call

**Example**:
```
batch_log_items:
  item_type: "progress_entry"
  items: [
    {status: "TODO", description: "Task 1"},
    {status: "TODO", description: "Task 2"}
  ]
```

## ADHD Optimizations

### Context Preservation
- **Auto-initialize**: Always call `get_active_context` at session start
- **Frequent saves**: Update active_context every 30 seconds during work
- **Gentle re-orientation**: Use context to restore mental model after interruptions

### Task Management
- **Complexity scoring**: 0.0-1.0 scale for cognitive load estimation
- **Energy matching**: Tag tasks with energy levels (low/medium/high)
- **Break tracking**: Log break_history in custom_data
- **Progress visualization**: Use status tracking for visual progress indicators

### Decision Genealogy
- Link decisions to show evolution: Decision A → Decision B → Decision C
- Track superseded decisions with relationship_type: "supersedes"
- Full-text search for quick discovery of past decisions

## Integration with SuperClaude Commands

ConPort enables context-aware workflows:

- `/sc:load` → Retrieve active_context to restore session
- `/sc:save` → Update active_context with current state
- `/sc:workflow` → Log progress entries for PRD-decomposed tasks
- `/sc:reflect` → Search decisions and patterns for insights
- `/sc:task` → Create linked task hierarchies with dependencies

## Performance

- **Query Speed**: 2-5ms for most operations (19-105x better than targets)
- **Graph Traversal**: Optimized with PostgreSQL AGE indexes
- **Semantic Search**: Vector embeddings with 0.37ms workspace detection
- **Database Size**: Currently 113 decisions + 12 relationships + custom data

## Best Practices

### Session Management
```
# Every session start:
1. get_active_context (restore where you left off)
2. get_recent_activity_summary (last 24 hours)
3. Continue work...
4. update_active_context (save progress)
```

### Decision Logging
```
# Log decisions with:
- Clear summary (what was decided)
- Detailed rationale (why)
- Implementation specifics (how)
- Tags for discoverability
```

### Task Tracking
```
# Create task hierarchies:
1. log_progress (parent task)
2. log_progress (subtask, parent_id set)
3. link_conport_items (link to decision)
4. update_progress (mark complete)
```

## Workspace ID

**Required Parameter**: All ConPort calls require `workspace_id`
**Format**: Absolute path to project root
**Example**: `/Users/hue/code/dopemux-mvp`

---

**Status**: ✅ Fully operational (PostgreSQL AGE on port 5455)
**Database**: 143 decisions logged (as of Decision #143)
**Performance**: All queries < 5ms
**Enhancement**: Knowledge graph with relationship tracking, semantic search
