#!/bin/bash
# supervisor-context.sh: Supervisor-level context for the top pane of window 3 (Claude).

# Ensure we're in the repo root
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO_ROOT"

while true; do
    clear
    echo "=== SUPERVISOR CONTEXT ==="
    
    if [ -d .git ]; then
        git branch --show-current | xargs echo "Branch:"
        git status --porcelain | wc -l | xargs echo "Staged/Unstaged changes:"
    else
        echo "Not a git repository."
    fi
    echo ""
    
    # Check current active TP from implementation queue
    CURRENT_TP=$(ls workspace/handoff/03_implementation | head -n 1)
    if [ -n "$CURRENT_TP" ]; then
        echo "Active TP: $CURRENT_TP"
        # Try to show intent
        if [ -f "workspace/handoff/03_implementation/$CURRENT_TP/TP.json" ]; then
            grep -o '"intent": "[^"]*"' "workspace/handoff/03_implementation/$CURRENT_TP/TP.json" | cut -d '"' -f 4 | head -n 1
        fi
    else
        echo "No active TP in implementation."
    fi
    echo ""
    
    # Audit status placeholder
    echo "Audit status: READY"
    
    sleep 5
done
