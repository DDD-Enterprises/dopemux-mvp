#!/bin/bash

# Quick Dopemux + Dashboard Tmux Launcher (minimal version)

cd /Users/hue/code/dopemux-mvp

# Kill existing session if exists
tmux kill-session -t dmx 2>/dev/null

# Create new session with horizontal split
tmux new-session -d -s dmx -n main
tmux send-keys -t dmx:0 "# Dopemux CLI ready" C-m
tmux split-window -h -t dmx:0
tmux send-keys -t dmx:0.1 "python dashboard/coordination_dashboard.py" C-m

# Focus left pane and attach
tmux select-pane -t dmx:0.0
tmux attach-session -t dmx