---
id: WORKTREE_EXAMPLES
title: Worktree_Examples
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Worktree_Examples (explanation) for dopemux documentation and developer workflows.
---
# Worktree Multi-Instance Examples

Real-world examples demonstrating ADHD-optimized parallel workflows with git worktrees.

## Example 1: Simple Feature Branch

**Scenario**: Implement authentication feature without disrupting main branch work

### Setup

```bash
# Create worktree for feature
cd /Users/hue/code/dopemux-mvp
git worktree add ../dopemux-auth -b feature/jwt-auth

# Open two terminals

# Terminal 1: Main worktree
cd /Users/hue/code/dopemux-mvp
# No env vars needed (default behavior)

# Terminal 2: Feature worktree
cd /Users/hue/code/dopemux-auth
export DOPEMUX_INSTANCE_ID="auth"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
```

### Workflow

**Terminal 2 (Feature)**: Start implementation
```bash
# Create isolated task
conport log_progress \
  --workspace_id "/Users/hue/code/dopemux-mvp" \
  --description "Implement JWT middleware for Express" \
  --status IN_PROGRESS

# Work on feature...
# This task is NOT visible in Terminal 1 (main)
```

**Terminal 1 (Main)**: Check what's happening
```bash
conport get_progress --workspace_id "/Users/hue/code/dopemux-mvp"
# Output: No IN_PROGRESS tasks visible (feature work is isolated)
```

**Terminal 2 (Feature)**: Complete implementation
```bash
# Mark complete
conport update_progress \
  --progress_id "$TASK_ID" \
  --status COMPLETED

# Now this task becomes shared!
```

**Terminal 1 (Main)**: Verify completion
```bash
conport get_progress --workspace_id "/Users/hue/code/dopemux-mvp"
# Output: [COMPLETED] Implement JWT middleware for Express ✅
```

---

## Example 2: Emergency Hotfix During Feature Work

**Scenario**: Production issue while working on feature - need to context switch without losing state

### Initial State

```bash
# Feature worktree - working on payments
cd /Users/hue/code/dopemux-payments
export DOPEMUX_INSTANCE_ID="payments"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# IN_PROGRESS task
conport log_progress \
  --description "Integrate Stripe payment webhook handlers" \
  --status IN_PROGRESS

# Current state saved in database with instance_id="payments"
```

### Emergency Hotfix

```bash
# Open NEW terminal for hotfix (don't close feature terminal!)
cd /Users/hue/code/dopemux-mvp  # Main worktree
# No DOPEMUX_INSTANCE_ID = main worktree

# Create hotfix worktree
git worktree add ../dopemux-hotfix-redis -b hotfix/redis-timeout

cd /Users/hue/code/dopemux-hotfix-redis
export DOPEMUX_INSTANCE_ID="hotfix-redis"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Work on hotfix
conport log_progress \
  --description "Fix Redis connection pool timeout" \
  --status IN_PROGRESS

# Complete hotfix
git add . && git commit -m "fix: Redis connection pool timeout"
conport update_progress --progress_id "$HOTFIX_TASK" --status COMPLETED

# Merge and deploy
git checkout main
git merge hotfix/redis-timeout
git push
```

### Return to Feature Work

```bash
# Switch back to original terminal (payments feature)
# Your IN_PROGRESS payment task is still there, untouched!

conport get_progress
# Output:
# [IN_PROGRESS] Integrate Stripe payment webhook handlers (your task)
# [COMPLETED] Fix Redis connection pool timeout (hotfix - now shared)

# Continue feature work without mental context reconstruction ✅
```

---

## Example 3: Multiple Parallel Features (ADHD Hyperfocus Workflow)

**Scenario**: Rotate between 3 features based on energy/interest (ADHD-optimized)

### Setup Three Worktrees

```bash
cd /Users/hue/code/dopemux-mvp

# Create worktrees
git worktree add ../dopemux-ui -b feature/dashboard-ui
git worktree add ../dopemux-api -b feature/graphql-api
git worktree add ../dopemux-docs -b feature/api-docs

# Verify
git worktree list
# /Users/hue/code/dopemux-mvp       [main]
# /Users/hue/code/dopemux-ui        [feature/dashboard-ui]
# /Users/hue/code/dopemux-api       [feature/graphql-api]
# /Users/hue/code/dopemux-docs      [feature/api-docs]
```

