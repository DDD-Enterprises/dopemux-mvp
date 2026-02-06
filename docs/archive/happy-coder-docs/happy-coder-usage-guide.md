---
id: HAPPY_CODER_USAGE_GUIDE
title: Happy_Coder_Usage_Guide
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Happy_Coder_Usage_Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Happy Coder - Practical Usage Guide

**Quick Start**: Get mobile notifications for your Dopemux development workflows in 5 minutes.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Happy CLI

```bash
npm install -g happy-coder
```

**Verify installation**:
```bash
happy --version
```

### Step 2: Configure Dopemux

Edit `~/.config/dopemux/dopemux.toml`:

```toml
[mobile]
enabled = true
default_panes = "primary"  # Monitor primary Claude pane
popup_mode = false         # Use tmux panes (not popup)
```

### Step 3: Start Dopemux Session

```bash
# Start Dopemux in tmux
dopemux start
```

### Step 4: Launch Happy Mobile Integration

```bash
# In your Dopemux tmux session
dopemux mobile start
```

**Expected output**:
```
✅ Happy session ready: workspace
```

### Step 5: Test Notification

```bash
dopemux mobile notify "Hello from Dopemux! 🎉"
```

**Check your phone**: You should receive a push notification!

---

## 📱 Common Use Cases

### Use Case 1: Long-Running Builds

**Scenario**: You start a build that takes 30 minutes, want to grab coffee without checking terminal.

```bash
# Start build
npm run build:production

# Build completes while you're away
# → Phone notifies: "✅ Production build complete"
```

**ADHD Benefit**: Reduces "is it done yet?" anxiety, enables guilt-free breaks.

### Use Case 2: Batch Documentation Processing

**Scenario**: Processing 100 markdown files, don't want to stare at terminal.

```bash
dopemux extract-pipeline ./docs --output ./processed

# Processing runs...
# → Phone notifies when complete: "✅ Extraction pipeline complete"
```

**ADHD Benefit**: Frees you to context-switch without mental overhead.

### Use Case 3: Overnight Test Suite

**Scenario**: Comprehensive test suite runs for hours, running overnight.

```bash
# Before bed (11 PM)
npm run test:e2e

# Morning (8 AM)
# → Check phone for result: "✅ E2E tests complete" or "❌ 12 tests failed"
```

**ADHD Benefit**: Wake up knowing status, no morning anxiety.

### Use Case 4: Multiple Claude Panes

**Scenario**: Working on multiple projects simultaneously in different panes.

```bash
# Launch Happy for all Claude panes
dopemux mobile start --all

# Each pane gets its own Happy session
# → Separate notifications for each project
```

**ADHD Benefit**: Parallel project tracking without mental juggling.

---

## 🎮 Command Reference

### Start Happy Sessions

```bash
# Monitor primary (active) Claude pane
dopemux mobile start

# Monitor all Claude panes
dopemux mobile start --all

# Monitor specific panes
dopemux mobile start --pane workspace --pane agent-2

# Use popup instead of panes (ephemeral)
# (Requires popup_mode = true in config)
dopemux mobile start
```

### Send Manual Notifications

```bash
# Simple message
dopemux mobile notify "Task complete!"

# Multi-word message
dopemux mobile notify "Build finished successfully 🎉"

# From script
./my-script.sh && dopemux mobile notify "Script done!"
```

### Stop Happy Sessions

```bash
# Stop all Happy sessions
dopemux mobile detach --all

# Stop specific session
dopemux mobile detach --pane workspace
```

### Check Happy Status

```bash
# List tmux panes (shows Happy sessions)
tmux list-panes -a | grep happy

# See mobile window
tmux select-window -t mobile
```

---

## ⚙️ Configuration Options

### Basic Configuration

**File**: `~/.config/dopemux/dopemux.toml`

```toml
[mobile]
enabled = true              # Master switch
default_panes = "primary"   # Which panes to monitor
popup_mode = false          # Use tmux panes vs popup
```

### Advanced Configuration (v2.0 - Future)

```toml
[mobile]
# Basic settings
enabled = true
default_panes = "all"
popup_mode = false

# Custom Happy servers (optional)
happy_server_url = "https://my-relay.com"
happy_webapp_url = "https://my-app.com"

# Future enhancements (not yet implemented)
notification_batching = true
batch_window_seconds = 30
batch_threshold = 3

quiet_hours_enabled = true
quiet_hours_start = "22:00"
quiet_hours_end = "08:00"

min_priority = "normal"
```

