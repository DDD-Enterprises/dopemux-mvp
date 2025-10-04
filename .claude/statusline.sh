#!/bin/bash
# Dopemux ADHD-Optimized Statusline
# Shows: focus, session time, ADHD Engine, context %, model

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

# Directory and git
dir=$(basename "$current_dir")
[ -z "$dir" ] && dir="~"

git_branch=""
if [ -d "$current_dir/.git" ]; then
    cd "$current_dir" 2>/dev/null
    git_branch=$(git branch --show-current 2>/dev/null)
fi

# Get ConPort status (active context + connection health)
CONPORT_STATUS="📴"  # Disconnected
FOCUS=""
SESSION_INFO=""
if command -v uvx >/dev/null 2>&1; then
    conport_output=$(timeout 0.8s uvx --from context-portal-mcp conport-mcp \
        get-active-context --workspace-id "$current_dir" 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$conport_output" ]; then
        CONPORT_STATUS="📊"  # Connected

        # Extract focus (truncate to 35 chars)
        focus_raw=$(echo "$conport_output" | jq -r '.current_focus // ""' 2>/dev/null)
        if [ -n "$focus_raw" ] && [ "$focus_raw" != "null" ]; then
            FOCUS=$(echo "$focus_raw" | cut -c1-35)
            [ ${#focus_raw} -gt 35 ] && FOCUS="${FOCUS}..."
        fi

        # Calculate session time in 25min chunks
        session_start=$(echo "$conport_output" | jq -r '.session_start // ""' 2>/dev/null)
        if [ -n "$session_start" ] && [ "$session_start" != "null" ]; then
            now=$(date +%s)
            start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${session_start%.*}" +%s 2>/dev/null || echo "$now")
            session_min=$(( (now - start_epoch) / 60 ))
            chunks=$(( session_min / 25 ))
            remain=$(( session_min % 25 ))
            SESSION_INFO="${chunks}×25+${remain}m"
        fi
    fi
fi

# ADHD Engine comprehensive status (single /health call for efficiency)
ADHD_STATUS="💤"
ENERGY_SYMBOL=""
ATTENTION_SYMBOL=""
BREAK_WARNING=""
ACCOMMODATIONS=""

# Get terminal width for progressive disclosure
term_width=$(tput cols 2>/dev/null || echo 120)

# Query ADHD Engine health (single call, all data)
adhd_health=$(timeout 0.4s curl -s http://localhost:8095/health 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$adhd_health" ]; then
    ADHD_STATUS="🧠"

    # Extract energy level
    energy=$(echo "$adhd_health" | jq -r '.current_state.energy_levels.current_user // ""' 2>/dev/null)
    if [ -n "$energy" ] && [ "$energy" != "null" ]; then
        case "$energy" in
            "hyperfocus") ENERGY_SYMBOL="⚡" ;;
            "high") ENERGY_SYMBOL="↑" ;;
            "medium") ENERGY_SYMBOL="=" ;;  # Always show
            "low") ENERGY_SYMBOL="↓" ;;
            "very_low") ENERGY_SYMBOL="⇣" ;;
        esac
    fi

    # Extract attention state (NEW)
    attention=$(echo "$adhd_health" | jq -r '.current_state.attention_states.current_user // ""' 2>/dev/null)
    if [ -n "$attention" ] && [ "$attention" != "null" ]; then
        case "$attention" in
            "hyperfocused") ATTENTION_SYMBOL="·👁️✨" ;;  # Always celebrate hyperfocus!
            "focused") ATTENTION_SYMBOL="·👁️" ;;  # Always show (good state worth seeing)
            "transitioning") [ "$term_width" -ge 90 ] && ATTENTION_SYMBOL="·👁️~" ;;  # Show if space
            "scattered") ATTENTION_SYMBOL="·👁️🌀" ;;  # Always show warning
            "overwhelmed") ATTENTION_SYMBOL="·👁️💥" ;;  # Always show alert
        esac
    fi

    # Check break recommendations (NEW)
    breaks_suggested=$(echo "$adhd_health" | jq -r '.accommodation_stats.breaks_suggested // 0' 2>/dev/null)
    active_accommodations=$(echo "$adhd_health" | jq -r '.current_state.active_accommodations.current_user // 0' 2>/dev/null)

    # Check if break needed by looking at active accommodations or stats
    if [ "$active_accommodations" -gt 0 ] || [ "$breaks_suggested" -gt 0 ]; then
        # Check if it's urgent (would need to query Redis, so use heuristic)
        if [ "$energy" = "very_low" ] || [ "$energy" = "low" ]; then
            BREAK_WARNING=" \033[31m☕!\033[0m"  # Red urgent
        else
            BREAK_WARNING=" \033[33m☕\033[0m"   # Yellow soon
        fi
    fi

    # Check for active protection (NEW)
    hyperfocus_protections=$(echo "$adhd_health" | jq -r '.accommodation_stats.hyperfocus_protections // 0' 2>/dev/null)
    if [ "$hyperfocus_protections" -gt 0 ] && [ "$attention" = "hyperfocused" ]; then
        ACCOMMODATIONS="·🛡️"
    fi
fi

# Build statusline
printf "\033[1;36m%s\033[0m" "$dir"

# Git branch + changes
if [ -n "$git_branch" ]; then
    printf " \033[33m%s%s\033[0m" "$git_branch" "$git_changes"
fi

printf " \033[2m|\033[0m"

# ConPort status
printf " %s" "$CONPORT_STATUS"

# Focus (if available)
if [ -n "$FOCUS" ]; then
    printf " \033[35m%s\033[0m" "$FOCUS"
fi

# Session time (if available)
if [ -n "$SESSION_INFO" ]; then
    printf " \033[36m[%s]\033[0m" "$SESSION_INFO"
fi

printf " \033[2m|\033[0m"

# ADHD Engine + energy + attention + warnings
printf " %s" "$ADHD_STATUS"
if [ -n "$ENERGY_SYMBOL" ]; then
    printf "%s" "$ENERGY_SYMBOL"
fi
if [ -n "$ATTENTION_SYMBOL" ]; then
    printf "%s" "$ATTENTION_SYMBOL"
fi
if [ -n "$BREAK_WARNING" ]; then
    printf "%s" "$BREAK_WARNING"
fi
if [ -n "$ACCOMMODATIONS" ]; then
    printf "%s" "$ACCOMMODATIONS"
fi

# Context usage (color coded)
if [ "$context_pct" -lt 60 ]; then
    printf " \033[32m%d%%\033[0m" "$context_pct"
elif [ "$context_pct" -lt 80 ]; then
    printf " \033[33m%d%%\033[0m" "$context_pct"
else
    printf " \033[31m%d%%\033[0m" "$context_pct"
fi

# Model
printf " \033[2m|\033[0m \033[90m%s\033[0m" "$model_name"
