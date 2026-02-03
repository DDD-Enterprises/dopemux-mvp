---
id: WORKTREE_GUIDE
title: Worktree_Guide
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Git Worktree Multi-Instance Support - User Guide

**Feature**: Isolated task tracking across git worktrees for ADHD-optimized parallel workflows
**Status**: ✅ Production Ready (Migration 007)
**Version**: Simple MVP

## Why Use Worktree Multi-Instance?

### The Problem

Traditional single-worktree development has a critical ADHD challenge:

```
You're implementing Feature A (IN_PROGRESS)
→ Urgent hotfix needed
→ Switch branches, lose context
→ Your Feature A tasks are now "orphaned" in the wrong context
→ Cognitive overhead trying to remember what was in-progress where
```

### The Solution

Git worktrees let you work on multiple branches simultaneously:

```
Main worktree (/dopemux-mvp)          Feature worktree (/dopemux-feature-auth)
└─ main branch                        └─ feature/auth branch
   └─ Shared tasks visible               └─ Isolated IN_PROGRESS tasks
   └─ COMPLETED tasks from all              └─ See own work + shared tasks
```

**Zero context destruction** when switching between worktrees!

## Quick Start (5 Minutes)

### 1. Create a Git Worktree

```bash
# From your main repository
cd /path/to/dopemux-mvp

# Create a linked worktree for feature work
git worktree add ../dopemux-feature-auth -b feature/auth

# Verify it was created
git worktree list
```

Output:
```
/path/to/dopemux-mvp              abc123 [main]
/path/to/dopemux-feature-auth     abc123 [feature/auth]
```

### 2. Set Environment Variables

Each terminal/shell session needs to know which worktree instance it is:

**In your feature worktree terminal**:
```bash
cd /path/to/dopemux-feature-auth

# Required: Set instance ID (use worktree name or branch name)
export DOPEMUX_INSTANCE_ID="feature-auth"

# Required: Point to main workspace (absolute path)
export DOPEMUX_WORKSPACE_ID="/path/to/dopemux-mvp"
```

**In your main worktree terminal**:
```bash
cd /path/to/dopemux-mvp

# No environment variables needed - main worktree is default
# (or set to empty string to be explicit)
export DOPEMUX_INSTANCE_ID=""
export DOPEMUX_WORKSPACE_ID="/path/to/dopemux-mvp"
```

### 3. Start Working!

That's it! ConPort will now automatically:
- Isolate your IN_PROGRESS tasks to the current worktree
- Share COMPLETED/BLOCKED tasks across all worktrees
- Preserve context when you switch between terminals

## How It Works

### Task Isolation Rules

ConPort uses **status-based routing** to determine visibility:

| Status | Instance ID | Visibility |
|--------|-------------|------------|
| **IN_PROGRESS** | Set to current instance | **Isolated** - only visible in this worktree |
| **PLANNED** | Set to current instance | **Isolated** - only visible in this worktree |
| **COMPLETED** | NULL (cleared) | **Shared** - visible in all worktrees |
| **BLOCKED** | NULL (cleared) | **Shared** - visible in all worktrees |
| **CANCELLED** | NULL (cleared) | **Shared** - visible in all worktrees |

### Automatic Status Transitions

When you mark a task as COMPLETED, ConPort automatically:
1. Clears the `instance_id` (sets to NULL)
2. Makes it visible to all worktrees
3. Updates the `updated_at` timestamp

**Example Flow**:
```
Feature Worktree:
  log_progress("Implement JWT auth", status="IN_PROGRESS")
  → instance_id = "feature-auth" (isolated)

  [Work on implementation...]

  update_progress(task_id, status="COMPLETED")
  → instance_id = NULL (now shared across all worktrees)

Main Worktree:
  get_progress()
  → Now sees the completed JWT auth task! ✅
```

## Environment Variable Setup

### Option 1: Shell Profile (Recommended)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Dopemux Worktree Detection
function set_dopemux_instance() {
  local git_dir=$(git rev-parse --git-dir 2>/dev/null)

  if [[ -f "$git_dir/worktrees" ]] || [[ "$git_dir" =~ "\.git/worktrees" ]]; then
    # This is a worktree - extract name from path
    local worktree_name=$(basename "$PWD")
    export DOPEMUX_INSTANCE_ID="$worktree_name"
    export DOPEMUX_WORKSPACE_ID="$(git rev-parse --show-toplevel)"
    echo "🔧 Worktree instance: $worktree_name"
  else
    # Main worktree
    export DOPEMUX_INSTANCE_ID=""
    export DOPEMUX_WORKSPACE_ID="$(git rev-parse --show-toplevel)"
    echo "🏠 Main worktree"
  fi
}

