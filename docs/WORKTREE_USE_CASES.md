# Worktree Use Cases - When and Why to Use Worktrees

## Quick Decision Guide

**Use worktrees when:**
- Working on multiple features simultaneously
- Need to preserve context across interruptions
- Want to experiment without risk
- Reviewing PRs while developing
- Handling emergency fixes during feature work
- Collaborating with shared workspace

**Don't use worktrees when:**
- Single linear development (just use branches)
- Quick bug fixes on same branch
- Temporary file viewing (use git show instead)

---

## Use Case 1: ADHD Developer - Multiple Features in Flight

### Problem
"I have ADHD and typically work on 2-3 features at once, switching based on energy and interest. Traditional git branches force me to stash/unstash constantly, and I lose context every time I switch."

### Solution with Worktrees

**Setup** (Once):
```bash
dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc
git worktree add /Users/hue/code/feature-a -b feature/authentication
git worktree add /Users/hue/code/feature-b -b feature/api-refactor
git worktree add /Users/hue/code/feature-c -b feature/ui-polish
```

**Daily Use**:
```bash
# Morning (high energy) - Complex API refactor
dwt api-refactor
export DOPEMUX_INSTANCE_ID="api"
# Code for 25 minutes

# Afternoon (medium energy) - UI polish
dwt ui-polish
export DOPEMUX_INSTANCE_ID="ui"
# Code for 25 minutes

# Evening (low energy) - Documentation
dwt authentication
export DOPEMUX_INSTANCE_ID="auth"
# Document the OAuth flow
```

### ADHD Benefits
- No stashing/unstashing mental overhead
- Physical terminals = external memory
- Switch based on energy, not forced linearity
- Each context perfectly preserved

---

## Use Case 2: Emergency Production Fix

### Problem
"Production is down and I'm deep in feature development with uncommitted changes. I need to fix the issue NOW without losing my work or creating conflicts."

### Solution

**Current State**:
```bash
Terminal 1: Deep in feature-payments
# 2 hours of uncommitted work
# In the zone, don't want to stop
```

**Emergency Action**:
```bash
# Open NEW terminal (don't touch Terminal 1!)
cd /Users/hue/code/dopemux-mvp
git worktree add /Users/hue/code/hotfix-now -b hotfix/redis-timeout
dwt redis-timeout
export DOPEMUX_INSTANCE_ID="hotfix"

# Fix, test, commit, push
git add . && git commit -m "fix: Redis timeout"
git push origin hotfix/redis-timeout

# Cleanup when merged
git worktree remove /Users/hue/code/hotfix-now

# Return to Terminal 1
# Your feature work is untouched
# Continue exactly where you left off
```

### Benefits
- Zero context loss
- No stash conflicts
- Feature work completely safe
- Immediate return to flow state

---

## Use Case 3: Reviewing PRs Without Disruption

### Problem
"I need to review a teammate's PR, but I'm in the middle of my own feature. Switching branches loses my context, and I don't want to commit incomplete work just to switch."

### Solution

```bash
# Your feature work (keep running)
Terminal 1: dwt my-feature
export DOPEMUX_INSTANCE_ID="my-feature"

# Create review worktree
Terminal 2:
git worktree add /Users/hue/code/review-pr-456 -b review/pr-456
git fetch origin pull/456/head:review/pr-456
dwt pr-456
export DOPEMUX_INSTANCE_ID="pr-review"

# Review code, test changes, leave comments
# When done, just close Terminal 2

# Terminal 1 still has your feature context
```

### Benefits
- Review without disrupting development
- Test PR changes in isolation
- Easy cleanup (delete worktree when done)
- No risk of mixing PR code with your work

---

## Use Case 4: Experimental Refactoring

### Problem
"I want to try a major refactoring but I'm not sure it will work. I don't want to risk breaking my stable development environment."

### Solution

```bash
# Stable work continues
Terminal 1: dwt stable-feature

# Create experiment
Terminal 2:
git worktree add /Users/hue/code/experiment -b experiment/new-architecture
dwt new-architecture
export DOPEMUX_INSTANCE_ID="experiment"

# Try aggressive changes
# Break things to learn
# No fear of consequences

# If successful:
git add . && git commit
# Merge to main branch

# If failed:
git worktree remove /Users/hue/code/experiment
# Experiment deleted, stable work unaffected
```

