List tasks with intelligent argument parsing.

Parse arguments to determine filters and display options:
- Status: pending, in-progress, done, review, deferred, cancelled
- Priority: high, medium, low (or priority:high)
- Special: subtasks, tree, dependencies, blocked
- IDs: Direct numbers (e.g., "1,3,5" or "1-5")
- Complex: "pending high" = pending AND high priority

Arguments: $ARGUMENTS

Let me parse your request intelligently:

1. **Detect Filter Intent**
   - If arguments contain status keywords → filter by status
   - If arguments contain priority → filter by priority
   - If arguments contain "subtasks" → include subtasks
   - If arguments contain "tree" → hierarchical view
   - If arguments contain numbers → show specific tasks
   - If arguments contain "blocked" → show blocked tasks only

2. **Smart Combinations**
   Examples of what I understand:
   - "pending high" → pending tasks with high priority
   - "done today" → tasks completed today
   - "blocked" → tasks with unmet dependencies
   - "1-5" → tasks 1 through 5
   - "subtasks tree" → hierarchical view with subtasks

3. **Execute Token-Efficient Query**
   Based on parsed intent, use the most efficient TaskMaster call:
   
   **Default Pattern** (recommended - saves ~5k tokens):
   - Always start with `status` filter and `withSubtasks=false`
   - Use `limit≤10` for unfiltered queries
   - Example: `status=pending withSubtasks=false`
   
   **Token-Conscious Execution**:
   - "pending" → `status=pending withSubtasks=false`
   - "pending high" → `status=pending withSubtasks=false` + client-side priority filter
   - "1-5" → `status=pending,done withSubtasks=false limit=10` + client-side ID filter
   - "blocked" → `status=pending withSubtasks=false` + dependency analysis

4. **Enhanced Display**
   - Group by relevant criteria
   - Show most important information first
   - Use visual indicators for quick scanning
   - Include relevant metrics

5. **Intelligent Suggestions**
   Based on what you're viewing, suggest next actions:
   - Many pending? → Suggest priority order
   - Many blocked? → Show dependency resolution
   - Looking at specific tasks? → Show related tasks