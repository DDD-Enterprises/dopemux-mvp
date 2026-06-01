Quick initialization with auto-confirmation.

Arguments: $ARGUMENTS

Initialize a TaskMaster project without prompts, accepting all defaults.

## Quick Setup

```bash
TaskMaster init -y
```

## What It Does

1. Creates `.TaskMaster/` directory structure
2. Initializes empty `tasks.json`
3. Sets up default configuration
4. Uses directory name as project name
5. Skips all confirmation prompts

## Smart Defaults

- Project name: Current directory name
- Description: "TaskMaster Project"
- Model config: Existing environment vars
- Task structure: Standard format

## Next Steps

After quick init:
1. Configure AI models if needed:
   ```
   /project:tm/models/setup
   ```

2. Parse PRD if available:
   ```
   /project:tm/parse-prd <file>
   ```

3. Or create first task:
   ```
   /project:tm/add-task create initial setup
   ```

Perfect for rapid project setup!