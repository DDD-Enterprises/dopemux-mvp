#!/bin/bash
# ADHD Tmux Status Script
# Targets ADHD Engine (8001) and Serena (8003) for real-time status.

ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:8001}"
SERENA_URL="${SERENA_URL:-http://localhost:8003}"
ADHD_TMUX_EMOJI="${ADHD_TMUX_EMOJI:-true}"

# Fetch state with aggressive timeout
STATE=$(curl -s --connect-timeout 0.5 --max-time 1 \
    "${ADHD_ENGINE_URL}/api/v1/state?user_id=default" 2>/dev/null)

if [ -z "$STATE" ] || [ "$STATE" = "null" ]; then
    if [ "$ADHD_TMUX_EMOJI" = "true" ]; then
        echo "#[fg=red]🔌 ADHD offline#[default]"
    else
        echo "#[fg=red][OFFLINE]#[default]"
    fi
    exit 0
fi

# Parse JSON (jq required for complex logic)
if command -v jq &> /dev/null; then
    ENERGY=$(echo "$STATE" | jq -r '.energy_level // "medium"')
    ATTENTION=$(echo "$STATE" | jq -r '.attention_state // "focused"')
    LOAD=$(echo "$STATE" | jq -r '.cognitive_load // 0')
    FLOW=$(echo "$STATE" | jq -r '.flow_state.active // false')
else
    # Fallback to defaults if jq missing
    ENERGY="medium"
    ATTENTION="focused"
    LOAD="0.5"
    FLOW="false"
fi

# Format output
if [ "$ADHD_TMUX_EMOJI" = "true" ]; then
    # Energy Icon
    case "$ENERGY" in
        "high")   E_ICON="#[fg=#a6e3a1]⚡#[default]" ;; # Green
        "medium") E_ICON="#[fg=#89b4fa]🔋#[default]" ;; # Blue
        "low")    E_ICON="#[fg=#f38ba8]🪫#[default]" ;; # Red
        *)        E_ICON="❓" ;;
    esac
    
    # Attention Icon
    case "$ATTENTION" in
        "hyperfocus")   A_ICON="#[fg=#cba6f7]🔥#[default]" ;; # Mauve
        "focused")      A_ICON="#[fg=#a6e3a1]🧠#[default]" ;; # Green
        "distracted")   A_ICON="#[fg=#f9e2af]💨#[default]" ;; # Yellow
        "fatigued")     A_ICON="#[fg=#f38ba8]😴#[default]" ;; # Red
        *)              A_ICON="🧠" ;;
    esac

    # Flow State
    if [ "$FLOW" = "true" ]; then
        F_ICON="#[fg=#89dceb]🌊#[default] " # Sky
    else
        F_ICON=""
    fi

    # Cognitive Load (1-100%)
    LOAD_PCT=$(echo "$LOAD * 100" | bc 2>/dev/null | cut -d. -f1)
    if [ -z "$LOAD_PCT" ]; then LOAD_PCT="--"; fi
    
    echo "${F_ICON}${E_ICON} ${A_ICON} ${LOAD_PCT}%"
else
    echo "[${ENERGY}/${ATTENTION}]"
fi
