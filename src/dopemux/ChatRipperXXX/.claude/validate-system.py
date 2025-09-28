#!/usr/bin/env python3
"""
Simple MCP System Validation Script
"""

import json
import os
from pathlib import Path
from datetime import datetime

def validate_system():
    """Simple system validation"""
    print("🔍 MCP System Validation")
    print("=" * 40)

    project_root = Path('.')
    claude_dir = project_root / '.claude'
    issues = []
    successes = []

    # Check directories
    required_dirs = [
        '.claude/todos',
        '.claude/templates',
        '.claude/monitoring',
        '.claude/workflows',
        '.claude/scripts'
    ]

    for dir_path in required_dirs:
        if (project_root / dir_path).exists():
            successes.append(f"✅ Directory: {dir_path}")
        else:
            issues.append(f"❌ Missing directory: {dir_path}")

    # Check key files
    key_files = [
        '.claude/mcp-config.json',
        '.claude/settings.json',
        '.claude/conport-integration.yaml',
        '.claude/system-validation.py',
        '.claude/monitoring/config.yaml'
    ]

    for file_path in key_files:
        if (project_root / file_path).exists():
            successes.append(f"✅ File: {file_path}")
        else:
            issues.append(f"❌ Missing file: {file_path}")

    # Check todo system
    todo_count = 0
    for priority in ['high', 'medium', 'low']:
        priority_dir = project_root / '.claude' / 'todos' / priority
        if priority_dir.exists():
            todo_count += len(list(priority_dir.glob('*.md')))

    if todo_count > 0:
        successes.append(f"✅ Todo system: {todo_count} tasks")
    else:
        issues.append("❌ No tasks found in todo system")

    # Summary
    print(f"\\n✅ Successes ({len(successes)}):")
    for success in successes:
        print(f"  {success}")

    if issues:
        print(f"\\n❌ Issues ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\\n✅ No issues found!")

    # Status
    if issues:
        print("\\n⚠️  SYSTEM STATUS: Needs attention")
        return False
    else:
        print("\\n✅ SYSTEM STATUS: Fully configured")
        print("\\n🚀 Ready to use optimized MCP workflows!")
        print("\\n💡 Try:")
        print("  python .claude/commands/todo-manager.py add 'Test task' high")
        print("  python .claude/monitoring/performance-tracker.py")
        return True

if __name__ == '__main__':
    validate_system()