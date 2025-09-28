#!/usr/bin/env python3
"""
Advanced Todo Manager
Comprehensive todo system with MCP integration and markdown management
"""

import json
import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

@dataclass
class TodoTask:
    id: str
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "TODO"
    dependencies: List[str] = None
    created: str = ""
    updated: str = ""
    context: str = ""
    related_files: List[str] = None
    implementation_notes: str = ""
    acceptance_criteria: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.related_files is None:
            self.related_files = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.updated:
            self.updated = datetime.now().isoformat()

class TodoManager:
    def __init__(self):
        self.todos_dir = Path('.claude/todos')
        self.todos_dir.mkdir(exist_ok=True)

        # Create priority directories
        for priority in ['high', 'medium', 'low']:
            (self.todos_dir / priority).mkdir(exist_ok=True)

        # Create main tracking files
        self.active_file = self.todos_dir / 'active.md'
        self.completed_file = self.todos_dir / 'completed.md'
        self.backlog_file = self.todos_dir / 'backlog.md'

        # Create MCP integration data
        self.mcp_data_file = self.todos_dir / 'mcp_integration.json'

    def _get_timestamp_id(self) -> str:
        """Generate timestamp-based ID"""
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def _parse_task_markdown(self, content: str) -> Optional[TodoTask]:
        """Parse markdown task content into TodoTask object"""
        try:
            lines = content.split('\n')
            task = TodoTask("", "")

            # Extract basic info
            for line in lines:
                if line.startswith('## Task: '):
                    task.title = line.replace('## Task: ', '').strip()
                elif line.startswith('- **ID**: '):
                    task.id = line.replace('- **ID**: ', '').strip()
                elif line.startswith('- **Priority**: '):
                    task.priority = line.replace('- **Priority**: ', '').strip().lower()
                elif line.startswith('- **Status**: '):
                    task.status = line.replace('- **Status**: ', '').strip().upper()
                elif line.startswith('- **Dependencies**: '):
                    deps_str = line.replace('- **Dependencies**: ', '').strip()
                    if deps_str != 'None':
                        task.dependencies = [d.strip('[] ') for d in deps_str.split(',')]
                elif line.startswith('- **Context**: '):
                    task.context = line.replace('- **Context**: ', '').strip()

            # Extract description
            desc_match = re.search(r'### Description\s*\n(.*?)(?=###|$)', content, re.DOTALL)
            if desc_match:
                task.description = desc_match.group(1).strip()

            # Extract implementation notes
            notes_match = re.search(r'### Implementation Notes\s*\n(.*?)(?=###|$)', content, re.DOTALL)
            if notes_match:
                task.implementation_notes = notes_match.group(1).strip()

            return task if task.title and task.id else None

        except Exception as e:
            print(f"Error parsing task markdown: {e}")
            return None

    def add_task(self, title: str, priority: str = "medium", description: str = "",
                 dependencies: List[str] = None, context: str = "") -> TodoTask:
        """Add new task"""
        task_id = self._get_timestamp_id()
        task = TodoTask(
            id=task_id,
            title=title,
            priority=priority.lower(),
            description=description,
            dependencies=dependencies or [],
            context=context or "manual_entry"
        )

        # Save to individual file
        self._save_task_to_file(task)

        # Update active.md
        self._update_active_file()

        print(f"✅ Added task: {task.title} (ID: {task.id})")
        return task

    def _save_task_to_file(self, task: TodoTask):
        """Save individual task to file"""
        priority_dir = self.todos_dir / task.priority
        priority_dir.mkdir(exist_ok=True)

        filename = f"task_{task.id.replace('-', '_').replace(':', '_')}.md"
        filepath = priority_dir / filename

        content = f"""## Task: {task.title}
- **ID**: {task.id}
- **Priority**: {task.priority.title()}
- **Status**: {task.status}
- **Context**: {task.context}
- **Dependencies**: {', '.join(f'[{d}]' for d in task.dependencies) if task.dependencies else 'None'}

### Description
{task.description or 'Task description to be added'}

### Acceptance Criteria
- [ ] {task.title} implemented
- [ ] Tests passing
- [ ] Documentation updated

### Implementation Notes
{task.implementation_notes or 'Implementation details to be added'}

### Related Files
{chr(10).join(f'- {f}' for f in task.related_files) if task.related_files else '- TBD'}

### ConPort Integration
- **Memory Key**: task_{task.id}
- **Tags**: {task.priority}, {task.context}, todo
"""

        with open(filepath, 'w') as f:
            f.write(content)

    def _update_active_file(self):
        """Update the main active.md file with current tasks"""
        content = ["# Active Tasks\n"]

        for priority in ['high', 'medium', 'low']:
            priority_dir = self.todos_dir / priority
            if not priority_dir.exists():
                continue

            content.append(f"\n## {priority.title()} Priority\n")

            for task_file in sorted(priority_dir.glob("*.md")):
                try:
                    with open(task_file, 'r') as f:
                        task_content = f.read()

                    # Extract basic info for summary
                    title_match = re.search(r'## Task: (.+)', task_content)
                    id_match = re.search(r'- \*\*ID\*\*: (.+)', task_content)
                    status_match = re.search(r'- \*\*Status\*\*: (.+)', task_content)

                    if title_match and id_match:
                        status = status_match.group(1) if status_match else 'TODO'
                        content.append(f"- [{id_match.group(1)}] {title_match.group(1)} - {status}")

                except Exception as e:
                    content.append(f"- Error reading {task_file.name}")

        content.append("
---
*This file is maintained automatically. Use `/todo-add`, `/todo-complete`, `/todo-priority` commands to manage tasks.*"        )

        with open(self.active_file, 'w') as f:
            f.write('\n'.join(content))

    def complete_task(self, task_id: str) -> bool:
        """Mark task as completed and move to archive"""
        task = self.find_task_by_id(task_id)
        if not task:
            print(f"❌ Task {task_id} not found")
            return False

        # Move task file to completed
        self._move_task_file(task, 'completed')

        # Update status in task object
        task.status = 'DONE'
        task.updated = datetime.now().isoformat()

        # Update completed.md
        self._update_completed_file(task)

        # Remove from active.md
        self._update_active_file()

        print(f"✅ Completed task: {task.title} (ID: {task.id})")
        return True

    def _move_task_file(self, task: TodoTask, new_status: str):
        """Move task file to appropriate directory"""
        old_priority_dir = self.todos_dir / task.priority
        new_dir = self.todos_dir / 'completed' if new_status == 'completed' else self.todos_dir / new_status

        if not new_dir.exists():
            new_dir.mkdir(exist_ok=True)

        old_file = old_priority_dir / f"task_{task.id.replace('-', '_').replace(':', '_')}.md"
        new_file = new_dir / f"task_{task.id.replace('-', '_').replace(':', '_')}.md"

        if old_file.exists():
            import shutil
            shutil.move(str(old_file), str(new_file))

            # Update task content with completion
            with open(new_file, 'r') as f:
                content = f.read()

            completion_note = f"\n### Completion Notes\n- **Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- **Status**: {new_status.upper()}\n"

            # Replace status line
            content = re.sub(r'- \*\*Status\*\*: .*', f'- **Status**: {new_status.upper()}', content)

            with open(new_file, 'w') as f:
                f.write(content + completion_note)

    def _update_completed_file(self, task: TodoTask):
        """Update completed.md with newly completed task"""
        try:
            if self.completed_file.exists():
                with open(self.completed_file, 'r') as f:
                    content = f.read()
            else:
                content = "# Completed Tasks\n\n## Today\n<!-- Tasks completed today will appear here -->\n\n## This Week\n<!-- Tasks completed this week will appear here -->\n\n## This Month\n<!-- Tasks completed this month will appear here -->\n"

            today_section = f"\n### {datetime.now().strftime('%Y-%m-%d')}\n- [{task.id}] {task.title} - {task.priority.title()} priority"

            # Insert after "Today" section
            content = content.replace("## Today\n<!-- Tasks completed today will appear here -->",
                                    f"## Today{today_section}\n<!-- Tasks completed today will appear here -->")

            with open(self.completed_file, 'w') as f:
                f.write(content)

        except Exception as e:
            print(f"Warning: Could not update completed file: {e}")

    def find_task_by_id(self, task_id: str) -> Optional[TodoTask]:
        """Find task by ID across all directories"""
        for priority_dir in [self.todos_dir / p for p in ['high', 'medium', 'low', 'completed', 'backlog']]:
            if not priority_dir.exists():
                continue

            for task_file in priority_dir.glob("*.md"):
                try:
                    with open(task_file, 'r') as f:
                        content = f.read()

                    if f'- **ID**: {task_id}' in content:
                        return self._parse_task_markdown(content)
                except Exception:
                    continue

        return None

    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        summary = {
            'total_active': 0,
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_status': {},
            'recent_completed': []
        }

        # Count active tasks
        for priority in ['high', 'medium', 'low']:
            priority_dir = self.todos_dir / priority
            if priority_dir.exists():
                count = len(list(priority_dir.glob("*.md")))
                summary['by_priority'][priority] = count
                summary['total_active'] += count

        # Count completed tasks (last 7 days)
        if self.completed_file.exists():
            try:
                with open(self.completed_file, 'r') as f:
                    content = f.read()

                # Simple count of recent completions
                today = datetime.now().date()
                week_ago = today - timedelta(days=7)

                summary['completed_this_week'] = content.count(str(today.year))
                summary['completed_today'] = content.count(str(today))

            except Exception:
                summary['completed_this_week'] = 0
                summary['completed_today'] = 0

        return summary

    def update_task_priority(self, task_id: str, new_priority: str) -> bool:
        """Update task priority and move to appropriate directory"""
        task = self.find_task_by_id(task_id)
        if not task:
            print(f"❌ Task {task_id} not found")
            return False

        old_priority = task.priority
        if old_priority == new_priority.lower():
            print(f"Task {task_id} already has priority: {new_priority}")
            return True

        # Update task priority
        task.priority = new_priority.lower()

        # Move file to new priority directory
        self._move_task_file(task, task.priority)

        # Update active file
        self._update_active_file()

        print(f"✅ Updated priority: {task.title} ({old_priority} → {new_priority})")
        return True

def main():
    manager = TodoManager()

    if len(sys.argv) < 2:
        print("Usage: python todo-manager.py <command> [args...]")
        print("\nCommands:")
        print("  add <title> [priority] [description] - Add new task")
        print("  complete <task_id> - Mark task as completed")
        print("  priority <task_id> <high|medium|low> - Change task priority")
        print("  status - Show status summary")
        print("  find <task_id> - Find and display task")
        return

    command = sys.argv[1].lower()

    try:
        if command == "add":
            if len(sys.argv) < 3:
                print("Usage: add <title> [priority] [description]")
                return

            title = sys.argv[2]
            priority = sys.argv[3] if len(sys.argv) > 3 else "medium"
            description = sys.argv[4] if len(sys.argv) > 4 else ""

            manager.add_task(title, priority, description)

        elif command == "complete":
            if len(sys.argv) < 3:
                print("Usage: complete <task_id>")
                return

            manager.complete_task(sys.argv[2])

        elif command == "priority":
            if len(sys.argv) < 4:
                print("Usage: priority <task_id> <high|medium|low>")
                return

            manager.update_task_priority(sys.argv[2], sys.argv[3])

        elif command == "status":
            summary = manager.get_status_summary()
            print("=== Todo Status Summary ===")
            print(f"Active Tasks: {summary['total_active']}")
            print(f"  High Priority: {summary['by_priority']['high']}")
            print(f"  Medium Priority: {summary['by_priority']['medium']}")
            print(f"  Low Priority: {summary['by_priority']['low']}")
            print(f"Completed This Week: {summary.get('completed_this_week', 0)}")
            print(f"Completed Today: {summary.get('completed_today', 0)}")

        elif command == "find":
            if len(sys.argv) < 3:
                print("Usage: find <task_id>")
                return

            task = manager.find_task_by_id(sys.argv[2])
            if task:
                print(f"Task: {task.title}")
                print(f"ID: {task.id}")
                print(f"Priority: {task.priority}")
                print(f"Status: {task.status}")
                print(f"Description: {task.description}")
            else:
                print(f"Task {sys.argv[2]} not found")

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()