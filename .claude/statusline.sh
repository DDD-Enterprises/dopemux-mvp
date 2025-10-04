#!/bin/bash
# Dopemux ADHD-Optimized Statusline
# Shows: focus, session time, ADHD Engine, context %, model

# Read JSON input
input=$(cat)

# Debug logging (uncomment to diagnose token extraction issues)
# echo "$input" > /tmp/statusline_debug.json
# echo "$(date) - context_used: $(echo "$input" | jq -r '.context.used // .tokens.used // .usage.input_tokens // .token_count.input // 0' 2>/dev/null)" >> /tmp/statusline_debug.log
# echo "$(date) - context_total: $(echo "$input" | jq -r '.context.total // .tokens.total // .usage.max_tokens // .token_count.max' 2>/dev/null)" >> /tmp/statusline_debug.log

# Extract with safe defaults
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // "."' 2>/dev/null)
[ -z "$current_dir" ] && current_dir="."

model_name=$(echo "$input" | jq -r '.model.display_name // .model.name // "Sonnet"' 2>/dev/null)
[ -z "$model_name" ] && model_name="Sonnet"

claude_version=$(echo "$input" | jq -r '.version // "2.x"' 2>/dev/null)
[ -z "$claude_version" ] && claude_version="2.x"

# Extract transcript path for token calculation
transcript_path=$(echo "$input" | jq -r '.transcript_path // ""' 2>/dev/null)

# Calculate cumulative token usage from transcript (fast, accurate)
if [ -f "$transcript_path" ]; then
    # Get most recent cache_read (current cached prompt size)
    cache_read=$(tac "$transcript_path" | jq -r '.message.usage.cache_read_input_tokens // 0' 2>/dev/null | grep -v '^0$' | head -1)
    [ -z "$cache_read" ] && cache_read=0

    # Sum all output_tokens (conversation history)
    output_total=$(jq -r '.message.usage.output_tokens // 0' "$transcript_path" 2>/dev/null | awk '{sum+=$1} END {print int(sum)}')
    [ -z "$output_total" ] && output_total=0

    # Get latest input_tokens (current user message)
    latest_input=$(tac "$transcript_path" | jq -r '.message.usage.input_tokens // 0' 2>/dev/null | grep -v '^0$' | head -1)
    [ -z "$latest_input" ] && latest_input=0

    # Context = current cached prompt + all outputs + current input
    # Note: cache_read already includes previous inputs, so we only add the LATEST input
    context_used=$((cache_read + output_total + latest_input))
else
    # Fallback: try JSON paths (likely won't work, but try anyway)
    context_used=$(echo "$input" | jq -r '.context.used // .tokens.used // 0' 2>/dev/null)
    [ -z "$context_used" ] || [ "$context_used" = "null" ] && context_used=0
fi

# Detect context window from model ID (more reliable than display_name)
model_id=$(echo "$input" | jq -r '.model.id // ""' 2>/dev/null)
context_total=200000  # Default for most models

case "$model_id" in
    *"opus"*)
        # Opus models: 200K
        context_total=200000
        ;;
    *"sonnet-4-5"*|*"sonnet-4.5"*)
        # Sonnet 4.5: Check if extended context variant
        # Most are 200K, some regions have 1M
        # Use JSON if provided, otherwise assume 200K
        json_total=$(echo "$input" | jq -r '.context.total // .tokens.total // 0' 2>/dev/null)
        if [ "$json_total" -gt 200000 ]; then
            context_total=$json_total
        else
            context_total=200000
        fi
        ;;
    *"sonnet"*|*"haiku"*)
        # Other Claude models: 200K
        context_total=200000
        ;;
    *)
        # Unknown model: try JSON, fallback to 200K
        json_total=$(echo "$input" | jq -r '.context.total // .tokens.total // 0' 2>/dev/null)
        [ "$json_total" -gt 0 ] && context_total=$json_total || context_total=200000
        ;;
esac

# Calculate context percentage (avoid division by zero)
if [ "$context_total" -gt 0 ]; then
    context_pct=$((context_used * 100 / context_total))
else
    context_pct=0
fi

# Directory and git
dir=$(basename "$current_dir")
[ -z "$dir" ] && dir="~"

git_branch=""
if [ -d "$current_dir/.git" ]; then
    cd "$current_dir" 2>/dev/null
    git_branch=$(git branch --show-current 2>/dev/null)
fi

# Get ConPort status via direct SQLite query (ultra-fast, no HTTP needed)
CONPORT_STATUS="⚠️"  # Disconnected
FOCUS=""
SESSION_INFO=""

# ConPort SQLite database path
conport_db="$current_dir/context_portal/context.db"

