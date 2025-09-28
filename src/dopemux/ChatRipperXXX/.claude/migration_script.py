#!/usr/bin/env python3
"""
Taskmaster to Markdown Todo Migration Script
Migrates all tasks from .taskmaster/tasks/tasks.json to the new markdown todo system
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def load_taskmaster_data():
    """Load all taskmaster data"""
    try:
        with open('.taskmaster/tasks/tasks.json', 'r') as f:
            taskmaster_data = json.load(f)

        with open('.taskmaster/state.json', 'r') as f:
            state_data = json.load(f)

        with open('.taskmaster/config.json', 'r') as f:
            config_data = json.load(f)

        return taskmaster_data, state_data, config_data

    except Exception as e:
        print(f"Error loading taskmaster data: {e}")
        return {}, {}, {}

def create_task_markdown(task: Dict[str, Any], task_id: int) -> str:
    """Convert a single task to markdown format"""
    title = task.get('title', 'Untitled Task')
    description = task.get('description', '')
    details = task.get('details', '')
    test_strategy = task.get('testStrategy', '')
    priority = task.get('priority', 'medium')
    status = task.get('status', 'pending')
    dependencies = task.get('dependencies', [])

    # Format priority
    priority_title = priority.title()

    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Format dependencies
    deps_text = ', '.join([f'[{dep}]' for dep in dependencies]) if dependencies else 'None'

    # Build markdown content
    markdown = f"""## Task: {title}
- **ID**: {timestamp}
- **Priority**: {priority_title}
- **Status**: {status.upper()}
- **Context**: taskmaster_migration
- **Dependencies**: {deps_text}

### Description
{description}

### Implementation Details
{details}

### Test Strategy
{test_strategy}

### Migration Notes
- Originally Task ID: {task_id}
- Migrated from taskmaster on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Priority mapping: {priority}
- Status mapping: {status}
- Dependencies: {dependencies}

### Related Files
- Original: .taskmaster/tasks/tasks.json
"""

    return markdown

def save_task_file(task_id: int, markdown_content: str, priority: str):
    """Save a task to the appropriate priority file"""
    todos_dir = Path('.claude/todos')
    todos_dir.mkdir(exist_ok=True)

    # Map priority to lowercase filename
    priority_map = {
        'high': 'high',
        'medium': 'medium',
        'low': 'low'
    }

    filename = priority_map.get(priority.lower(), 'medium')
    task_file = f"task_{task_id:03d}.md"
    filepath = todos_dir / filename / task_file

    # Ensure priority directory exists
    filepath.parent.mkdir(exist_ok=True)

    with open(filepath, 'w') as f:
        f.write(markdown_content)

    print(f"Created: {filepath} (priority: {priority})")

def migrate_tasks():
    """Main migration function"""
    print("🚀 Starting Taskmaster Migration")
    print("=" * 50)

    # Load taskmaster data
    taskmaster_data, state_data, config_data = load_taskmaster_data()

    if not taskmaster_data:
        print("❌ No taskmaster data found!")
        return

    # Extract tasks
    master_tasks = taskmaster_data.get('master', {}).get('tasks', [])

    if not master_tasks:
        print("❌ No tasks found in taskmaster data!")
        return

    print(f"📊 Found {len(master_tasks)} tasks to migrate")

    # Create directory structure
    for priority in ['high', 'medium', 'low']:
        Path(f'.claude/todos/{priority}').mkdir(parents=True, exist_ok=True)

    # Migrate each task
    migrated_count = 0
    priority_counts = {'high': 0, 'medium': 0, 'low': 0}

    for task in master_tasks:
        task_id = task.get('id', migrated_count + 1)
        priority = task.get('priority', 'medium')

        try:
            # Convert to markdown
            markdown_content = create_task_markdown(task, task_id)

            # Save to appropriate file
            save_task_file(task_id, markdown_content, priority)

            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            migrated_count += 1

        except Exception as e:
            print(f"❌ Error migrating task {task_id}: {e}")
            continue

    # Create migration summary
    summary = f"""
# Taskmaster Migration Summary

**Migration Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Tasks Migrated**: {migrated_count}

## Priority Breakdown
- **High Priority**: {priority_counts.get('high', 0)} tasks
- **Medium Priority**: {priority_counts.get('medium', 0)} tasks
- **Low Priority**: {priority_counts.get('low', 0)} tasks

## File Structure Created
```
.claude/todos/
├── high/
│   ├── task_001.md
│   └── ...
├── medium/
│   ├── task_002.md
│   └── ...
├── low/
│   ├── task_003.md
│   └── ...
├── active.md
├── completed.md
├── backlog.md
└── README.md
```

## Next Steps
1. Review migrated tasks in their respective priority folders
2. Update task statuses using the new todo system commands:
   - `/todo-status` - View current statistics
   - `/todo-add [task] [priority]` - Add new tasks
   - `/todo-complete [task_id]` - Mark tasks complete

## Original Data Preserved
- Original taskmaster data: `.taskmaster/` (backup kept)
- All task details, dependencies, and metadata preserved
- Status mappings maintained (pending → TODO, done → DONE, etc.)
"""

    with open('.claude/todos/migration_summary.md', 'w') as f:
        f.write(summary)

    print("✅ Migration Complete!")
    print(f"📊 Migrated {migrated_count} tasks")
    print(f"📁 See .claude/todos/ for all migrated tasks")
    print(f"📋 See .claude/todos/migration_summary.md for details")

    # Display priority breakdown
    print("\nPriority Breakdown:")
    for priority, count in priority_counts.items():
        print(f"  {priority.title()}: {count} tasks")

if __name__ == '__main__':
    migrate_tasks()