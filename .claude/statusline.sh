#!/bin/bash
# Dopemux ADHD-Optimized Statusline
# Shows: focus, session time, ADHD Engine, context %, model

# Read JSON input
input=$(cat)

# Determine repository root (statusline runs from ~/.claude)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_TRACKER_SCRIPT="$PROJECT_ROOT/scripts/ccr_model_tracker.sh"
CCR_ACTUAL_MODEL=""
CCR_ROUTE_ALIAS=""
CCR_RESOLVED_TARGET=""
if [ -x "$MODEL_TRACKER_SCRIPT" ]; then
    CCR_ACTUAL_MODEL="$($MODEL_TRACKER_SCRIPT --statusline 2>/dev/null)"
    # Validate that we got a meaningful result
    if [ -z "$CCR_ACTUAL_MODEL" ] || [ "$CCR_ACTUAL_MODEL" = "LLM:" ]; then
        CCR_ACTUAL_MODEL=""
    fi

    CCR_ROUTE_ALIAS="$($MODEL_TRACKER_SCRIPT --route 2>/dev/null)"
    if [ -z "$CCR_ROUTE_ALIAS" ] || [ "$CCR_ROUTE_ALIAS" = "LLM:" ]; then
        CCR_ROUTE_ALIAS=""
    fi

    CCR_RESOLVED_TARGET="$($MODEL_TRACKER_SCRIPT --resolved 2>/dev/null)"
    if [ -z "$CCR_RESOLVED_TARGET" ] || [ "$CCR_RESOLVED_TARGET" = "LLM:" ]; then
        CCR_RESOLVED_TARGET=""
    fi
fi

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
        # Sonnet 4.5: Two variants exist
        # - Regular: 200K context (claude-sonnet-4-5-20250929)
        # - Extended: 1M context (indicated by JSON or model ID suffix)
        json_total=$(echo "$input" | jq -r '.context.total // .tokens.total // 0' 2>/dev/null)
        if [ "$json_total" -ge 1000000 ]; then
            # Extended context variant (1M)
            context_total=1000000
        elif [ "$json_total" -gt 200000 ] && [ "$json_total" -lt 1000000 ]; then
            # Use whatever JSON provides if it's between 200K and 1M
            context_total=$json_total
        else
            # Default to regular 200K variant
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

# Check for 200K+ token warning (Claude Code v1.0.88+)
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false' 2>/dev/null)

# Directory and git
dir=$(basename "$current_dir")
[ -z "$dir" ] && dir="~"

git_branch=""
if [ -d "$current_dir/.git" ]; then
    cd "$current_dir" 2>/dev/null
    git_branch=$(git branch --show-current 2>/dev/null)
fi

# Worktree indicator (show tree icon for multi-instance branches)
WORKTREE_ICON=""
if [ -n "${DOPEMUX_INSTANCE_ID:-}" ]; then
    WORKTREE_ICON=" 🌳"  # Tree for linked worktrees
fi

# Get enhanced PM/MCP/ADHD metrics from pm-status.sh (context-aware)
PM_STATUS_METRICS=""
if [ -f "$PROJECT_ROOT/scripts/pm-status.sh" ]; then
    PM_STATUS_METRICS=$("$PROJECT_ROOT/scripts/pm-status.sh" 2>/dev/null || echo "PM: Offline")
else
    PM_STATUS_METRICS="PM: Script Missing"
fi

# MCP Server Status (fast port checks with nc)
MCP_CONTEXT7="⚠️"   # 📚 Documentation (port 3002)
MCP_ZEN="⚠️"        # 🧠 Multi-model reasoning (port 3003)
MCP_SERENA="⚠️"     # 🔬 Code intelligence (port 3006)
MCP_DDG="⚠️"        # 📊 Decision Graph (port 3016)
MCP_DOPE="⚠️"       # 🔎 Semantic Search - via Qdrant (port 6333)
MCP_DESKTOP="⚠️"    # 🖥️ Context switching (port 3012)
MCP_ACTIVITY="⚠️"   # 🎯 Activity Capture (port 8096)

# Determine live port bases so multi-instance MCP clusters report accurately
declare -a MCP_PORT_BASES=()

add_port_base() {
    local base="$1"
    if [ -z "$base" ]; then
        return
    fi
    if ! [[ "$base" =~ ^[0-9]+$ ]]; then
        return
    fi
    for existing in "${MCP_PORT_BASES[@]}"; do
        if [ "$existing" = "$base" ]; then
            return
        fi
    done
    MCP_PORT_BASES+=("$base")
}