# Auto-detect on directory change
chpwd() {
  if git rev-parse --git-dir >/dev/null 2>&1; then
    set_dopemux_instance
  fi
}
```

Now every time you `cd` into a worktree, the environment is set automatically!

### Option 2: Manual Export (Quick Start)

For testing or temporary use:

```bash
# Feature worktree
export DOPEMUX_INSTANCE_ID="feature-auth"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Verify
echo "Instance: $DOPEMUX_INSTANCE_ID"
echo "Workspace: $DOPEMUX_WORKSPACE_ID"
```

### Option 3: `.env` File (Per-Worktree)

Create `.env.local` in each worktree:

```bash
# In /path/to/dopemux-feature-auth/.env.local
DOPEMUX_INSTANCE_ID=feature-auth
DOPEMUX_WORKSPACE_ID=/path/to/dopemux-mvp
```

Then use `direnv` or manually source:
```bash
source .env.local
```

## Real-World Workflows

### Workflow 1: Feature Development in Parallel

**Scenario**: Working on authentication feature while main worktree handles urgent fixes

```bash
# Terminal 1: Main worktree
cd /path/to/dopemux-mvp
# No env vars needed

# Create shared project plan
conport log_progress \
  --description "Q4 2025 Feature Roadmap" \
  --status COMPLETED

# This is visible to all worktrees ✅

# Terminal 2: Feature worktree
cd /path/to/dopemux-feature-auth
export DOPEMUX_INSTANCE_ID="feature-auth"
export DOPEMUX_WORKSPACE_ID="/path/to/dopemux-mvp"

# Start feature work (isolated)
conport log_progress \
  --description "Implement JWT middleware" \
  --status IN_PROGRESS

# This is NOT visible in main worktree ✅
# When complete, mark as COMPLETED and it becomes shared ✅
```

### Workflow 2: Hotfix Without Context Loss

**Scenario**: Feature work interrupted by production hotfix

```bash
# Terminal 1: Feature worktree (keep running)
cd /path/to/dopemux-feature-auth
export DOPEMUX_INSTANCE_ID="feature-auth"

# Your IN_PROGRESS tasks stay here, untouched
conport get_progress
# Shows: [IN_PROGRESS] Implement JWT middleware

# Terminal 2: Open new terminal for hotfix
cd /path/to/dopemux-mvp
# Main worktree - no env vars

# Hotfix work (separate context)
conport log_progress \
  --description "Fix Redis connection timeout" \
  --status IN_PROGRESS

# Your feature work is still in Terminal 1, unchanged
# Zero context destruction! ✅
```

### Workflow 3: Multiple Features in Parallel

**Scenario**: Working on 3 features simultaneously (ADHD-optimized task switching)

```bash
# Create worktrees
git worktree add ../dopemux-auth -b feature/auth
git worktree add ../dopemux-payments -b feature/payments
git worktree add ../dopemux-analytics -b feature/analytics

# Terminal 1: Auth feature
cd ../dopemux-auth
export DOPEMUX_INSTANCE_ID="auth"
export DOPEMUX_WORKSPACE_ID="/path/to/dopemux-mvp"

# Terminal 2: Payments feature
cd ../dopemux-payments
export DOPEMUX_INSTANCE_ID="payments"
export DOPEMUX_WORKSPACE_ID="/path/to/dopemux-mvp"

# Terminal 3: Analytics feature
cd ../dopemux-analytics
export DOPEMUX_INSTANCE_ID="analytics"
export DOPEMUX_WORKSPACE_ID="/path/to/dopemux-mvp"

# Each terminal has isolated IN_PROGRESS tasks
# Switch between terminals without losing context ✅
```

## Active Context Per Instance

Each worktree gets its own `active_context` in ConPort:

```bash
# Feature worktree
export DOPEMUX_INSTANCE_ID="feature-auth"
conport update_active_context \
  --active_context "Working on JWT authentication"

# Main worktree (different context)
conport update_active_context \
  --active_context "Code review and deployment"

# Both contexts are independent and preserved ✅
```

## Querying Tasks

### Get All Visible Tasks (Current Instance)

```bash
# Returns:
# - All shared tasks (instance_id = NULL)
# - Your own IN_PROGRESS tasks (instance_id = current)
conport get_progress
```

### Example Output

**In main worktree**:
```json
[
  {
    "status": "COMPLETED",
    "instance_id": null,
    "description": "Deploy production hotfix"
  },
  {
    "status": "BLOCKED",
    "instance_id": null,
    "description": "Waiting for API keys"
  }
]
```

**In feature worktree** (`DOPEMUX_INSTANCE_ID="feature-auth"`):
```json
[
  {
    "status": "COMPLETED",
    "instance_id": null,
    "description": "Deploy production hotfix"
  },
  {
    "status": "BLOCKED",
    "instance_id": null,
    "description": "Waiting for API keys"
  },
  {
    "status": "IN_PROGRESS",
    "instance_id": "feature-auth",
    "description": "Implement JWT middleware"
  }
]
```

Notice: Feature worktree sees shared tasks + its own isolated task!

## Troubleshooting

### Problem: Tasks Not Isolating

**Symptom**: IN_PROGRESS tasks visible in all worktrees

**Solution**: Verify environment variables are set:
```bash
echo "Instance: $DOPEMUX_INSTANCE_ID"
echo "Workspace: $DOPEMUX_WORKSPACE_ID"
```

If empty, set them:
```bash
export DOPEMUX_INSTANCE_ID="your-worktree-name"
export DOPEMUX_WORKSPACE_ID="/absolute/path/to/main/repo"
```

### Problem: Tasks Not Sharing After COMPLETED

**Symptom**: COMPLETED tasks still isolated to worktree

**Solution**: Verify the ConPort server is running the updated code:
```bash
# Restart ConPort MCP server
docker restart dopemux-mcp-conport

