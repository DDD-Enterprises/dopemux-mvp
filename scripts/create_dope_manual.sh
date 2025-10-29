#!/bin/bash
# Simple DOPE Layout - Manual Creation from OUTSIDE tmux
# Run this from a regular terminal while tmux session exists

SESSION="dopemux"

echo "🎨 Creating DOPE layout panes in session: $SESSION"
echo

# Kill existing session and start fresh
tmux kill-session -t "$SESSION" 2>/dev/null
sleep 1

# Create new session
tmux new-session -d -s "$SESSION"
echo "✅ Created session"

# Split into main areas
# Bottom 25% for agent
tmux split-window -v -t "$SESSION" -p 25
AGENT_PANE=$(tmux list-panes -t "$SESSION" -F "#{pane_id}" | tail -1)

# Top 75% split into monitors (top 20%) and work area (55%)
tmux select-pane -t "$SESSION:0.0"
tmux split-window -v -t "$SESSION:0.0" -p 73

# Split top section for monitors
tmux select-pane -t "$SESSION:0.0"
tmux split-window -h -t "$SESSION:0.0" -p 35

# Create metrics bar below monitors
tmux select-pane -t "$SESSION:0.0"
tmux split-window -v -t "$SESSION:0.0" -p 12

echo "✅ Created monitors and metrics bar"

# Split middle section for orchestrator and sandbox
tmux select-pane -t "$SESSION:0.3"
tmux split-window -h -t "$SESSION:0.3" -p 25

echo "✅ Created orchestrator and sandbox"

# Set pane titles
tmux select-pane -t "$SESSION:0.0" -T "📊 monitor:adhd"
tmux select-pane -t "$SESSION:0.1" -T "⚙️ monitor:system"
tmux select-pane -t "$SESSION:0.2" -T "📈 metrics:bar"
tmux select-pane -t "$SESSION:0.3" -T "🎯 orchestrator:control"
tmux select-pane -t "$SESSION:0.4" -T "🎮 sandbox:shell"
tmux select-pane -t "$SESSION:0.5" -T "🤖 agent:primary"

echo "✅ Set pane titles"

# Apply NEON colors
tmux select-pane -t "$SESSION:0.0" -P 'fg=#020617,bg=#94fadb'  # ADHD - cyan bg
tmux select-pane -t "$SESSION:0.1" -P 'fg=#020617,bg=#f5f26d'  # System - yellow bg
tmux select-pane -t "$SESSION:0.2" -P 'fg=#7dfbf6,bg=#020617'  # Metrics - cyan text
tmux select-pane -t "$SESSION:0.3" -P 'fg=#7dfbf6,bg=#0a1628'  # Orchestrator - cyan/navy
tmux select-pane -t "$SESSION:0.4" -P 'fg=#ff8bd1,bg=#1a0520'  # Sandbox - pink/purple
tmux select-pane -t "$SESSION:0.5" -P 'fg=#94fadb,bg=#041628'  # Agent - teal/blue

echo "✅ Applied NEON colors"

# Focus on orchestrator
tmux select-pane -t "$SESSION:0.3"

# List final layout
echo
echo "📋 Final pane layout:"
tmux list-panes -t "$SESSION" -F "#{pane_index}: #{pane_title} (#{pane_width}x#{pane_height})"

echo
echo "🎉 DOPE Layout created!"
echo
echo "To attach:"
echo "  tmux attach -t $SESSION"
echo
echo "Pane navigation:"
echo "  Ctrl+B then Arrow keys - Move between panes"
echo "  Ctrl+B then q - Show pane numbers"
echo "  Ctrl+B then z - Zoom current pane"
echo
echo "To apply enhancements:"
echo "  bash scripts/enhance_dope_layout.sh"
