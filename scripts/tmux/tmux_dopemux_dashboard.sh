#!/bin/bash

# Dopemux + Dashboard Tmux Session Launcher
# Creates a split-pane tmux session with dopemux and event dashboard

SESSION_NAME="dopemux-dev"
WORKSPACE="/Users/hue/code/dopemux-mvp"

# Kill existing session if it exists
tmux has-session -t $SESSION_NAME 2>/dev/null
if [ $? == 0 ]; then
    echo "🔄 Killing existing session: $SESSION_NAME"
    tmux kill-session -t $SESSION_NAME
fi

echo "🚀 Starting Dopemux Development Environment"
echo "=========================================="

# Create new tmux session
tmux new-session -d -s $SESSION_NAME -c $WORKSPACE

# Rename first window
tmux rename-window -t $SESSION_NAME:0 'DopemuxDev'

# First pane (left): Dopemux CLI
tmux send-keys -t $SESSION_NAME:0 "cd $WORKSPACE" C-m
tmux send-keys -t $SESSION_NAME:0 "clear" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '🧠 Dopemux CLI Ready'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '=========================================='" C-m
tmux send-keys -t $SESSION_NAME:0 "echo 'Commands:'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '  dopemux status    - Show instance status'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '  dopemux list      - List all instances'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '  dopemux start     - Start an instance'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '=========================================='" C-m
tmux send-keys -t $SESSION_NAME:0 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0 "# Ready for dopemux commands" C-m

# Split window vertically (creates right pane)
tmux split-window -h -t $SESSION_NAME:0 -c $WORKSPACE

# Second pane (right): Dashboard
tmux send-keys -t $SESSION_NAME:0.1 "cd $WORKSPACE" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '📊 Starting Coordination Dashboard...'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '=========================================='" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo 'Dashboard will be available at:'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '  http://localhost:8090'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo 'Redis Commander available at:'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '  http://localhost:8081'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '=========================================='" C-m
tmux send-keys -t $SESSION_NAME:0.1 "sleep 2" C-m
tmux send-keys -t $SESSION_NAME:0.1 "python dashboard/coordination_dashboard.py" C-m

# Set pane titles (requires tmux 2.3+)
tmux select-pane -t $SESSION_NAME:0.0 -T "Dopemux CLI"
tmux select-pane -t $SESSION_NAME:0.1 -T "Event Dashboard"

# Enable pane borders and titles
tmux set-option -t $SESSION_NAME pane-border-status top
tmux set-option -t $SESSION_NAME pane-border-format "#{pane_index}: #{pane_title}"

# Focus on left pane (Dopemux CLI)
tmux select-pane -t $SESSION_NAME:0.0

# Attach to session
echo "✅ Attaching to tmux session: $SESSION_NAME"
echo ""
echo "📝 Tmux Key Bindings:"
echo "  Ctrl+b %     - Split vertically"
echo "  Ctrl+b \"     - Split horizontally"
echo "  Ctrl+b ←/→   - Switch panes"
echo "  Ctrl+b d     - Detach from session"
echo "  Ctrl+b x     - Kill current pane"
echo ""

tmux attach-session -t $SESSION_NAME