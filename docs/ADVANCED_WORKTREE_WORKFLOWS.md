# Advanced Worktree Workflows - ADHD-Optimized Development

## Overview

This guide shows advanced patterns for combining worktrees, multi-instance support, and ADHD-friendly development workflows.

**Key Insight**: Worktrees provide physical context separation, while instance IDs provide logical task isolation.

---

## Workflow 1: Hyperfocus Rotation (Energy-Based Development)

### Scenario
Rotate between 3 features based on energy level and focus capacity throughout the day.

### Setup

```bash
# One-time: Install shell integration
dopemux shell-setup bash >> ~/.bashrc
source ~/.bashrc

# Create worktrees for different complexity levels
git worktree add /Users/hue/code/dopemux-ui -b feature/dashboard-ui       # Medium complexity
git worktree add /Users/hue/code/dopemux-api -b feature/graphql-api      # High complexity
git worktree add /Users/hue/code/dopemux-docs -b feature/documentation   # Low complexity
```

### Terminal Setup (Keep 3 Terminals Open)

**Terminal 1: High Energy Tasks (API)**
```bash
dwt graphql-api
export DOPEMUX_INSTANCE_ID="api-work"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Create isolated task
python -c "
from scripts.mcp-wrappers.conport_direct import log_progress
log_progress(
    workspace_id='/Users/hue/code/dopemux-mvp',
    status='IN_PROGRESS',
    description='Implement GraphQL resolvers for user management'
)
"
```

**Terminal 2: Medium Energy Tasks (UI)**
```bash
dwt dashboard-ui
export DOPEMUX_INSTANCE_ID="ui-work"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
```

**Terminal 3: Low Energy Tasks (Docs)**
```bash
dwt documentation
export DOPEMUX_INSTANCE_ID="docs-work"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
```

### Daily Workflow

```bash
# 9:00 AM - High energy → Complex API work
# Switch to Terminal 1 (already in dopemux-api worktree)
# Work for 25 minutes

# 10:30 AM - Energy dip → Medium complexity UI
# Switch to Terminal 2 (already in dopemux-ui worktree)
# Work for 25 minutes

# 3:00 PM - Low energy → Documentation
# Switch to Terminal 3 (already in dopemux-docs worktree)
# Work for 25 minutes

# Each terminal preserves context
# No mental reconstruction needed when switching
```

### ADHD Benefits
- Physical terminals = clear context boundaries
- No directory switching overhead
- Energy-appropriate task selection
- Visual reminder of what you're working on

---

## Workflow 2: Emergency Hotfix Without Disruption

### Scenario
Production issue occurs while working on a feature. Need to fix without losing feature context.

### Setup

**Current State: Working on feature**
```bash
# Terminal 1: Feature development
dwt payments-feature
export DOPEMUX_INSTANCE_ID="payments"
# Deep in the zone, lots of uncommitted changes
```

### Emergency Response

**Step 1: Create hotfix worktree (NEW terminal)**
```bash
# Terminal 2: Emergency hotfix
cd /Users/hue/code/dopemux-mvp
git worktree add /Users/hue/code/dopemux-hotfix-redis -b hotfix/redis-connection
dwt redis-connection
export DOPEMUX_INSTANCE_ID="hotfix-redis"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
```

**Step 2: Fix and deploy**
```bash
# Make fix in Terminal 2
# Terminal 1 is untouched - your feature work is safe

# Commit and push
git add .
git commit -m "fix: Redis connection pool timeout"
git push origin hotfix/redis-connection

# Create PR, deploy, celebrate
```

**Step 3: Return to feature work**
```bash
# Switch back to Terminal 1
# Your context is exactly where you left it
# No mental reconstruction needed
# Continue coding immediately
```

**Step 4: Cleanup**
```bash
# After hotfix is merged
cd /Users/hue/code/dopemux-mvp
git worktree remove /Users/hue/code/dopemux-hotfix-redis
```

### ADHD Benefits
- Zero context loss during interruption
- Physical separation prevents mistakes
- Clear visual distinction (different terminals)
- Immediate return to flow state

---

## Workflow 3: Parallel Review + Development

### Scenario
Review someone's PR while continuing your own feature work.

### Setup

```bash
# Terminal 1: Your feature work
dwt my-feature
export DOPEMUX_INSTANCE_ID="my-feature"

# Terminal 2: PR review
git worktree add /Users/hue/code/dopemux-review-pr-123 -b review/pr-123
git fetch origin pull/123/head:review/pr-123
dwt pr-123
export DOPEMUX_INSTANCE_ID="pr-review"
```

### Workflow

**When notification arrives:**
```bash
# Switch to Terminal 2 (review)
# Review code, leave comments, test changes
# Terminal 1 stays in your feature context

# Done reviewing?
# Switch back to Terminal 1
# No context reconstruction needed
```

