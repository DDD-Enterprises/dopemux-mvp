#!/usr/bin/env python3
"""
DopeconBridge Renaming Script

Renames all references from "DopeconBridge" to "DopeconBridge" across:
- Code
- Documentation
- Environment variables
- Configuration files

Usage:
    python3 scripts/rename_to_dopecon_bridge.py
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Repository root
REPO_ROOT = Path(__file__).parent.parent

# Renaming patterns (old_pattern, new_pattern)
RENAMINGS = [
    # Code references
    ("DopeconBridge", "DopeconBridge"),
    ("dopecon_bridge", "dopecon_bridge"),
    ("dopecon-bridge", "dopecon-bridge"),
    ("DopeconBridge", "DopeconBridge"),
    ("DOPECON_BRIDGE", "DOPECON_BRIDGE"),
    
    # Service name
    ("mcp-dopecon-bridge", "dopecon-bridge"),
    ("MCP DopeconBridge", "DopeconBridge"),
    
    # File/directory names
    ("dopecon_bridge_client", "dopecon_bridge_client"),
]

# Files to rename
FILE_RENAMINGS = [
    # Shared client directory
    ("services/shared/dopecon_bridge_client", "services/shared/dopecon_bridge_client"),
    
    # Documentation files
    ("DOPECON_BRIDGE_COMPLETE.md", "DOPECONBRIDGE_COMPLETE.md"),
    ("DOPECON_BRIDGE_MIGRATION_COMPLETE.md", "DOPECONBRIDGE_MIGRATION_COMPLETE.md"),
    ("DOPECON_BRIDGE_QUICK_START.md", "DOPECONBRIDGE_QUICK_START.md"),
    ("DOPECON_BRIDGE_EXECUTIVE_SUMMARY.md", "DOPECONBRIDGE_EXECUTIVE_SUMMARY.md"),
    ("DOPECON_BRIDGE_INDEX.md", "DOPECONBRIDGE_INDEX.md"),
    (".env.dopecon_bridge.example", ".env.dopecon_bridge.example"),
]

# Files/directories to skip
SKIP_PATTERNS = [
    "__pycache__",
    ".git",
    ".pyc",
    "node_modules",
    ".venv",
    "venv",
]


def should_skip(path: Path) -> bool:
    """Check if path should be skipped"""
    for pattern in SKIP_PATTERNS:
        if pattern in str(path):
            return True
    return False


def replace_in_file(file_path: Path, replacements: List[Tuple[str, str]]) -> int:
    """Replace patterns in a file. Returns number of replacements made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacement_count = 0
        
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                replacement_count += content.count(new) - original_content.count(new)
                original_content = content
        
        if content != original_content or replacement_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return replacement_count
        
        return 0
    except (UnicodeDecodeError, PermissionError):
        return 0


def rename_files_and_dirs():
    """Rename files and directories"""
    print("🔄 Renaming files and directories...")
    
    for old_path, new_path in FILE_RENAMINGS:
        old_full = REPO_ROOT / old_path
        new_full = REPO_ROOT / new_path
        
        if old_full.exists():
            print(f"   {old_path} → {new_path}")
            if old_full.is_dir():
                os.rename(old_full, new_full)
            else:
                old_full.rename(new_full)
        else:
            print(f"   ⚠️  {old_path} not found (skipping)")


def update_file_contents():
    """Update all file contents"""
    print("\n🔄 Updating file contents...")
    
    # Find all relevant files
    extensions = ['.py', '.md', '.yaml', '.yml', '.json', '.sh', '.txt', '.example']
    files_updated = 0
    total_replacements = 0
    
    for ext in extensions:
        for file_path in REPO_ROOT.rglob(f'*{ext}'):
            if should_skip(file_path):
                continue
            
            replacements = replace_in_file(file_path, RENAMINGS)
            if replacements > 0:
                files_updated += 1
                total_replacements += replacements
                print(f"   ✓ {file_path.relative_to(REPO_ROOT)} ({replacements} changes)")
    
    return files_updated, total_replacements


