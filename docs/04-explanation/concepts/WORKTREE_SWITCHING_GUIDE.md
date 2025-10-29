---
id: WORKTREE_SWITCHING_GUIDE
title: Worktree_Switching_Guide
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Worktree Switching - Installation & Usage Guide

## The Problem

The original `dopemux worktrees switch` command cannot work due to a fundamental POSIX limitation:

**Python subprocesses cannot change the parent shell's working directory.**

This affects ALL programming languages, not just Python. When you run:
```bash
python -m dopemux worktrees switch ui-build
```

The Python process changes ITS OWN directory, but your shell stays in the original location.

## The Solution: Shell Integration

We provide shell functions that execute `cd` in your shell's context, enabling proper directory switching.

---

## Quick Start (Choose Your Shell)

### Bash

```bash
# Install (one-time setup)
python -m dopemux shell-setup bash >> ~/.bashrc
source ~/.bashrc

# Use
dwt ui-build           # Switch to ui-build worktree
dwt code               # Fuzzy match: switches to code-cleanup
dwtls                  # List all worktrees
dwtcur                 # Show current worktree
```

### Zsh

```bash
# Install (one-time setup)
python -m dopemux shell-setup zsh >> ~/.zshrc
source ~/.zshrc

# Use
dwt ui-build           # Switch to ui-build worktree
dwt code               # Fuzzy match: switches to code-cleanup
dwtls                  # List all worktrees
dwtcur                 # Show current worktree
```

---

## How It Works

### Architecture

```
OLD (Broken):
┌─────────────┐         ┌──────────────┐
│ Your Shell  │  run >  │ Python CLI   │
│ pwd: /main  │ ─────>  │ os.chdir()   │
│             │  <───   │ cwd: /wt     │
│ pwd: /main  │         │ [exits]      │
└─────────────┘         └──────────────┘
     Still in /main!

NEW (Working):
┌─────────────┐         ┌──────────────┐
│ Shell Fn    │  call > │ Python CLI   │
│ get path    │ ─────>  │ return path  │
│ cd $path    │  <───   │ /wt/path     │
│ pwd: /wt    │         └──────────────┘
└─────────────┘
     Successfully switched!
```

### What Gets Installed

When you run `dopemux shell-setup bash >> ~/.bashrc`, you get:

1. **dopemux_switch()** - Main function for switching
2. **dwt** - Convenient alias (dwt = dopemux worktree)
3. **dwtls** - Quick worktree listing
4. **dwtcur** - Show current worktree
5. **Tab completion** - Auto-complete branch names

---

## Features

### Fuzzy Matching (ADHD-Friendly)

No need to remember exact branch names:

```bash
dwt ui           # Matches: ui-build
dwt feat         # Matches: feature/test-worktree-isolation
dwt code         # Matches: code-cleanup
```

If multiple matches found, you'll see a list:

```bash
$ dwt test
❌ Multiple matches found for 'test':
  • test-feature-1
  • test-feature-2
  • feature/test-worktree-isolation

💡 Tip: Please specify the exact branch name
```

### Visual Feedback

```bash
$ dwt ui-build
✅ Switched to worktree: /Users/hue/code/ui-build
   Branch: ui-build
```

### Error Handling

```bash
$ dwt nonexistent
❌ Worktree not found: nonexistent

                        Git Worktrees
┌────────────────┬─────────────────┬────────┬─────────┐
│ Branch         │ Path            │ Status │ Current │
├────────────────┼─────────────────┼────────┼─────────┤
│ main           │ dopemux-mvp     │ clean  │    →    │
│ ui-build       │ ui-build        │ dirty  │         │
│ code-cleanup   │ code-cleanup    │ clean  │         │
└────────────────┴─────────────────┴────────┴─────────┘
```

---

## Manual Installation (Alternative)

If you prefer to install manually:

### Step 1: Source the Integration

```bash
# Add this to your ~/.bashrc or ~/.zshrc
source /Users/hue/code/dopemux-mvp/scripts/shell_integration.sh
```

### Step 2: Reload Shell