### ADHD Benefits
- Review doesn't disrupt development flow
- Can pause review anytime (just switch terminals)
- Code stays organized (review branch separate)
- Easy cleanup after review

---

## Workflow 4: Experiment Without Risk

### Scenario
Want to try a risky refactoring without breaking main development.

### Setup

```bash
# Current: Stable feature work
dwt stable-feature
export DOPEMUX_INSTANCE_ID="stable"

# Create experiment worktree
git worktree add /Users/hue/code/dopemux-experiment -b experiment/refactor-auth
dwt refactor-auth
export DOPEMUX_INSTANCE_ID="experiment"
```

### Experimentation

```bash
# In experiment worktree:
# Try aggressive refactoring
# Break things intentionally to learn
# No fear of losing stable work

# If experiment succeeds:
git add . && git commit -m "experimental: successful refactor"
# Merge to stable branch

# If experiment fails:
cd /Users/hue/code/dopemux-mvp
git worktree remove /Users/hue/code/dopemux-experiment
# No cleanup needed in main branch - experiment isolated
```

### ADHD Benefits
- Safe experimentation environment
- No "what if I break it" anxiety
- Easy rollback (just delete worktree)
- Learning without consequences

---

## Workflow 5: Multi-Day Tasks with Context Preservation

### Scenario
Large refactoring that will take 3-5 days with frequent interruptions.

### Setup

```bash
# Day 1: Create dedicated worktree
git worktree add /Users/hue/code/dopemux-big-refactor -b feature/auth-refactor
dwt auth-refactor
export DOPEMUX_INSTANCE_ID="auth-refactor"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# Start work
# Make progress for 2 hours
# Leave terminal open
```

### Daily Pattern

```bash
# Day 2: Resume
# Terminal is still there with exact context
# All uncommitted changes preserved
# ConPort has your IN_PROGRESS tasks
# Just continue coding

# Day 3: Same pattern
# No "where was I?" reconstruction
# Physical terminal = mental bookmark

# Day 4: Complete
# Mark tasks complete
# Merge to main
# Cleanup worktree
```

### ADHD Benefits
- Permanent context preservation
- Physical terminal acts as bookmark
- No daily "warm up" time
- Interruption-resistant workflow

---

## Workflow 6: Team Collaboration (Shared Workspace)

### Scenario
Two developers on same codebase, different features, need task isolation.

### Setup

**Developer Alice:**
```bash
cd /shared/dopemux-project
git worktree add /shared/alice-auth -b alice/oauth-integration
dwt oauth-integration
export DOPEMUX_INSTANCE_ID="alice-auth"
export DOPEMUX_WORKSPACE_ID="/shared/dopemux-project"

# Create isolated task
# IN_PROGRESS tasks only visible to Alice
```

**Developer Bob:**
```bash
cd /shared/dopemux-project
git worktree add /shared/bob-payments -b bob/stripe-integration
dwt stripe-integration
export DOPEMUX_INSTANCE_ID="bob-payments"
export DOPEMUX_WORKSPACE_ID="/shared/dopemux-project"

# Create isolated task
# IN_PROGRESS tasks only visible to Bob
```

### Collaboration Pattern

**Parallel Work:**
```bash
# Alice and Bob work simultaneously
# Each sees only their own IN_PROGRESS tasks
# No interference or confusion
```

**Sharing Completed Work:**
```bash
# Alice completes OAuth
conport update-progress --progress_id 42 --status COMPLETED
# Bob now sees it!

# Bob can learn from Alice's implementation
# Or build on top of completed work
```

### ADHD Benefits
- Clear boundaries (your work vs others)
- No cognitive overload from seeing others' WIP
- Sharing only happens intentionally (on completion)
- Reduces coordination anxiety

---

## Workflow 7: Quick Shell Integration Setup

### One-Liner Installation

```bash
# Bash users:
dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc && echo "✅ Shell integration installed! Use: dwt <branch>"

# Zsh users:
dopemux shell-setup zsh >> ~/.zshrc && source ~/.zshrc && echo "✅ Shell integration installed! Use: dwt <branch>"
```

### Verification

```bash
# Test that dwt command exists
type dwt
# Should show: "dwt is an alias for dopemux_switch"

# Test switching
dwt ui-build
pwd  # Should show: /Users/hue/code/ui-build

# Test fuzzy matching
dwt ui
pwd  # Should still work (matches ui-build)
```

---

## Environment Variable Reference

### Required for Instance Isolation

```bash
# Set in each terminal/worktree for task isolation
export DOPEMUX_INSTANCE_ID="<unique-identifier>"
# Examples: "feature-ui", "hotfix", "experiment", "alice-auth"
# If empty/unset, uses main instance (no isolation)

export DOPEMUX_WORKSPACE_ID="/absolute/path/to/main/repo"
# Should always point to main repository root
# Even if you're in a worktree, use main repo path
```