### Default Panes Options

```toml
# Option 1: Primary pane (active or first)
default_panes = "primary"

# Option 2: All Claude panes
default_panes = "all"

# Option 3: Specific panes by name
default_panes = ["workspace", "agent-primary"]
```

---

## 🔧 Troubleshooting

### "Happy CLI not found"

**Problem**: `dopemux mobile start` says "Happy CLI not found"

**Solution**:
```bash
# Install Happy globally
npm install -g happy-coder

# Verify
which happy
```

### "No Claude panes found"

**Problem**: Can't detect Claude sessions

**Solution**:
```bash
# Ensure you're in a Dopemux session
dopemux start

# Or manually start Claude in tmux
tmux new-window -n workspace
# Then run: claude code

# Retry
dopemux mobile start
```

### "tmux not detected"

**Problem**: Not running inside tmux

**Solution**:
```bash
# Start tmux first
tmux

# Then start Dopemux
dopemux start
```

### Notifications Not Received

**Problem**: Happy runs but phone doesn't get notifications

**Check**:
```bash
# 1. Verify Happy is running
tmux list-panes -a | grep happy

# 2. Test notification manually
dopemux mobile notify "Test"

# 3. Check Happy logs
tmux select-window -t mobile
# View Happy output

# 4. Verify mobile config
grep -A5 "\[mobile\]" ~/.config/dopemux/dopemux.toml
```

### Multiple Happy Sessions Running

**Problem**: Too many Happy panes

**Solution**:
```bash
# Stop all Happy sessions
dopemux mobile detach --all

# Restart fresh
dopemux mobile start
```

---

## 🧠 ADHD Workflow Tips

### Tip 1: Use During Hyperfocus

**Problem**: Get so focused you forget about long-running tasks

**Solution**:
```bash
# Start task
npm run build

# Continue hyperfocus on other work
# Phone will notify when done → gentle reminder without breaking flow
```

### Tip 2: Guilt-Free Breaks

**Problem**: Anxiety about taking breaks ("did that task finish?")

**Solution**:
- Start long task
- Enable notifications
- Take walk/coffee break
- Phone notifies when done → return refreshed, knowing status

### Tip 3: Context Switch Recovery

**Problem**: Switching between projects causes mental overhead

**Solution**:
```bash
# Project A
dopemux mobile start --pane project-a

# Switch to Project B
# → Still get Project A notifications
# → Easy to remember to check results later
```

### Tip 4: Overnight Peace of Mind

**Problem**: Start task before bed, anxious about checking in morning

**Solution**:
- Start overnight task (tests, builds, processing)
- Check phone notification in morning
- Know immediately if successful → plan day accordingly

---

## 📊 Usage Patterns

### Pattern 1: Single Developer, One Project

```toml
[mobile]
enabled = true
default_panes = "primary"  # Just monitor active pane
```

```bash
dopemux start
dopemux mobile start  # Monitors current pane
```

### Pattern 2: Multiple Projects in Parallel

```toml
[mobile]
enabled = true
default_panes = "all"  # Monitor all panes
```

```bash
dopemux start
# Open multiple Claude panes for different projects
dopemux mobile start --all  # Monitors all
```

### Pattern 3: Selective Monitoring

```toml
[mobile]
enabled = true
default_panes = ["critical-project"]
```

```bash
# Only monitor important projects
dopemux mobile start --pane critical-project
```

### Pattern 4: Popup for Quick Tasks

```toml
[mobile]
enabled = true
popup_mode = true  # Ephemeral sessions
```

```bash
# Quick task monitoring
dopemux mobile start
# Happy appears in popup, auto-closes when done
```

---

## 🎯 Best Practices

### DO ✅

- **Start Happy at beginning of session** (minimal setup friction)
- **Use for long-running tasks** (builds, tests, extractions)
- **Test notifications early** (verify setup works)
- **Monitor critical projects only** (reduce noise)
- **Stop Happy when done** (clean up panes)

### DON'T ❌

- **Don't monitor trivial tasks** (no need for "ls" notifications)
- **Don't run multiple Happy instances per pane** (causes duplicate notifications)
- **Don't leave Happy running 24/7** (restart fresh each session)
- **Don't use for interactive commands** (defeats the purpose)

---

## 🔮 Future Features (v2.0)

### Smart Batching

**Problem**: 50 file extractions = 50 notifications

**Future**:
```bash
# Enable batching
[mobile]
notification_batching = true

# Result: "✅ 50 tasks completed" (single notification)
```

