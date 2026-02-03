#!/bin/bash
# Quick Enhancements for DOPE Layout
# Run this after starting dopemux to add extra features

echo "🎨 Applying DOPE Layout Enhancements..."

# Get the current tmux session name
SESSION="${1:-dopemux}"

# Enhancement: Add git branch to status bar (update interval 5s)
tmux set-option -g status-interval 5

# Enhancement: Add pane resize hotkeys
tmux bind-key -n C-M-Left resize-pane -L 5
tmux bind-key -n C-M-Right resize-pane -R 5
tmux bind-key -n C-M-Up resize-pane -U 2
tmux bind-key -n C-M-Down resize-pane -D 2

echo "✅ Added resize hotkeys: Ctrl+Alt+Arrows"

# Enhancement: Add pane swap hotkeys
tmux bind-key -n C-S-Left swap-pane -U
tmux bind-key -n C-S-Right swap-pane -D

echo "✅ Added pane swap: Ctrl+Shift+Arrows"

# Enhancement: Add zoom toggle
tmux bind-key -n C-M-z resize-pane -Z

echo "✅ Added zoom toggle: Ctrl+Alt+Z"

# Enhancement: Better mouse support
tmux set-option -g mouse on

echo "✅ Enabled mouse support"

# Enhancement: Increase scrollback
tmux set-option -g history-limit 50000

echo "✅ Increased scrollback to 50000 lines"

# Enhancement: Better copy mode
tmux set-option -g mode-keys vi
tmux bind-key -T copy-mode-vi v send-keys -X begin-selection
tmux bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel

echo "✅ Configured vi-style copy mode"

# Enhancement: Status bar update with git branch (for current session)
GIT_STATUS="#(cd #{pane_current_path}; git branch --show-current 2>/dev/null | sed 's/.*/🌿 &/' || echo '📂')"

# Get current status-right and prepend git branch
CURRENT_STATUS=$(tmux show-option -gqv status-right)
NEW_STATUS="${GIT_STATUS} ${CURRENT_STATUS}"
tmux set-option -g status-right "$NEW_STATUS"

echo "✅ Added git branch to status bar"

# Enhancement: Pane border colors based on focus
tmux set-hook -g pane-focus-in 'run-shell "tmux select-pane -P bg=#0a1628"'
tmux set-hook -g pane-focus-out 'run-shell "tmux select-pane -P bg=#020617"'

echo "✅ Added focus-based pane highlighting"

echo ""
echo "🎉 All enhancements applied!"
echo ""
echo "New hotkeys:"
echo "  Ctrl+Alt+Arrows  - Resize panes"
echo "  Ctrl+Shift+Arrows - Swap panes"
echo "  Ctrl+Alt+Z       - Toggle pane zoom"
echo "  Mouse            - Click, drag, scroll"
echo ""
echo "Status bar now shows:"
echo "  🌿 - Current git branch"
echo "  📂 - No git repo"
echo ""