if [ -f "$conport_db" ] && command -v sqlite3 >/dev/null 2>&1; then
    # Query active_context table (singleton, no workspace_id needed)
    conport_data=$(sqlite3 "$conport_db" "SELECT content FROM active_context LIMIT 1" 2>/dev/null)

    if [ -n "$conport_data" ]; then
        CONPORT_STATUS="✅"  # Connected

        # Extract current_focus from JSON (use jq if available, otherwise basic parsing)
        focus_raw=$(echo "$conport_data" | jq -r '.current_focus // ""' 2>/dev/null)
        if [ -n "$focus_raw" ] && [ "$focus_raw" != "null" ] && [ "$focus_raw" != "" ]; then
            FOCUS=$(echo "$focus_raw" | cut -c1-35)
            [ ${#focus_raw} -gt 35 ] && FOCUS="${FOCUS}..."
        fi

        # Calculate session time (sexy, intuitive format)
        session_start=$(echo "$conport_data" | jq -r '.session_start // ""' 2>/dev/null)
        if [ -n "$session_start" ] && [ "$session_start" != "null" ] && [ "$session_start" != "" ]; then
            now=$(date +%s)
            # Remove Z suffix and any fractional seconds for parsing
            clean_time="${session_start%Z}"
            clean_time="${clean_time%.*}"
            start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$clean_time" +%s 2>/dev/null || echo "$now")
            session_sec=$(( now - start_epoch ))

            # Only show positive elapsed time
            if [ "$session_sec" -gt 0 ]; then
                session_min=$(( session_sec / 60 ))
                hours=$(( session_min / 60 ))
                mins=$(( session_min % 60 ))

                # Format: "1h 23m" or just "23m" if under 1 hour
                if [ "$hours" -gt 0 ]; then
                    SESSION_INFO="${hours}h ${mins}m"
                else
                    SESSION_INFO="${mins}m"
                fi
            fi
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

    # Extract energy level - lightning bolt + direction
    energy=$(echo "$adhd_health" | jq -r '.current_state.energy_levels.current_user // ""' 2>/dev/null)
    if [ -n "$energy" ] && [ "$energy" != "null" ]; then
        case "$energy" in
            "hyperfocus") ENERGY_SYMBOL="⚡⚡" ;;  # Double lightning for hyperfocus
            "high") ENERGY_SYMBOL="⚡↑" ;;
            "medium") ENERGY_SYMBOL="⚡=" ;;  # Balanced/level
            "low") ENERGY_SYMBOL="⚡↓" ;;
            "very_low") ENERGY_SYMBOL="⚡⇣" ;;
        esac
    fi

    # Extract attention state - eye + state indicator
    attention=$(echo "$adhd_health" | jq -r '.current_state.attention_states.current_user // ""' 2>/dev/null)
    if [ -n "$attention" ] && [ "$attention" != "null" ]; then
        case "$attention" in
            "hyperfocused") ATTENTION_SYMBOL="👁️✨" ;;  # Eye with sparkles for hyperfocus
            "focused") ATTENTION_SYMBOL="👁️●" ;;  # Eye with solid dot for focused
            "transitioning") [ "$term_width" -ge 90 ] && ATTENTION_SYMBOL="👁️~" ;;  # Eye with wave for shifting
            "scattered") ATTENTION_SYMBOL="👁️🌀" ;;  # Eye with spiral for scattered
            "overwhelmed") ATTENTION_SYMBOL="👁️💥" ;;  # Eye with explosion for overwhelmed
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

    # Check for active protection
    hyperfocus_protections=$(echo "$adhd_health" | jq -r '.accommodation_stats.hyperfocus_protections // 0' 2>/dev/null)
    if [ "$hyperfocus_protections" -gt 0 ] && [ "$attention" = "hyperfocused" ]; then
        ACCOMMODATIONS="🛡️"  # Shield for hyperfocus protection
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

# ADHD Engine - compact emoji state
printf " %s" "$ADHD_STATUS"
if [ -n "$ENERGY_SYMBOL" ]; then
    printf " %s" "$ENERGY_SYMBOL"
fi
if [ -n "$ATTENTION_SYMBOL" ]; then
    printf " %s" "$ATTENTION_SYMBOL"
fi
if [ -n "$ACCOMMODATIONS" ]; then
    printf " %s" "$ACCOMMODATIONS"
fi
if [ -n "$BREAK_WARNING" ]; then
    printf "%s" "$BREAK_WARNING"
fi

# Context usage (show tokens + percentage, color coded)
# Convert to K format for readability (e.g., 86K/200K)
used_k=$(( context_used / 1000 ))
total_k=$(( context_total / 1000 ))

if [ "$context_pct" -lt 60 ]; then
    printf " \033[32m%dK/%dK (%d%%)\033[0m" "$used_k" "$total_k" "$context_pct"
elif [ "$context_pct" -lt 80 ]; then
    printf " \033[33m%dK/%dK (%d%%)\033[0m" "$used_k" "$total_k" "$context_pct"
else
    printf " \033[31m%dK/%dK (%d%%)\033[0m" "$used_k" "$total_k" "$context_pct"
fi

# Model
printf " \033[2m|\033[0m \033[90m%s\033[0m" "$model_name"
