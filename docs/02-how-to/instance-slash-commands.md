---
id: instance-slash-commands
title: Instance Switching Slash Commands
type: how-to
owner: dopemux-core
date: 2025-10-04
adhd_cognitive_load: 0.3
adhd_attention_required: low
adhd_interruption_safe: true
tags:
- slash-commands
- multi-instance
- adhd-optimization
- quick-reference
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Instance Switching Slash Commands

Zero-friction instance switching from within Claude Code sessions.

## Overview

Instead of opening new terminals for multi-instance workflows, use slash commands to switch instances seamlessly from within your Claude Code session.

**ADHD Benefits**:
- ✅ No terminal switching (cognitive load reduction)
- ✅ Same Claude session (zero context loss)
- ✅ Instant environment updates (no manual env var export)
- ✅ Auto-pruning of dead instances (workspace hygiene)

## Available Commands

### `/instance` - Show Current Instance

Display information about the currently active instance.

**Usage**:
```
/instance
```

**Output**:
```
🏗️  **Current Instance**

**Instance ID**: B
**Port Base**: 3030
**Git Branch**: feature/auth
**Working Directory**: /Users/hue/code/dopemux-mvp/worktrees/B
**Worktree**: Yes
**Workspace Root**: /Users/hue/code/dopemux-mvp

**Service Ports**:
- ConPort: 3037
- Serena: 3036
- Task-Master: 3035
```

---

### `/instance new <branch>` - Create New Instance

Create a new instance with an isolated worktree and switch to it.

**Usage**:
```
/instance new feature/authentication
/instance new hotfix/redis-connection
/instance new experiment/new-ui
```

**What Happens**:
1. Detects running instances
2. Allocates next available instance ID (B, C, D, E)
3. Creates git worktree with your branch
4. Updates environment variables in current process
5. Changes working directory to worktree
6. Ready for instance-specific work!

**Example**:
```
/instance new feature/auth

✅ **New Instance Created**

**Instance ID**: B
**Port Base**: 3030
**Branch**: feature/auth
**Worktree Path**: /Users/hue/code/dopemux-mvp/worktrees/B

Environment variables updated. Current directory changed to worktree.

**Next steps**:
1. Services will use instance-specific ports
2. ConPort data isolated (IN_PROGRESS tasks private)
3. Run `/instance list` to see all instances
```

---

### `/instance switch <id>` - Switch to Existing Instance

Switch to an already-created instance (including main worktree A).

**Usage**:
```
/instance switch A     # Switch to main worktree
/instance switch B     # Switch to instance B
/instance switch C     # Switch to instance C
```

**What Happens**:
1. Verifies worktree exists
2. Updates environment variables
3. Changes working directory
4. Updates current instance context

**Example**:
```
/instance switch A

🔄 **Switched to Instance A**

**Port Base**: 3000
**Git Branch**: main
**Working Directory**: /Users/hue/code/dopemux-mvp

Environment variables updated. Current directory changed.

**Service Ports**:
- ConPort: 3007
- Serena: 3006
- Task-Master: 3005
```

**Error Handling**:
```
/instance switch D

Error: Worktree for instance D does not exist.
Use `/instance new` to create it.
```

---

### `/instance list` - List All Instances

Show all running instances and available worktrees.

**Usage**:
```
/instance list
```

**Output**:
```
**Running Instances:**
- **A** (port 3000) - main - ✅ Healthy
- **B** (port 3030) - feature/auth - ✅ Healthy

**Available Worktrees:**
   **A**: main (/Users/hue/code/dopemux-mvp)
👉 **B**: feature/auth (/Users/hue/code/dopemux-mvp/worktrees/B)
   **C**: hotfix/redis (/Users/hue/code/dopemux-mvp/worktrees/C)

**Commands:**
- `/instance new <branch>` - Create new instance
- `/instance switch <id>` - Switch to instance
- `/instance prune` - Cleanup dead instances
```

**Legend**:
- 👉 = Currently active instance
- ✅ Healthy = Instance services running
- ⚠️ Unknown = Instance status unclear

---

### `/instance prune` - Auto-Cleanup Dead Instances

Automatically remove worktrees for instances that are no longer running.

**Usage**:
```
/instance prune
```

**What Happens**:
1. Detects all worktrees
2. Checks which instances are running
3. Identifies stopped instances (worktree exists but not running)
4. Removes dead worktrees (except main worktree A)
5. Reports results

**Example (instances to clean)**:
```
/instance prune

🧹 **Instance Prune Results**

**Removed 2 dead instance(s):**
- ✅ Instance C: /Users/hue/code/dopemux-mvp/worktrees/C
- ✅ Instance D: /Users/hue/code/dopemux-mvp/worktrees/D
```

**Example (nothing to clean)**:
```
/instance prune

✅ **No dead instances to prune**

All worktrees are either running or main worktree (A).
```

**ADHD Benefit**: Regular pruning prevents workspace clutter and disk bloat.

---

## Common Workflows

### Feature Development

```bash
# Start in main (instance A)
/instance

# Create feature instance
/instance new feature/authentication

# Work on authentication...
# All IN_PROGRESS tasks isolated to instance B

# Switch back to main to check something
/instance switch A

# Resume feature work
/instance switch B

# When done, cleanup
/instance prune
```

### Hotfix While Working on Feature

```bash
# Currently in instance B (feature work)
/instance list

# Production bug! Create hotfix instance
/instance new hotfix/redis-connection

# Now in instance C (isolated hotfix)
# Fix the bug, commit, push

# Switch back to feature work
/instance switch B

# All context preserved ✅
```

### Context Switching

