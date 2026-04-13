# Todo System Commands

## Core Commands

### /todo-add
```markdown
Add a new task to the active todo list.

**Usage**: /todo-add "Task description" [priority:high|medium|low]

**Examples**:
- /todo-add "Implement user authentication system" high
- /todo-add "Write unit tests for API endpoints" medium
- /todo-add "Update README documentation" low

**Behavior**:
- Creates new task with timestamp-based ID
- Adds to appropriate priority section in active.md
- Logs to ConPort with context tags
- Creates OpenMemory context for cross-session tracking
```

### /todo-complete
```markdown
Mark a task as completed and move to archive.

**Usage**: /todo-complete [TASK_ID]

**Examples**:
- /todo-complete 20240907-143052
- /todo-complete latest (completes most recent task)

**Behavior**:
- Moves task from active.md to completed.md
- Updates completion timestamp
- Archives implementation notes to ConPort
- Updates OpenMemory with success patterns
```

### /todo-priority
```markdown
Change the priority of an existing task.

**Usage**: /todo-priority [TASK_ID] [high|medium|low]

**Examples**:
- /todo-priority 20240907-143052 low
- /todo-priority latest high

**Behavior**:
- Updates task priority in active.md
- Reorganizes task within priority sections
- Updates ConPort priority context
- Adjusts Sequential Thinking analysis priority
```

### /todo-block
```markdown
Mark a task as blocked with reason.

**Usage**: /todo-block [TASK_ID] "blocking reason"

**Examples**:
- /todo-block 20240907-143052 "Waiting for API documentation"
- /todo-block latest "Dependency on external service"

**Behavior**:
- Changes task status to BLOCKED
- Logs blocking reason in task details
- Creates ConPort blocker tracking
- Suggests Sequential Thinking for workaround analysis
```

### /todo-backlog
```markdown
Move a task to the backlog for later consideration.

**Usage**: /todo-backlog [TASK_ID]

**Examples**:
- /todo-backlog 20240907-143052

**Behavior**:
- Moves task from active.md to backlog.md
- Preserves all task details
- Maintains ConPort context
- Allows reactivation with /todo-reactivate
```

### /todo-reactivate
```markdown
Move a task from backlog back to active.

**Usage**: /todo-reactivate [TASK_ID]

**Examples**:
- /todo-reactivate 20240907-143052

**Behavior**:
- Moves task from backlog.md to active.md
- Updates priority based on current assessment
- Refreshes ConPort context
- Re-evaluates with Sequential Thinking
```

## Status Commands

### /todo-status
```markdown
Show comprehensive todo statistics and dashboard.

**Behavior**:
- Displays active task count by priority
- Shows completion trends
- Lists blocked tasks with reasons
- Provides ConPort memory usage stats
- Shows OpenMemory context coverage
```

### /todo-search
```markdown
Search tasks by content, tags, or context.

**Usage**: /todo-search "search term" [filter:active|completed|backlog|all]

**Examples**:
- /todo-search "authentication"
- /todo-search "API" completed
- /todo-search "urgent" all

**Behavior**:
- Searches ConPort for relevant context
- Uses OpenMemory for pattern matching
- Returns ranked results with context
```

### /todo-show
```markdown
Show detailed information for a specific task.

**Usage**: /todo-show [TASK_ID]

**Examples**:
- /todo-show 20240907-143052
- /todo-show latest

**Behavior**:
- Retrieves full task details from markdown
- Shows ConPort implementation notes
- Displays OpenMemory context history
- Provides Sequential Thinking analysis summary
```

## Advanced Commands

### /todo-analyze
```markdown
Analyze task patterns and provide insights.

**Usage**: /todo-analyze [period:week|month|all]

**Behavior**:
- Uses Sequential Thinking for pattern analysis
- Identifies productivity trends
- Suggests optimization opportunities
- Provides ConPort learning recommendations
```

### /todo-context
```markdown
Show context integration status for tasks.

**Behavior**:
- Displays ConPort memory coverage
- Shows OpenMemory cross-session links
- Lists Sequential Thinking analysis availability
- Provides Claude-Context integration status
```

### /todo-integrate
```markdown
Ensure full MCP integration for task management.

**Usage**: /todo-integrate [TASK_ID]

**Behavior**:
- Validates ConPort memory storage
- Confirms OpenMemory context creation
- Tests Sequential Thinking analysis
- Verifies Claude-Context code links
- Ensures Serena implementation tracking
```

## Implementation Details

### Command Pattern Matching
```python
patterns = {
    "/todo-add (.+) (high|medium|low)": "add_task",
    "/todo-complete (.+)": "complete_task",
    "/todo-priority (.+) (high|medium|low)": "change_priority",
    "/todo-block (.+) \"(.+)\'": "block_task",
    "/todo-status": "show_status",
    "/todo-show (.+)": "show_task",
    "/todo-search (.+) (.+)": "search_tasks"
}
```

### Integration Points
- **ConPort**: Task implementation tracking and memory
- **OpenMemory**: Cross-session context and patterns
- **Sequential Thinking**: Task analysis and decomposition
- **Claude-Context**: Code reference linking
- **Serena**: Implementation tracking and validation

### File Management
- `active.md`: Current work tasks by priority
- `completed.md`: Completed task archive with timestamps
- `backlog.md`: Future consideration tasks
- `templates/task.md`: New task creation template

### Context Optimization
- Automatic task deduplication via ConPort
- Cross-session context preservation via OpenMemory
- Pattern learning and suggestion via Sequential Thinking
- Code-aware task linking via Claude-Context
- Implementation validation via Serena