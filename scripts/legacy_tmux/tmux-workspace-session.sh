#!/usr/bin/env bash
# Create/switch a dopemux tmux session per workspace and set workspace context
set -euo pipefail

WS_ID="${1:-}"
if [ -z "${WS_ID}" ]; then
  echo "Usage: scripts/tmux-workspace-session.sh <workspace-id>" >&2
  exit 1
fi

SESSION="dopemux-orchestrator-${WS_ID}"
export WORKSPACE_ID="${WS_ID}"

# Create session if missing
if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  tmux new-session -d -s "${SESSION}" -n orchestration
fi

# Set session-scoped workspace variable for statusline and env
tmux set-option -t "${SESSION}" -g @workspace "${WS_ID}"
tmux set-environment -t "${SESSION}" -g WORKSPACE_ID "${WS_ID}"

# Attach or switch
if tmux display-message -p "#S" >/dev/null 2>&1; then
  tmux switch-client -t "${SESSION}"
else
  tmux attach -t "${SESSION}"
fi
