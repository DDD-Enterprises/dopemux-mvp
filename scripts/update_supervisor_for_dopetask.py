#!/usr/bin/env python3
"""
Script to update supervisor configurations for dopeTask migration.
This script helps automate the transition from taskX to dopeTask in supervisor setups.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def find_files_with_patterns(root_dir: str, patterns: List[str]) -> List[Path]:
    """Find files containing any of the specified patterns."""
    matches = []
    root_path = Path(root_dir)
    
    for pattern in patterns:
        # Use grep to find files efficiently
        try:
            result = subprocess.run(
                ["grep", "-rl", pattern, str(root_path)],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = Path(line)
                    if file_path not in matches:
                        matches.append(file_path)
        except subprocess.CalledProcessError:
            # grep returned no matches, continue
            pass
    
    return matches


def update_file_content(file_path: Path, replacements: List[Tuple[str, str]]) -> bool:
    """Update file content with specified replacements."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def main():
    """Main migration function."""
    print("🚀 dopeTask Supervisor Migration Script")
    print("=" * 50)
    
    # Define search patterns and replacements
    search_patterns = [
        "taskx",
        ".taskx_venv",
        "vendor/taskx",
        "TASKX_",
        "taskX"
    ]
    
    replacements = [
        ("taskx", "dopetask"),
        (".taskx_venv", ".dopetask_venv"),
        ("vendor/taskx", "vendor/dopetask"),
        ("TASKX_", "DOPETASK_"),
        ("taskX", "dopeTask"),
        ("TaskX", "dopeTask"),
    ]
    
    # Find files that need updating
    print("🔍 Searching for files to update...")
    files_to_update = find_files_with_patterns(".", search_patterns)
    
    if not files_to_update:
        print("✅ No files found needing migration!")
        return 0
    
    print(f"📁 Found {len(files_to_update)} files that may need updating:")
    for i, file_path in enumerate(files_to_update, 1):
        print(f"  {i}. {file_path}")
    
    # Ask for confirmation
    confirm = input("\n🔧 Proceed with updates? (y/n): ").strip().lower()
    if confirm != 'y':
        print("🎭 Migration cancelled.")
        return 0
    
    # Perform updates and track which files were actually changed.
    updated_count = 0
    updated_set: set = set()
    for file_path in files_to_update:
        if update_file_content(file_path, replacements):
            print(f"✅ Updated: {file_path}")
            updated_count += 1
            updated_set.add(file_path)
        else:
            print(f"⚠️  No changes needed: {file_path}")
    
    print(f"\n🎉 Migration complete!")
    print(f"📊 Updated {updated_count}/{len(files_to_update)} files")
    
    # Generate migration report (use tracked set; do NOT re-run replacements)
    report_path = Path("dopetask_migration_report.txt")
    with report_path.open('w', encoding='utf-8') as f:
        f.write("dopeTask Migration Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Files processed: {len(files_to_update)}\n")
        f.write(f"Files updated: {updated_count}\n")
        f.write(f"Files unchanged: {len(files_to_update) - updated_count}\n\n")
        
        f.write("Updated files:\n")
        for file_path in files_to_update:
            status = "UPDATED" if file_path in updated_set else "CHECKED"
            f.write(f"  [{status}] {file_path}\n")
    
    print(f"📄 Migration report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    import subprocess
    sys.exit(main())
