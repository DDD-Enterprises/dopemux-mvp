#!/usr/bin/env python3
"""
Clipboard-to-Patch Script
- Automatically determines the correct patch file based on cursor state
- Reads patch content from clipboard
- Validates and formats the patch
- Outputs to both file and stdout
- Ensures git diff compliance
- Provides detailed logging
"""

import sys
import json
import pyperclip
from pathlib import Path
import re
import subprocess
from datetime import datetime


def log_message(message, level="INFO"):
    """Log messages with timestamps and levels"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)


def load_state(state_path):
    """Load the current state to determine the cursor position."""
    log_message(f"Loading state from {state_path}")
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
        log_message(f"State loaded successfully. Current cursor: {state.get('cursor', 0)}")
        return state
    except FileNotFoundError:
        log_message(f"Error: State file not found at {state_path}", "ERROR")
        sys.exit(1)
    except json.JSONDecodeError:
        log_message(f"Error: Invalid JSON in state file at {state_path}", "ERROR")
        sys.exit(1)


def validate_and_format_patch(patch_content):
    """
    Validate and format the patch to ensure git diff compliance.
    - Ensures proper diff headers
    - Fixes line prefixes (+, -, or space)
    - Validates unified diff format
    """
    log_message("Processing and validating patch content")
    
    lines = patch_content.splitlines()
    total_lines = len(lines)
    log_message(f"Input patch has {total_lines} lines")
    
    # Check for diff headers
    has_diff_header = any(line.startswith('diff --git') for line in lines)
    if not has_diff_header:
        log_message("Warning: Patch doesn't appear to be a git diff (missing 'diff --git')", "WARNING")
    
    # Count different line types
    additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
    context = sum(1 for line in lines if line.startswith(' '))
    
    log_message(f"Patch statistics: +{additions} additions, -{deletions} deletions, {context} context lines")
    
    # Ensure proper line prefixes in diff hunks
    formatted_lines = []
    in_hunk = False
    fixed_lines = 0
    
    for i, line in enumerate(lines, 1):
        if line.startswith('@@'):
            in_hunk = True
            formatted_lines.append(line)
        elif in_hunk:
            if line.startswith(('+', '-', ' ')):
                formatted_lines.append(line)
            elif line == '':
                formatted_lines.append(line)
            else:
                # Fix lines that don't have proper prefixes
                log_message(f"Warning: Fixed line {i} without proper prefix: {line[:50]}", "WARNING")
                formatted_lines.append(' ' + line)
                fixed_lines += 1
        else:
            formatted_lines.append(line)
    
    if fixed_lines > 0:
        log_message(f"Fixed {fixed_lines} lines without proper prefixes")
    
    formatted_patch = '\n'.join(formatted_lines)
    log_message(f"Formatted patch has {len(formatted_lines)} lines")
    
    return formatted_patch


def main():
    log_message("=== Starting PATCHIT ===")
    
    # Define paths
    repo_root = Path(".").resolve()
    state_path = repo_root / "tools/prompt_rewrite_v4/state.json"
    out_dir = repo_root / "out"
    
    log_message(f"Repository root: {repo_root}")
    log_message(f"State file: {state_path}")
    log_message(f"Output directory: {out_dir}")
    
    # Ensure the output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)
    log_message(f"Output directory ensured: {out_dir}")
    
    # Load the current state to get the cursor
    state = load_state(state_path)
    cursor = state.get("cursor", 0)
    
    # Read from clipboard
    log_message("Reading patch content from clipboard...")
    try:
        patch_content = pyperclip.paste()
        if not patch_content.strip():
            log_message("Error: Clipboard is empty", "ERROR")
            sys.exit(1)
        
        # Show first few lines for verification
        preview_lines = patch_content.splitlines()[:3]
        log_message(f"Clipboard content preview:\n{chr(10).join(preview_lines)}")
        log_message(f"Total characters in clipboard: {len(patch_content)}")
        
    except pyperclip.PyperclipException as e:
        log_message(f"Error reading from clipboard: {e}", "ERROR")
        sys.exit(1)
    
    # Ensure patch ends with newline (fixes "corrupt patch" errors)
    if not patch_content.endswith('\n'):
        log_message("🔧 Adding missing newline at end of patch", "INFO")
        patch_content = patch_content + '\n'
    
    # Check if patch has proper git diff headers, add if missing
    if not patch_content.startswith('diff --git'):
        log_message("🔧 Adding missing git diff headers", "INFO")
        
        # Try to extract the file path from the patch (handle leading spaces)
        file_path = None
        for line in patch_content.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith('--- a/'):
                file_path = stripped_line.split(' ', 1)[1]
                break
            elif stripped_line.startswith('+++ b/'):
                file_path = stripped_line.split(' ', 1)[1]
                break
            elif stripped_line.startswith('--- '):
                file_path = stripped_line[4:].strip()
                break
            elif stripped_line.startswith('+++ '):
                file_path = stripped_line[4:].strip()
                break
        
        if file_path:
            # Remove a/ or b/ prefix if present
            if file_path.startswith('a/'):
                clean_path = file_path[2:]
            elif file_path.startswith('b/'):
                clean_path = file_path[2:]
            else:
                clean_path = file_path
                
            log_message(f"🎯 Detected file: {clean_path}", "INFO")
            # Add proper git diff headers
            git_header = f"diff --git a/{clean_path} b/{clean_path}\n"
            old_header = f"--- a/{clean_path}\n"
            new_header = f"+++ b/{clean_path}\n"
            
            # Remove any existing headers completely
            lines = patch_content.splitlines()
            clean_lines = []
            for line in lines:
                if line.startswith('@@'):
                    # Keep hunk headers
                    clean_lines.append(line)
                elif line.strip().startswith(('--- a/', '+++ b/', '--- ', '+++ ')):
                    # Skip all header lines (old and new style), including those with leading spaces
                    continue
                else:
                    # Keep everything else
                    clean_lines.append(line)
            
            # Rebuild with proper headers
            formatted_patch = git_header + old_header + new_header
            for line in clean_lines:
                formatted_patch += line + '\n'
        else:
            log_message("⚠️  Could not determine file path from patch", "WARNING")
            formatted_patch = patch_content
    else:
        # Validate and format the patch normally
        log_message("Validating and formatting patch...")
        formatted_patch = validate_and_format_patch(patch_content)
    
    # Ensure formatted patch also ends with newline
    if not formatted_patch.endswith('\n'):
        log_message("🔧 Adding missing newline to formatted patch", "INFO")
        formatted_patch = formatted_patch + '\n'
    
    # Robust patch format fixing
    log_message("Applying robust patch format fixes...")
    
    # Fix 1: Ensure proper line endings
    formatted_patch = formatted_patch.replace('\r\n', '\n').replace('\r', '\n')
    
    # Fix 2: Handle multiple hunks - ensure proper structure
    lines = formatted_patch.splitlines()
    fixed_lines = []
    in_hunk = False
    hunk_count = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('@@'):
            hunk_count += 1
            in_hunk = True
            fixed_lines.append(line)
        elif in_hunk:
            if line.startswith(('+', '-', ' ', '\\')):
                fixed_lines.append(line)
            elif line == '':
                # Empty line in hunk - keep as context
                fixed_lines.append(line)
            else:
                # Line without proper prefix - convert to context
                log_message(f"🔧 Fixing line {i+1} without proper prefix in hunk", "INFO")
                fixed_lines.append(' ' + line)
        else:
            fixed_lines.append(line)
    
    formatted_patch = '\n'.join(fixed_lines)
    
    # Fix 3: Ensure final newline
    if not formatted_patch.endswith('\n'):
        formatted_patch += '\n'
    
    log_message(f"✅ Applied robust patch format fixes (found {hunk_count} hunks)")
    
    # Define the output file path
    output_file = out_dir / f"response_{cursor}.patch"
    log_message(f"Output file will be: {output_file}")
    
    # Write the patch content to the file
    log_message(f"Writing patch to file...")
    with open(output_file, 'w') as f:
        f.write(formatted_patch)
    log_message(f"✅ Patch written to {output_file}")
    
    # Also output to stdout
    log_message("Outputting patch to stdout...")
    print(formatted_patch)
    
    # Verify it's a valid git diff
    log_message("Validating patch with git...")
    try:
        result = subprocess.run(
            ['git', 'apply', '--check', str(output_file)],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log_message("✅ Patch is valid and ready to apply")
        else:
            error_output = result.stderr.strip()
            log_message(f"⚠️  Patch validation warning: {error_output}", "WARNING")
            
            # Provide helpful guidance for common issues
            if "corrupt patch" in error_output:
                log_message("💡 Tip: The patch appears corrupted. This might be due to:", "INFO")
                log_message("   - Missing newline at end of file", "INFO")
                log_message("   - Improper diff format", "INFO")
                log_message("   - Try regenerating the patch with 'git diff'", "INFO")
            elif "does not exist" in error_output:
                log_message("💡 Tip: The file referenced in the patch doesn't exist", "INFO")
                log_message("   - Make sure the file path is correct", "INFO")
                log_message("   - The file might need to be created first", "INFO")
            elif "whitespace" in error_output:
                log_message("💡 Tip: Whitespace issues detected", "INFO")
                log_message("   - Try using 'git apply --whitespace=nowarn' if this is intentional", "INFO")
            
            log_message("⚠️  The patch may still work with 'git apply --reject'", "WARNING")
            
    except FileNotFoundError:
        log_message("⚠️  Git not found - unable to validate patch", "WARNING")
        log_message("💡 Tip: Install git or add it to your PATH", "INFO")
    
    log_message("=== PATCHIT Complete ===")
    log_message(f"📄 Patch saved to: {output_file}")
    log_message(f"📋 File size: {output_file.stat().st_size} bytes")
    log_message(f"🔧 Next step: Run `python tools/prompt_rewrite_v4/run_batch.py --apply` to apply the patch.")


if __name__ == "__main__":
    main()