# Verify migration 007 was applied
docker exec dopemux-postgres-primary psql -U dopemux -d conport -c "
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'progress_entries'
AND column_name = 'instance_id';
"
```

Should return `instance_id` column.

### Problem: Old Tasks Missing

**Symptom**: Tasks created before migration not visible

**Solution**: All pre-migration tasks have `instance_id=NULL` (shared). Run:
```bash
docker exec dopemux-postgres-primary psql -U dopemux -d conport -c "
SELECT status, instance_id, description
FROM progress_entries
ORDER BY created_at DESC
LIMIT 10;
"
```

Verify `instance_id` is NULL for old tasks.

### Problem: Wrong Workspace ID

**Symptom**: No tasks visible at all

**Solution**: Workspace ID must match exactly:
```bash
# Check what's in database
docker exec dopemux-postgres-primary psql -U dopemux -d conport -c "
SELECT DISTINCT workspace_id FROM progress_entries;
"

# Set to match
export DOPEMUX_WORKSPACE_ID="/exact/path/from/database"
```

## Advanced Usage

### Custom Instance Names

You can use any naming convention:

```bash
# By feature name
export DOPEMUX_INSTANCE_ID="auth-feature"

# By developer name
export DOPEMUX_INSTANCE_ID="alice-dev"

# By sprint/milestone
export DOPEMUX_INSTANCE_ID="sprint-23"

# By ticket number
export DOPEMUX_INSTANCE_ID="JIRA-1234"
```

### Temporary Instance Switching

Override instance for a single command:

```bash
# Run as different instance temporarily
DOPEMUX_INSTANCE_ID="other-instance" conport get_progress
```

### Shared Team Workspace

Multiple developers can share the same workspace:

```bash
# Developer 1
export DOPEMUX_INSTANCE_ID="alice-auth"
export DOPEMUX_WORKSPACE_ID="/shared/dopemux-mvp"

# Developer 2
export DOPEMUX_INSTANCE_ID="bob-payments"
export DOPEMUX_WORKSPACE_ID="/shared/dopemux-mvp"

# Both see shared COMPLETED tasks
# Each has isolated IN_PROGRESS tasks
```

## Migration from Single-Worktree

### Before Migration

```bash
# All tasks visible globally
conport get_progress
# → Shows all tasks regardless of status
```

### After Migration (Backward Compatible)

**Without environment variables** (default behavior):
```bash
# Works exactly the same as before
conport get_progress
# → Shows all tasks with instance_id=NULL (shared)
```

**With environment variables** (new multi-instance behavior):
```bash
export DOPEMUX_INSTANCE_ID="my-instance"
conport get_progress
# → Shows shared tasks + isolated tasks for "my-instance"
```

**No code changes required** - entirely opt-in via environment variables!

## Best Practices

### 1. Consistent Instance Naming

Use clear, descriptive instance IDs:
- ✅ `feature-auth`, `hotfix-redis`, `refactor-api`
- ❌ `wt1`, `temp`, `test`

### 2. Set Workspace ID to Main Repo

Always point to the main repository root:
```bash
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
# NOT: /Users/hue/code/dopemux-feature-auth
```

### 3. Mark Tasks Complete Promptly

Transition to COMPLETED when done so others can see your work:
```bash
conport update_progress --id "$TASK_ID" --status COMPLETED
```

### 4. Use BLOCKED for Cross-Worktree Issues

If blocked on something affecting all worktrees:
```bash
# Automatically shared (instance_id = NULL)
conport log_progress \
  --description "Blocked: Waiting for staging environment" \
  --status BLOCKED
```

### 5. Clean Up Old Worktrees

Remove worktrees you're done with:
```bash
git worktree remove /path/to/old-worktree
```

Tasks remain in database (instance_id preserved for history).

## Limitations (Simple MVP)

1. **Manual Environment Variables**: No automatic git detection (planned for future)
2. **5 Core Tools Only**: Only these ConPort tools support multi-instance:
   - `log_progress`
   - `get_progress`
   - `update_progress`
   - `get_active_context`
   - `update_active_context`
3. **No UI Visualization**: Terminal-only for now
4. **No Historical Migration**: Old decisions/patterns stay shared (instance_id=NULL)

## Next Steps

1. ✅ Set up your first worktree
2. ✅ Configure environment variables
3. ✅ Create isolated IN_PROGRESS task
4. ✅ Mark complete and watch it become shared
5. 🎉 Enjoy context-preserving parallel workflows!

## Support

- **Documentation**: `/docker/mcp-servers/conport/migrations/README.md`
- **Validation Results**: `/docker/mcp-servers/conport/migrations/VALIDATION_RESULTS.md`
- **Tests**: Run `pytest tests/test_worktree_routing.py -v`

---

**Happy parallel development!** 🚀