```bash
# Working on feature A (instance B)
# Need to switch to feature B (instance C)

/instance switch C

# Work on feature B...

# Back to feature A
/instance switch B

# Zero cognitive overhead ✅
# No environment variable export ✅
# No terminal switching ✅
```

### Workspace Hygiene

```bash
# Weekly cleanup
/instance list
# See which instances are dead

/instance prune
# Remove all stopped instances

# Fresh workspace ✅
```

---

## Technical Details

### Environment Variables Updated

When switching instances, these environment variables are automatically updated in the current Claude Code process:

```bash
DOPEMUX_INSTANCE_ID       # A, B, C, D, E (or empty for main)
DOPEMUX_WORKSPACE_ID      # /Users/hue/code/dopemux-mvp
DOPEMUX_PORT_BASE         # 3000, 3030, 3060, 3090, 3120
TASK_MASTER_PORT          # port_base + 5
SERENA_PORT               # port_base + 6
CONPORT_PORT              # port_base + 7
INTEGRATION_BRIDGE_PORT   # port_base + 16
LEANTIME_URL              # http://localhost:3001 (always shared)
```

### Working Directory Changes

```python
# Before switch (instance A)
os.getcwd()
# /Users/hue/code/dopemux-mvp

# After /instance new feature/auth (instance B)
os.getcwd()
# /Users/hue/code/dopemux-mvp/worktrees/B

# After /instance switch A
os.getcwd()
# /Users/hue/code/dopemux-mvp
```

### ConPort Data Routing

ConPort automatically uses `DOPEMUX_INSTANCE_ID` to route data:

- **Instance A** (`DOPEMUX_INSTANCE_ID=""`)
  - IN_PROGRESS tasks: visible only in A
  - COMPLETED tasks: visible everywhere

- **Instance B** (`DOPEMUX_INSTANCE_ID="B"`)
  - IN_PROGRESS tasks: visible only in B
  - COMPLETED tasks: visible everywhere

**Shared across all instances**:
- Decisions (always shared)
- System patterns (always shared)
- COMPLETED/BLOCKED/CANCELLED tasks

---

## Comparison: Terminal vs Slash Commands

### Traditional Multi-Terminal Approach

```bash
# Terminal 1
cd /Users/hue/code/dopemux-mvp
dopemux start
# Working in instance A...

# Terminal 2 (new terminal required ❌)
cd /Users/hue/code/dopemux-mvp
dopemux start
# Accept creating instance B
# Working in instance B...

# Switch back to instance A
# Must switch terminal windows ❌
# Context loss from window switching ❌
```

**ADHD Cognitive Load**: HIGH ❌
- Terminal switching overhead
- Window management distraction
- Context loss between switches

### Slash Command Approach

```bash
# Same terminal, same Claude session ✅
/instance new feature/auth
# Now in instance B

# Work on feature...

/instance switch A
# Back to main worktree

# Resume feature
/instance switch B

# Zero terminal switching ✅
# Zero context loss ✅
```

**ADHD Cognitive Load**: MINIMAL ✅
- Single terminal window
- Same Claude session
- Seamless instance switching

---

## Troubleshooting

### "Worktree for instance X does not exist"

**Problem**: Trying to switch to non-existent instance.

**Solution**:
```
/instance list          # Check available worktrees
/instance new feature/X # Create the instance first
```

### "Maximum instances (5) already running"

**Problem**: All instance slots (A-E) occupied.

**Solution**:
```
/instance list          # See all running instances
/instance prune         # Cleanup dead instances
# Or stop one manually (Ctrl+C in that terminal)
```

### Environment Variables Not Updating

**Problem**: After switching, ConPort shows wrong instance.

**Solution**:
```
/instance               # Verify current instance
# Environment variables update in current process only
# If in new terminal, restart with dopemux start
```

### Git Errors When Creating Instance

**Problem**: Branch already exists or worktree path in use.

**Solution**:
```
# Check existing branches
git branch -a

# Use different branch name
/instance new feature/auth-v2

# Or cleanup dead worktrees
/instance prune
```

---

## Best Practices

### ADHD-Optimized Usage

1. **Use `/instance list` frequently**
   - Visual reminder of available contexts
   - Shows current instance (👉 marker)
   - Low cognitive overhead

2. **Regular pruning**
   - Run `/instance prune` weekly
   - Prevents workspace clutter
   - Maintains focus on active work

3. **Descriptive branch names**
   - `/instance new feature/jwt-auth` ✅
   - `/instance new test` ❌

4. **One feature per instance**
   - Keep context boundaries clear
   - Easier mental model
   - Simpler switching decisions

### Instance Naming Conventions

```bash
# Features
/instance new feature/authentication
/instance new feature/dashboard-redesign

# Hotfixes
/instance new hotfix/redis-connection
/instance new hotfix/memory-leak

# Experiments
/instance new experiment/new-architecture
/instance new experiment/performance-test

# Refactoring
/instance new refactor/database-layer
/instance new refactor/api-cleanup
```

---

## Summary

**Slash Commands**:
- `/instance` - Show current
- `/instance new <branch>` - Create and switch
- `/instance switch <id>` - Switch to existing
- `/instance list` - List all
- `/instance prune` - Auto-cleanup

**Benefits**:
- ✅ Zero terminal switching
- ✅ Zero context loss
- ✅ Automatic environment updates
- ✅ Workspace hygiene
- ✅ ADHD-optimized UX

**vs Traditional**:
- **Cognitive Load**: Minimal vs High
- **Context Loss**: None vs Frequent
- **Speed**: Instant vs Slow
- **Convenience**: High vs Low

---

**Implementation**: Claude Code + Dopemux Multi-Instance
**Status**: ✅ Production Ready
**Related**: [Multi-Instance Workflow Guide](multi-instance-workflow.md)
