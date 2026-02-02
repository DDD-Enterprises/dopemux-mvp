#!/bin/bash
#
# Dopemux ADHD Dashboard - Tmux Top Pane Setup
# =============================================
#
# Splits current tmux window to add compact ADHD dashboard at top
#

SESSION=$(tmux display-message -p '#S')
WINDOW=$(tmux display-message -p '#I')

echo "🚀 Setting up Dopemux ADHD Dashboard in top pane..."

# Split window horizontally (top/bottom)
# -v = vertical split (creates top/bottom panes)
# -p 20 = top pane gets 20% of height (about 4-5 lines)
tmux split-window -v -p 20 -t "$SESSION:$WINDOW"

# Move focus to top pane
tmux select-pane -t 0

# Launch compact dashboard in top pane
tmux send-keys "python3 scripts/dopemux-compact-dashboard.py show --mode all" C-m

# Move focus back to bottom pane (main work area)
tmux select-pane -t 1

echo "✅ Dashboard added to top pane!"
echo ""
echo "Controls:"
echo "  Ctrl+b ↑/↓  : Switch between panes"
echo "  Ctrl+b q    : Show pane numbers"
echo "  Ctrl+b x    : Close dashboard pane"
echo ""
echo "Top pane shows:"
echo "  Line 1: Cognitive state (energy, session, health)"
echo "  Line 2: Untracked work warnings"
echo "  Line 3: Active tasks from Leantime"