### Benefits
- Risk-free experimentation
- Learning without anxiety
- Easy rollback
- Stable work protected

---

## Use Case 5: Long-Running Refactoring (Multi-Day)

### Problem
"I have a 5-day refactoring task. I get interrupted constantly and lose context every time I return to work."

### Solution

```bash
# Day 1: Create dedicated worktree
git worktree add /Users/hue/code/big-refactor -b refactor/auth-system
dwt auth-system
export DOPEMUX_INSTANCE_ID="auth-refactor"

# Work for 2 hours, leave terminal open

# Day 2-5: Resume
# Terminal is still open with exact context
# All uncommitted changes preserved
# ConPort has your IN_PROGRESS tasks
# Just continue coding

# No "where was I?" reconstruction needed
```

### Benefits
- Perfect context preservation across days
- No daily warm-up time
- Terminal acts as physical bookmark
- ADHD-friendly interruption recovery

---

## Use Case 6: Team Collaboration (Shared Codebase)

### Problem
"Two developers working on same repository but different features. We need our tasks isolated so we don't see each other's incomplete work, but we want to share completed features."

### Solution

**Developer Alice**:
```bash
git worktree add /team/alice-oauth -b alice/oauth
dwt oauth
export DOPEMUX_INSTANCE_ID="alice-oauth"
export DOPEMUX_WORKSPACE_ID="/team/shared-project"

# Create isolated task
# Only Alice sees her IN_PROGRESS work
```

**Developer Bob**:
```bash
git worktree add /team/bob-payments -b bob/payments
dwt payments
export DOPEMUX_INSTANCE_ID="bob-payments"
export DOPEMUX_WORKSPACE_ID="/team/shared-project"

# Create isolated task
# Only Bob sees his IN_PROGRESS work
```

**Sharing**:
```bash
# Alice completes OAuth
conport update-progress --status COMPLETED
# Bob now sees it and can build on it

# Bob completes payments
conport update-progress --status COMPLETED
# Alice can now integrate with payments
```

### Benefits
- Private work stays private
- Completed work shared automatically
- No confusion from WIP tasks
- Clear collaboration boundaries

---

## Use Case 7: Multi-Platform Testing

### Problem
"I need to test the same code on different OS configurations or with different environment setups."

### Solution

```bash
# Setup different test environments
git worktree add /Users/hue/code/test-python39 -b test/python39
git worktree add /Users/hue/code/test-python312 -b test/python312

# Terminal 1: Python 3.9 testing
dwt python39
pyenv local 3.9
pytest

# Terminal 2: Python 3.12 testing
dwt python312
pyenv local 3.12
pytest

# Compare results without switching Python versions
```

### Benefits
- Isolated test environments
- No version switching overhead
- Parallel test execution
- Easy comparison

---

## Use Case 8: Documentation Sync Development

### Problem
"I'm implementing a feature and need to write documentation simultaneously. Switching between code and docs branches loses context."

### Solution

```bash
# Terminal 1: Implementation
dwt feature-impl
export DOPEMUX_INSTANCE_ID="impl"
# Write code

# Terminal 2: Documentation
dwt feature-docs
export DOPEMUX_INSTANCE_ID="docs"
# Write docs explaining what you just coded

# Keep both terminals visible
# Code in one window, docs in another
# Context preserved in both
```

### Benefits
- Write docs while implementation fresh in mind
- No context switching overhead
- Docs stay in sync with code
- Visual split-screen workflow

---

## Use Case 9: Learning New Codebase

### Problem
"I'm new to this codebase and want to explore different modules without losing my place."

### Solution

```bash
# Main exploration
Terminal 1: dwt main (read-only)

# Create experimental worktrees for trying things
git worktree add /Users/hue/code/explore-auth -b explore/auth
git worktree add /Users/hue/code/explore-db -b explore/database

# Terminal 2: Explore authentication
dwt auth
# Make changes to understand
# Break things to learn
# Delete when done

# Terminal 3: Explore database
dwt database
# Try queries
# Modify schemas
# Delete when done

# Terminal 1 stays clean for reference
```

