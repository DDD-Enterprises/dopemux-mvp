#!/bin/bash
# Dopemux Path C Migration Status Line
# Shows migration progress, ADHD Engine status, and current phase

# Read JSON input
input=$(cat)

# Extract Claude Code context
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')

# Path C Migration Status (update as we progress)
MIGRATION_PHASE="Week 4 Pre-Day 1"
PROGRESS="67%"
WEEKS_DONE="3/4"

# Check ADHD Engine status
if curl -s http://localhost:8095/health >/dev/null 2>&1; then
    ADHD_STATUS="🟢 ADHD"
else
    ADHD_STATUS="🔴 ADHD"
fi

# Directory with home substitution
dir="${current_dir/$HOME/~}"

# Git info
if [ -d "$current_dir/.git" ]; then
    cd "$current_dir" 2>/dev/null
    git_branch=$(git branch --show-current 2>/dev/null)
    git_status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$git_status" != "0" ]; then
        git_info=" $git_branch ±$git_status"
    else
        git_info=" $git_branch"
    fi
else
    git_info=""
fi

# Build statusline
printf "\033[1;36m%s\033[0m" "$dir"  # Cyan directory
printf "\033[33m%s\033[0m" "$git_info"  # Yellow git
printf " \033[2m|\033[0m "  # Separator
printf "\033[1;35mPath C:\033[0m \033[32m%s\033[0m" "$PROGRESS"  # Migration progress
printf " \033[2m%s\033[0m" "$WEEKS_DONE"  # Weeks done
printf " \033[2m|\033[0m %s" "$ADHD_STATUS"  # ADHD Engine status
printf " \033[2m|\033[0m \033[36m%s\033[0m" "$MIGRATION_PHASE"  # Current phase
printf " \033[2m|\033[0m \033[90m%s\033[0m" "$model_name"  # Model name