### Terminal Setup (One Per Feature)

**Terminal 1: UI Feature**
```bash
cd /Users/hue/code/dopemux-ui
export DOPEMUX_INSTANCE_ID="ui"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

conport log_progress \
  --description "Build dashboard component library" \
  --status IN_PROGRESS
```

**Terminal 2: API Feature**
```bash
cd /Users/hue/code/dopemux-api
export DOPEMUX_INSTANCE_ID="api"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

conport log_progress \
  --description "Implement GraphQL resolvers for user management" \
  --status IN_PROGRESS
```

**Terminal 3: Docs Feature**
```bash
cd /Users/hue/code/dopemux-docs
export DOPEMUX_INSTANCE_ID="docs"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

conport log_progress \
  --description "Write OpenAPI spec for REST endpoints" \
  --status IN_PROGRESS
```

### ADHD-Optimized Workflow

```bash
# Morning: High energy → Work on complex API (Terminal 2)
# Afternoon: Medium energy → Work on UI (Terminal 1)
# Evening: Low energy → Work on docs (Terminal 3)

# Each terminal maintains independent context
# Switch based on energy/focus without losing state ✅
```

### Completing Features

```bash
# Terminal 1: UI complete
conport update_progress --progress_id "$UI_TASK" --status COMPLETED
# Now visible in all terminals ✅

# Terminal 2: API blocked (waiting on code review)
conport update_progress --progress_id "$API_TASK" --status BLOCKED
# Automatically shared - everyone knows it's blocked ✅

# Terminal 3: Docs still in progress
# No update - stays isolated to this terminal
```

---

## Example 4: Shared Project Planning from Main Worktree

**Scenario**: Create high-level project tasks visible to all feature worktrees

### Main Worktree (Project Planning)

```bash
cd /Users/hue/code/dopemux-mvp
# No instance ID = main worktree

# Create shared project milestones (status = COMPLETED or PLANNED)
conport log_progress \
  --description "Q4 2025 Milestone: User Authentication System" \
  --status PLANNED

# This is shared (instance_id = NULL for PLANNED in main worktree)
```

### Feature Worktrees Can See Project Plan

```bash
# In any feature worktree
cd /Users/hue/code/dopemux-auth
export DOPEMUX_INSTANCE_ID="auth"

conport get_progress
# Output includes:
# [PLANNED] Q4 2025 Milestone: User Authentication System (shared)
# [IN_PROGRESS] Your isolated feature tasks...
```

**Note**: PLANNED tasks created in feature worktrees are isolated. Only PLANNED tasks from main worktree (instance_id=NULL) are shared.

---

## Example 5: Team Collaboration with Instance Isolation

**Scenario**: Two developers working on same repository, different features

### Developer Alice: Authentication Feature

```bash
# Alice's machine
cd /shared/dopemux-mvp
git worktree add ../dopemux-alice-auth -b alice/feature-auth

cd ../dopemux-alice-auth
export DOPEMUX_INSTANCE_ID="alice-auth"
export DOPEMUX_WORKSPACE_ID="/shared/dopemux-mvp"

# Alice's isolated work
conport log_progress \
  --description "Implement OAuth2 provider integration" \
  --status IN_PROGRESS
```

### Developer Bob: Payment Feature

```bash
# Bob's machine (same shared repo)
cd /shared/dopemux-mvp
git worktree add ../dopemux-bob-payments -b bob/feature-payments

cd ../dopemux-bob-payments
export DOPEMUX_INSTANCE_ID="bob-payments"
export DOPEMUX_WORKSPACE_ID="/shared/dopemux-mvp"

# Bob's isolated work
conport log_progress \
  --description "Add Stripe subscription management" \
  --status IN_PROGRESS
```

### Visibility Rules

```bash
# Alice queries
conport get_progress
# Sees: Her IN_PROGRESS OAuth2 task (isolated)
# Sees: Shared COMPLETED tasks from Bob
# Does NOT see: Bob's IN_PROGRESS payment task ✅

# Bob queries
conport get_progress
# Sees: His IN_PROGRESS payment task (isolated)
# Sees: Shared COMPLETED tasks from Alice
# Does NOT see: Alice's IN_PROGRESS OAuth2 task ✅
```

