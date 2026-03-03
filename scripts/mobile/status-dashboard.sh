#!/bin/bash
# status-dashboard.sh: Mobile-optimized status dashboard for window 1.

# Ensure we're in the repo root
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO_ROOT"

while true; do
    clear
    echo "=== dNh_CRM Status Dashboard ==="
    date
    echo ""
    
    echo "--- Repository Context ---"
    if [ -d .git ]; then
        git branch --show-current | xargs echo "Branch:"
        git log -1 --oneline | xargs echo "Last Commit:"
    else
        echo "Not a git repository."
    fi
    echo ""
    
    echo "--- Services (Docker) ---"
    docker ps --format "table {{.Names}}	{{.Status}}" | head -n 5
    echo ""
    
    echo "--- Active TPs ---"
    find workspace/handoff/03_implementation -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | xargs echo "In Implementation:"
    find workspace/handoff/01_planning -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | xargs echo "In Planning:"
    echo ""
    
    echo "--- Recent Logs (Errors) ---"
    # Placeholder for log tailing
    echo "No errors detected (mock)."
    
    sleep 2
done
