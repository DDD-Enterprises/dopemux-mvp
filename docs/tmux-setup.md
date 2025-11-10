# Dopemux Tmux Setup Guide

## Overview

This guide documents the ADHD-optimized tmux configuration for the Dopemux development environment, featuring a dynamic status bar and Rich Continuous monitor panes for enhanced workflow awareness.

## Layout Structure

### Status Bar (Bottom)
```
[session-name 🟢 High] Load: 0.5 Dec: 143 Sonnet 4.5 (1M) 🧠
```

- **Left**: Session name + ADHD energy symbol (⚠️ Low, 🟡 Med, 🟢 High from TMUX_ADHD_ENERGY env var)
- **Right**: Cognitive load gauge, ConPort decisions count, Model display with context window, Active pane indicator
- **Refresh**: 10s intervals for low-latency ADHD metrics
- **Colors**: Gruvbox-inspired (colour0 bg, colour4 accents, colour3 warnings)

### Monitor Panes Layout
```
┌─────────────────┬─────────────────┐
│   Worktree      │     Logs        │
│   Monitor       ├─────────────────┤
│                 │   Metrics       │
│                 │   Monitor       │
└─────────────────┴─────────────────┘
```

- **Worktree Monitor (Left)**: Git status + diff summary, updates every 5s via watch
- **Logs Monitor (Top-Right)**: Filtered dopemux.log tail (ERROR/WARN/INFO), continuous updates
- **Metrics Monitor (Bottom-Right)**: ADHD Engine + ConPort API dashboard, updates every 5s via watch

## Setup Instructions

### Prerequisites
- tmux installed
- Dopemux services running (ADHD Engine on port 8080, ConPort on port 5455)
- Scripts in `scripts/` directory (executable permissions set)

### Configuration
1. **Source the config**:
   ```bash
   tmux source-file .tmux.conf
   ```

2. **Set model variables** (in tmux command mode Ctrl-b :):
   ```bash
   :set -g @model "Sonnet 4.5"
   :set -g @ctx_window "1M"
   ```

### Monitor Pane Setup (Manual)
Since tmux layouts vary, use this manual setup for consistent monitoring:

1. **Create worktree pane**:
   ```bash
   :split-window -h
   :send-keys '~/code/dopemux-mvp/scripts/tmux-monitor-worktree.sh; watch -n 5 ~/code/dopemux-mvp/scripts/tmux-monitor-worktree.sh' C-m
   :select-pane -T "monitor:worktree"
   ```

2. **Create logs pane**:
   ```bash
   :split-window -v
   :send-keys '~/code/dopemux-mvp/scripts/tmux-monitor-logs.sh' C-m
   :select-pane -T "monitor:logs"
   ```

3. **Create metrics pane**:
   ```bash
   :split-window -v
   :send-keys '~/code/dopemux-mvp/scripts/tmux-monitor-metrics.sh; watch -n 5 ~/code/dopemux-mvp/scripts/tmux-monitor-metrics.sh' C-m
   :select-pane -T "monitor:metrics"
   ```

### Automated Setup Script
Use `scripts/start-monitors.sh` for a dedicated monitors window (requires tmux session restart for best results).

## Monitor Scripts

### tmux-monitor-worktree.sh
- **Purpose**: Git repository status monitoring
- **Output**: Diff stats + changed file list (top 10)
- **ADHD Benefits**: Quick commit readiness check, reduces status anxiety
- **Refresh**: 5s via watch

### tmux-monitor-logs.sh
- **Purpose**: Application log monitoring with filtering
- **Output**: ERROR/WARN/INFO lines from dopemux.log (last 20)
- **ADHD Benefits**: Urgent-first display, filters noise for critical events
- **Refresh**: Continuous tail

### tmux-monitor-metrics.sh
- **Purpose**: ADHD Engine and ConPort API metrics
- **Output**: Energy/load levels + decisions count
- **ADHD Benefits**: Real-time cognitive state awareness
- **Refresh**: 5s via watch

## ADHD Optimization Features

### Progressive Disclosure
- **Status Bar**: Symbols for instant scan, hover/details on demand
- **Monitors**: Urgent items (errors/high load) prioritized, limited lines prevent overwhelm

### Cognitive Load Management
- **Low-Latency Updates**: 5-10s refreshes match ADHD focus cycles
- **Error Handling**: Graceful fallbacks (e.g., "N/A" if API unavailable)
- **Visual Hierarchy**: Color-coded warnings (yellow/red) for attention prioritization

### Workflow Integration
- **Dopemux Awareness**: Links to ADHD Engine/ConPort for contextual data
- **Session Persistence**: Monitors resume state across tmux sessions
- **Multi-Pane Harmony**: Complements existing orchestrator/sandbox/agent layout

## Performance Considerations

- **CPU Usage**: <5% for all monitors combined
- **Memory**: Minimal (<10MB for scripts + buffers)
- **Network**: API calls use 2s timeouts to avoid blocking
- **Refresh Optimization**: Polled updates prevent continuous process overhead

## Troubleshooting

### Common Issues

**Monitors show "API unavailable"**
- Ensure Dopemux services are running
- Check ports: ADHD Engine (8080), ConPort (5455)
- Verify network connectivity

**Scripts not found**
- Ensure scripts are in `scripts/` and executable: `chmod +x scripts/tmux-monitor-*.sh`
- Use absolute paths if needed: `/full/path/to/scripts/tmux-monitor-worktree.sh`

**Status bar not updating**
- Check refresh interval: `tmux show-options -g status-interval`
- Reload config: `tmux source-file .tmux.conf`

**Pane layout issues**
- Manual setup provides most reliable results
- Avoid complex existing layouts when setting up monitors

### Debug Commands
```bash
# Test scripts individually
~/code/dopemux-mvp/scripts/tmux-monitor-worktree.sh
~/code/dopemux-mvp/scripts/tmux-monitor-metrics.sh

# Check tmux options
tmux show-options -g | grep status
tmux show-options -g | grep @model

# View current pane structure
tmux list-panes
```

## Customization

### Environment Variables
```bash
# Override log file path
export DOPEMUX_LOG_FILE="/custom/path/dopemux.log"

# Set ADHD energy manually
export TMUX_ADHD_ENERGY="med"
```

### Color Customization
Modify `.tmux.conf` status bar colors:
```bash
set-option -g status-style bg=colour0,fg=colour7  # Background/foreground
set-option -g status-left "#[bg=colour4,fg=colour15]..."  # Left section
set-option -g status-right "#[bg=colour0,fg=colour4]..."  # Right section
```

### Refresh Intervals
Adjust in `.tmux.conf`:
```bash
set-option -g status-interval 10  # Status bar refresh (seconds)
# In scripts: watch -n 5 (monitor refresh)
```

## Integration with Dopemux Workflow

- **Session Start**: Source config, set model vars, start monitors
- **Development Flow**: Status bar shows energy/load, monitors provide context
- **Break Management**: Metrics help identify fatigue points
- **Context Preservation**: Monitors maintain awareness across interruptions

## Version History

- **v1.0**: Basic ADHD metrics status bar
- **v2.0**: Rich Continuous monitor panes with API integration
- **Current**: Full dashboard with scripts and documentation

## Support

For issues with tmux configuration, check tmux man pages or GitHub issues. For Dopemux-specific features, refer to project documentation or ADHD Engine API docs.