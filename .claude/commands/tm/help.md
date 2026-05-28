Show help for TaskMaster commands.

Arguments: $ARGUMENTS

Display help for TaskMaster commands. If arguments provided, show specific command help.

## TaskMaster Command Help

### Quick Navigation

Type `/project:tm/` and use tab completion to explore all commands.

### Command Categories

#### 🚀 Setup & Installation
- `/project:tm/setup/install` - Comprehensive installation guide
- `/project:tm/setup/quick-install` - One-line global install

#### 📋 Project Setup
- `/project:tm/init` - Initialize new project
- `/project:tm/init/quick` - Quick setup with auto-confirm
- `/project:tm/models` - View AI configuration
- `/project:tm/models/setup` - Configure AI providers

#### 🎯 Task Generation
- `/project:tm/parse-prd` - Generate tasks from PRD
- `/project:tm/parse-prd/with-research` - Enhanced parsing
- `/project:tm/generate` - Create task files

#### 📝 Task Management
- `/project:tm/list` - List tasks (natural language filters)
- `/project:tm/show <id>` - Display task details
- `/project:tm/add-task` - Create new task
- `/project:tm/update` - Update tasks naturally
- `/project:tm/next` - Get next task recommendation

#### 🔄 Status Management
- `/project:tm/set-status/to-pending <id>`
- `/project:tm/set-status/to-in-progress <id>`
- `/project:tm/set-status/to-done <id>`
- `/project:tm/set-status/to-review <id>`
- `/project:tm/set-status/to-deferred <id>`
- `/project:tm/set-status/to-cancelled <id>`

#### 🔍 Analysis & Breakdown
- `/project:tm/analyze-complexity` - Analyze task complexity
- `/project:tm/expand <id>` - Break down complex task
- `/project:tm/expand/all` - Expand all eligible tasks

#### 🔗 Dependencies
- `/project:tm/add-dependency` - Add task dependency
- `/project:tm/remove-dependency` - Remove dependency
- `/project:tm/validate-dependencies` - Check for issues

#### 🤖 Workflows
- `/project:tm/workflows/smart-flow` - Intelligent workflows
- `/project:tm/workflows/pipeline` - Command chaining
- `/project:tm/workflows/auto-implement` - Auto-implementation

#### 📊 Utilities
- `/project:tm/utils/analyze` - Project analysis
- `/project:tm/status` - Project dashboard
- `/project:tm/learn` - Interactive learning

### Natural Language Examples

```
/project:tm/list pending high priority
/project:tm/update mark all API tasks as done
/project:tm/add-task create login system with OAuth
/project:tm/show current
```

### Getting Started

1. Install: `/project:tm/setup/quick-install`
2. Initialize: `/project:tm/init/quick`
3. Learn: `/project:tm/learn start`
4. Work: `/project:tm/workflows/smart-flow`

For detailed command info: `/project:tm/help <command-name>`