### Quiet Hours

**Problem**: Late-night builds wake you up

**Future**:
```bash
[mobile]
quiet_hours_enabled = true
quiet_hours_start = "22:00"
quiet_hours_end = "08:00"

# Build at 2 AM completes silently
# Check in morning instead
```

### Priority Filtering

**Problem**: Too many low-priority notifications

**Future**:
```bash
[mobile]
min_priority = "normal"  # Only normal+ priority

# Low-priority cleanups don't notify
# Critical builds always notify
```

**Timeline**: 3 weeks (see `HAPPY_CODER_ENHANCEMENTS.md`)

---

## 📚 Integration Examples

### Example 1: Production Deployment

```bash
#!/bin/bash
# deploy.sh

echo "Starting production deployment..."
dopemux mobile notify "🚀 Deployment started"

npm run build || {
    dopemux mobile notify "❌ Build failed!"
    exit 1
}

npm run test || {
    dopemux mobile notify "❌ Tests failed!"
    exit 1
}

npm run deploy || {
    dopemux mobile notify "❌ Deployment failed!"
    exit 1
}

dopemux mobile notify "✅ Production deployed successfully! 🎉"
```

### Example 2: Batch Processing Script

```bash
#!/bin/bash
# process_docs.sh

total=0
for file in docs/*.md; do
    dopemux extract-docs "$file"
    ((total++))
done

dopemux mobile notify "✅ Processed $total documents"
```

### Example 3: Test Suite with Failure Details

```bash
#!/bin/bash
# test.sh

if npm run test; then
    dopemux mobile notify "✅ All tests passed!"
else
    failed=$(grep "failed" test-output.txt | wc -l)
    dopemux mobile notify "❌ $failed tests failed"
fi
```

### Example 4: Automated Hooks

**Git pre-push hook** (`.git/hooks/pre-push`):
```bash
#!/bin/bash

echo "Running pre-push checks..."
dopemux mobile notify "🔍 Pre-push checks starting"

if npm run test; then
    dopemux mobile notify "✅ Pre-push checks passed"
else
    dopemux mobile notify "❌ Pre-push checks failed"
    exit 1
fi
```

---

## 🎓 Learning Resources

### Documentation
- **Integration Guide**: `HAPPY_CODER_INTEGRATION.md` (technical details)
- **Enhancement Roadmap**: `HAPPY_CODER_ENHANCEMENTS.md` (future features)
- **This Guide**: Practical usage patterns

### Community
- **Issues**: Report bugs at GitHub repository
- **Discussions**: Share workflows and tips
- **PRs**: Contribute improvements

### Happy Coder Resources
- **Official Docs**: `npm info happy-coder`
- **GitHub**: Search for "happy-coder npm"

---

## ✅ Quick Reference Card

```bash
# Setup (once)
npm install -g happy-coder
# Edit ~/.config/dopemux/dopemux.toml → enabled = true

# Daily Usage
dopemux start                    # Start Dopemux
dopemux mobile start             # Launch Happy
dopemux mobile notify "Test"     # Test notification
dopemux mobile detach --all      # Stop Happy

# Configuration
default_panes = "primary"        # Monitor active pane
default_panes = "all"            # Monitor all panes
default_panes = ["pane1"]        # Monitor specific panes
popup_mode = true                # Use popup instead of panes

# Troubleshooting
which happy                      # Check installation
tmux list-panes -a | grep happy  # Check Happy sessions
tmux select-window -t mobile     # View Happy window
```

---

## 🎯 Success Checklist

**First Time Setup**:
- [ ] Installed `happy-coder` via npm
- [ ] Configured `dopemux.toml` with `mobile.enabled = true`
- [ ] Started Dopemux in tmux
- [ ] Launched Happy with `dopemux mobile start`
- [ ] Tested with `dopemux mobile notify "Test"`
- [ ] Received notification on phone ✅

**Daily Workflow**:
- [ ] Start Dopemux session
- [ ] Launch Happy integration
- [ ] Work on tasks (builds, tests, extractions)
- [ ] Receive notifications on phone
- [ ] Stop Happy when done
- [ ] Clean exit from Dopemux

**Advanced Usage**:
- [ ] Configured custom server URLs (optional)
- [ ] Set up specific pane monitoring
- [ ] Created integration scripts
- [ ] Tested failure notifications
- [ ] Explored popup mode

---

**Next Steps**: Start using Happy Coder in your daily workflow, then provide feedback for v2.0 enhancements!
