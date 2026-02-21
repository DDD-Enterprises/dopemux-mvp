---
id: ORCHESTRATOR-INTEGRATION-COMPLETE
title: Orchestrator Integration Complete
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Orchestrator Integration Complete (explanation) for dopemux documentation
  and developer workflows.
---
# ✅ Dopemux Orchestrator + ADHD Dashboard Integration - COMPLETE

## 🎯 What Was Built

**Complete tmux orchestrator environment** with integrated ADHD dashboard for optimal ADHD developer workflow.

### Two Layouts Created:

1. **Full Orchestrator** - 4-pane professional environment
2. **Minimal** - 2-pane quick launcher

---

## 🚀 Quick Start

### Launch Full Orchestrator (Recommended)

```bash
./scripts/launch-dopemux-orchestrator.sh
```

Creates:
```
┌──────────────────── 🧠 ADHD Dashboard (20% height) ────────────────────┐
│ ⚡ MED ✓23m 💚95 | 📋 24 uncommitted | ✓ 1 in progress              │
├────────────────┬──────────────┬──────────────────────────────────────┤
│                │              │                                      │
│   Dopemux CLI  │ Service Logs │  Monitoring & Status                │
│   (pane 1)     │ (pane 2)     │  (pane 3)                           │
│                │              │                                      │
│                │              │  - Docker containers                │
│                │              │  - Service health                   │
│                │              │  - Resource usage                   │
│                │              │                                      │
└────────────────┴──────────────┴──────────────────────────────────────┘
```

### Launch Minimal (Fast)

```bash
./scripts/launch-dopemux-minimal.sh
```

Creates:
```
┌──────────────────── 🧠 ADHD Dashboard ─────────────────────┐
│ ⚡ Energy | 📋 Warnings | ✓ Tasks                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Dopemux CLI (80% height)                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 Full Orchestrator Layout Details

### Pane 0: ADHD Dashboard (Top, 20% height)

**Shows:**
- Line 1: Cognitive state (energy, session, health, peak hour)
- Line 2: Untracked work warnings (uncommitted, stale branches)
- Line 3: Active tasks (Leantime integration)

**Auto-refreshes:** Every 5 seconds

**Script:** `scripts/dopemux-compact-dashboard.py show`

### Pane 1: Dopemux CLI (Bottom-Left, 33% width)

**Purpose:** Main command interface

**Pre-loaded commands:**
```bash
# Status
dopemux status
dopemux list
docker ps

# Service management
docker-compose up -d
docker-compose down
docker-compose logs -f

# ADHD Engine
curl localhost:8095/api/v1/energy-level/hue
curl localhost:8096/metrics

# Quick actions
make start
make stop
make logs
```

### Pane 2: Service Logs (Bottom-Middle, 33% width)

**Purpose:** Real-time log monitoring

**Ready to run:**
```bash
# All services
docker-compose logs -f

# Specific services
docker-compose logs -f adhd_engine
docker logs -f staging-activity-capture
docker logs -f staging-break-suggester
```

### Pane 3: Monitoring & Status (Bottom-Right, 33% width)

**Shows:**
- Docker container status (live)
- Service health checks
- System resource usage

**Runs:** Typer/Rich dashboard system pane OR `docker ps` watch

---

## 🎮 Tmux Controls

### Navigation
```
Ctrl+b ←/→/↑/↓   Navigate between panes
Ctrl+b q         Show pane numbers (press number to jump)
Ctrl+b o         Cycle through panes
Ctrl+b ;         Toggle between current and previous pane
```

### Pane Management
```
Ctrl+b z         Zoom current pane (full screen toggle)
Ctrl+b x         Close current pane (with confirmation)
Ctrl+b !         Break pane into new window
```

### Session Management
```
Ctrl+b d         Detach from session (keeps running)
Ctrl+b $         Rename session
Ctrl+b s         List all sessions
```

### Window Management
```
Ctrl+b c         Create new window
Ctrl+b n/p       Next/previous window
Ctrl+b 0-9       Jump to window number
```

---

## 🔧 Configuration & Customization

### Change Dashboard Refresh Rate

Edit `scripts/dopemux-compact-dashboard.py`:
```python
refresh: int = typer.Option(5, ...)  # Change 5 to desired seconds
```

Or pass at runtime:
```bash
python3 scripts/dopemux-compact-dashboard.py show --refresh 10
```

### Change Pane Heights

Edit `scripts/launch-dopemux-orchestrator.sh`:
```bash
# Line 42: Change -p 80 to adjust dashboard height
tmux split-window -v -p 80 -t $SESSION_NAME:0
# 80 = bottom pane gets 80%, top gets 20%
# Try: -p 85 for smaller dashboard (15%)
#      -p 75 for larger dashboard (25%)
```

### Change Pane Widths

Edit `scripts/launch-dopemux-orchestrator.sh`:
```bash
# Line 75: Adjust CLI vs Logs+Monitoring
tmux split-window -h -p 67 -t $SESSION_NAME:0.1
# 67 = right section gets 67%, left gets 33%

# Line 78: Adjust Logs vs Monitoring
tmux split-window -h -p 50 -t $SESSION_NAME:0.2
# 50 = equal split
```

### Add Custom Pane

```bash
# Add after line 165 in launch-dopemux-orchestrator.sh

# Create 4th pane
tmux split-window -h -t $SESSION_NAME:0.3
tmux select-pane -t $SESSION_NAME:0.4 -T "Custom Pane"
tmux send-keys -t $SESSION_NAME:0.4 "your-command-here" C-m
```

---

## 🔗 Integration with Makefile

Add to your `Makefile`:

```makefile
.PHONY: orchestrator dashboard minimal

# Launch full orchestrator environment
orchestrator:
    @./scripts/launch-dopemux-orchestrator.sh

