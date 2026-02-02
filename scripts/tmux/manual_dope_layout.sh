#!/bin/bash
# Manual DOPE Layout Creation Script
# Run this INSIDE your tmux session to add the missing panes

echo "🎨 Manually creating DOPE layout panes..."
echo

# Get the current pane ID
CURRENT_PANE=$(tmux display-message -p '#{pane_id}')
echo "📍 Starting from pane: $CURRENT_PANE"

# Assuming you have orchestrator and agent already
# Let's create the full layout manually

echo
echo "Creating monitor panes at top..."

# Create top section for monitors by splitting current pane
tmux split-window -v -t "$CURRENT_PANE" -p 80

# Get the new bottom pane
BOTTOM_PANE=$(tmux display-message -p '#{pane_id}')

# Now split the top for monitors
tmux select-pane -t "$CURRENT_PANE"
tmux split-window -h -p 35

# Label the monitors
MONITOR_LEFT=$(tmux display-message -t "{left}" -p '#{pane_id}')
MONITOR_RIGHT=$(tmux display-message -t "{right}" -p '#{pane_id}')

echo "✅ Created monitors"

# Create metrics bar below monitors
tmux select-pane -t "$MONITOR_LEFT"
tmux split-window -v -p 10

METRICS_BAR=$(tmux display-message -p '#{pane_id}')
echo "✅ Created metrics bar"

# Create middle section (orchestrator + sandbox)
# Select the pane below metrics
tmux select-pane -D

# Split for sandbox on right
tmux split-window -h -p 25

ORCHESTRATOR=$(tmux display-message -t "{left}" -p '#{pane_id}')
SANDBOX=$(tmux display-message -t "{right}" -p '#{pane_id}')

echo "✅ Created orchestrator and sandbox"

# The bottom should be agents already
echo "✅ Agent pane already exists"

# Set pane titles with emojis
tmux select-pane -t "$MONITOR_LEFT" -T "📊 monitor:adhd"
tmux select-pane -t "$MONITOR_RIGHT" -T "⚙️ monitor:system"
tmux select-pane -t "$METRICS_BAR" -T "📈 metrics:bar"
tmux select-pane -t "$ORCHESTRATOR" -T "🎯 orchestrator:control"
tmux select-pane -t "$SANDBOX" -T "🎮 sandbox:shell"

echo "✅ Set pane titles"

# Apply NEON colors
echo
echo "Applying NEON theme colors..."

# Orchestrator (cyan on dark navy)
tmux select-pane -t "$ORCHESTRATOR" -P 'fg=#7dfbf6,bg=#0a1628'

# Sandbox (pink on dark purple)
tmux select-pane -t "$SANDBOX" -P 'fg=#ff8bd1,bg=#1a0520'

# Metrics bar (cyan on very dark)
tmux select-pane -t "$METRICS_BAR" -P 'fg=#7dfbf6,bg=#020617'

echo "✅ Applied colors"

# Focus on orchestrator
tmux select-pane -t "$ORCHESTRATOR"

echo
echo "🎉 DOPE Layout created manually!"
echo
echo "Panes:"
echo "  📊 Monitor (ADHD) - Top left"
echo "  ⚙️ Monitor (System) - Top right"
echo "  📈 Metrics Bar - Below monitors"
echo "  🎯 Orchestrator - Middle left (HUGE!)"
echo "  🎮 Sandbox - Middle right"
echo "  🤖 Agent - Bottom"
echo
echo "Try: bash scripts/enhance_dope_layout.sh to add hotkeys"