### Optional (Auto-Detected if Not Set)

```bash
export DOPEMUX_PORT_BASE="3030"
# Auto-allocated by instance manager if not set
# Manual setting useful for custom port requirements
```

---

## Quick Reference Commands

### Worktree Management

```bash
# List all worktrees
dwtls
# OR: dopemux worktrees list

# Show current worktree
dwtcur
# OR: dopemux worktrees current

# Switch to worktree (requires shell integration)
dwt <branch-name>
# OR: cd $(dopemux worktrees switch-path <branch-name>)

# Cleanup unused worktrees
dopemux worktrees cleanup --dry-run  # Preview
dopemux worktrees cleanup --force    # Execute
```

### Instance Management

```bash
# List running instances
dopemux instances list

# Resume orphaned instance
dopemux instances resume <instance-id>

# Cleanup stopped instances
dopemux instances cleanup
```

### Task Isolation (ConPort)

```bash
# Create isolated task (visible only in this instance)
# Requires DOPEMUX_INSTANCE_ID to be set
python -m conport log-progress \
  --workspace_id "$DOPEMUX_WORKSPACE_ID" \
  --status IN_PROGRESS \
  --description "Your task"

# Mark complete (becomes shared across all instances)
python -m conport update-progress \
  --progress_id <id> \
  --status COMPLETED
```

---

## Common Patterns

### Pattern: Feature Branch Development

```bash
# 1. Create feature branch worktree
git worktree add /Users/hue/code/feature-name -b feature/name
dwt name

# 2. Set instance isolation
export DOPEMUX_INSTANCE_ID="feature-name"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# 3. Work with isolation
# Your IN_PROGRESS tasks are private

# 4. Share when ready
# Mark tasks COMPLETED to share with team
```

### Pattern: Context-Switch Safe

```bash
# Keep terminals open for different contexts
Terminal 1: Main branch (monitoring, reviews)
Terminal 2: Feature A (primary development)
Terminal 3: Feature B (secondary task)

# Switch terminals instead of switching directories
# Context preserved in each terminal
```

### Pattern: Clean Workspace

```bash
# Weekly cleanup
dopemux worktrees cleanup --dry-run
# Review what will be removed
dopemux worktrees cleanup --force
# Remove merged feature branches
```

---

## Troubleshooting

### Issue: dwt command not found

**Cause**: Shell integration not installed or sourced

**Fix**:
```bash
# Reinstall
dopemux shell-setup bash >> ~/.bashrc
source ~/.bashrc

# Verify
type dwt
```

### Issue: Switch doesn't change directory

**Cause**: Using deprecated `dopemux worktrees switch` command

**Fix**:
```bash
# Use shell integration instead
dwt <branch-name>

# OR workaround
cd $(dopemux worktrees switch-path <branch-name>)
```

### Issue: Tasks not isolated between worktrees

**Cause**: `DOPEMUX_INSTANCE_ID` not set

**Fix**:
```bash
# Set per terminal
export DOPEMUX_INSTANCE_ID="unique-name"
export DOPEMUX_WORKSPACE_ID="/path/to/main/repo"
```

### Issue: Workspace detection wrong

**Cause**: Working in nested directory, not worktree root

**Fix**:
```bash
# MCP wrappers use git root detection
# Ensure you're in a git repository
git rev-parse --show-toplevel
# This is what MCP servers will use
```

---

## Performance Tips

### Reduce Git Overhead

The `dopemux worktrees current` command caches results for 30 seconds to prevent spawning hundreds of git processes during MCP operations.

```bash
# Use cache (default)
dopemux worktrees current

# Force fresh detection
dopemux worktrees current --no-cache
```

### Terminal Reuse

Keep terminals open instead of creating new ones:
```bash
# BETTER: Reuse terminals
Terminal 1: dwt feature-a  # Keep open all day
Terminal 2: dwt feature-b  # Keep open all day

# WORSE: Create/destroy
# Creates overhead and loses context
```

---

## Integration with Multi-Instance

### Automatic Port Allocation

When you run `dopemux start` in different worktrees:

```bash
# Terminal 1: Main worktree
cd /Users/hue/code/dopemux-mvp
dopemux start
# Instance A: Ports 3000, 3005, 3006, 3007...

# Terminal 2: Feature worktree
dwt feature-ui
dopemux start
# Instance B: Ports 3030, 3035, 3036, 3037...
# Automatically detected and allocated!
```

### Service Port Mapping

Each instance gets offset ports:
```
Instance A (main):    Port 3000 base
├─ TaskMaster:       3005
├─ Serena:           3006
├─ ConPort:          3007
└─ Integration:      3016

Instance B (worktree): Port 3030 base
├─ TaskMaster:        3035
├─ Serena:            3036
├─ ConPort:           3037
└─ Integration:       3046
```