# Launch minimal 2-pane
minimal:
    @./scripts/launch-dopemux-minimal.sh

# Just the dashboard (3 panes side-by-side)
dashboard:
    @./scripts/launch-adhd-dashboard.sh

# Attach to existing orchestrator session
attach:
    @tmux attach -t dopemux-orchestrator || echo "No session found. Run 'make orchestrator' first"

# Kill orchestrator session
kill-orchestrator:
    @tmux kill-session -t dopemux-orchestrator 2>/dev/null || echo "No session to kill"
```

Then use:
```bash
make orchestrator   # Launch full environment
make minimal        # Quick launch
make attach         # Reattach to existing session
```

---

## 🎨 Pane Titles & Status Bar

The orchestrator automatically sets pane titles:

```
Pane 0: 🧠 ADHD Dashboard
Pane 1: Dopemux CLI
Pane 2: Service Logs
Pane 3: Monitoring
```

These appear in the pane border (top).

### Custom Titles

Change titles dynamically:
```bash
# From within any pane
tmux select-pane -T "My Custom Title"
```

---

## 📈 Workflow Examples

### Typical Development Session

1. **Launch orchestrator**
   ```bash
   ./scripts/launch-dopemux-orchestrator.sh
   ```

2. **Start services** (Pane 1: CLI)
   ```bash
   docker-compose up -d
   ```

3. **Watch logs** (Pane 2: Logs)
   ```bash
   docker-compose logs -f adhd_engine
   ```

4. **Monitor dashboard** (Pane 0: auto-updates)
   - Glance at energy level
   - Check session time
   - Watch for untracked work warnings

5. **Work in CLI** (Pane 1)
   - Run dopemux commands
   - Test features
   - Git operations

### Debugging Session

1. **Zoom log pane** (Pane 2)
   ```
   Ctrl+b → → (navigate to logs pane)
   Ctrl+b z (zoom to full screen)
   ```

2. **Watch specific service**
   ```bash
   docker logs -f staging-activity-capture
   ```

3. **Check ADHD dashboard for context**
   ```
   Ctrl+b z (un-zoom)
   Ctrl+b ↑ (navigate to dashboard)
   ```

4. **Return to work**
   ```
   Ctrl+b ↓ (back to CLI)
   ```

### Quick Status Check

1. **Attach to running session**
   ```bash
   tmux attach -t dopemux-orchestrator
   ```

2. **Glance at all 4 panes**
   - Top: ADHD state
   - Left: CLI ready
   - Middle: Logs streaming
   - Right: Containers running

3. **Detach when done**
   ```
   Ctrl+b d
   ```

---

## 🚨 Troubleshooting

### Dashboard pane shows error

**Symptom:** Top pane shows Python import error

**Fix:**
```bash
# Install dependencies
pip3 install typer rich requests

# Or use fallback
# Edit launch-dopemux-orchestrator.sh line 54-55
# Uncomment the simple dashboard fallback
```

### Panes are too small

**Fix:** Increase terminal window size, then relaunch

Or adjust percentages in the script:
```bash
# Make dashboard larger
tmux split-window -v -p 75  # Dashboard gets 25% instead of 20%

# Make CLI wider
tmux split-window -h -p 60  # CLI gets 40% instead of 33%
```

### Session already exists

**Fix:**
```bash
# Kill old session
tmux kill-session -t dopemux-orchestrator

# Or attach to it
tmux attach -t dopemux-orchestrator
```

### Dashboard not updating

**Check:**
1. Services running? `docker ps`
2. ADHD Engine accessible? `curl localhost:8095/api/v1/energy-level/hue`
3. Activity Capture running? `curl localhost:8096/metrics`

**Restart dashboard pane:**
```
Ctrl+b → → (navigate to dashboard pane)
Ctrl+b x (close pane)
# Manually split and restart:
tmux split-window -v -p 20
python3 scripts/dopemux-compact-dashboard.py show
```

---

## 📊 Comparison: Layouts

| Feature | Full Orchestrator | Minimal | 3-Pane Dashboard |
|---------|------------------|---------|------------------|
| Panes | 4 (dashboard + 3) | 2 (dashboard + CLI) | 3 (side by side) |
| Dashboard | Compact (top) | Compact (top) | Full 3-pane |
| CLI | ✓ Dedicated | ✓ Main pane | ✗ |
| Logs | ✓ Dedicated | ✗ (use CLI) | ✗ |
| Monitoring | ✓ Dedicated | ✗ (use CLI) | ✓ System pane |
| Best for | Full development | Quick tasks | Monitoring only |
| Startup | ~2 seconds | ~1 second | ~1 second |

---

## 🎯 Use Cases

### When to use Full Orchestrator
- Active development sessions (2+ hours)
- Need to monitor logs constantly
- Working on multiple services
- Debugging complex issues
- Team demos/pair programming

### When to use Minimal
- Quick checks (5-15 min)
- Single task focus
- Distraction-sensitive moments
- Low energy state (simpler is better)
- Small terminal window

### When to use 3-Pane Dashboard
- Pure monitoring (no active work)
- Status board on second monitor
- Team visibility dashboard
- System health checks
- Demo/presentation mode

---

## 🎉 Summary

✅ **Full orchestrator layout** (4 panes)
✅ **Minimal layout** (2 panes)
✅ **ADHD dashboard integration** (top pane)
✅ **Pre-configured commands** (CLI pane)
✅ **Log monitoring** (dedicated pane)
✅ **System monitoring** (Typer/Rich or docker watch)
✅ **Makefile integration** (make orchestrator)
✅ **Comprehensive documentation** (this file)

**Launch now:**
```bash
./scripts/launch-dopemux-orchestrator.sh
```

**Built for ADHD developers, by ADHD developers** 🧠⚡
