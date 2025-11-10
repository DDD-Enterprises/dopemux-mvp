#!/bin/bash
# Start Rich Continuous Monitors for Dopemux tmux
# Creates a new window with monitor panes

# Ensure session exists
tmux has-session -t dopemux 2>/dev/null || tmux new-session -d -s dopemux

# Create new window for monitors
tmux new-window -t dopemux -n monitors

# Set up worktree monitor (left pane)
tmux send-keys -t dopemux:monitors '~/scripts/tmux-monitor-worktree.sh; watch -n 5 ~/scripts/tmux-monitor-worktree.sh' C-m
tmux select-pane -T "monitor:worktree"

# Split for logs monitor (top-right)
tmux split-window -h -t dopemux:monitors
tmux send-keys -t dopemux:monitors.1 '~/scripts/tmux-monitor-logs.sh' C-m
tmux select-pane -T "monitor:logs"

# Split for metrics monitor (bottom-right)
tmux split-window -v -t dopemux:monitors.1
tmux send-keys -t dopemux:monitors.2 '~/scripts/tmux-monitor-metrics.sh; watch -n 5 ~/scripts/tmux-monitor-metrics.sh' C-m
tmux select-pane -T "monitor:metrics"

echo "Dopemux monitors started in 'monitors' window. Switch with: tmux select-window -t dopemux:monitors"