### Database Isolation

ConPort uses `(workspace_id, instance_id)` for task filtering:

```sql
-- Main instance (instance_id = NULL):
SELECT * FROM progress_entries
WHERE workspace_id = '/path' AND instance_id IS NULL;
-- Returns only shared tasks

-- Feature instance:
SELECT * FROM progress_entries
WHERE workspace_id = '/path'
  AND (instance_id IS NULL OR instance_id = 'feature-ui');
-- Returns shared tasks + own isolated tasks
```

---

## Best Practices

### 1. One Feature = One Worktree + One Instance ID

```bash
git worktree add /path/to/feature -b feature/name
dwt name
export DOPEMUX_INSTANCE_ID="feature-name"
```

### 2. Use Descriptive Instance IDs

```bash
# GOOD: Self-documenting
export DOPEMUX_INSTANCE_ID="oauth-integration"
export DOPEMUX_INSTANCE_ID="ui-dashboard"
export DOPEMUX_INSTANCE_ID="hotfix-memory-leak"

# AVOID: Cryptic
export DOPEMUX_INSTANCE_ID="B"
export DOPEMUX_INSTANCE_ID="temp"
```

### 3. Cleanup Merged Branches

```bash
# After PR merged
dopemux worktrees cleanup --dry-run
# Review, then:
dopemux worktrees cleanup --force
```

### 4. Keep Terminals Open

```bash
# Each terminal = one context
# Switching terminals < switching directories
# Context preserved in terminal history
```

### 5. Share Consciously

```bash
# Keep work private while in progress
status=IN_PROGRESS  # Isolated to instance

# Share when ready
status=COMPLETED    # Visible to all instances
status=BLOCKED      # Visible to all (for help)
```

---

## Shell Integration Aliases

After installing shell integration, you get these commands:

| Alias | Full Command | Description |
|-------|--------------|-------------|
| `dwt <branch>` | `dopemux_switch <branch>` | Switch to worktree |
| `dwtls` | `dopemux worktrees list` | List all worktrees |
| `dwtcur` | `dopemux worktrees current` | Show current worktree |

**Custom Aliases You Can Add:**

```bash
# Add to ~/.bashrc or ~/.zshrc

# Quick switch to common worktrees
alias ui='dwt ui-build'
alias api='dwt api-server'
alias docs='dwt documentation'
alias main='dwt main'

# Switch and show status
dwtstat() {
    dwt "$1" && git status --short
}

# Switch and start dopemux
dwtstart() {
    dwt "$1" && dopemux start
}

# Create new feature worktree
dwtadd() {
    local branch_name="$1"
    git worktree add "/Users/hue/code/$branch_name" -b "feature/$branch_name"
    dwt "$branch_name"
    export DOPEMUX_INSTANCE_ID="$branch_name"
    export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
    echo "✅ Ready for development in $branch_name"
}
```

---

## Workflow Comparison

### Before Worktrees (Traditional)

```bash
# Working on feature A
git checkout feature-a
# Make changes...
# Uncommitted work

# Hotfix needed!
git stash              # Lose context
git checkout main      # Mental switch
git checkout -b hotfix
# Fix issue
git checkout feature-a # Mental switch back
git stash pop          # Hope it works
# Reconstruct mental model
```

**ADHD Impact**: High cognitive load, context loss, anxiety about stash conflicts

### After Worktrees (ADHD-Optimized)

```bash
# Working on feature A
dwt feature-a
# Make changes...
# Leave terminal open

# Hotfix needed!
# Open NEW terminal
git worktree add ../hotfix -b hotfix
dwt hotfix
# Fix issue
# Close hotfix terminal

# Return to original terminal
# Exact same context
# Continue immediately
```

**ADHD Impact**: Zero cognitive load, perfect context preservation, no anxiety

---

## Summary

**Worktree System Status**: FULLY FUNCTIONAL

**What Works**:
- ✅ Worktree creation and management
- ✅ Shell integration for switching (dwt command)
- ✅ Automatic workspace detection
- ✅ Multi-instance support (manual instance ID setup)
- ✅ Task isolation per instance
- ✅ Shared task visibility on completion

**Installation Required** (One-Time):
```bash
dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc
```

**ADHD Benefits Delivered**:
- Physical context separation
- Zero-overhead switching
- Interrupt-safe workflows
- Conscious task sharing
- Energy-based task selection

---

## See Also

- `docs/WORKTREE_SWITCHING_GUIDE.md` - Installation and troubleshooting
- `docker/mcp-servers/conport/docs/WORKTREE_EXAMPLES.md` - ConPort-specific patterns
- `.claude/CLAUDE.md` - Project integration instructions
