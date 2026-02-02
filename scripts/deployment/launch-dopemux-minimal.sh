#!/bin/bash
#
# Minimal Dopemux Orchestrator Layout
# ====================================
#
# Quick launcher with just the essentials:
#   - ADHD Dashboard (top, compact)
#   - CLI (main work area)
#

SESSION="dmx"

# Kill existing
tmux kill-session -t $SESSION 2>/dev/null

cd /Users/hue/code/dopemux-mvp

# Create session
tmux new-session -d -s $SESSION -n main

# Split: top 20% for dashboard, bottom 80% for work
tmux split-window -v -p 80 -t $SESSION:0

# Top pane: ADHD Dashboard
if [ -f scripts/dopemux-compact-dashboard.py ]; then
    tmux send-keys -t $SESSION:0.0 "python3 scripts/dopemux-compact-dashboard.py show" C-m
else
    tmux send-keys -t $SESSION:0.0 "while true; do clear; echo '🧠 ADHD Dashboard'; date; sleep 5; done" C-m
fi

# Bottom pane: CLI
tmux send-keys -t $SESSION:0.1 "echo '🚀 Dopemux CLI Ready'; echo 'Run: docker-compose up -d'" C-m

# Set pane titles
tmux set-option -t $SESSION pane-border-status top
tmux select-pane -t $SESSION:0.0 -T "🧠 Dashboard"
tmux select-pane -t $SESSION:0.1 -T "CLI"

# Focus CLI and attach
tmux select-pane -t $SESSION:0.1
tmux attach-session -t $SESSION
