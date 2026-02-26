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


import argparse
import subprocess


def find_files_with_patterns(root_dir: str, patterns: List[str]) -> List[Path]:
    """Find files containing any of the specified patterns using grep for speed."""
    matches = set()
    root_path = Path(root_dir).resolve()
    
    for pattern in patterns:
        try:
            # -r recursive, -l list filenames only, -I ignore binary files
            result = subprocess.run(
                ["grep", "-rlI", pattern, str(root_path)],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = Path(line)
                    # Skip .git and other hidden metadata directories
                    if any(part.startswith('.') and part != '.' for part in file_path.parts):
                        continue
                    matches.add(file_path)
        except subprocess.CalledProcessError:
            pass
    
    return sorted(list(matches))


def update_file_content(file_path: Path, replacements: List[Tuple[str, str]], dry_run: bool = False) -> bool:
    """Update file content with specified replacements."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="dopeTask Supervisor Migration Script")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")
    parser.add_argument("--root", default=".", help="Root directory to search (default: current)")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("🚀 dopeTask Supervisor Migration Script")
    if args.dry_run:
        print("🔍 RUNNING IN DRY-RUN MODE (No changes will be saved)")
    print("=" * 50)
    
    search_patterns = ["taskx", ".taskx_venv", "vendor/taskx", "TASKX_", "taskX", "TaskX"]
    replacements = [
        ("taskx", "dopetask"),
        (".taskx_venv", ".dopetask_venv"),
        ("vendor/taskx", "vendor/dopetask"),
        ("TASKX_", "DOPETASK_"),
        ("taskX", "dopeTask"),
        ("TaskX", "dopeTask"),
    ]
    
    print(f"🔍 Searching for files in '{args.root}'...")
    files_to_update = find_files_with_patterns(args.root, search_patterns)
    
    if not files_to_update:
        print("✅ No files found needing migration!")
        return 0
    
    print(f"📁 Found {len(files_to_update)} files that may need updates")
    
    if not args.no_confirm and not args.dry_run:
        confirm = input("\n🔧 Proceed with updates? (y/n): ").strip().lower()
        if confirm != 'y':
            print("🎭 Migration cancelled.")
            return 0
    
    # Perform updates and track results
    results = []
    updated_count = 0
    
    for file_path in files_to_update:
        status = update_file_content(file_path, replacements, dry_run=args.dry_run)
        if status:
            print(f"  {'🔍' if args.dry_run else '✅'} {'Would update' if args.dry_run else 'Updated'}: {file_path}")
            updated_count += 1
            results.append((file_path, "UPDATED"))
        else:
            results.append((file_path, "NO_CHANGE"))
    
    print(f"\n{'🏁 Dry run' if args.dry_run else '🎉 Migration'} complete!")
    print(f"📊 {'Identified' if args.dry_run else 'Updated'} {updated_count}/{len(files_to_update)} files")
    
    # Save report
    report_path = Path("dopetask_migration_report.txt")
    with report_path.open('w', encoding='utf-8') as f:
        f.write(f"dopeTask Migration Report {'(DRY RUN)' if args.dry_run else ''}\n")
        f.write("=" * 40 + "\n\n")
        for path, status in results:
            f.write(f"[{status}] {path}\n")
    
    print(f"📄 Report saved to: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