```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

## Usage Examples

### Basic Switching

```bash
# List available worktrees
dwtls

# Switch to a worktree
dwt ui-build

# Verify you switched
pwd                          # /Users/hue/code/ui-build
git branch --show-current   # ui-build
```

### ADHD-Optimized Workflow

```bash
# Morning: Work on UI
dwt ui
# ... code for 25 minutes ...

# Afternoon: Switch to backend
dwt api
# ... code for 25 minutes ...

# Evening: Documentation
dwt docs
# ... write docs ...

# Each switch preserves context
# Each worktree maintains independent state
```

### With Multi-Instance

```bash
# Terminal 1: Main worktree
cd /Users/hue/code/dopemux-mvp
python -m dopemux start  # Instance A on port 3000

# Terminal 2: Feature worktree
dwt ui-build
python -m dopemux start  # Instance B on port 3030
                         # Auto-detects different workspace!

# Both instances run independently
# ConPort isolates IN_PROGRESS tasks
# Completed tasks shared across instances
```

---

## Troubleshooting

### Shell integration not working

**Check if sourced**:
```bash
type dopemux_switch
# Should show: "dopemux_switch is a function"
```

**If not found**:
```bash
# Re-source your shell config
source ~/.bashrc  # or ~/.zshrc
```

### Switch-path works but shell function doesn't

**Verify Python command works**:
```bash
python -m dopemux worktrees switch-path ui-build
# Should output: /Users/hue/code/ui-build
```

**Test shell function manually**:
```bash
dopemux_switch ui-build
# Should actually change directory
```

### Fuzzy match finds wrong worktree

Use exact branch name:
```bash
dwt feature/my-exact-branch-name
```

---

## Comparison: Old vs New

### OLD (Broken) Command
```bash
$ python -m dopemux worktrees switch ui-build
📍 Now in: /Users/hue/code/ui-build  # Misleading!

$ pwd
/Users/hue/code/dopemux-mvp          # Didn't actually switch!
```

### NEW (Working) Shell Integration
```bash
$ dwt ui-build
✅ Switched to worktree: /Users/hue/code/ui-build

$ pwd
/Users/hue/code/ui-build            # Actually switched!
```

---

## Advanced Usage

### Custom Aliases

Add to your shell config:

```bash
# Quick switch to common worktrees
alias ui='dwt ui-build'
alias api='dwt api-server'
alias docs='dwt documentation'

# Switch and show status
alias dwtstat='dwt $1 && git status --short'
```

### Integration with Tools

```bash
# Switch and start dopemux
dwt ui-build && python -m dopemux start

# Switch and run tests
dwt feature && pytest

# Switch and open editor
dwt docs && code .
```

---

## Implementation Details

### Files Modified

1. **src/dopemux/worktree_manager_enhanced.py**
   - Added: `get_worktree_path_for_switch()` method
   - Provides path lookup without directory change

2. **src/dopemux/worktree_commands.py**
   - Added: `get_worktree_path()` wrapper function

3. **src/dopemux/cli.py**
   - Added: `worktrees switch-path` command (machine-readable output)
   - Added: `shell-setup` command (installation helper)
   - Updated: `worktrees switch` with deprecation warning

4. **scripts/shell_integration.sh** (NEW)
   - Shell functions for bash/zsh
   - Tab completion support
   - ADHD-friendly aliases

### Why This Solution

**Technical Reasons**:
- Works with POSIX constraints, not against them
- Shell executes cd in its own context
- Clean separation of concerns (Python=logic, Shell=execution)

**ADHD Benefits**:
- Simple 3-letter command (`dwt`)
- Fuzzy matching reduces cognitive load
- Visual feedback confirms switch
- Tab completion reduces typing

**Maintainability**:
- No hacky workarounds
- Clear responsibilities
- Easy to test and validate

---

## Next Steps

1. **Install**: `dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc`
2. **Test**: `dwt ui-build && pwd`
3. **Use**: Enjoy proper worktree switching!

For questions or issues, see the main Dopemux documentation or run:
```bash
python -m dopemux worktrees --help
python -m dopemux shell-setup --help
```