extract_port_base() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return
    fi
    local line
    line=$(grep -E 'DOPEMUX_PORT_BASE' "$file" 2>/dev/null | tail -1)
    if [ -z "$line" ]; then
        return
    fi
    line="${line#*=}"
    line="${line//\"/}"
    line="${line//\'/}"
    echo "$line"
}

add_port_base "${DOPEMUX_PORT_BASE:-}"
add_port_base "${PORT_BASE:-}"

env_port_base=$(extract_port_base "$PROJECT_ROOT/.dopemux/env/current.env")
add_port_base "$env_port_base"

sh_port_base=$(extract_port_base "$PROJECT_ROOT/.dopemux/env/current.sh")
add_port_base "$sh_port_base"

# Always include default + fallback bases so secondary instances still display
for fallback_base in 3000 3030 3060 3090 3120; do
    add_port_base "$fallback_base"
done

check_mcp_port() {
    local offset="$1"
    local base
    for base in "${MCP_PORT_BASES[@]}"; do
        local port=$((base + offset))
        if nc -z -w 1 localhost "$port" >/dev/null 2>&1; then
            echo "$port"
            return 0
        fi
    done
    return 1
}

# Fast port checks using nc (netcat) - now multi-instance aware
if context7_port=$(check_mcp_port 2); then MCP_CONTEXT7="📚"; fi
if zen_port=$(check_mcp_port 3); then MCP_ZEN="🧠"; fi
if serena_port=$(check_mcp_port 6); then MCP_SERENA="🔬"; fi
if ddg_port=$(check_mcp_port 16); then MCP_DDG="📊"; fi
if nc -z -w 1 localhost 6333 2>/dev/null; then MCP_DOPE="🔎"; fi
if desktop_port=$(check_mcp_port 12); then MCP_DESKTOP="🖥️"; fi
if nc -z -w 1 localhost 8096 2>/dev/null; then MCP_ACTIVITY="🎯"; fi

# ADHD Engine status is now handled by pm-status.sh integration above

# Build enhanced statusline with integrated PM metrics
if [ -n "$WORKSPACE_NAME" ]; then
    printf "\033[1;35m%s\033[0m " "$WORKSPACE_NAME"
fi
printf "\033[1;36m%s\033[0m" "$dir"

# Git branch + changes
if [ -n "$git_branch" ]; then
    printf " \033[33m%s%s\033[0m" "$git_branch" "$git_changes"
fi

# Worktree icon (if multi-instance)
if [ -n "$WORKTREE_ICON" ]; then
    printf "%s" "$WORKTREE_ICON"
fi

printf " \033[2m|\033[0m"

# Integrated PM/MCP/ADHD metrics from pm-status.sh (context-aware)
printf "%s" "$PM_STATUS_METRICS"

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

# Warning if exceeds 200K (Claude Code v1.0.88+)
if [ "$exceeds_200k" = "true" ]; then
    printf " \033[31m⚠️>200K\033[0m"
fi

# Model (Claude selection vs actual CCR/LiteLLM route)
model_display="$model_name"

# Use CCR-detected model (actual routed model) or fallback
if [ -n "$CCR_ACTUAL_MODEL" ]; then
    # Use CCR-detected model from logs/config
    model_display="$CCR_ACTUAL_MODEL"
else
    # Fallback: try to get more specific model info from JSON
    json_model_id=$(echo "$input" | jq -r '.model.id // ""' 2>/dev/null)
    if [ -n "$json_model_id" ] && [ "$json_model_id" != "null" ]; then
        case "$json_model_id" in
            *"sonnet-4-5"*|*"sonnet-4.5"*) model_display="Sonnet-4.5" ;;
            *"sonnet"*) model_display="Sonnet" ;;
            *"haiku"*) model_display="Haiku" ;;
            *"opus"*) model_display="Opus" ;;
            *) model_display="${model_name:-Sonnet}" ;;
        esac
    fi
fi

model_detail=""
if [ -n "$CCR_ROUTE_ALIAS" ] && [ -n "$CCR_RESOLVED_TARGET" ]; then
    model_detail="CCR ${CCR_ROUTE_ALIAS} -> LLM ${CCR_RESOLVED_TARGET}"
elif [ -n "$CCR_ROUTE_ALIAS" ]; then
    model_detail="CCR ${CCR_ROUTE_ALIAS}"
elif [ -n "$CCR_RESOLVED_TARGET" ]; then
    model_detail="LLM ${CCR_RESOLVED_TARGET}"
fi

printf " \033[2m|\033[0m \033[90m%s\033[0m" "$model_display"
if [ -n "$model_detail" ]; then
    printf " \033[2m(%s)\033[0m" "$model_detail"
fi