### Benefits
- Safe exploration (main untouched)
- Multiple exploration paths
- Easy cleanup (delete explore worktrees)
- Learn without fear

---

## Use Case 10: Pair Programming

### Problem
"Pair programming remotely - need to share code state without git commits."

### Solution

```bash
# Both developers: Same workspace_id, different instance_id

# Developer A:
dwt pairing-a
export DOPEMUX_INSTANCE_ID="dev-a"
export DOPEMUX_WORKSPACE_ID="/shared/project"

# Developer B:
dwt pairing-b
export DOPEMUX_INSTANCE_ID="dev-b"
export DOPEMUX_WORKSPACE_ID="/shared/project"

# Share completed units of work via ConPort
# Each developer sees completed work
# WIP stays private until ready
```

### Benefits
- Clear ownership of tasks
- Flexible collaboration
- No forced commits
- Progress visibility

---

## Anti-Patterns (Don't Do This)

### ❌ Anti-Pattern 1: Too Many Worktrees

```bash
# DON'T: Create worktree for every tiny change
git worktree add feature-1
git worktree add feature-2
git worktree add feature-3
# ... 20 worktrees
```

**Why**: Cognitive overhead of tracking many contexts

**DO**: Keep 2-4 active worktrees maximum

### ❌ Anti-Pattern 2: Not Cleaning Up

```bash
# DON'T: Leave merged branches as worktrees
# Clutter accumulates
```

**DO**: Clean up after merging
```bash
dopemux worktrees cleanup --dry-run
dopemux worktrees cleanup --force
```

### ❌ Anti-Pattern 3: Working Directly on Main

```bash
# DON'T: Use worktrees but still commit to main
dwt main
# Make changes directly
```

**DO**: Always use feature branches in worktrees

### ❌ Anti-Pattern 4: Forgetting Instance ID

```bash
# DON'T: Skip setting instance ID when you need isolation
dwt feature
# No instance ID set
# Tasks are shared instead of isolated
```

**DO**: Set instance ID for each worktree
```bash
export DOPEMUX_INSTANCE_ID="feature-name"
```

---

## Quick Decision Matrix

| Scenario | Use Worktree? | Why? |
|----------|---------------|------|
| Multiple features simultaneously | YES | Context preservation |
| Emergency hotfix during development | YES | Zero disruption |
| PR review | YES | Isolated testing |
| Experiment/learning | YES | Safe exploration |
| Quick bug fix (same feature) | NO | Overkill - just commit |
| Reading code | NO | git show is simpler |
| Single feature, linear work | NO | Regular branches fine |

---

## Success Metrics

**Before Worktrees**:
- Context switch overhead: 5-15 minutes
- Stash conflicts: ~20% of switches
- Anxiety about losing work: High
- Parallel features: Difficult/stressful

**After Worktrees**:
- Context switch overhead: < 1 second (terminal switch)
- Stash conflicts: 0% (no stashing needed)
- Anxiety: Low (work always preserved)
- Parallel features: Natural and easy

---

## Getting Started

### Minimal Setup

```bash
# 1. Install shell integration
dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc

# 2. Create your first worktree
git worktree add /Users/hue/code/my-feature -b feature/my-feature

# 3. Switch to it
dwt my-feature

# 4. Set instance ID (for task isolation)
export DOPEMUX_INSTANCE_ID="my-feature"
export DOPEMUX_WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

# 5. Start working!
```

### Recommended Workflow

1. **One feature = One worktree**
2. **One terminal per worktree** (keep open)
3. **Descriptive instance IDs**
4. **Cleanup after merging**
5. **Use dwt for switching** (not cd)

---

## Conclusion

Worktrees are a powerful tool for ADHD-optimized development when used correctly. They provide:

- **Physical context separation** (different directories)
- **Mental clarity** (different terminals)
- **Zero-overhead switching** (just change terminals)
- **Perfect context preservation** (no stashing)
- **Safe experimentation** (isolated environments)

Combined with Dopemux's multi-instance support and ConPort task isolation, you get a development environment that works WITH your ADHD, not against it.

**Start simple**: Create one worktree for your next feature and experience the difference.