### Sharing Completed Work

```bash
# Alice completes OAuth2
conport update_progress --progress_id "$ALICE_TASK" --status COMPLETED

# Bob now sees it!
conport get_progress
# Output:
# [COMPLETED] Implement OAuth2 provider integration (Alice - now shared)
# [IN_PROGRESS] Add Stripe subscription management (Bob - still isolated)
```

---

## Example 6: Active Context Per Instance

**Scenario**: Maintain different context/notes for each worktree

### Feature Worktree Context

```bash
cd /Users/hue/code/dopemux-auth
export DOPEMUX_INSTANCE_ID="auth"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Set feature-specific context
conport update_active_context \
  --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{
    "current_focus": "JWT authentication implementation",
    "blockers": ["Need API key from DevOps"],
    "next_steps": ["Write integration tests", "Update API docs"]
  }'

# Retrieve context later
conport get_active_context
# Shows: Context specific to "auth" instance
```

### Main Worktree Context (Different!)

```bash
cd /Users/hue/code/dopemux-mvp
# No instance ID

# Set main worktree context
conport update_active_context \
  --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{
    "current_focus": "Code reviews and deployment monitoring",
    "recent_deploys": ["v2.3.1 - hotfix deployed"],
    "next_sprint": "Sprint 24 planning"
  }'

# Retrieve context
conport get_active_context
# Shows: Context for main worktree (different from auth instance)
```

**Each instance maintains independent active context** ✅

---

## Example 7: ADHD Pomodoro Workflow

**Scenario**: Use worktrees for 25-minute focus sessions

### Setup

```bash
# Create session-specific worktrees
git worktree add ../dopemux-session1 -b session/auth-jwt
git worktree add ../dopemux-session2 -b session/api-refactor
```

### Session 1 (25 minutes)

```bash
cd /Users/hue/code/dopemux-session1
export DOPEMUX_INSTANCE_ID="session1"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Start timer (25 min)
conport log_progress \
  --description "Session 1: Implement JWT auth middleware" \
  --status IN_PROGRESS

# Work for 25 minutes...
# Timer ends - mark progress
conport update_progress --progress_id "$SESSION1_TASK" --status IN_PROGRESS
# (Still isolated - not done yet)
```

### Break (5 minutes)

Switch terminal, take break. Your session1 task stays preserved.

### Session 2 (25 minutes)

```bash
cd /Users/hue/code/dopemux-session2
export DOPEMUX_INSTANCE_ID="session2"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Different focus, different worktree
conport log_progress \
  --description "Session 2: Refactor API error handling" \
  --status IN_PROGRESS

# Work for 25 minutes...
```

### End of Day

```bash
# Mark completed sessions
conport update_progress --progress_id "$SESSION1_TASK" --status COMPLETED
conport update_progress --progress_id "$SESSION2_TASK" --status COMPLETED

# Both now shared across all worktrees ✅
```

---

## Best Practices from Examples

1. **One Terminal Per Worktree**: Keep terminals open to preserve mental context
2. **Descriptive Instance IDs**: Use feature names, not generic names
3. **Mark Complete Promptly**: Share finished work immediately
4. **Use BLOCKED for Cross-Cutting Issues**: Make blockers visible to all
5. **Leverage Active Context**: Store worktree-specific notes and state
6. **Clean Up Old Worktrees**: Remove when feature is merged

---

## Quick Reference

```bash
# Create worktree
git worktree add ../worktree-name -b branch-name

# Set environment
export DOPEMUX_INSTANCE_ID="instance-name"
export DOPEMUX_WORKSPACE_ID="/absolute/path/to/main/repo"

# Create isolated task
conport log_progress --description "Task" --status IN_PROGRESS

# Mark complete (becomes shared)
conport update_progress --progress_id "$ID" --status COMPLETED

# Query visible tasks
conport get_progress

# Remove worktree
git worktree remove /path/to/worktree
```

Happy parallel development! 🚀
