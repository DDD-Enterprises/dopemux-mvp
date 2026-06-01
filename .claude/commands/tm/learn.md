Learn about TaskMaster capabilities through interactive exploration.

Arguments: $ARGUMENTS

## Interactive TaskMaster Learning

Based on your input, I'll help you discover capabilities:

### 1. **What are you trying to do?**

If $ARGUMENTS contains:
- "start" / "begin" → Show project initialization workflows
- "manage" / "organize" → Show task management commands  
- "automate" / "auto" → Show automation workflows
- "analyze" / "report" → Show analysis tools
- "fix" / "problem" → Show troubleshooting commands
- "fast" / "quick" → Show efficiency shortcuts

### 2. **Intelligent Suggestions**

Based on your project state:

**No tasks yet?**
```
You'll want to start with:
1. /project:TaskMaster:init <prd-file>
   → Creates tasks from requirements
   
2. /project:TaskMaster:parse-prd <file>
   → Alternative task generation

Try: /project:TaskMaster:init demo-prd.md
```

**Have tasks?**
Let me analyze what you might need...
- Many pending tasks? → Learn sprint planning
- Complex tasks? → Learn task expansion
- Daily work? → Learn workflow automation

### 3. **Command Discovery**

**By Category:**
- 📋 Task Management: list, show, add, update, complete
- 🔄 Workflows: auto-implement, sprint-plan, daily-standup
- 🛠️ Utilities: check-health, complexity-report, sync-memory
- 🔍 Analysis: validate-deps, show dependencies

**By Scenario:**
- "I want to see what to work on" → `/project:TaskMaster:next`
- "I need to break this down" → `/project:TaskMaster:expand <id>`
- "Show me everything" → `/project:TaskMaster:status`
- "Just do it for me" → `/project:workflows:auto-implement`

### 4. **Power User Patterns**

**Command Chaining:**
```
/project:TaskMaster:next
/project:TaskMaster:start <id>
/project:workflows:auto-implement
```

**Smart Filters:**
```
/project:TaskMaster:list pending high
/project:TaskMaster:list blocked
/project:TaskMaster:list 1-5 tree
```

**Automation:**
```
/project:workflows:pipeline init → expand-all → sprint-plan
```

### 5. **Learning Path**

Based on your experience level:

**Beginner Path:**
1. init → Create project
2. status → Understand state
3. next → Find work
4. complete → Finish task

**Intermediate Path:**
1. expand → Break down complex tasks
2. sprint-plan → Organize work
3. complexity-report → Understand difficulty
4. validate-deps → Ensure consistency

**Advanced Path:**
1. pipeline → Chain operations
2. smart-flow → Context-aware automation
3. Custom commands → Extend the system

### 6. **Try This Now**

Based on what you asked about, try:
[Specific command suggestion based on $ARGUMENTS]

Want to learn more about a specific command?
Type: /project:help <command-name>