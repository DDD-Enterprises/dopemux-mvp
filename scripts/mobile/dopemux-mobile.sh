#!/bin/bash
#
# dopemux-mobile.sh: Starts or attaches to the dopemux mobile session.
#
# This script sets up a predefined tmux workspace tailored for mobile development.
# It uses a dedicated socket (-L) to avoid conflicts with other tmux sessions.
#
# Usage:
#   ./dopemux-mobile.sh
#

set -e

SOCKET_NAME="dopemux-mobile"
SESSION_NAME="dopemux-mobile"

# Path logic: prefer local repo config, fallback to $HOME/.tmux.mobile.conf
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
LOCAL_CONFIG="$REPO_ROOT/configs/mobile/tmux.mobile.conf"
HOME_CONFIG="$HOME/.tmux.mobile.conf"

if [ -f "$LOCAL_CONFIG" ]; then
    CONFIG_FILE="$LOCAL_CONFIG"
elif [ -f "$HOME_CONFIG" ]; then
    CONFIG_FILE="$HOME_CONFIG"
else
    echo "Error: Tmux config file not found at $LOCAL_CONFIG or $HOME_CONFIG"
    exit 1
fi

# Check if the session already exists on the specific socket.
if ! tmux -L "$SOCKET_NAME" has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Creating new dopemux-mobile session..."

    # Start a new, detached session with the first window named "Control".
    tmux -L "$SOCKET_NAME" -f "$CONFIG_FILE" new-session -d -s "$SESSION_NAME" -n "Control"

    # Create the remaining windows.
    tmux -L "$SOCKET_NAME" new-window -t "$SESSION_NAME":1 -n "Status"
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":1 "$REPO_ROOT/scripts/mobile/status-dashboard.sh" C-m
    
    tmux -L "$SOCKET_NAME" new-window -t "$SESSION_NAME":2 -n "Logs"
    # Placeholder for logs window
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":2 "echo 'LOGS WINDOW (Tail your logs here)'" C-m
    
    tmux -L "$SOCKET_NAME" new-window -t "$SESSION_NAME":3 -n "Claude"
    # Special split: Supervisor on top (0), Implementer on bottom (1)
    tmux -L "$SOCKET_NAME" split-window -v -t "$SESSION_NAME":3.0 -l 10
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":3.0 "$REPO_ROOT/scripts/mobile/supervisor-context.sh" C-m
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":3.1 "echo 'IMPLEMENTER PANE: Run your agent/editor here'" C-m

    tmux -L "$SOCKET_NAME" new-window -t "$SESSION_NAME":4 -n "Tasks"
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":4 "ls workspace/handoff" C-m

    tmux -L "$SOCKET_NAME" new-window -t "$SESSION_NAME":5 -n "Editor"
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":5 "nvim" C-m

    tmux -L "$SOCKET_NAME" new-window -t "$SESSION_NAME":6 -n "Monitor"
    tmux -L "$SOCKET_NAME" send-keys -t "$SESSION_NAME":6 "top" C-m

    # Select the "Control" window as the starting point.
    tmux -L "$SOCKET_NAME" select-window -t "$SESSION_NAME":0
    echo "Session created."
else
    echo "Attaching to existing dopemux-mobile session..."
fi

# Attach to the session, using the correct socket.
exec tmux -L "$SOCKET_NAME" attach-session -t "$SESSION_NAME"
