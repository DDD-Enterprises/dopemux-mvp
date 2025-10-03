#!/bin/bash
# Dopemux ADHD-Optimized Statusline

# Read JSON input
input=$(cat)

# Extract with safe defaults
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // "."' 2>/dev/null)
[ -z "$current_dir" ] && current_dir="."

model_name=$(echo "$input" | jq -r '.model.display_name // .model.name // "Sonnet"' 2>/dev/null)
[ -z "$model_name" ] && model_name="Sonnet"

claude_version=$(echo "$input" | jq -r '.version // "2.x"' 2>/dev/null)
[ -z "$claude_version" ] && claude_version="2.x"

context_used=$(echo "$input" | jq -r '.context.used // 0' 2>/dev/null)
[ -z "$context_used" ] && context_used=0

context_total=$(echo "$input" | jq -r '.context.total // 1000000' 2>/dev/null)
[ -z "$context_total" ] && context_total=1000000

# Calculate context percentage
context_pct=$((context_used * 100 / context_total))

# Directory
dir=$(basename "$current_dir")
[ -z "$dir" ] && dir="~"

# Git branch
git_branch=""
if [ -d "$current_dir/.git" ]; then
    cd "$current_dir" 2>/dev/null
    git_branch=$(git branch --show-current 2>/dev/null)
fi

# ADHD Engine status
ADHD_STATUS="💤"
if timeout 0.2s curl -s http://localhost:8095/health >/dev/null 2>&1; then
    ADHD_STATUS="🧠"
fi

# Build statusline (simplified, fast)
printf "\033[1;36m%s\033[0m" "$dir"

if [ -n "$git_branch" ]; then
    printf " \033[33m%s\033[0m" "$git_branch"
fi

printf " \033[2m|\033[0m %s" "$ADHD_STATUS"

# Context usage (color coded)
if [ "$context_pct" -lt 60 ]; then
    printf " \033[2m|\033[0m \033[32m%d%%\033[0m" "$context_pct"
elif [ "$context_pct" -lt 80 ]; then
    printf " \033[2m|\033[0m \033[33m%d%%\033[0m" "$context_pct"
else
    printf " \033[2m|\033[0m \033[31m%d%%\033[0m" "$context_pct"
fi

# Model
printf " \033[2m|\033[0m \033[90m%s v%s\033[0m" "$model_name" "$claude_version"