def create_summary_report(files_updated: int, total_replacements: int):
    """Create summary report"""
    report = f"""
# DopeconBridge Renaming - Complete

## Summary

Successfully renamed all references from "DopeconBridge" to "DopeconBridge"

### Statistics
- **Files Updated:** {files_updated}
- **Total Replacements:** {total_replacements}
- **Directories Renamed:** {len([r for r in FILE_RENAMINGS if (REPO_ROOT / r[0]).is_dir() if (REPO_ROOT / r[0]).exists()])}
- **Files Renamed:** {len([r for r in FILE_RENAMINGS if not (REPO_ROOT / r[0]).is_dir() if (REPO_ROOT / r[0]).exists()])}

### What Changed

#### Code References
- `DopeconBridge` → `DopeconBridge`
- `dopecon_bridge` → `dopecon_bridge`
- `DopeconBridge` → `DopeconBridge`
- `DOPECON_BRIDGE` → `DOPECON_BRIDGE`

#### Directory Structure
- `services/shared/dopecon_bridge_client/` → `services/shared/dopecon_bridge_client/`
- `services/mcp-dopecon-bridge/` → `services/dopecon-bridge/`

#### Documentation Files
- `DOPECON_BRIDGE_*.md` → `DOPECONBRIDGE_*.md`
- `.env.dopecon_bridge.example` → `.env.dopecon_bridge.example`

#### Environment Variables
- `DOPECON_BRIDGE_URL` → `DOPECON_BRIDGE_URL`
- `DOPECON_BRIDGE_TOKEN` → `DOPECON_BRIDGE_TOKEN`
- `DOPECON_BRIDGE_SOURCE_PLANE` → `DOPECON_BRIDGE_SOURCE_PLANE`

### Updated Imports

Old:
```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient
```

New:
```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient
```

### Updated Environment

Old:
```bash
export DOPECON_BRIDGE_URL=http://localhost:3016
```

New:
```bash
export DOPECON_BRIDGE_URL=http://localhost:3016
```

## Verification

Run these commands to verify the changes:

```bash
# Check for any remaining "DopeconBridge" references
grep -r "DopeconBridge" services/ --include="*.py" || echo "✓ All code updated"

# Check for remaining environment variable references  
grep -r "DOPECON_BRIDGE" . --include="*.py" --include="*.md" || echo "✓ All env vars updated"

# Verify new client can be imported
python3 -c "from services.shared.dopecon_bridge_client import DopeconBridgeClient; print('✓ Client imports successfully')"

# Run tests
python3 -m pytest tests/shared/test_dopecon_bridge_client.py -v
```

## Next Steps

1. **Update Docker Compose** - Change service names and env vars
2. **Update CI/CD** - Change any hardcoded references
3. **Run Tests** - Verify all tests still pass
4. **Update README** - Main project README references

## Files Modified

Check git status to see all modified files:
```bash
git status
git diff --name-only
```

---

**Renaming completed successfully!**
All references to "DopeconBridge" have been updated to "DopeconBridge".
"""
    
    report_path = REPO_ROOT / "DOPECONBRIDGE_RENAMING_COMPLETE.md"
    with open(report_path, 'w') as f:
        f.write(report.strip())
    
    print(f"\n📄 Summary report created: {report_path}")


def main():
    """Main renaming function"""
    print("=" * 60)
    print("DopeconBridge Renaming Script")
    print("=" * 60)
    print()
    print("This script will rename all references from 'DopeconBridge'")
    print("to 'DopeconBridge' across code, docs, and configuration.")
    print()
    
    # Confirm
    response = input("Continue? [y/N]: ").strip().lower()
    if response != 'y':
        print("Aborted.")
        return
    
    # Rename files and directories
    rename_files_and_dirs()
    
    # Update file contents
    files_updated, total_replacements = update_file_contents()
    
    # Create summary
    create_summary_report(files_updated, total_replacements)
    
    print()
    print("=" * 60)
    print("✅ Renaming Complete!")
    print("=" * 60)
    print(f"   Files updated: {files_updated}")
    print(f"   Total replacements: {total_replacements}")
    print()
    print("Next steps:")
    print("1. Run tests: python3 -m pytest tests/shared/")
    print("2. Update Docker Compose files manually")
    print("3. Review git diff for changes")
    print()


if __name__ == "__main__":
    main()
